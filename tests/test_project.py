from pathlib import Path

from tkai.core.project import Project


def test_project_defaults(tmp_path: Path):
    project = Project(
        name="demo",
        root=tmp_path,
    )

    assert project.name == "demo"
    assert project.root == tmp_path
    assert project.version == "0.1.0"
    assert project.template is None
    assert project.author is None
    assert project.description is None
    assert project.metadata == {}


def test_project_validate_success(tmp_path: Path):
    project = Project(
        name="demo",
        root=tmp_path,
    )

    assert project.validate() is True


def test_project_validate_fail():
    project = Project(
        name="",
        root=Path("/path/not/exists"),
    )

    assert project.validate() is False


def test_project_exists(tmp_path: Path):
    project = Project(
        name="demo",
        root=tmp_path,
    )

    assert project.exists is False

    project.config_file.write_text("", encoding="utf-8")

    assert project.exists is True


def test_project_to_dict(tmp_path: Path):
    project = Project(
        name="demo",
        root=tmp_path,
        template="fastapi",
        author="tkai",
        description="demo project",
        metadata={"a": 1},
    )

    data = project.to_dict()

    assert data["name"] == "demo"
    assert data["template"] == "fastapi"
    assert data["author"] == "tkai"
    assert data["description"] == "demo project"
    assert data["metadata"] == {"a": 1}


def test_project_from_dict(tmp_path: Path):
    project = Project(
        name="demo",
        root=tmp_path,
        template="cli",
        author="tester",
    )

    data = project.to_dict()

    loaded = Project.from_dict(data)

    assert loaded.name == project.name
    assert loaded.root == project.root
    assert loaded.version == project.version
    assert loaded.template == project.template
    assert loaded.author == project.author
    assert loaded.description == project.description
    assert loaded.metadata == project.metadata