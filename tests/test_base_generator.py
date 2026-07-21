from pathlib import Path

from tkai.core.context import Context
from tkai.generators.base import BaseGenerator


class DemoGenerator(BaseGenerator):

    def generate(self, **kwargs):
        return "ok"


def test_generator_name():
    ctx = Context()

    gen = DemoGenerator(ctx)

    assert gen.name == "DemoGenerator"


def test_write_read(tmp_path: Path):
    ctx = Context()

    gen = DemoGenerator(ctx)

    file = tmp_path / "demo.txt"

    gen.write(file, "hello")

    assert file.exists()

    assert gen.read(file) == "hello"


def test_exists(tmp_path: Path):
    ctx = Context()

    gen = DemoGenerator(ctx)

    file = tmp_path / "a.txt"

    assert not gen.exists(file)

    gen.write(file, "1")

    assert gen.exists(file)


def test_generate():
    ctx = Context()

    gen = DemoGenerator(ctx)

    assert gen.generate() == "ok"