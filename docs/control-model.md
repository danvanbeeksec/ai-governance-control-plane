# External Control Framework

The AI Governance Control Plane does not define or maintain an authoritative control framework or control library.

The separate [AI Governance Control Framework](https://github.com/danvanbeeksec/ai-governance-control-framework) owns the control architecture, domain definitions, requirements, evidence guidance, implementation guidance, and public-source mappings.

## Implemented ingestion boundary

The Control Plane installs an exact framework repository commit and consumes the packaged bytes of the explicitly pinned framework artifact. A verified local path remains available for framework development. The integration:

- validates the artifact digest, library schema, versions, control count, control records, unique IDs, and reference keys;
- records the repository, framework version, schema version, commit, and digest with a decision record;
- preserves stable external control IDs;
- keeps risk classification and control-selection rules in the Control Plane;
- avoids silently modifying imported control requirements;
- requires explicit review before adopting a new framework version.

The source pin is maintained in `data/framework-source.yaml`, and the same exact commit is installed through `requirements.txt`. The control plane does not make a runtime network request, cache a committed copy of the framework, or silently follow a branch. Dependency installation obtains the package at build time, and the digest proves whether its artifact matches the reviewed pin.

The [Control Applicability Methodology](control-applicability-methodology.md) and its machine-readable rule contract define how recommendations separate enterprise dependencies, system controls, factual triggers, and human determinations. The [Control Recommendation Engine](control-recommendation-engine.md) implements that contract. Evidence workflows and runtime enforcement are not implemented in the current milestone.
