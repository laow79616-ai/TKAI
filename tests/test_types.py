from pathlib import Path

from tkai.core.types import JsonDict, PathLike


def test_pathlike():
    value: PathLike = Path("demo")

    assert isinstance(value, Path)


def test_jsondict():
    data: JsonDict = {
        "name": "tkai",
        "version": "0.1.0",
    }

    assert data["name"] == "tkai"