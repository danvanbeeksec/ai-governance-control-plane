"""Read-only access to packaged Control Plane policy resources."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path


def _resource_bytes(name: str) -> bytes:
    packaged = files(__package__).joinpath("resources", name)
    try:
        return packaged.read_bytes()
    except FileNotFoundError:
        return (Path(__file__).resolve().parents[2] / "data" / name).read_bytes()


def risk_model_bytes() -> bytes:
    return _resource_bytes("risk-model.yaml")


def applicability_methodology_bytes() -> bytes:
    return _resource_bytes("control-applicability-rules.yaml")


def framework_manifest_bytes() -> bytes:
    return _resource_bytes("framework-source.yaml")
