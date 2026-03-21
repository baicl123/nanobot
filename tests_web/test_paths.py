"""Tests for user path functions."""

from pathlib import Path

import pytest

from nanobot.config.paths import (
    get_user_workspace_path,
    get_user_sessions_path,
    get_user_memory_path,
)


def test_user_workspace_path(monkeypatch, tmp_path: Path) -> None:
    """Test user workspace path generation."""
    monkeypatch.setattr(
        "nanobot.config.paths.get_workspace_path",
        lambda ws=None: tmp_path
    )

    workspace = get_user_workspace_path("60079031")
    assert workspace == tmp_path / "users" / "60079031"
    assert workspace.exists()


def test_user_sessions_path(monkeypatch, tmp_path: Path) -> None:
    """Test user sessions path generation."""
    monkeypatch.setattr(
        "nanobot.config.paths.get_workspace_path",
        lambda ws=None: tmp_path
    )

    sessions_dir = get_user_sessions_path("60079031")
    assert sessions_dir == tmp_path / "users" / "60079031" / "sessions"
    assert sessions_dir.exists()


def test_user_memory_path(monkeypatch, tmp_path: Path) -> None:
    """Test user memory path generation."""
    monkeypatch.setattr(
        "nanobot.config.paths.get_workspace_path",
        lambda ws=None: tmp_path
    )

    memory_dir = get_user_memory_path("60079031")
    assert memory_dir == tmp_path / "users" / "60079031" / "memory"
    assert memory_dir.exists()


def test_different_users_have_different_paths(monkeypatch, tmp_path: Path) -> None:
    """Test different users have different workspace paths."""
    monkeypatch.setattr(
        "nanobot.config.paths.get_workspace_path",
        lambda ws=None: tmp_path
    )

    workspace1 = get_user_workspace_path("60079031")
    workspace2 = get_user_workspace_path("60079214")

    assert workspace1 != workspace2
