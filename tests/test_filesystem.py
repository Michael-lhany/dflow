import pytest

from dflow.core.filesystem import remove_path


def test_remove_path_rejects_project_root(tmp_path):
    with pytest.raises(ValueError, match="outside project"):
        remove_path(tmp_path, tmp_path)


def test_remove_path_rejects_external_target(tmp_path):
    project_root = tmp_path / "project"
    external_file = tmp_path / "external.txt"
    project_root.mkdir()
    external_file.write_text("keep\n", encoding="utf-8")

    with pytest.raises(ValueError, match="outside project"):
        remove_path(external_file, project_root)

    assert external_file.exists()
