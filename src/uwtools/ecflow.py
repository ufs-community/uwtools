"""
Support for creating ecFlow suite definitions and ecf scripts.
"""

from __future__ import annotations

import json
import os
import random
import re
import shutil
import signal
import socket
from copy import deepcopy
from functools import cache
from pathlib import Path
from subprocess import CalledProcessError, Popen
from textwrap import dedent
from threading import Event, Thread, current_thread
from time import sleep
from typing import TYPE_CHECKING, cast

from ecflow import (  # type: ignore[import-untyped]
    Client,
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

if TYPE_CHECKING:
    from types import FrameType

    from ecflow import NodeContainer


# Public

ECFLOW_PORT_MIN = 1024  # minimum TCP port number accepted by ecFlow
ECFLOW_PORT_MAX = 49151  # maximum TCP port number accepted by ecFlow


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


def server(
    config: dict | YAMLConfig | Path | None,
    port: int | None = None,
    insecure: bool = False,
    report: bool = False,
) -> None:
    """
    Start an ecFlow server, optionally with SSL security enabled.

    The server runs in the foreground until interrupted (e.g. via CTRL-C), then terminated.

    :param config: Config providing server settings (None => read stdin).
    :param port: TCP port to use (None => random port between ECFLOW_PORT_MIN and ECFLOW_PORT_MAX).
    :param insecure: Start the server without SSL security.
    :param report: Output server details (e.g. hostname, port) as JSON to stdout.
    :raises UWError: If the server fails to start.
    """

    def shutdown(_signum: int, _frame: FrameType | None) -> None:
        log.info("Terminating")
        thread.terminal.set()
        proc = cast(Popen, thread.proc)
        proc.send_signal(signal.SIGINT)
        proc.wait()

    config = YAMLConfig(config)
    config.dereference()
    validate(config)
    server_cfg = config.data[STR.ecflow][STR.server]
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
    signal.signal(signal.SIGINT, shutdown)
    thread.start()
    _server_wait(thread, insecure, report_vars if report else None)
    thread.join()
    if thread.error:
        raise UWError(thread.error)


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


# Private

_SSL_DIR = Path.home() / ".ecflowrc" / "ssl"
_SSL_KEY = "server.key"
_SSL_CERT = "server.crt"
_SSL_DHPARAM = "dh2048.pem"
_SSL_FILES = [_SSL_DHPARAM, _SSL_CERT, _SSL_KEY]


class _ECFlowDef:
    """
    Generate an ecFlow definition file from a YAML config.
    """

    def __init__(self, config: dict | YAMLConfig | Path | None = None) -> None:
        self._scripts: dict[Path, str] = {}
        log.debug("Creating ecFlow definition from %s", config or "stdin")
        cfgobj = config if isinstance(config, YAMLConfig) else YAMLConfig(config)
        cfgobj.dereference()
        validate(cfgobj)
        self._config = cfgobj.data[STR.ecflow][STR.suitedef]
        self._scheduler = self._config.get(STR.scheduler)
        self._d = Defs()
        log.debug("Adding workflow components to suite definition.")
        self._add_workflow_components()
        log.debug("Workflow components added. Scripts: %s", list(self._scripts.keys()))
        check_errors = self._d.check()
        assert not check_errors, check_errors

    def __str__(self):
        return self._d.__str__()

    # Public

    def write_ecf_scripts(self, path: Path | str) -> None:
        """
        The ecf scripts for this workflow.

        :param path: Where to write the ecFlow scripts.
        """

        if not self._scripts:
            log.warning("No scripts are configured for this workflow.")
            return

        log.debug("Writing ecf scripts to %s", path)
        for subpath, content in self._scripts.items():
            outpath = Path(path) / subpath
            outpath.parent.mkdir(parents=True, exist_ok=True)
            log.debug("Writing script: %s", outpath)
            outpath.write_text(content)

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

    # Private

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
                case STR.repeat:  # Only one repeat is allowed per node.
                    self._add_repeat(subconfig, name, node)
                case STR.script:
                    self._create_ecf_script(subconfig, node)
                case STR.trigger:  # Only one trigger is allowed per node.
                    node.add_trigger(subconfig)
                case STR.vars:  # add_variable accepts a dict.
                    node.add_variable(subconfig)
                case STR.expand:  # Already processed by _expand_block.
                    pass
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

    def _create_ecf_script(self, config: dict, task: Task) -> None:
        """
        Write the ecf script for the task to disk.

        :param config: The configuration for the script.
        :param task: The task node.
        """
        scheduler = (
            self._jobscheduler(
                account=config.get(STR.account, ""),
                execution=config.get(STR.execution, ""),
                rundir=config.get(STR.rundir, ""),
            )
            if self._scheduler
            else None
        )
        execution = config[STR.execution]
        try:
            cmd = execution[STR.incantation]
        except KeyError as e:
            msg = "The execution block for %s must include 'incantation'" % task.name()
            raise UWConfigError(msg) from e
        script_contents = self._ecflowscript(
            execution=[cmd],
            manual=config.get(STR.manual, f"Script to run {task.name()}"),
            envcmds=execution.get(STR.envcmds, []),
            pre_includes=config.get(STR.pre_includes, []),
            post_includes=config.get(STR.post_includes, []),
            scheduler=scheduler,
        )

        path = (
            Path(task.get_abs_node_path().lstrip("/")).parent
            / f"{task.name().split('_', 1)[-1]}.ecf"
        )
        self._scripts[path] = script_contents

    def _ecflowscript(
        self,
        execution: list[str],
        manual: str,
        envcmds: list[str] | None = None,
        envvars: dict[str, str] | None = None,
        pre_includes: list[str] | None = None,
        post_includes: list[str] | None = None,
        scheduler: JobScheduler | None = None,
    ) -> str:
        """
        Return a driver ecFlow script.

        :param execution: Statements to execute.
        :param manual: A brief explanation of purpose of script.
        :param envcmds: Shell commands to set up runtime environment.
        :param envvars: Environment variables to set in runtime environment.
        :param pre_includes: Names of scripts to be included before execution.
        :param post_includes: Names of scripts to be included after execution.
        :param scheduler: A configured job-scheduler object.
        """
        template = """
        {directives}

        model=%MODEL%

        {pre_includes}

        {envcmds}

        {envvars}

        {execution}
        if [[ $? -ne 0 ]]; then
           ecflow_client --msg="***JOB ${ECF_NAME} ERROR RUNNING J-SCRIPT ***"
           ecflow_client --abort
           exit 1
        fi

        {post_includes}

        %manual
        {manual}
        %end
        """
        pre_includes = pre_includes or []
        post_includes = post_includes or []
        directives = scheduler.directives if scheduler else ""
        initcmds = scheduler.initcmds if scheduler else [""]
        rs = dedent(template).format(
            directives="\n".join(directives),
            envcmds="\n".join(envcmds or []),
            envvars="\n".join([f"export {k}={v}" for k, v in (envvars or {}).items()]),
            execution="\n".join([*initcmds, *execution]),
            manual=manual,
            pre_includes="\n".join([f"%include <{inc}>" for inc in pre_includes]),
            post_includes="\n".join([f"%include <{inc}>" for inc in post_includes]),
            ECF_NAME="ECF_NAME",
        )
        return re.sub(r"\n\n\n+", "\n\n", rs.strip()) + "\n"

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

    def _jobscheduler(self, account: str, execution: dict, rundir: Path | str) -> JobScheduler:
        """
        Use the execution block to build a JobScheduler object.

        :param account: The user account for the batch system.
        :param execution: The standard UW YAML execution block.
        :param rundir: The directory where the task will run.
        """
        threads = execution.get(STR.threads)
        resources = {
            STR.account: account,
            STR.rundir: rundir,
            STR.scheduler: self._scheduler,
            STR.stdout: "%s.out" % Path(rundir),
            **({STR.threads: threads} if threads else {}),
            **execution.get(STR.batchargs, {}),
        }
        return JobScheduler.get_scheduler(resources)

    def _tag_name(self, key: str) -> tuple[str, str]:
        """
        Return the tag and metadata extracted from a metadata-bearing key.

        :param key: A string of the form "<tag>_<metadata>" (or simply STR.<tag>).
        :return: Tag and name of key.
        """
        # For example, key "task_foo_bar" will be split into tag "task" and name "foo_bar".
        parts = key.split("_")
        tag = parts[0]
        name = "_".join(parts[1:]) if parts[1:] else ""
        return tag, name


class _ServerThread(Thread):
    """
    A thread that runs an ecFlow server, tracking the port in use and shutdown state.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.error: str | None = None
        self.port: int | None = None
        self.proc: Popen | None = None
        self.terminal = Event()


@cache
def _client(port: int, insecure: bool) -> Client:
    """
    Returns an ecFlow client, optionally with SSL enabled.

    :param port: TCP port to use.
    :param insecure: Start the server without SSL security.
    """
    hostname = socket.gethostname()
    c = Client(hostname, str(port))
    if not insecure:
        c.enable_ssl()
    return c


def _node(cls: type[Node], name: str) -> Node:
    """
    Returns an ecFlow suite-definition node of the given type, with the given name.

    :param cls: The ecFlow suite-definiton class to instantiate.
    :param name: The name of the node.
    """
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


def _server_report(port: int, report_vars: dict[str, str] | None) -> None:
    """
    Print ecFlow server details as JSON to stdout.

    :param port: The TCP port the server is using.
    :param report_vars: Server variables to report, exclusive of ECF_PORT.
    """
    if report_vars:
        vars_ = {**report_vars, "ECF_PORT": str(port)}
        # Flush so downstream consumers (e.g. a piped jq) see the report while the server runs,
        # rather than only when the block-buffered stream is flushed at server exit.
        print(json.dumps({"vars": vars_}, indent=2, sort_keys=True), flush=True)


def _server_start(rundir: Path, env: dict[str, str], port: int | None, insecure: bool) -> None:
    """
    Thread target: launch ecflow_server, hunting for a free port if none was specified.

    :param rundir: Directory to run the server in (ECF_HOME).
    :param env: Base environment variables for the server.
    :param port: TCP port to use (None => random port between ECFLOW_PORT_MIN and ECFLOW_PORT_MAX).
    :param insecure: Start the server without SSL security.
    """

    def complain(error: str, messages: str | None = None) -> None:
        thread.terminal.set()
        thread.error = error
        if messages:
            for line in messages.split("\n"):
                log.error(line)

    rundir.mkdir(parents=True, exist_ok=True)
    thread = cast(_ServerThread, current_thread())
    callback = lambda proc: setattr(thread, "proc", proc)
    static = port is not None
    while not thread.terminal.is_set():
        port = port if static else random.randint(ECFLOW_PORT_MIN, ECFLOW_PORT_MAX)  # noqa: S311
        thread.port = port
        parts = ["ecflow_server", "--port", str(port), None if insecure else "--ssl"]
        cmd = list(filter(None, parts))
        log.debug("Trying to start server on port %s", port)
        try:
            run_shell_cmd(cmd=cmd, cwd=rundir, env=env, quiet=True, callback=callback)
        except CalledProcessError as e:
            thread.port = None
            if "bind: Address already in use" in (e.stdout or ""):
                if static:
                    complain(f"Requested port {port} is unavailable")
                else:
                    log.debug("Port %s already in use", port)
                    continue  # try next random port
            else:
                complain(f"ecflow_server failed on port {port}: {e.stdout}", e.stdout or "")
        except OSError as e:
            complain(f"Failed to launch ecflow_server: {e}", thread.error)
        break


def _server_wait(thread: _ServerThread, insecure: bool, report_vars: dict[str, str] | None) -> None:
    """
    Wait for the server to respond to a ping, then optionally report its details.

    :param thread: The running server thread.
    :param insecure: Do not use SSL.
    :param report_vars: Server variables to report as JSON (None => do not report).
    """
    while not thread.terminal.is_set():
        port = thread.port
        if port:
            try:
                _client(port, insecure).ping()
            except RuntimeError as e:
                if "Failed to connect" not in str(e):
                    raise
            else:
                log.info("Server started on port %s", port)
                _server_report(port, report_vars)
                break
        sleep(0.2)


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
