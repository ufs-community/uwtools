"""
Support for creating ecFlow suite definitions and ecf scripts.
"""

from __future__ import annotations

import json
import os
import random
import re
import signal
import socket
from copy import deepcopy
from pathlib import Path
from subprocess import STDOUT, CalledProcessError, check_output
from textwrap import dedent
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
from uwtools.exceptions import UWConfigError, UWError
from uwtools.logging import log
from uwtools.scheduler import JobScheduler
from uwtools.strings import EC, STR
from uwtools.utils.file import writable
from uwtools.utils.processing import run_shell_cmd

if TYPE_CHECKING:
    from types import FrameType

    from ecflow import NodeContainer


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
        self._config = cfgobj.data[EC.ecflow][EC.suitedef]
        self._scheduler = self._config.get(STR.scheduler)
        self._d = Defs()
        log.debug("Adding workflow components to suite definition.")
        self._add_workflow_components()
        log.debug("Workflow components added. Scripts: %s", list(self._scripts.keys()))
        check_errors = self._d.check()
        assert not check_errors, check_errors

    def __str__(self):
        return self._d.__str__()

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

                case EC.family:
                    self._add_node(subconfig, Family(name), node, refs)
                case EC.families:
                    self._expand_block(subconfig, name, Family, node, refs)
                case EC.task:
                    self._add_node(subconfig, Task(name), node, refs)
                case EC.tasks:
                    self._expand_block(subconfig, name, Task, node, refs)

                # Node attribute cases

                case EC.defstatus:
                    node.add_defstatus(getattr(DState, subconfig))
                case EC.events:
                    for event in subconfig:
                        if isinstance(event, list):
                            node.add_event(*event)
                        else:
                            node.add_event(event)
                case EC.inlimits:
                    add_items(node.add_inlimit, subconfig)
                case EC.labels:
                    add_items(node.add_label, subconfig)
                case EC.late:
                    node.add_late(Late(**subconfig))
                case EC.limits:
                    add_items(node.add_limit, subconfig)
                case EC.meters:
                    add_items(node.add_meter, subconfig)
                case EC.repeat:  # Only one repeat is allowed per node.
                    self._add_repeat(subconfig, name, node)
                case EC.script:
                    self._create_ecf_script(subconfig, node)
                case EC.trigger:  # Only one trigger is allowed per node.
                    node.add_trigger(subconfig)
                case EC.vars:  # add_variable accepts a dict.
                    node.add_variable(subconfig)
                case EC.expand:  # Already processed by _expand_block.
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
            case EC.date:
                repeat = RepeatDate
            case EC.datelist | EC.enumerated | EC.string:
                repeat = RepeatEnumerated
            case EC.datetime:
                repeat = RepeatDateTime
            case EC.day:
                repeat = RepeatDay
            case EC.int:
                repeat = RepeatInteger

        # The schema-checked config blocks for each of these will be the variable and either the
        # start/end/[step] keys or the list key. Since they must be passed as positional arguments,
        # ensure their order is either (argument, start, end, [step]) or (argument, list).
        args = [
            config.get(k)
            for k in (EC.variable, EC.start, EC.end, EC.step, EC.list)
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
                case EC.extern:
                    for ext in subconfig:
                        self._d.add_extern(ext)
                case EC.vars:
                    self._d.add_variable(subconfig)
                case EC.suite:
                    self._add_node(subconfig, Suite(name), self._d)
                case EC.suites:
                    self._expand_block(subconfig, name, Suite, self._d)

    def _create_ecf_script(self, config: dict, task: Task) -> None:
        """
        Write the ecf script for the task to disk.

        :param config: The configuration for the script.
        :param task: The task node.
        """
        scheduler = (
            self._jobscheduler(
                account=config.get(EC.account, ""),
                execution=config.get(EC.execution, ""),
                rundir=config.get(EC.rundir, ""),
            )
            if self._scheduler
            else None
        )
        execution = config[STR.execution]
        try:
            cmd = execution[EC.incantation]
        except KeyError as e:
            msg = "The execution block for %s must include 'incantation'" % task.name()
            raise UWConfigError(msg) from e
        script_contents = self._ecflowscript(
            execution=[cmd],
            manual=config.get(EC.manual, f"Script to run {task.name()}"),
            envcmds=execution.get(EC.envcmds, []),
            pre_includes=config.get(EC.pre_includes, []),
            post_includes=config.get(EC.post_includes, []),
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
        expand = config[EC.expand]

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
                EC.config: new_block[new_name],
                EC.node: nodetype(new_name),
                EC.parent: parent,
                EC.refs: new_refs,
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


def realize(
    config: YAMLConfig | Path | None,
    output_path: Path | None = None,
    scripts_path: Path | None = None,
) -> str:
    """
    Realize the ecFlow suite defined in a given YAML as a Suite Definition and corresponding ecf
    scripts (if ``scripts_path`` is provided).

    :param config: Path to YAML input file (None => read ``stdin``), or YAMLConfig object.
    :param output_path: Path to write the rendered Suite Definition file (None => write to
        ``stdout``).
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


def _provision_ssl(ssl_dir: Path = _SSL_DIR) -> None:
    """
    Ensure SSL certificates exist in ``$HOME/.ecflowrc/ssl``.

    If all required files exist, logs that they will be reused. If the directory exists but is
    missing one or more required files, logs an error and raises ``UWError``. If the directory does
    not exist, creates it and generates the required SSL files using ``openssl``.

    :param ssl_dir: Directory where SSL certificates are stored. Defaults to
        ``$HOME/.ecflowrc/ssl``.
    :raises UWError: If the SSL directory exists but is incomplete, or if certificate generation
        fails.
    """
    existing = [f for f in _SSL_FILES if (ssl_dir / f).exists()]
    if len(existing) == len(_SSL_FILES):
        log.info("Using existing SSL certificates in %s", ssl_dir)
        return
    if existing:
        missing = sorted(set(_SSL_FILES) - set(existing))
        msg = (
            f"SSL directory {ssl_dir} exists but is missing required file(s): {missing}. "
            "Provide all required files or remove the directory to allow regeneration."
        )
        raise UWError(msg)
    log.info("Creating SSL directory %s", ssl_dir)
    ssl_dir.mkdir(parents=True, exist_ok=True)
    _ssl_generate_key(ssl_dir / _SSL_KEY)
    _ssl_generate_cert(ssl_dir / _SSL_CERT, ssl_dir / _SSL_KEY)
    _ssl_generate_dhparam(ssl_dir / _SSL_DHPARAM)
    log.info("SSL credentials written to %s", ssl_dir)


def _ssl_touch(path: Path) -> None:
    """
    Create an empty file with owner-only (600) permissions.

    The file is created with restricted permissions before any content is written, so that sensitive
    key material is never exposed with open permissions.

    :param path: Path of the file to create.
    """
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.close(fd)
    path.chmod(0o600)


def _ssl_generate_key(path: Path) -> None:
    """
    Generate a 2048-bit RSA private key (no password) at ``path``.

    :param path: Destination for the private key file.
    :raises UWError: If ``openssl`` reports failure.
    """
    _ssl_touch(path)
    log.info("Generating SSL private key: %s", path)
    success, _ = run_shell_cmd(f"openssl genrsa -out {path} 2048")
    if not success:
        msg = f"Failed to generate SSL private key at {path}"
        raise UWError(msg)
    path.chmod(0o600)


def _ssl_generate_cert(path: Path, key_path: Path) -> None:
    """
    Generate a self-signed X.509 certificate at ``path`` using the key at ``key_path``.

    :param path: Destination for the certificate file.
    :param key_path: Path to the existing RSA private key.
    :raises UWError: If ``openssl`` reports failure.
    """
    hostname = socket.gethostname()
    _ssl_touch(path)
    log.info("Generating SSL certificate: %s", path)
    cmd = f"openssl req -x509 -key {key_path} -new -out {path} -days 3650 -subj '/CN={hostname}'"
    success, _ = run_shell_cmd(cmd)
    if not success:
        msg = f"Failed to generate SSL certificate at {path}"
        raise UWError(msg)
    path.chmod(0o600)


def _ssl_generate_dhparam(path: Path) -> None:
    """
    Generate 2048-bit Diffie-Hellman parameters at ``path``.

    This step can take several minutes.

    :param path: Destination for the DH parameters file.
    :raises UWError: If ``openssl`` reports failure.
    """
    _ssl_touch(path)
    log.info("Generating DH parameters (this may take a few minutes): %s", path)
    success, _ = run_shell_cmd(f"openssl dhparam -out {path} 2048")
    if not success:
        msg = f"Failed to generate DH parameters at {path}"
        raise UWError(msg)
    path.chmod(0o600)


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
    config: dict | YAMLConfig | Path | None = None,
    port: int | None = None,
    insecure: bool = False,
    report: bool = False,
) -> None:
    """
    Start an ecFlow server on an available TCP port, optionally with SSL security enabled.

    The server runs in the foreground until interrupted (e.g. via CTRL-C), at which point it is
    shut down gracefully via ``ecflow_client --terminate``.

    :param config: A ``dict``, a ``YAMLConfig``, or a path to a YAML file providing server settings
        (``None`` => read ``stdin``).
    :param port: TCP port to use (``None`` => pick a random available port from 1024-49151).
    :param insecure: Start the server without SSL security.
    :param report: Output server details (e.g. hostname, port) as JSON to ``stdout``.
    :raises UWError: If the server fails to start.
    """
    cfg = YAMLConfig(config)
    cfg.dereference()
    validate(cfg)
    server_cfg = cfg.data[EC.ecflow][EC.server]
    if not insecure:
        _provision_ssl()
    rundir = Path(server_cfg["ECF_HOME"])
    cfg_vars = {k: str(v) for k, v in server_cfg.items()}
    env = {**os.environ, **cfg_vars}
    if insecure:
        # ecFlow enables SSL if ECF_SSL is set to any value, so unset it for an insecure server.
        env.pop("ECF_SSL", None)
    else:
        env["ECF_SSL"] = "1"
    # Server variables to echo back when reporting: all config-supplied ECF_* values plus the
    # runtime-determined host and SSL setting. ECF_PORT is added once the port is known.
    report_vars = {**cfg_vars, "ECF_HOST": socket.gethostname()}
    if not insecure:
        report_vars["ECF_SSL"] = "1"
    thread = _ServerThread(target=_server_start, args=[rundir, env, port, insecure])
    # ecflow_client must speak SSL to a secure server, else requests fail with a TLS mismatch.
    ssl_opt = "" if insecure else "--ssl "

    def shutdown(_signum: int, _frame: FrameType | None) -> None:
        log.info("Terminating")
        thread.terminal.set()
        if thread.port:
            run_shell_cmd(
                cmd=f"ecflow_client {ssl_opt}--port {thread.port} --terminate=yes", quiet=True
            )

    signal.signal(signal.SIGINT, shutdown)
    thread.start()
    _server_wait(thread, ssl_opt=ssl_opt, report_vars=report_vars if report else None)
    thread.join()
    if thread.error:
        raise UWError(thread.error)


def _server_start(rundir: Path, env: dict[str, str], port: int | None, insecure: bool) -> None:
    """
    Thread target: launch ``ecflow_server``, hunting for a free port if none was specified.

    The subprocess is placed in its own session (``start_new_session=True``) so that it does not
    receive the terminal's SIGINT; the main thread alone handles keyboard interrupts and shuts the
    server down gracefully. (``start_new_session`` is preferred over ``preexec_fn``, which the
    Python docs warn is unsafe in a multi-threaded process.)

    :param rundir: Directory to run the server in (``ECF_HOME``).
    :param env: Base environment variables for the server.
    :param port: A specific port to use, or ``None`` to pick a random port (1024-49151).
    :param insecure: Start the server without SSL security.
    """
    thread = cast(_ServerThread, current_thread())
    fixed = port is not None
    cmd = ["ecflow_server", *([] if insecure else ["--ssl"])]
    while not thread.terminal.is_set():
        # ecFlow accepts ports only in the registered range 1024-49151.
        candidate = port if fixed else random.randint(1024, 49151)  # noqa: S311
        log.debug("Trying to start server on port %s", candidate)
        thread.port = candidate
        try:
            check_output(  # noqa: S603
                cmd,
                cwd=rundir,
                encoding="utf-8",
                env={**env, "ECF_PORT": str(candidate)},
                start_new_session=True,
                stderr=STDOUT,
                text=True,
            )
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
    :param ssl_opt: ``ecflow_client`` SSL option (``"--ssl "`` for secure servers, else ``""``).
    :param report_vars: Server variables to report as JSON once the server is up (``None`` => do
        not report).
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
    Print ecFlow server details as JSON to ``stdout``.

    :param port: The TCP port the server is using.
    :param report_vars: Server variables to report, exclusive of ``ECF_PORT``.
    """
    vars_ = {**report_vars, "ECF_PORT": str(port)}
    # Flush so downstream consumers (e.g. a piped jq) see the report while the server runs, rather
    # than only when the block-buffered stream is flushed at server exit.
    print(json.dumps({"vars": vars_}, indent=2, sort_keys=True), flush=True)


def validate(config: dict | YAMLConfig | Path | None = None) -> bool:
    """
    Validate an ecFlow config against the internal ecFlow schema.

    :param config: A ``dict``, a ``YAMLConfig``, a path to a YAML file, or ``None``
        (``None`` => read ``stdin``).
    :return: ``True`` if the config conforms to the schema.
    :raises: ``UWConfigError`` if validation fails.
    """
    kwargs: dict = {"schema_name": EC.ecflow, "desc": "ecFlow config"}
    if isinstance(config, (dict, YAMLConfig)):
        kwargs["config_data"] = config
    else:
        kwargs["config_path"] = config
    validate_internal(**kwargs)
    return True
