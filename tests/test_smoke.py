from pathlib import Path


def test_project_package_exists() -> None:
    assert Path("src/applyhome_alert/__init__.py").exists()
