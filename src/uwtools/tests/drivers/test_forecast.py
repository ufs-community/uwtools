# pylint: disable=missing-class-docstring, missing-function-docstring,protected-access,redefined-outer-name
"""
Tests for forecast driver.
"""
import datetime as dt
import logging
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from pytest import fixture, raises

from uwtools import scheduler
from uwtools.config.core import NMLConfig, YAMLConfig
from uwtools.config.j2template import J2Template
from uwtools.drivers import forecast
from uwtools.drivers.driver import Driver
from uwtools.drivers.forecast import FV3Forecast, MPASForecast
from uwtools.tests.support import compare_files, fixture_path
from uwtools.utils.file import readable, writable


class TestForecast:
    def test_batch_script(self):
        expected = """
#SBATCH --account=user_account
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --qos=batch
#SBATCH --time=00:01:00
KMP_AFFINITY=scatter
OMP_NUM_THREADS=1
OMP_STACKSIZE=512m
MPI_TYPE_DEPTH=20
ESMF_RUNTIME_COMPLIANCECHECK=OFF:depth=4
srun --export=NONE test_exec.py
""".strip()
        config_file = fixture_path("forecast.yaml")
        with patch.object(Driver, "_validate", return_value=True):
            forecast = FV3Forecast(config_file=config_file)
        assert forecast.batch_script().content() == expected


class TestFV3Forecast:
    def test_create_directory_structure(self, tmp_path):
        """
        Tests create_directory_structure method given a directory.
        """

        rundir = tmp_path / "rundir"

        # Test delete behavior when run directory does not exist.
        FV3Forecast.create_directory_structure(rundir, "delete")
        assert (rundir / "RESTART").is_dir()

        # Create a file in the run directory.
        test_file = rundir / "test.txt"
        test_file.touch()
        assert test_file.is_file()

        # Test delete behavior when run directory exists. Test file should be gone
        # since old run directory was deleted.
        FV3Forecast.create_directory_structure(rundir, "delete")
        assert (rundir / "RESTART").is_dir()
        assert not test_file.is_file()

        # Test rename behavior when run directory exists.
        FV3Forecast.create_directory_structure(rundir, "rename")
        copy_directory = next(tmp_path.glob("%s_*" % rundir.name))
        assert (copy_directory / "RESTART").is_dir()

        # Test quit behavior when run directory exists.
        with raises(SystemExit) as pytest_wrapped_e:
            FV3Forecast.create_directory_structure(rundir, "quit")
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 1

    @fixture
    def create_field_table_update_obj(self):
        return YAMLConfig(fixture_path("FV3_GFS_v16_update.yaml"))

    def test_create_field_table_with_base_file(self, create_field_table_update_obj, tmp_path):
        """
        Tests create_field_table method with optional base file.
        """
        base_file = fixture_path("FV3_GFS_v16.yaml")
        outfldtbl_file = tmp_path / "field_table_two.FV3_GFS"
        expected = fixture_path("field_table_from_base.FV3_GFS")
        config_file = tmp_path / "fcst.yaml"
        forecast_config = create_field_table_update_obj
        forecast_config["forecast"]["field_table"]["base_file"] = base_file
        forecast_config.dump(config_file)
        FV3Forecast(config_file).create_field_table(outfldtbl_file)
        assert compare_files(expected, outfldtbl_file)

    def test_create_field_table_without_base_file(self, tmp_path):
        """
        Tests create_field_table without optional base file.
        """
        outfldtbl_file = tmp_path / "field_table_one.FV3_GFS"
        expected = fixture_path("field_table_from_input.FV3_GFS")
        config_file = fixture_path("FV3_GFS_v16_update.yaml")
        FV3Forecast(config_file).create_field_table(outfldtbl_file)
        assert compare_files(expected, outfldtbl_file)

    def test_create_model_configure(self, tmp_path):
        """
        Test that providing a YAML base input file and a config file will create and update YAML
        config file.
        """

        config_file = fixture_path("fruit_config_similar_for_fcst.yaml")
        base_file = fixture_path("fruit_config.yaml")
        fcst_config_file = tmp_path / "fcst.yml"

        fcst_config = YAMLConfig(config_file)
        fcst_config["forecast"]["model_configure"]["base_file"] = base_file
        fcst_config.dump(fcst_config_file)

        output_file = (tmp_path / "test_config_from_yaml.yaml").as_posix()
        with patch.object(FV3Forecast, "_validate", return_value=True):
            forecast_obj = FV3Forecast(config_file=fcst_config_file)
        cycle = dt.datetime.now()
        date_values = {
            "start_year": cycle.strftime("%Y"),
            "start_month": cycle.strftime("%m"),
            "start_day": cycle.strftime("%d"),
            "start_hour": cycle.strftime("%H"),
            "start_minute": cycle.strftime("%M"),
            "start_second": cycle.strftime("%S"),
        }
        forecast_obj.create_model_configure(cycle, output_file)
        expected = YAMLConfig(base_file)
        expected.update_values(
            YAMLConfig(config_file)["forecast"]["model_configure"]["update_values"]
        )
        expected.update_values(date_values)
        expected_file = tmp_path / "expected_yaml.yaml"
        expected.dump(expected_file)
        assert compare_files(expected_file, output_file)

    def test_create_model_configure_call_private(self, tmp_path):
        basefile = str(tmp_path / "base.yaml")
        infile = fixture_path("forecast.yaml")
        outfile = str(tmp_path / "out.yaml")
        cycle = dt.datetime.now()
        for path in infile, basefile:
            Path(path).touch()
        with patch.object(Driver, "_create_user_updated_config") as _create_user_updated_config:
            with patch.object(FV3Forecast, "_validate", return_value=True):
                with patch.object(forecast, "YAMLConfig") as YAMLConfig:
                    FV3Forecast(config_file=infile).create_model_configure(cycle, outfile)
        _create_user_updated_config.assert_called_with(
            config_class=YAMLConfig, config_values={}, output_path=outfile
        )

    @fixture
    def create_namelist_assets(self, tmp_path):
        return NMLConfig(fixture_path("simple.nml")), tmp_path / "create_out.nml"

    def test_create_namelist_call_private(self, tmp_path):
        basefile = str(tmp_path / "base.yaml")
        infile = fixture_path("forecast.yaml")
        outfile = str(tmp_path / "out.yaml")
        for path in infile, basefile:
            Path(path).touch()
        with patch.object(Driver, "_create_user_updated_config") as _create_user_updated_config:
            with patch.object(FV3Forecast, "_validate", return_value=True):
                # pylint: disable=unused-variable
                with patch.object(forecast, "YAMLConfig") as YAMLConfig:
                    FV3Forecast(config_file=infile).create_namelist(outfile)
        _create_user_updated_config.assert_called_with(
            config_class=NMLConfig, config_values={}, output_path=outfile
        )

    def test_create_namelist_with_base_file(self, create_namelist_assets, tmp_path):
        """
        Tests create_namelist method with optional base file.
        """
        update_obj, outnml_file = create_namelist_assets
        base_file = fixture_path("simple3.nml")
        fcst_config = {
            "forecast": {
                "namelist": {
                    "base_file": base_file,
                    "update_values": update_obj.data,
                },
            },
        }
        fcst_config_file = tmp_path / "fcst.yml"
        YAMLConfig.dump_dict(cfg=fcst_config, path=fcst_config_file)
        FV3Forecast(fcst_config_file).create_namelist(outnml_file)
        expected = """
&salad
    base = 'kale'
    fruit = 'banana'
    vegetable = 'tomato'
    how_many = 12
    dressing = 'balsamic'
    toppings = ,
    extras = 0
    dessert = .false.
    appetizer = ,
/
""".lstrip()
        with open(outnml_file, "r", encoding="utf-8") as out_file:
            assert out_file.read() == expected

    def test_create_namelist_without_base_file(self, create_namelist_assets, tmp_path):
        """
        Tests create_namelist method without optional base file.
        """
        update_obj, outnml_file = create_namelist_assets
        fcst_config = {
            "forecast": {
                "namelist": {
                    "update_values": update_obj.data,
                },
            },
        }
        fcst_config_file = tmp_path / "fcst.yml"
        YAMLConfig.dump_dict(cfg=fcst_config, path=fcst_config_file)
        FV3Forecast(fcst_config_file).create_namelist(outnml_file)
        expected = """
&salad
    base = 'kale'
    fruit = 'banana'
    vegetable = 'tomato'
    how_many = 12
    dressing = 'balsamic'
/
""".lstrip()
        with open(outnml_file, "r", encoding="utf-8") as out_file:
            assert out_file.read() == expected

    def test_forecast_run_cmd(self):
        """
        Tests that the command to be used to run the forecast executable was built successfully.
        """
        config_file = fixture_path("forecast.yaml")
        with patch.object(FV3Forecast, "_validate", return_value=True):
            fcstobj = FV3Forecast(config_file=config_file)
            srun_expected = "srun --export=NONE test_exec.py"
            fcstobj._config["runtime_info"]["mpi_args"] = ["--export=NONE"]
            assert srun_expected == fcstobj.run_cmd()
            mpirun_expected = "mpirun -np 4 test_exec.py"
            fcstobj._experiment_config["platform"]["mpicmd"] = "mpirun"
            fcstobj._config["runtime_info"]["mpi_args"] = ["-np", 4]
            assert mpirun_expected == fcstobj.run_cmd()
            fcstobj._experiment_config["platform"]["mpicmd"] = "mpiexec"
            fcstobj._config["runtime_info"]["mpi_args"] = [
                "-n",
                4,
                "-ppn",
                8,
                "--cpu-bind",
                "core",
                "-depth",
                2,
            ]
            mpiexec_expected = "mpiexec -n 4 -ppn 8 --cpu-bind core -depth 2 test_exec.py"
            assert mpiexec_expected == fcstobj.run_cmd()

    @fixture
    def fv3_mpi_assets(self):
        return [
            "KMP_AFFINITY=scatter",
            "OMP_NUM_THREADS=1",
            "OMP_STACKSIZE=512m",
            "MPI_TYPE_DEPTH=20",
            "ESMF_RUNTIME_COMPLIANCECHECK=OFF:depth=4",
            "srun --export=NONE test_exec.py",
        ]

    @fixture
    def fv3_run_assets(self, tmp_path):
        batch_script = tmp_path / "batch.sh"
        config_file = fixture_path("forecast.yaml")
        config = YAMLConfig(config_file)
        config["forecast"]["run_dir"] = tmp_path.as_posix()
        config["forecast"]["cycle-dependent"] = {"foo-file": str(tmp_path / "foo")}
        config["forecast"]["static"] = {"static-foo-file": str(tmp_path / "foo")}
        return batch_script, config_file, config.data["forecast"]

    def test_run_direct(self, fv3_mpi_assets, fv3_run_assets):
        _, config_file, config = fv3_run_assets
        expected_command = " ".join(fv3_mpi_assets)
        with patch.object(FV3Forecast, "_validate", return_value=True):
            with patch.object(forecast, "execute") as execute:
                fcstobj = FV3Forecast(config_file=config_file)
                with patch.object(fcstobj, "_config", config):
                    fcstobj.run(cycle=dt.datetime.now())
                execute.assert_called_once_with(cmd=expected_command)

    @pytest.mark.parametrize("with_batch_script", [True, False])
    def test_run_dry_run(self, capsys, fv3_mpi_assets, fv3_run_assets, with_batch_script):
        logging.getLogger().setLevel(logging.INFO)
        batch_script, config_file, config = fv3_run_assets
        if with_batch_script:
            batch_components = [
                "#!/bin/bash",
                "#SBATCH --account=user_account",
                "#SBATCH --nodes=1",
                "#SBATCH --ntasks-per-node=1",
                "#SBATCH --qos=batch",
                "#SBATCH --time=00:01:00",
            ] + fv3_mpi_assets
            run_expected = "\n".join(batch_components)
        else:
            batch_script = None
            run_expected = " ".join(fv3_mpi_assets)

        with patch.object(FV3Forecast, "_validate", return_value=True):
            fcstobj = FV3Forecast(config_file=config_file, dry_run=True, batch_script=batch_script)
            with patch.object(fcstobj, "_config", config):
                fcstobj.run(cycle=dt.datetime.now())
        assert run_expected in capsys.readouterr().out

    def test_run_submit(self, fv3_run_assets):
        batch_script, config_file, config = fv3_run_assets
        with patch.object(FV3Forecast, "_validate", return_value=True):
            with patch.object(scheduler, "execute") as execute:
                fcstobj = FV3Forecast(config_file=config_file, batch_script=batch_script)
                with patch.object(fcstobj, "_config", config):
                    fcstobj.run(cycle=dt.datetime.now())
                execute.assert_called_once_with(cmd=f"sbatch {batch_script}")

    def test_schema_file(self):
        """
        Tests that the schema is properly defined with a file value.
        """

        config_file = fixture_path("forecast.yaml")
        with patch.object(Driver, "_validate", return_value=True):
            forecast = FV3Forecast(config_file=config_file)

        path = Path(forecast.schema_file)
        assert path.is_file()

    def test__prepare_config_files(self, create_field_table_update_obj, tmp_path):
        model_configure_file = fixture_path("fruit_config.yaml")
        namelist_file = tmp_path / "namelist.IN"
        namelist_file.touch()
        config_file = tmp_path / "fcst.yaml"
        fcst_config = {
            "forecast": {
                "field_table": create_field_table_update_obj["forecast"]["field_table"],
                "model_configure": {
                    "base_file": model_configure_file,
                },
                "namelist": {
                    "base_file": namelist_file.as_posix(),
                },
            },
        }
        YAMLConfig.dump_dict(cfg=fcst_config, path=config_file)
        with patch.object(Driver, "_validate", return_value=True):
            forecast = FV3Forecast(config_file=config_file)
        cycle = dt.datetime.now()
        forecast._prepare_config_files(cycle=cycle, run_directory=tmp_path)

        assert (tmp_path / "field_table").is_file()
        assert (tmp_path / "model_configure").is_file()
        assert (tmp_path / "input.nml").is_file()


# MPAS Tests


class TestMPASForecast:
    def test_create_namelist(self, tmp_path):
        """
        Test that providing a YAML base input file and a config file will create and update the MPAS
        namelist, including the cycle date.
        """

        # Create a fcst config file with a namelist entry
        config_file = fixture_path("fruit_config_similar_for_fcst.yaml")
        fcst_config = YAMLConfig(config_file)

        # Update the config to have the same namelist settings as the model_configure section in the
        # origional file.
        base_file = fixture_path("fruit_config.nml")
        fcst_config["forecast"]["namelist"] = {
            "base_file": base_file,
            "update_values": {
                "config": fcst_config["forecast"]["model_configure"]["update_values"],
            },
        }

        # Write it to a file
        fcst_config_file = tmp_path / "fcst.yml"
        fcst_config.dump(fcst_config_file)

        # Use it to create a forecast object.
        with patch.object(MPASForecast, "_validate", return_value=True):
            forecast_obj = MPASForecast(config_file=fcst_config_file)
        cycle = dt.datetime.now()
        output_file = tmp_path / "output.nml"
        forecast_obj.create_namelist(cycle, output_file)

        date_values = {
            "nhyd_model": {
                "config_start_time": cycle.strftime("%Y-%m-%d_%H:%M:%S"),
            },
        }
        expected = NMLConfig(base_file)
        expected.update_values(fcst_config["forecast"]["namelist"]["update_values"])
        expected.update_values(date_values)
        expected_file = tmp_path / "expected.nml"
        expected.dump(expected_file)

        assert compare_files(expected_file, output_file)

    @fixture
    def streams_config(self, tmp_path):
        template_path = tmp_path / "template.jinja2"
        with open(template_path, "w", encoding="utf-8") as f:
            f.write("roses are {{roses}}, violets are {{violets}}")

        fcst_config = {
            "forecast": {
                "streams": {
                    "template": template_path.as_posix(),
                    "vars": {
                        "roses": "red",
                        "violets": "blue",
                    },
                },
            },
        }
        fcst_config_file = tmp_path / "fcst.yaml"
        YAMLConfig.dump_dict(cfg=fcst_config, path=fcst_config_file)
        return str(template_path), fcst_config_file

    @pytest.mark.parametrize("output_stream", ["stream.out", None])
    def test_create_streams(self, capsys, output_stream, streams_config, tmp_path):
        """
        A stream file in MPAS is treated as a template.

        Test that providing a Forecast config file with the correct structure will fill in the
        template as requested.
        """

        template_path, fcst_config_file = streams_config
        with patch.object(Driver, "_validate", return_value=True):
            fcst_obj = MPASForecast(fcst_config_file)
        if output_stream is not None:
            output_stream = tmp_path / output_stream
        fcst_obj.create_streams(output_stream)

        with readable(template_path) as f:
            template_str = f.read()
        template = J2Template(values={"roses": "red", "violets": "blue"}, template_str=template_str)
        expected = tmp_path / "expected.txt"
        rendered = template.render()
        with writable(expected) as f:
            print(rendered, file=f)
        if output_stream is None:
            actual = capsys.readouterr().out
            assert actual.strip() == rendered.strip()
        else:
            assert compare_files(expected, output_stream)

    def test_schema_file(self):
        """
        Tests that the schema is properly defined with a file value.
        """
        config_file = fixture_path("forecast.yaml")
        with patch.object(Driver, "_validate", return_value=True):
            forecast = MPASForecast(config_file=config_file)

        path = Path(forecast.schema_file)
        assert path.is_file()

    def test__define_boundary_files(self):
        config_file = fixture_path("forecast.yaml")
        with patch.object(Driver, "_validate", return_value=True):
            forecast = MPASForecast(config_file=config_file)

        assert not forecast._define_boundary_files()

    @pytest.mark.parametrize("delimiter", [" ", "\n"])
    def test__mpi_env_variables(self, delimiter, tmp_path):
        config_file = tmp_path / "fcst.yaml"
        fcst_config = yaml.safe_load(
            """
forecast:
  mpi_settings:
    FI_PROVIDER: efa
    I_MPI_DEBUG: 4
    I_MPI_FABRICS: "shm:ofi"
    I_MPI_OFI_LIBRARY_INTERNAL: 0
    I_MPI_OFI_PROVIDER: efa
"""
        )
        YAMLConfig.dump_dict(cfg=fcst_config, path=config_file)
        with patch.object(Driver, "_validate", return_value=True):
            forecast = MPASForecast(config_file=config_file)

        output = forecast._mpi_env_variables(delimiter=delimiter)
        expected = [
            "FI_PROVIDER=efa",
            "I_MPI_DEBUG=4",
            "I_MPI_FABRICS=shm:ofi",
            "I_MPI_OFI_LIBRARY_INTERNAL=0",
            "I_MPI_OFI_PROVIDER=efa",
        ]

        expected = delimiter.join(expected)
        assert output == expected

    def test__prepare_config_files(self, tmp_path):
        namelist_file = tmp_path / "namelist.IN"
        streams_file = tmp_path / "streams.IN"
        namelist_file.touch()
        streams_file.touch()
        config_file = tmp_path / "fcst.yaml"
        fcst_config = {
            "forecast": {
                "namelist": {
                    "base_file": namelist_file.as_posix(),
                },
                "streams": {
                    "template": streams_file.as_posix(),
                    "vars": {},
                },
            },
        }
        YAMLConfig.dump_dict(cfg=fcst_config, path=config_file)
        with patch.object(Driver, "_validate", return_value=True):
            forecast = MPASForecast(config_file=config_file)
        cycle = dt.datetime.now()
        forecast._prepare_config_files(cycle=cycle, run_directory=tmp_path)

        assert (tmp_path / "namelist.atmosphere").is_file()
        assert (tmp_path / "streams.atmosphere").is_file()
