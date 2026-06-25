"""
Support for creating ecFlow suite definitions and ecf scripts.
"""

from __future__ import annotations

import json
import os
import random
import shutil
import signal
import socket
from copy import deepcopy
from pathlib import Path
from subprocess import CalledProcessError
from threading import Event, Thread, current_thread
from time import sleep
from typing import TYPE_CHECKING, cast

from ecflow import (  # type: ignore[import-untyped]
    Defs,
    DState,
    Family,
    Late,
    Node,
    RepeatDate,
    RepeatDateTime,
    RepeatDay,
    RepeatEnumerated,
    RepeatInteger,
    Suite,
    Task,
)

from uwtools.config.formats.yaml import YAMLConfig
from uwtools.config.validator import validate_internal
from uwtools.exceptions import UWConfigError, UWError, UWSSLCertificateError
from uwtools.logging import log
from uwtools.scheduler import JobScheduler
from uwtools.strings import STR
from uwtools.utils.file import writable
from uwtools.utils.processing import run_shell_cmd

ECFLOW_PORT_MIN = 1024  # minimum TCP port number accepted by ecFlow
ECFLOW_PORT_MAX = 49151  # maximum TCP port number accepted by ecFlow

if TYPE_CHECKING:
    from types import FrameType

    from ecflow import NodeContainer


class _ECFlowDef:
    """
    Generate an ecFlow definition file from a YAML config.
    """

    def __init__(self, config: dict | YAMLConfig | Path | None = None) -> None:
        log.debug("Creating ecFlow definition from %s", config or "stdin")
        cfgobj = config if isinstance(config, YAMLConfig) else YAMLConfig(config)
        cfgobj.dereference()
        validate(cfgobj)
        self._config = cfgobj.data[STR.ecflow][STR.suitedef]
        self._d = Defs()
        self._scheduler = self._config.get(STR.scheduler)
        self._scripts: dict[str, str] = {}
        log.debug("Adding workflow components to suite definition.")
        self._add_workflow_components()
        log.debug("Workflow components added. Scripts: %s", list(self._scripts.keys()))
        check_errors = self._d.check()
        assert not check_errors, check_errors

    def __str__(self):
        return self._d.__str__()

    def write_ecf_scripts(self, path: Path) -> None:
        """
        The ecf scripts for this workflow.

        :param path: Where to write the ecFlow scripts.
        """
        if self._scripts:
            for subpath, content in self._scripts.items():
                assert subpath.startswith("/")
                outpath = Path(str(path) + subpath).with_suffix(".ecf")
                outpath.parent.mkdir(parents=True, exist_ok=True)
                log.debug("Writing ecf script: %s", outpath)
                outpath.write_text(content + "\n")
        else:
            log.debug("No scripts are configured for this workflow.")

    def write_suite_definition(self, path: Path | None) -> None:
        """
        The suite definition artifact.

        :param path: Where to write the suite definition.
        """
        if path:
            log.debug("Creating output directory for suite definition: %s", path)
            path.mkdir(parents=True, exist_ok=True)
            path = path / "suite.def"
            log.debug("Writing suite definition to: %s", path)
        else:
            log.debug("No output path provided, writing the suite definition to stdout.")
        with writable(path) as f:
            print(str(self).rstrip("\n"), file=f)

    def _add_node(  # noqa: PLR0912
        self,
        config: dict,
        node: Node,
        parent: NodeContainer,
        refs: dict | None = None,
    ) -> None:
        """
        Add a suite|family|task (node) to a suite|family (parent).

        :param config: Configuration data for these components.
        :param node: The node to add to the parent.
        :param parent: The parent object to add this node to.
        :param refs: Optional references from expanded nodes from higher in the tree.
        """
        parent.add(node)
        add_items = lambda method, cfg: [method(*args) for args in cfg]
        for key, subconfig in config.items():
            tag, name = self._tag_name(key)
            match tag:
                # Tree buiding cases
                case STR.family:
                    self._add_node(subconfig, _node(Family, name), node, refs)
                case STR.families:
                    self._expand_block(subconfig, name, Family, node, refs)
                case STR.task:
                    self._add_node(subconfig, _node(Task, name), node, refs)
                case STR.tasks:
                    self._expand_block(subconfig, name, Task, node, refs)
                # Node attribute cases
                case STR.defstatus:
                    node.add_defstatus(getattr(DState, subconfig))
                case STR.events:
                    for event in subconfig:
                        if isinstance(event, list):
                            node.add_event(*event)
                        else:
                            node.add_event(event)
                case STR.inlimits:
                    add_items(node.add_inlimit, subconfig)
                case STR.labels:
                    add_items(node.add_label, subconfig)
                case STR.late:
                    node.add_late(Late(**subconfig))
                case STR.limits:
                    add_items(node.add_limit, subconfig)
                case STR.meters:
                    add_items(node.add_meter, subconfig)
                case STR.repeat:
                    self._add_repeat(subconfig, name, node)
                case STR.script:
                    self._prepare_ecf_script(subconfig, node)
                case STR.trigger:
                    node.add_trigger(subconfig)
                case STR.vars:
                    node.add_variable(subconfig)
                case STR.expand:
                    pass  # Already processed by _expand_block.
                case _:
                    msg = f"Unrecognized tag: {tag}"
                    raise AssertionError(msg)

    def _add_repeat(self, config: dict, name: str, node: Node) -> None:
        """
        Adds a repeat to a node.

        :param config: Configuration for the repeat.
        :param name: The name of the repeat.
        :param node: The node to add the repeat to.
        """
        match name:
            case STR.date:
                repeat = RepeatDate
            case STR.datelist | STR.enumerated | STR.string:
                repeat = RepeatEnumerated
            case STR.datetime:
                repeat = RepeatDateTime
            case STR.day:
                repeat = RepeatDay
            case STR.int:
                repeat = RepeatInteger
        # The schema-checked config blocks for each of these will be the variable and either the
        # start/end/[step] keys or the list key. Since they must be passed as positional arguments,
        # ensure their order is either (argument, start, end, [step]) or (argument, list).
        args = [
            config.get(k)
            for k in (STR.variable, STR.start, STR.end, STR.step, STR.list)
            if config.get(k) is not None
        ]
        node.add_repeat(repeat(*args))

    def _add_workflow_components(self) -> None:
        """
        Add suite(s) and other attributes to the suite definition.
        """
        for key, subconfig in self._config.items():
            tag, name = self._tag_name(key)
            match tag:
                case STR.extern:
                    for ext in subconfig:
                        self._d.add_extern(ext)
                case STR.vars:
                    self._d.add_variable(subconfig)
                case STR.suite:
                    self._add_node(subconfig, _node(Suite, name), self._d)
                case STR.suites:
                    self._expand_block(subconfig, name, Suite, self._d)

    def _expand_block(
        self,
        config: dict,
        name: str,
        nodetype: Node,
        parent: NodeContainer,
        refs: dict | None = None,
    ) -> None:
        """
        Expand a YAML block over a set of named Nodes.

        :param config: Configuration data for these components.
        :param name: Name of this suite.
        :param nodetype: The class of Node that needs expanding (Suite, Family, or Task)
        :param parent: The parent object to add this set of Nodes to.
        :param refs: Variable/value pairs used in higher-level expand blocks.
        """
        refs = refs if refs is not None else {}
        expand = config[STR.expand]
        # Check to make sure all lists are the same length.
        try:
            assert list(zip(*expand.values(), strict=True))
        except ValueError as e:
            msg = "All expand variables under %s must be the same length" % (parent.name())
            raise UWConfigError(msg) from e
        # Build up the new blocks in the suite definition.
        primary_variable = list(expand.keys())[0]
        for i in range(len(expand[primary_variable])):
            new_refs = deepcopy(refs)
            new_refs.update({k: v[i] for k, v in expand.items()})
            new_block = YAMLConfig({name: config}).dereference(context={"ec": new_refs})
            new_name = list(new_block.keys())[0]
            args = {
                STR.config: new_block[new_name],
                STR.node: _node(nodetype, new_name),
                STR.parent: parent,
                STR.refs: new_refs,
            }
            self._add_node(**args)

    def _prepare_ecf_script(self, config: dict, task: Task) -> None:
        """
        Prepare and store an ecf script to later write to disk.

        :param config: The configuration for the script.
        :param task: The ecFlow task node.
        """
        directives = ""
        if self._scheduler:
            props = {STR.scheduler: self._scheduler, **config[STR.batchargs]}
            scheduler = JobScheduler.get_scheduler(props)
            directives = "\n".join(scheduler.directives)
        fmt = lambda k: "\n".join(f"%include {x}" for x in config.get(STR.includes, {}).get(k, []))
        includes_entry, includes_exit = map(fmt, [STR.entry, STR.exit])
        sections = filter(None, [directives, includes_entry, "{body}", includes_exit])
        contents = "\n\n".join(sections).format(body=config[STR.body])
        self._scripts[task.get_abs_node_path()] = contents

    def _tag_name(self, key: str) -> tuple[str, str]:
        """
        Return the tag and metadata extracted from a metadata-bearing key.

        :param key: A string of the form "<tag>_<metadata>" (or simply STR.<tag>).
        :return: Tag and name of key.
        """
        # For example, key "task_foo_bar" will be split into tag "task" and name "foo_bar".
        parts = key.split("_", maxsplit=1)
        tag = parts[0]
        name = parts[1] if len(parts) > 1 else ""
        return tag, name


def realize(
    config: YAMLConfig | Path | None,
    output_path: Path | None = None,
    scripts_path: Path | None = None,
) -> str:
    """
    Realize the ecFlow suite defined in a given YAML as a Suite Definition and corresponding ecf
    scripts (if 'scripts_path' is provided).

    :param config: Path to YAML input file (None => read stdin), or YAMLConfig object.
    :param output_path: Path to write the rendered Suite Definition file (None => write to stdout).
    :param scripts_path: Path to write the rendered ecf scripts (None => do not write scripts).
    :return: Suite Definition as a string.
    """
    suite = _ECFlowDef(config)
    suite.write_suite_definition(output_path)
    if scripts_path:
        suite.write_ecf_scripts(scripts_path)
    return str(suite)


# Private helpers


_SSL_DIR = Path.home() / ".ecflowrc" / "ssl"
_SSL_KEY = "server.key"
_SSL_CERT = "server.crt"
_SSL_DHPARAM = "dh2048.pem"
_SSL_FILES = [_SSL_DHPARAM, _SSL_CERT, _SSL_KEY]


def _node(cls: type[Node], name: str) -> Node:
    try:
        return cls(name)
    except RuntimeError as e:
        raise UWConfigError(str(e)) from e


def _openssl() -> Path:
    """
    Return the absolute path to the openssl executable.

    :raises UWError: If openssl is not found on PATH.
    """
    path = shutil.which("openssl")
    if path is None:
        msg = "openssl not found on PATH"
        raise UWError(msg)
    return Path(path)


def _ssl_check(prefix: str | None) -> None:
    """
    Verify that the appropriate SSL certificate triplet exists in $HOME/.ecflowrc/ssl.

    The files comprising the triplet are <prefix>.{crt,key,pem} when 'prefix' is provided, otherwise
    the default files specified by _SSL_FILES.

    :param prefix: The <host>.<port> prefix identifying the certificate triplet.
    :raises UWSSLCertificateError: If one or more of the required files are missing.
    """
    fns = [f"{prefix}{ext}" for ext in (".crt", ".key", ".pem")] if prefix else _SSL_FILES
    paths = [_SSL_DIR / fn for fn in fns]
    if missing := [path for path in paths if not path.is_file()]:
        if _SSL_DIR.is_dir() or prefix:
            log.error("Missing SSL certificate file(s): %s", ", ".join(map(str, missing)))
        if _SSL_DIR.is_dir() and not prefix:
            log.error("Provide these files or remove %s to automatically generate", _SSL_DIR)
        raise UWSSLCertificateError
    log.info("Using SSL certificates %s in %s", ", ".join(fns), _SSL_DIR)


def _ssl_provision() -> None:
    """
    Provision SSL certificates in $HOME/.ecflowrc/ssl.

    :raises UWError: If or if certificate generation fails.
    """
    _SSL_DIR.mkdir(parents=True, exist_ok=True)
    _ssl_generate_key(_SSL_DIR / _SSL_KEY)
    _ssl_generate_cert(_SSL_DIR / _SSL_CERT, _SSL_DIR / _SSL_KEY)
    _ssl_generate_dhparam(_SSL_DIR / _SSL_DHPARAM)
    log.info("SSL certificate files written to %s", _SSL_DIR)


def _ssl_generate_cert(path: Path, key_path: Path) -> None:
    """
    Generate a self-signed X.509 certificate at 'path' using the key at 'key_path'.

    :param path: Destination for the certificate file.
    :param key_path: Path to the existing RSA private key.
    :raises UWError: If openssl reports failure.
    """
    hostname = socket.gethostname()
    log.info("Generating SSL certificate: %s", path)
    cmd = "umask 077 && %s req -x509 -key %s -new -out %s -days 3650 -subj /CN=%s" % (
        _openssl(),
        key_path,
        path,
        hostname,
    )
    success, _ = run_shell_cmd(cmd=cmd, quiet=True)
    if not success:
        msg = f"Failed to generate SSL certificate at {path}"
        raise UWError(msg)


def _ssl_generate_dhparam(path: Path) -> None:
    """
    Generate 2048-bit Diffie-Hellman parameters at 'path'.

    :param path: Destination for the DH parameters file.
    :raises UWError: If openssl reports failure.
    """
    log.info("Generating DH parameters: %s", path)
    cmd = "umask 077 && %s dhparam -out %s 2048" % (_openssl(), path)
    success, _ = run_shell_cmd(cmd=cmd, quiet=True)
    if not success:
        msg = f"Failed to generate DH parameters at {path}"
        raise UWError(msg)


def _ssl_generate_key(path: Path) -> None:
    """
    Generate a 2048-bit RSA private key (no password) at 'path'.

    :param path: Destination for the private key file.
    :raises UWError: If openssl reports failure.
    """
    log.info("Generating SSL private key: %s", path)
    cmd = "umask 077 && %s genrsa -out %s 2048" % (_openssl(), path)
    success, _ = run_shell_cmd(cmd=cmd, quiet=True)
    if not success:
        msg = f"Failed to generate SSL private key at {path}"
        raise UWError(msg)


class _ServerThread(Thread):
    """
    A thread that runs an ecFlow server, tracking the port in use and shutdown state.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.port: int | None = None
        self.terminal = Event()
        self.error: str | None = None


def server(
    config: dict | YAMLConfig | Path | None,
    port: int | None = None,
    insecure: bool = False,
    report: bool = False,
) -> None:
    """
    Start an ecFlow server on an available TCP port, optionally with SSL security enabled.

    The server runs in the foreground until interrupted (e.g. via CTRL-C), at which point it is shut
    down gracefully via 'ecflow_client --terminate'.

    :param config: A dict, a YAMLConfig, or a path to a YAML file providing server settings (None =>
        read stdin).
    :param port: TCP port to use (None => pick a random available port from the range
        ECFLOW_PORT_MIN through ECFLOW_PORT_MAX).
    :param insecure: Start the server without SSL security.
    :param report: Output server details (e.g. hostname, port) as JSON to stdout.
    :raises UWError: If the server fails to start.
    """
    cfg = YAMLConfig(config)
    cfg.dereference()
    validate(cfg)
    server_cfg = cfg.data[STR.ecflow][STR.server]
    # ECF_SSL in the YAML config can be: True (SSL on, default cert location), a <host>.<port>
    # prefix string selecting named certificates in $HOME/.ecflowrc/ssl, False (SSL off), or absent
    # (defaults to SSL on with auto-provisioned default certificates).
    ecf_ssl = server_cfg.get("ECF_SSL")
    ssl_on = not insecure and ecf_ssl is not False
    if ssl_on:
        try:
            _ssl_check(ecf_ssl)
        except UWSSLCertificateError:
            if ecf_ssl in [None, True]:
                _ssl_provision()
    rundir = Path(server_cfg["ECF_HOME"])
    # Exclude ECF_SSL from cfg_vars: it is handled explicitly below (it may be a bool in the YAML,
    # and ecFlow interprets any non-empty env string as an SSL flag or cert path).
    cfg_vars = {k: str(v) for k, v in server_cfg.items() if k != "ECF_SSL"}
    env = {**os.environ, **cfg_vars}
    if ssl_on:
        env["ECF_SSL"] = ecf_ssl if isinstance(ecf_ssl, str) else "1"
    else:
        # ecFlow enables SSL if ECF_SSL is set to any value, so unset it for an insecure server.
        env.pop("ECF_SSL", None)
    # Server variables to echo back when reporting: all config-supplied ECF_* values plus the
    # runtime-determined host and SSL setting. ECF_PORT is added once the port is known.
    report_vars = {**cfg_vars, "ECF_HOST": socket.gethostname()}
    if ssl_on:
        report_vars["ECF_SSL"] = ecf_ssl if isinstance(ecf_ssl, str) else "1"
    thread = _ServerThread(target=_server_start, args=[rundir, env, port, insecure])
    # ecflow_client must speak SSL to a secure server, else requests fail with a TLS mismatch.
    ssl_opt = "" if insecure else "--ssl "

    def shutdown(_signum: int, _frame: FrameType | None) -> None:
        log.info("Terminating")
        thread.terminal.set()
        if thread.port:
            cmd = "ecflow_client %s--port %s --terminate=yes" % (ssl_opt, thread.port)
            run_shell_cmd(cmd=cmd, quiet=True)

    signal.signal(signal.SIGINT, shutdown)
    thread.start()
    _server_wait(thread, ssl_opt=ssl_opt, report_vars=report_vars if report else None)
    thread.join()
    if thread.error:
        raise UWError(thread.error)


def _server_start(rundir: Path, env: dict[str, str], port: int | None, insecure: bool) -> None:
    """
    Thread target: launch ecflow_server, hunting for a free port if none was specified.

    The subprocess is placed in its own session (start_new_session=True) so that it does not
    receive the terminal's SIGINT; the main thread alone handles keyboard interrupts and shuts the
    server down gracefully. ('start_new_session' is preferred over 'preexec_fn', which the
    Python docs warn is unsafe in a multi-threaded process.)

    The run directory (ECF_HOME) is created if it does not already exist.

    :param rundir: Directory to run the server in (ECF_HOME).
    :param env: Base environment variables for the server.
    :param port: A specific port to use, or None to pick a random port from the range
        ECFLOW_PORT_MIN through ECFLOW_PORT_MAX.
    :param insecure: Start the server without SSL security.
    """
    thread = cast(_ServerThread, current_thread())
    fixed = port is not None
    # Create the run directory (ECF_HOME) on the user's behalf if it does not already exist.
    rundir.mkdir(parents=True, exist_ok=True)
    while not thread.terminal.is_set():
        # ecFlow accepts ports only in the registered range ECFLOW_PORT_MIN-ECFLOW_PORT_MAX.
        candidate = (
            port if fixed else random.randint(ECFLOW_PORT_MIN, ECFLOW_PORT_MAX)  # noqa: S311
        )
        log.debug("Trying to start server on port %s", candidate)
        thread.port = candidate
        try:
            cmd = "ecflow_server%s" % ("" if insecure else " --ssl")
            run_shell_cmd(cmd=cmd, cwd=rundir, env={**env, "ECF_PORT": str(candidate)}, quiet=True)
        except CalledProcessError as e:
            if "bind: Address already in use" in (e.stdout or ""):
                thread.port = None
                if fixed:
                    thread.terminal.set()
                    thread.error = f"Requested port {candidate} is unavailable"
                    return
                log.debug("Port %s already in use", candidate)
                continue
            thread.terminal.set()
            thread.error = f"ecflow_server failed on port {candidate}: {e.stdout}"
            for line in (e.stdout or "").split("\n"):
                log.error(line)
            return
        except OSError as e:
            # The server could not be launched at all, e.g. ecflow_server is not on PATH or the
            # run directory (ECF_HOME) does not exist. Set terminal so the waiter does not hang.
            thread.terminal.set()
            thread.error = f"Failed to launch ecflow_server: {e}"
            log.error(thread.error)
            return


def _server_wait(thread: _ServerThread, ssl_opt: str, report_vars: dict[str, str] | None) -> None:
    """
    Wait for the server to respond to a ping, then optionally report its details.

    :param thread: The running server thread.
    :param ssl_opt: ecflow_client SSL option ('--ssl' for secure servers, else the empty string).
    :param report_vars: Server variables to report as JSON once the server is up (None => do not
        report).
    """
    while not thread.terminal.is_set():
        if thread.port:
            cmd = f"ecflow_client {ssl_opt}--port {thread.port} --ping"
            success, _ = run_shell_cmd(cmd=cmd, quiet=True)
            if success:
                log.info("Server started on port %s", thread.port)
                if report_vars is not None:
                    _server_report(port=thread.port, report_vars=report_vars)
                break
        # Wait briefly before re-checking, so polling does not spin a CPU core or hammer
        # ecflow_client while the server starts up (or fails to).
        sleep(0.2)


def _server_report(port: int, report_vars: dict[str, str]) -> None:
    """
    Print ecFlow server details as JSON to stdout.

    :param port: The TCP port the server is using.
    :param report_vars: Server variables to report, exclusive of ECF_PORT.
    """
    vars_ = {**report_vars, "ECF_PORT": str(port)}
    # Flush so downstream consumers (e.g. a piped jq) see the report while the server runs, rather
    # than only when the block-buffered stream is flushed at server exit.
    print(json.dumps({"vars": vars_}, indent=2, sort_keys=True), flush=True)


def validate(config: dict | YAMLConfig | Path | None = None) -> bool:
    """
    Validate an ecFlow config against the internal ecFlow schema.

    :param config: A dict, a YAMLConfig, a path to a YAML file, or None (None => read stdin).
    :return: True if the config conforms to the schema.
    :raises: UWConfigError if validation fails.
    """
    kwargs: dict = {"schema_name": STR.ecflow, "desc": "ecFlow config"}
    if isinstance(config, (dict, YAMLConfig)):
        kwargs["config_data"] = config
    else:
        kwargs["config_path"] = config
    validate_internal(**kwargs)
    return True
