import os
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from scalify_cli.cmdline import app, g_exclusivity, g_gpu_exclusivity


@pytest.fixture(scope="function")
def runner():
    g_exclusivity.reset_for_testing()
    g_gpu_exclusivity.reset_for_testing()
    return CliRunner()


@pytest.fixture(scope="function")
def mock_execute():
    with patch("scalify_cli.command.install.execute") as mock:
        yield mock


@pytest.fixture(scope="function")
def mock_prompt_select_enum():
    def mocked_prompt_select_enum(question: str, choices: list, force_prompting: bool = False):
        return choices[0]

    with patch(
        "scalify_cli.ui.prompt_select_enum",
        new=mocked_prompt_select_enum,
    ) as mock:
        yield mock


@pytest.fixture(autouse=True)
def mock_tracking_consent():
    with patch("scalify_cli.tracking.prompt_tracking_consent"):
        yield


@pytest.mark.parametrize(
    "cmd",
    [
        ["--here", "install"],
        ["--workspace", "./ScalifyUI", "install"],
    ],
)
def test_install_here(cmd, runner, mock_execute, mock_prompt_select_enum):
    result = runner.invoke(app, cmd)
    assert result.exit_code == 0, result.stdout

    args, _ = mock_execute.call_args
    url, scalify_path, *_ = args
    assert url == "https://github.com/khulnasoft/scalify"
    assert scalify_path == os.path.join(os.getcwd(), "ScalifyUI")


def test_version(runner):
    result = runner.invoke(app, ["-v"])
    assert result.exit_code == 0
    assert "0.0.0" in result.stdout


@pytest.fixture
def mock_run_execute():
    with patch("scalify_cli.command.run.execute") as mock:
        yield mock


def _write_workflow(tmp_path):
    wf = tmp_path / "wf.json"
    wf.write_text('{"1": {"class_type": "X", "inputs": {}}}')
    return str(wf)


class TestRunApiKeyResolution:
    """typer envvar resolution: --api-key + SCALIFY_API_KEY must reach run.execute()."""

    def test_envvar_is_picked_up(self, runner, mock_run_execute, tmp_path):
        wf = _write_workflow(tmp_path)
        result = runner.invoke(
            app, ["run", "--workflow", wf], env={"SCALIFY_API_KEY": "env-key-xyz", "SCALIFY_WHERE": "local"}
        )
        assert result.exit_code == 0, result.output
        assert mock_run_execute.call_args.kwargs["api_key"] == "env-key-xyz"

    def test_flag_overrides_envvar(self, runner, mock_run_execute, tmp_path):
        wf = _write_workflow(tmp_path)
        result = runner.invoke(
            app,
            ["run", "--workflow", wf, "--api-key", "flag-key-abc"],
            env={"SCALIFY_API_KEY": "env-key-xyz", "SCALIFY_WHERE": "local"},
        )
        assert result.exit_code == 0, result.output
        assert mock_run_execute.call_args.kwargs["api_key"] == "flag-key-abc"

    def test_absent_resolves_to_none(self, runner, mock_run_execute, tmp_path):
        wf = _write_workflow(tmp_path)
        # Explicit empty env to neutralize any host-level SCALIFY_API_KEY leak.
        result = runner.invoke(app, ["run", "--workflow", wf], env={"SCALIFY_API_KEY": "", "SCALIFY_WHERE": "local"})
        assert result.exit_code == 0, result.output
        assert mock_run_execute.call_args.kwargs["api_key"] is None

    def test_envvar_trailing_whitespace_is_stripped(self, runner, mock_run_execute, tmp_path):
        wf = _write_workflow(tmp_path)
        result = runner.invoke(
            app, ["run", "--workflow", wf], env={"SCALIFY_API_KEY": "  sk-abc\n", "SCALIFY_WHERE": "local"}
        )
        assert result.exit_code == 0, result.output
        assert mock_run_execute.call_args.kwargs["api_key"] == "sk-abc"

    def test_whitespace_only_collapses_to_none(self, runner, mock_run_execute, tmp_path):
        wf = _write_workflow(tmp_path)
        result = runner.invoke(app, ["run", "--workflow", wf], env={"SCALIFY_API_KEY": "   \n\t", "SCALIFY_WHERE": "local"})
        assert result.exit_code == 0, result.output
        assert mock_run_execute.call_args.kwargs["api_key"] is None
