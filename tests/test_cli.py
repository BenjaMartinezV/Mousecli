import argparse
import os

import pytest

from mousecli import cli


def test_token_persists_between_runs(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "config_dir", lambda: tmp_path)
    first = cli.load_token()
    assert first
    assert cli.load_token() == first


def test_new_token_replaces_saved_one(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "config_dir", lambda: tmp_path)
    first = cli.load_token()
    assert cli.load_token(regenerate=True) != first


def test_token_file_is_private(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "config_dir", lambda: tmp_path)
    cli.load_token()
    if os.name != "nt":
        assert (tmp_path / "token").stat().st_mode & 0o777 == 0o600


@pytest.mark.parametrize("value", ["0", "65536", "not-a-port"])
def test_port_must_be_valid(value):
    with pytest.raises(argparse.ArgumentTypeError):
        cli.valid_port(value)


def test_valid_port_is_integer():
    assert cli.valid_port("8765") == 8765
