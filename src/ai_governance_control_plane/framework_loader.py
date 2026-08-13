"""Pinned, read-only ingestion for the external AI control framework."""

from __future__ import annotations

import argparse
import hashlib
import hmac
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .models import FrameworkSource


class FrameworkIngestionError(ValueError):
    """Raised when a framework source or artifact violates the pinned contract."""


class SourcePin(BaseModel):
    model_config = ConfigDict(extra="forbid")

    repository: str = Field(min_length=1)
    commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class ExpectedFramework(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str
    library_version: str
    control_count: int = Field(gt=0)


class FrameworkManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: SourcePin
    expected: ExpectedFramework


class ApplicabilityCondition(BaseModel):
    model_config = ConfigDict(extra="forbid")
    field: str = Field(min_length=1)
    operator: Literal["in", "contains_any"]
    values: list[str] = Field(min_length=1)


class ApplicabilityTriggerGroup(BaseModel):
    model_config = ConfigDict(extra="forbid")
    all: list[ApplicabilityCondition] = Field(min_length=1)


class ApplicabilityMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")
    contexts: list[str] = Field(min_length=1)
    mode: Literal["universal", "conditional", "human_determination"]
    trigger_conditions: list[ApplicabilityTriggerGroup] = Field(default_factory=list)
    required_inputs: list[str] = Field(default_factory=list)
    exclusions: list[str] = Field(default_factory=list)
    rationale: str = Field(min_length=1)


class ControlRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    control_id: str = Field(pattern=r"^AI-[A-Z]+-[0-9]{3}$")
    domain: str = Field(min_length=1)
    layer: str = Field(pattern=r"^(enterprise|ai_system|both)$")
    title: str = Field(min_length=1)
    objective: str = Field(min_length=1)
    requirement: str = Field(min_length=1)
    applicability: str = Field(min_length=1)
    applicability_metadata: ApplicabilityMetadata | None = None
    evidence_examples: list[str] = Field(min_length=1)
    implementation_notes: str = Field(min_length=1)
    references: list[str] = Field(min_length=1)


class LibraryMetadata(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    status: str = Field(min_length=1)
    description: str = Field(min_length=1)


class FrameworkDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str
    library: LibraryMetadata
    reference_catalog: dict[str, str]
    controls: list[ControlRecord] = Field(min_length=1)


class LoadedFramework(BaseModel):
    """Validated external data plus provenance for downstream decision records."""

    source: FrameworkSource
    reference_catalog: dict[str, str]
    controls: list[ControlRecord]


def load_manifest(path: str | Path) -> FrameworkManifest:
    try:
        with Path(path).open(encoding="utf-8") as stream:
            return FrameworkManifest.model_validate(yaml.safe_load(stream))
    except (OSError, yaml.YAMLError, ValidationError) as exc:
        raise FrameworkIngestionError(f"Framework manifest is invalid: {exc}") from exc


def load_framework_bytes(
    artifact_bytes: bytes, manifest_path: str | Path
) -> LoadedFramework:
    """Verify and load framework bytes against the pinned external-source contract."""
    manifest = load_manifest(manifest_path)
    actual_digest = hashlib.sha256(artifact_bytes).hexdigest()
    if not hmac.compare_digest(actual_digest, manifest.source.sha256):
        raise FrameworkIngestionError(
            f"Framework digest mismatch: expected {manifest.source.sha256}, got {actual_digest}"
        )

    try:
        document = FrameworkDocument.model_validate(yaml.safe_load(artifact_bytes))
    except (yaml.YAMLError, ValidationError) as exc:
        raise FrameworkIngestionError(f"Framework artifact schema is invalid: {exc}") from exc

    if document.schema_version != manifest.expected.schema_version:
        raise FrameworkIngestionError("Framework schema version does not match the pinned manifest")
    if document.library.version != manifest.expected.library_version:
        raise FrameworkIngestionError("Framework library version does not match the pinned manifest")
    if len(document.controls) != manifest.expected.control_count:
        raise FrameworkIngestionError("Framework control count does not match the pinned manifest")

    control_ids = [control.control_id for control in document.controls]
    if len(control_ids) != len(set(control_ids)):
        raise FrameworkIngestionError("Framework control IDs must be unique")
    reference_keys = set(document.reference_catalog)
    for control in document.controls:
        unknown = set(control.references) - reference_keys
        if unknown:
            raise FrameworkIngestionError(
                f"Control {control.control_id} contains unknown references: {sorted(unknown)}"
            )

    provenance = FrameworkSource(
        repository=manifest.source.repository,
        library_version=document.library.version,
        schema_version=document.schema_version,
        commit=manifest.source.commit,
        digest=f"sha256:{actual_digest}",
        status="loaded",
    )
    return LoadedFramework(
        source=provenance,
        reference_catalog=document.reference_catalog,
        controls=document.controls,
    )


def load_framework(source_path: str | Path, manifest_path: str | Path) -> LoadedFramework:
    """Verify and load one framework artifact without changing either repository."""
    artifact_path = Path(source_path)
    try:
        artifact_bytes = artifact_path.read_bytes()
    except OSError as exc:
        raise FrameworkIngestionError(f"Framework artifact cannot be read: {exc}") from exc
    return load_framework_bytes(artifact_bytes, manifest_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a pinned AI control framework artifact.")
    parser.add_argument("--source", required=True, help="Path to the external controls.yaml artifact")
    parser.add_argument(
        "--manifest", default="data/framework-source.yaml", help="Path to the source pin manifest"
    )
    args = parser.parse_args()
    framework = load_framework(args.source, args.manifest)
    print(
        f"Loaded {len(framework.controls)} controls from {framework.source.repository} "
        f"at {framework.source.commit}; {framework.source.digest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
