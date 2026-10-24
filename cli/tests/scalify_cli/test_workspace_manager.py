import os
from unittest.mock import MagicMock, patch

import pytest

from scalify_cli.workspace_manager import (
    WorkspaceType,
    _find_scalifyui_root,
    _has_scalifyui_markers,
    _paths_match,
    check_scalify_repo,
)


class TestPathsMatch:
    def test_identical_paths(self, tmp_path):
        d = tmp_path / "scalify"
        d.mkdir()
        assert _paths_match(str(d), str(d))

    def test_symlink_to_same_dir(self, tmp_path):
        real = tmp_path / "real"
        real.mkdir()
        link = tmp_path / "link"
        link.symlink_to(real)
        assert _paths_match(str(real), str(link))

    def test_different_paths(self, tmp_path):
        a = tmp_path / "a"
        b = tmp_path / "b"
        a.mkdir()
        b.mkdir()
        assert not _paths_match(str(a), str(b))

    def test_nonexistent_paths_same(self):
        assert _paths_match("/nonexistent/same", "/nonexistent/same")

    def test_nonexistent_paths_different(self):
        assert not _paths_match("/nonexistent/a", "/nonexistent/b")

    def test_trailing_slash(self, tmp_path):
        d = tmp_path / "scalify"
        d.mkdir()
        assert _paths_match(str(d), str(d) + "/")

    def test_dot_components(self, tmp_path):
        d = tmp_path / "scalify"
        d.mkdir()
        assert _paths_match(str(d), str(d) + "/./")

    def test_parent_component(self, tmp_path):
        d = tmp_path / "scalify"
        d.mkdir()
        sub = d / "sub"
        sub.mkdir()
        assert _paths_match(str(d), str(sub) + "/..")

    def test_one_exists_one_not(self, tmp_path):
        d = tmp_path / "exists"
        d.mkdir()
        # samefile will raise because the second path doesn't exist;
        # fallback compares realpath strings, which will differ
        assert not _paths_match(str(d), "/nonexistent/path")

    def test_double_symlink(self, tmp_path):
        real = tmp_path / "real"
        real.mkdir()
        link1 = tmp_path / "link1"
        link1.symlink_to(real)
        link2 = tmp_path / "link2"
        link2.symlink_to(link1)
        assert _paths_match(str(link1), str(link2))
        assert _paths_match(str(real), str(link2))


_ALL_MARKERS = ["main.py", "scalify", "nodes.py", "scalify_extras", "scalify_api"]
_MARKER_DIRS = {"scalify", "scalify_extras", "scalify_api"}


def _create_scalifyui_markers(path, markers=None):
    """Create ScalifyUI marker files/directories under *path*."""
    if markers is None:
        markers = _ALL_MARKERS
    for m in markers:
        p = path / m
        if m in _MARKER_DIRS:
            p.mkdir(exist_ok=True)
        else:
            p.touch()


class TestHasScalifyuiMarkers:
    def test_all_five_markers(self, tmp_path):
        _create_scalifyui_markers(tmp_path)
        assert _has_scalifyui_markers(str(tmp_path)) is True

    @pytest.mark.parametrize("omit", _ALL_MARKERS)
    def test_any_four_of_five_sufficient(self, tmp_path, omit):
        remaining = [m for m in _ALL_MARKERS if m != omit]
        _create_scalifyui_markers(tmp_path, remaining)
        assert _has_scalifyui_markers(str(tmp_path)) is True

    @pytest.mark.parametrize(
        "present",
        [
            ["main.py", "scalify", "nodes.py"],
            ["scalify", "scalify_extras", "scalify_api"],
            ["main.py", "nodes.py", "scalify_api"],
        ],
    )
    def test_three_markers_insufficient(self, tmp_path, present):
        _create_scalifyui_markers(tmp_path, present)
        assert _has_scalifyui_markers(str(tmp_path)) is False

    def test_empty_directory(self, tmp_path):
        assert _has_scalifyui_markers(str(tmp_path)) is False

    def test_nonexistent_path(self):
        assert _has_scalifyui_markers("/nonexistent/path/xyz") is False


def _make_manager(*, use_here=None, specified_workspace=None, use_recent=None):
    """Create a fresh WorkspaceManager with reset singleton."""
    from scalify_cli.workspace_manager import WorkspaceManager

    WorkspaceManager._instances = {}
    mgr = WorkspaceManager()
    mgr.use_here = use_here
    mgr.use_recent = use_recent
    mgr.specified_workspace = specified_workspace
    return mgr


def _mock_config(mgr, default_workspace=None, recent_workspace=None):
    """Replace config_manager with a mock that returns the given values."""
    mock_cm = MagicMock()

    def _get(key):
        from scalify_cli import constants

        if key == constants.CONFIG_KEY_DEFAULT_WORKSPACE:
            return default_workspace
        if key == constants.CONFIG_KEY_RECENT_WORKSPACE:
            return recent_workspace
        return None

    mock_cm.get.side_effect = _get
    mgr.config_manager = mock_cm
    return mock_cm


class TestFindScalifyuiRoot:
    """Tests for the upward directory walk in _find_scalifyui_root."""

    def test_markers_at_given_path(self, tmp_path):
        _create_scalifyui_markers(tmp_path)
        assert _find_scalifyui_root(str(tmp_path)) == str(tmp_path)

    def test_walks_up_to_parent_with_markers(self, tmp_path):
        _create_scalifyui_markers(tmp_path)
        subdir = tmp_path / "custom_nodes" / "MyNode"
        subdir.mkdir(parents=True)
        assert _find_scalifyui_root(str(subdir)) == str(tmp_path)

    def test_walks_up_multiple_levels(self, tmp_path):
        _create_scalifyui_markers(tmp_path)
        deep = tmp_path / "custom_nodes" / "MyNode" / "lib" / "utils"
        deep.mkdir(parents=True)
        assert _find_scalifyui_root(str(deep)) == str(tmp_path)

    def test_no_markers_anywhere(self, tmp_path):
        subdir = tmp_path / "a" / "b"
        subdir.mkdir(parents=True)
        assert _find_scalifyui_root(str(subdir)) is None

    def test_returns_nearest_root(self, tmp_path):
        """Nested ScalifyUI installs: returns the closest (deepest) match."""
        outer = tmp_path / "outer"
        inner = outer / "inner"
        inner.mkdir(parents=True)
        _create_scalifyui_markers(outer)
        _create_scalifyui_markers(inner)
        subdir = inner / "custom_nodes"
        subdir.mkdir()
        assert _find_scalifyui_root(str(subdir)) == str(inner)


class TestCheckScalifyRepoFallback:
    """Tests for the marker-based fallback in check_scalify_repo."""

    def test_nonexistent_path(self):
        found, path = check_scalify_repo("/nonexistent/path/xyz")
        assert found is False
        assert path is None

    def test_non_git_dir_with_all_markers(self, tmp_path):
        _create_scalifyui_markers(tmp_path)
        found, path = check_scalify_repo(str(tmp_path))
        assert found is True
        assert path == str(tmp_path)

    def test_non_git_dir_with_four_markers(self, tmp_path):
        _create_scalifyui_markers(tmp_path, ["main.py", "scalify", "nodes.py", "scalify_api"])
        found, path = check_scalify_repo(str(tmp_path))
        assert found is True
        assert path == str(tmp_path)

    def test_non_git_dir_insufficient_markers(self, tmp_path):
        _create_scalifyui_markers(tmp_path, ["main.py", "scalify", "nodes.py"])
        found, path = check_scalify_repo(str(tmp_path))
        assert found is False
        assert path is None

    def test_non_git_empty_dir(self, tmp_path):
        found, path = check_scalify_repo(str(tmp_path))
        assert found is False
        assert path is None

    def test_returned_path_is_absolute(self, tmp_path):
        """Path with '..' components is resolved to a clean absolute path."""
        _create_scalifyui_markers(tmp_path)
        subdir = tmp_path / "sub"
        subdir.mkdir()
        dotdot_path = os.path.join(str(subdir), "..")
        found, path = check_scalify_repo(dotdot_path)
        assert found is True
        assert os.path.isabs(path)
        assert ".." not in path

    def test_subdirectory_walks_up_to_root(self, tmp_path):
        """check_scalify_repo from a subdirectory resolves to the ScalifyUI root."""
        _create_scalifyui_markers(tmp_path)
        subdir = tmp_path / "custom_nodes" / "MyNode"
        subdir.mkdir(parents=True)
        found, path = check_scalify_repo(str(subdir))
        assert found is True
        assert path == str(tmp_path)

    def test_fork_repo_with_markers_detected(self, tmp_path):
        """Git repo with non-ScalifyUI remote + markers → detected via fallback."""
        import git as gitmodule

        repo = gitmodule.Repo.init(str(tmp_path))
        repo.create_remote("origin", "https://github.com/someone/ScalifyUI-fork")
        (tmp_path / "README.md").write_text("fork")
        repo.index.add(["README.md"])
        repo.index.commit("init")

        _create_scalifyui_markers(tmp_path)

        found, path = check_scalify_repo(str(tmp_path))
        assert found is True
        assert path == str(tmp_path)

    def test_fork_repo_without_markers_not_detected(self, tmp_path):
        """Git repo with non-ScalifyUI remote and no markers → not detected."""
        import git as gitmodule

        repo = gitmodule.Repo.init(str(tmp_path))
        repo.create_remote("origin", "https://github.com/someone/other-project")
        (tmp_path / "README.md").write_text("other")
        repo.index.add(["README.md"])
        repo.index.commit("init")

        found, path = check_scalify_repo(str(tmp_path))
        assert found is False
        assert path is None


class TestStep1Workspace:
    def test_workspace_flag_takes_priority(self):
        mgr = _make_manager(specified_workspace="/opt/scalify")
        _mock_config(mgr)
        path, ws_type = mgr.get_workspace_path()
        assert ws_type == WorkspaceType.SPECIFIED
        assert path == "/opt/scalify"

    @patch("scalify_cli.workspace_manager.check_scalify_repo")
    @patch("scalify_cli.workspace_manager.os.getcwd")
    def test_workspace_overrides_cwd_matching_default(self, mock_getcwd, mock_check):
        """--workspace wins even when cwd is the default workspace."""
        mock_getcwd.return_value = "/home/user/scalify/ScalifyUI"
        mock_check.return_value = (True, "/home/user/scalify/ScalifyUI")

        mgr = _make_manager(specified_workspace="/other/ScalifyUI")
        _mock_config(mgr, default_workspace="/home/user/scalify/ScalifyUI")

        path, ws_type = mgr.get_workspace_path()
        assert ws_type == WorkspaceType.SPECIFIED
        assert path == "/other/ScalifyUI"


class TestStep3Here:
    @patch("scalify_cli.workspace_manager.check_scalify_repo")
    @patch("scalify_cli.workspace_manager.os.getcwd")
    def test_here_flag_forces_current_dir_even_if_matches_default(self, mock_getcwd, mock_check):
        """--here always returns CURRENT_DIR, even when cwd IS the default."""
        mock_getcwd.return_value = "/home/user/scalify/ScalifyUI"
        mock_check.return_value = (True, "/home/user/scalify/ScalifyUI")

        mgr = _make_manager(use_here=True)
        _mock_config(mgr, default_workspace="/home/user/scalify/ScalifyUI")

        path, ws_type = mgr.get_workspace_path()
        assert ws_type == WorkspaceType.CURRENT_DIR
        assert path == "/home/user/scalify/ScalifyUI"

    @patch("scalify_cli.workspace_manager.check_scalify_repo")
    @patch("scalify_cli.workspace_manager.os.getcwd")
    def test_here_flag_non_scalify_dir_appends_scalifyui(self, mock_getcwd, mock_check):
        """--here in a non-ScalifyUI dir returns cwd/ScalifyUI."""
        mock_getcwd.return_value = "/home/user/projects"
        mock_check.return_value = (False, None)

        mgr = _make_manager(use_here=True)
        _mock_config(mgr)

        path, ws_type = mgr.get_workspace_path()
        assert ws_type == WorkspaceType.CURRENT_DIR
        assert path == os.path.join("/home/user/projects", "ScalifyUI")


class TestStep4AutoDetect:
    @patch("scalify_cli.workspace_manager.check_scalify_repo")
    @patch("scalify_cli.workspace_manager.os.getcwd")
    def test_cwd_matches_default_returns_default_type(self, mock_getcwd, mock_check):
        """Core fix: cwd is the configured default workspace -> DEFAULT."""
        mock_getcwd.return_value = "/home/user/scalify/ScalifyUI"
        mock_check.return_value = (True, "/home/user/scalify/ScalifyUI")

        mgr = _make_manager(use_here=None)
        _mock_config(mgr, default_workspace="/home/user/scalify/ScalifyUI")

        with patch("scalify_cli.workspace_manager._paths_match", return_value=True):
            path, ws_type = mgr.get_workspace_path()

        assert ws_type == WorkspaceType.DEFAULT
        assert path == "/home/user/scalify/ScalifyUI"

    @patch("scalify_cli.workspace_manager.check_scalify_repo")
    @patch("scalify_cli.workspace_manager.os.getcwd")
    def test_cwd_different_repo_returns_current_dir(self, mock_getcwd, mock_check):
        """cwd is a ScalifyUI repo but NOT the default -> CURRENT_DIR."""
        mock_getcwd.return_value = "/home/user/other/ScalifyUI"
        mock_check.return_value = (True, "/home/user/other/ScalifyUI")

        mgr = _make_manager(use_here=None)
        _mock_config(mgr, default_workspace="/home/user/scalify/ScalifyUI")

        with patch("scalify_cli.workspace_manager._paths_match", return_value=False):
            path, ws_type = mgr.get_workspace_path()

        assert ws_type == WorkspaceType.CURRENT_DIR
        assert path == "/home/user/other/ScalifyUI"

    @patch("scalify_cli.workspace_manager.check_scalify_repo")
    @patch("scalify_cli.workspace_manager.os.getcwd")
    def test_cwd_repo_no_default_configured(self, mock_getcwd, mock_check):
        """cwd is a ScalifyUI repo, no default configured -> CURRENT_DIR."""
        mock_getcwd.return_value = "/home/user/scalify/ScalifyUI"
        mock_check.return_value = (True, "/home/user/scalify/ScalifyUI")

        mgr = _make_manager(use_here=None)
        _mock_config(mgr, default_workspace=None)

        path, ws_type = mgr.get_workspace_path()
        assert ws_type == WorkspaceType.CURRENT_DIR
        assert path == "/home/user/scalify/ScalifyUI"

    @patch("scalify_cli.workspace_manager.check_scalify_repo")
    @patch("scalify_cli.workspace_manager.os.getcwd")
    def test_cwd_repo_empty_default_returns_current_dir(self, mock_getcwd, mock_check):
        """default_workspace is empty string -> treated as not configured."""
        mock_getcwd.return_value = "/home/user/scalify/ScalifyUI"
        mock_check.return_value = (True, "/home/user/scalify/ScalifyUI")

        mgr = _make_manager(use_here=None)
        _mock_config(mgr, default_workspace="")

        path, ws_type = mgr.get_workspace_path()
        assert ws_type == WorkspaceType.CURRENT_DIR

    @patch("scalify_cli.workspace_manager.check_scalify_repo")
    @patch("scalify_cli.workspace_manager.os.getcwd")
    def test_paths_match_called_with_correct_args(self, mock_getcwd, mock_check):
        """Verify _paths_match receives resolved path and default_workspace."""
        mock_getcwd.return_value = "/cwd"
        mock_check.return_value = (True, "/resolved/ScalifyUI")

        mgr = _make_manager(use_here=None)
        _mock_config(mgr, default_workspace="/configured/default")

        with patch("scalify_cli.workspace_manager._paths_match", return_value=False) as mock_pm:
            mgr.get_workspace_path()

        mock_pm.assert_called_once_with("/resolved/ScalifyUI", "/configured/default")


class TestNoHereSkipsStep4:
    @patch("scalify_cli.workspace_manager.check_scalify_repo")
    @patch("scalify_cli.workspace_manager.os.getcwd")
    def test_no_here_skips_cwd_detection(self, mock_getcwd, mock_check):
        """--no-here (use_here=False) skips step 4 entirely, falls to step 5."""
        mock_getcwd.return_value = "/home/user/scalify/ScalifyUI"
        mock_check.return_value = (True, "/home/user/scalify/ScalifyUI")

        mgr = _make_manager(use_here=False)
        _mock_config(mgr, default_workspace="/home/user/scalify/ScalifyUI")

        path, ws_type = mgr.get_workspace_path()

        assert ws_type == WorkspaceType.DEFAULT
        assert path == "/home/user/scalify/ScalifyUI"
        # getcwd should never be called because step 4 is skipped
        mock_getcwd.assert_not_called()


class TestStep5ConfiguredDefault:
    @patch("scalify_cli.workspace_manager.check_scalify_repo")
    @patch("scalify_cli.workspace_manager.os.getcwd")
    def test_not_scalify_repo_falls_through_to_default(self, mock_getcwd, mock_check):
        """cwd is NOT a ScalifyUI repo -> falls through to configured default."""
        mock_getcwd.return_value = "/home/user/projects"
        mock_check.side_effect = lambda path: (
            (True, "/home/user/scalify/ScalifyUI") if path == "/home/user/scalify/ScalifyUI" else (False, None)
        )

        mgr = _make_manager(use_here=None)
        _mock_config(mgr, default_workspace="/home/user/scalify/ScalifyUI")

        path, ws_type = mgr.get_workspace_path()
        assert ws_type == WorkspaceType.DEFAULT
        assert path == "/home/user/scalify/ScalifyUI"


class TestStep6RecentFallback:
    @patch("scalify_cli.workspace_manager.check_scalify_repo")
    @patch("scalify_cli.workspace_manager.os.getcwd")
    def test_no_default_falls_to_recent(self, mock_getcwd, mock_check):
        """No default configured, valid recent workspace -> RECENT."""
        mock_getcwd.return_value = "/home/user/projects"
        mock_check.side_effect = lambda path: (
            (True, "/home/user/recent/ScalifyUI") if path == "/home/user/recent/ScalifyUI" else (False, None)
        )

        mgr = _make_manager(use_here=None, use_recent=None)
        _mock_config(
            mgr,
            default_workspace=None,
            recent_workspace="/home/user/recent/ScalifyUI",
        )

        path, ws_type = mgr.get_workspace_path()
        assert ws_type == WorkspaceType.RECENT
        assert path == "/home/user/recent/ScalifyUI"


class TestStep7FallbackDefault:
    @patch("scalify_cli.workspace_manager.utils.get_not_user_set_default_workspace")
    @patch("scalify_cli.workspace_manager.check_scalify_repo", return_value=(False, None))
    @patch("scalify_cli.workspace_manager.os.getcwd", return_value="/tmp/random")
    def test_all_fallbacks_exhausted(self, _cwd, _check, mock_fallback):
        """Nothing configured, cwd not a repo -> system fallback DEFAULT."""
        mock_fallback.return_value = "/home/user/scalify"
        mgr = _make_manager(use_here=None, use_recent=None)
        _mock_config(mgr, default_workspace=None, recent_workspace=None)

        path, ws_type = mgr.get_workspace_path()
        assert ws_type == WorkspaceType.DEFAULT
        assert path == "/home/user/scalify"


class TestFullIntegration:
    """Create a real git repo that looks like ScalifyUI (with the right remote)
    and exercise the entire get_workspace_path flow with no mocked internals.
    Only os.getcwd and ConfigManager are faked."""

    @staticmethod
    def _create_scalify_repo(path):
        """Create a bare-minimum git repo with a ScalifyUI remote."""
        import git as gitmodule

        repo = gitmodule.Repo.init(path)
        repo.create_remote("origin", "https://github.com/khulnasoft/scalify")
        # Need at least one commit for repo to be fully valid
        readme = os.path.join(path, "main.py")
        with open(readme, "w") as f:
            f.write("# ScalifyUI\n")
        repo.index.add(["main.py"])
        repo.index.commit("init")
        return repo

    def test_cwd_is_default_workspace_real_repo(self, tmp_path):
        """Bug repro: cd into default workspace -> must return DEFAULT."""
        scalify_dir = str(tmp_path / "ScalifyUI")
        self._create_scalify_repo(scalify_dir)

        mgr = _make_manager(use_here=None)
        _mock_config(mgr, default_workspace=scalify_dir)

        with patch("scalify_cli.workspace_manager.os.getcwd", return_value=scalify_dir):
            path, ws_type = mgr.get_workspace_path()

        assert ws_type == WorkspaceType.DEFAULT
        assert path == scalify_dir

    def test_cwd_is_default_workspace_via_symlink(self, tmp_path):
        """Default stored as symlink, cwd is the real path -> DEFAULT."""
        real_dir = tmp_path / "real_scalify"
        self._create_scalify_repo(str(real_dir))
        link = tmp_path / "scalify_link"
        link.symlink_to(real_dir)

        mgr = _make_manager(use_here=None)
        _mock_config(mgr, default_workspace=str(link))

        with patch("scalify_cli.workspace_manager.os.getcwd", return_value=str(real_dir)):
            path, ws_type = mgr.get_workspace_path()

        assert ws_type == WorkspaceType.DEFAULT

    def test_cwd_is_subdir_of_default_workspace(self, tmp_path):
        """cd into custom_nodes/ inside default workspace -> DEFAULT."""
        scalify_dir = tmp_path / "ScalifyUI"
        self._create_scalify_repo(str(scalify_dir))
        subdir = scalify_dir / "custom_nodes"
        subdir.mkdir()

        mgr = _make_manager(use_here=None)
        _mock_config(mgr, default_workspace=str(scalify_dir))

        with patch("scalify_cli.workspace_manager.os.getcwd", return_value=str(subdir)):
            path, ws_type = mgr.get_workspace_path()

        assert ws_type == WorkspaceType.DEFAULT
        assert path == str(scalify_dir)

    def test_two_repos_cwd_in_non_default(self, tmp_path):
        """Two ScalifyUI repos exist; cwd is in the non-default one -> CURRENT_DIR."""
        default_dir = tmp_path / "default_scalify"
        other_dir = tmp_path / "other_scalify"
        self._create_scalify_repo(str(default_dir))
        self._create_scalify_repo(str(other_dir))

        mgr = _make_manager(use_here=None)
        _mock_config(mgr, default_workspace=str(default_dir))

        with patch("scalify_cli.workspace_manager.os.getcwd", return_value=str(other_dir)):
            path, ws_type = mgr.get_workspace_path()

        assert ws_type == WorkspaceType.CURRENT_DIR
        assert path == str(other_dir)

    def test_default_workspace_trailing_slash(self, tmp_path):
        """Config has trailing slash, git working_dir doesn't -> DEFAULT."""
        scalify_dir = str(tmp_path / "ScalifyUI")
        self._create_scalify_repo(scalify_dir)

        mgr = _make_manager(use_here=None)
        _mock_config(mgr, default_workspace=scalify_dir + "/")

        with patch("scalify_cli.workspace_manager.os.getcwd", return_value=scalify_dir):
            path, ws_type = mgr.get_workspace_path()

        assert ws_type == WorkspaceType.DEFAULT

    def test_here_flag_overrides_even_with_real_repo(self, tmp_path):
        """--here forces CURRENT_DIR even in a real default workspace repo."""
        scalify_dir = str(tmp_path / "ScalifyUI")
        self._create_scalify_repo(scalify_dir)

        mgr = _make_manager(use_here=True)
        _mock_config(mgr, default_workspace=scalify_dir)

        with patch("scalify_cli.workspace_manager.os.getcwd", return_value=scalify_dir):
            path, ws_type = mgr.get_workspace_path()

        assert ws_type == WorkspaceType.CURRENT_DIR

    def test_not_in_any_repo_falls_to_configured_default(self, tmp_path):
        """cwd is a plain dir, configured default exists -> DEFAULT via step 5."""
        scalify_dir = str(tmp_path / "ScalifyUI")
        self._create_scalify_repo(scalify_dir)
        plain_dir = str(tmp_path / "plain")
        os.makedirs(plain_dir)

        mgr = _make_manager(use_here=None)
        _mock_config(mgr, default_workspace=scalify_dir)

        with patch("scalify_cli.workspace_manager.os.getcwd", return_value=plain_dir):
            path, ws_type = mgr.get_workspace_path()

        assert ws_type == WorkspaceType.DEFAULT
        assert path == scalify_dir

    def test_non_git_scalifyui_detected_as_cwd(self, tmp_path):
        """Non-git ScalifyUI (zip download) detected when cd'd into it."""
        scalify_dir = tmp_path / "ScalifyUI"
        scalify_dir.mkdir()
        _create_scalifyui_markers(scalify_dir)

        mgr = _make_manager(use_here=None)
        _mock_config(mgr, default_workspace=str(scalify_dir))

        with patch("scalify_cli.workspace_manager.os.getcwd", return_value=str(scalify_dir)):
            path, ws_type = mgr.get_workspace_path()

        assert ws_type == WorkspaceType.DEFAULT
        assert path == str(scalify_dir)

    def test_non_git_scalifyui_as_configured_default(self, tmp_path):
        """Non-git ScalifyUI install works as configured default (step 5)."""
        scalify_dir = tmp_path / "ScalifyUI"
        scalify_dir.mkdir()
        _create_scalifyui_markers(scalify_dir)
        plain_dir = tmp_path / "other"
        plain_dir.mkdir()

        mgr = _make_manager(use_here=None)
        _mock_config(mgr, default_workspace=str(scalify_dir))

        with patch("scalify_cli.workspace_manager.os.getcwd", return_value=str(plain_dir)):
            path, ws_type = mgr.get_workspace_path()

        assert ws_type == WorkspaceType.DEFAULT
        assert path == str(scalify_dir)

    def test_non_git_scalifyui_from_subdirectory(self, tmp_path):
        """Non-git ScalifyUI detected when cd'd into custom_nodes/ subdirectory."""
        scalify_dir = tmp_path / "ScalifyUI"
        scalify_dir.mkdir()
        _create_scalifyui_markers(scalify_dir)
        subdir = scalify_dir / "custom_nodes" / "MyNode"
        subdir.mkdir(parents=True)

        mgr = _make_manager(use_here=None)
        _mock_config(mgr, default_workspace=str(scalify_dir))

        with patch("scalify_cli.workspace_manager.os.getcwd", return_value=str(subdir)):
            path, ws_type = mgr.get_workspace_path()

        assert ws_type == WorkspaceType.DEFAULT
        assert path == str(scalify_dir)

    def test_fork_repo_detected_as_scalifyui(self, tmp_path):
        """ScalifyUI fork (non-standard remote) detected via marker fallback."""
        import git as gitmodule

        scalify_dir = tmp_path / "ScalifyUI"
        repo = gitmodule.Repo.init(str(scalify_dir))
        repo.create_remote("origin", "https://github.com/someone/ScalifyUI-fork")
        (scalify_dir / "README.md").write_text("fork")
        repo.index.add(["README.md"])
        repo.index.commit("init")

        _create_scalifyui_markers(scalify_dir)

        mgr = _make_manager(use_here=None)
        _mock_config(mgr, default_workspace=str(scalify_dir))

        with patch("scalify_cli.workspace_manager.os.getcwd", return_value=str(scalify_dir)):
            path, ws_type = mgr.get_workspace_path()

        assert ws_type == WorkspaceType.DEFAULT
        assert path == str(scalify_dir)


class TestLazyResolution:
    """``workspace_path``/``workspace_type`` resolve on first read, not in ``entry()``."""

    def test_path_is_none_before_setup(self):
        """``_make_manager`` cannot reset the singleton, so ask for a genuinely fresh one."""
        from scalify_cli.utils import reset_singleton_for_testing
        from scalify_cli.workspace_manager import WorkspaceManager

        reset_singleton_for_testing(WorkspaceManager)
        mgr = WorkspaceManager()
        assert mgr.workspace_path is None
        assert mgr.workspace_type is None

    def test_setup_does_not_probe(self):
        mgr = _make_manager()
        with patch("scalify_cli.workspace_manager.check_scalify_repo", side_effect=AssertionError("probed")):
            mgr.setup_workspace_manager()

    def test_first_read_resolves_once(self):
        mgr = _make_manager()
        mgr.setup_workspace_manager()
        with patch.object(mgr, "get_workspace_path", return_value=("/ws", WorkspaceType.DEFAULT)) as resolve:
            assert mgr.workspace_path == "/ws"
            assert mgr.workspace_type == WorkspaceType.DEFAULT
            assert mgr.workspace_path == "/ws"
        assert resolve.call_count == 1

    def test_second_setup_discards_the_cached_path(self):
        """``scalify install`` re-runs setup with the freshly created repo dir."""
        mgr = _make_manager()
        mgr.setup_workspace_manager(specified_workspace="/first")
        assert mgr.workspace_path == "/first"
        mgr.setup_workspace_manager(specified_workspace="/second")
        assert mgr.workspace_path == "/second"


class TestWorkspaceFreeCommands:
    """Commands that never read the workspace must not pay for the git probe."""

    @staticmethod
    def _invoke(args):
        from typer.testing import CliRunner

        import scalify_cli.workspace_manager as workspace_manager_module
        from scalify_cli.cmdline import app

        with patch.object(
            workspace_manager_module, "check_scalify_repo", side_effect=AssertionError("workspace was probed")
        ):
            return CliRunner().invoke(app, args)

    @pytest.mark.parametrize("command", [["knowledge", "status"], ["cloud", "status"]])
    def test_no_workspace_probe(self, command):
        result = self._invoke(["--json", *command])
        assert not isinstance(result.exception, AssertionError), result.exception

    def test_which_still_resolves_the_workspace(self):
        from typer.testing import CliRunner

        import scalify_cli.workspace_manager as workspace_manager_module
        from scalify_cli.cmdline import app

        with patch.object(workspace_manager_module, "check_scalify_repo", return_value=(True, "/sentinel/ScalifyUI")):
            result = CliRunner().invoke(app, ["--json", "which"])

        assert result.exit_code == 0, result.output
        assert "/sentinel/ScalifyUI" in result.output

    def test_gitpython_is_not_imported(self):
        import subprocess
        import sys

        source = (
            "import sys\n"
            "from typer.testing import CliRunner\n"
            "from scalify_cli.cmdline import app\n"
            "CliRunner().invoke(app, ['--json', 'knowledge', 'status'])\n"
            "assert 'git' not in sys.modules, 'GitPython was imported'\n"
        )
        subprocess.run([sys.executable, "-c", source], check=True, capture_output=True, timeout=120)
