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
