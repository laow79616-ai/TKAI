"""Static validation for the V2.1 GitHub Actions delivery pipeline."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parents[2]
WORKFLOWS = ROOT / ".github" / "workflows"


def test_python_workflow_runs_quality_tests_and_package_build() -> None:
    workflow = (WORKFLOWS / "ci.yml").read_text(encoding="utf-8")

    assert "runs-on: ubuntu-latest" in workflow
    assert "ruff check ." in workflow
    assert 'python -m pip install -e ".[dev]" pydantic' in workflow
    assert "python -m pytest" in workflow
    for version in ('- "3.10"', '- "3.11"', '- "3.12"'):
        assert version in workflow
    assert "python -m build" in workflow
    assert "actions/upload-artifact@v4" in workflow
    assert "dist/" in workflow


def test_container_workflow_validates_compose_and_builds_both_images() -> None:
    workflow = (WORKFLOWS / "containers.yml").read_text(encoding="utf-8")

    assert "runs-on: ubuntu-latest" in workflow
    assert "docker compose config --quiet" in workflow
    assert "Dockerfile.api" in workflow
    assert "Dockerfile.dashboard" in workflow
    assert "docker/build-push-action@v7" in workflow
    assert workflow.count("actions/upload-artifact@v4") == 1
    assert "push: true" not in workflow


def test_container_workflow_compares_compose_services_order_independently() -> None:
    workflow = (WORKFLOWS / "containers.yml").read_text(encoding="utf-8")

    for deployment in ("default", "production", "observability"):
        assert (
            f'{deployment}_actual="$(docker compose'
            in workflow
        )
        assert f'{deployment}_actual" = "${deployment}_expected"' in workflow

    assert workflow.count("config --services | sort)") == 3
    assert workflow.count("' | sort)") == 3
    assert (
        "test \"$(docker compose config --services)\""
        not in workflow
    )


def test_container_workflow_preserves_strict_expected_service_sets() -> None:
    workflow = (WORKFLOWS / "containers.yml").read_text(encoding="utf-8")
    base = r"postgres\napi\ndashboard\nnginx\n"
    observability = (
        base
        + r"prometheus\ngrafana\nloki\nalloy\nalertmanager"
        + r"\npostgres-exporter\nnginx-exporter\n"
    )

    assert f"default_expected=\"$(printf '{base}' | sort)\"" in workflow
    assert f"production_expected=\"$(printf '{base}' | sort)\"" in workflow
    assert (
        f"observability_expected=\"$(printf '{observability}' | sort)\""
        in workflow
    )
