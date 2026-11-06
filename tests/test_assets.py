"""Packaging layout: the same structure as kubeflow/pipelines-components."""

import datetime
import importlib.util
import pathlib

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load_generator():
    spec = importlib.util.spec_from_file_location(
        "gen_component_assets", ROOT / "scripts" / "gen_component_assets.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_generated_files_are_current() -> None:
    for path, content in load_generator().expected_files().items():
        assert path.read_text(encoding="utf-8") == content, f"run the generator: {path}"


def test_metadata_follows_the_kep_schema() -> None:
    generator = load_generator()
    folders = generator.component_folders()
    assert len(folders) == 24
    for folder in folders:
        metadata = yaml.safe_load((folder / "metadata.yaml").read_text())
        assert metadata["name"] == folder.name
        assert metadata["stability"] in {"alpha", "beta", "stable"}
        assert metadata["dependencies"]["kubeflow"][0]["name"] == "Pipelines"
        verified = datetime.datetime.fromisoformat(metadata["lastVerified"].replace("Z", "+00:00"))
        assert verified.tzinfo is not None
