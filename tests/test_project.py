from dflow.core.project import create_project


def test_new_project_does_not_create_unused_sim_logs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    create_project("example")

    project_root = tmp_path / "example"
    assert not (project_root / "sim" / "logs").exists()
    assert (project_root / "sim" / "waves").is_dir()
