# Inventory and persistence

## Phase 2 domain architecture

`AI System` is the durable conceptual parent. It owns stable identity, purpose, provider/model
metadata, distinct owner roles, lifecycle state, autonomy, information sensitivity, vendor status,
visibility, record type, timestamps, and reassessment triggers. Assessments are immutable child
events. Each history event retains the submitted assessment, risk decision, framework version and
digest, control-applicability output, and timestamp.

The external AI Governance Control Framework remains authoritative for control statements and
mappings. Stored applicability results are historical evaluation output, not a copied control
library or a new source of control authority.

```text
AI System
├── inventory metadata and owner roles
└── assessment history (append only)
    ├── submitted facts
    ├── inherent-risk decision and rationale
    ├── framework version, commit, and digest
    └── control applicability outcomes
```

## Data modes

### Demo mode, the default

`CONTROL_PLANE_DATA_MODE=demo` uses `SessionInventoryRepository`. It preloads fictional inventory
records into Streamlit session state. New systems and assessments remain in memory for that browser
session. The repository does not open SQLite or write user submissions to disk. Restarting or ending
the session returns the inventory to the clean synthetic seed.

This is the only supported public anonymous deployment mode. Public users must submit fictional or
synthetic information only.

### Local developer mode

`CONTROL_PLANE_DATA_MODE=local` uses SQLite for developer and test use. The default database is
`.local/control-plane.db`; set `CONTROL_PLANE_DATABASE` to choose another path.

```bash
CONTROL_PLANE_DATA_MODE=local streamlit run app.py
```

Local mode creates its schema on first use and seeds the inventory only when it is empty. It is not
a public data service and supplies no authentication, authorization, encryption, tenancy, retention,
backup, or enterprise workflow controls.

## Inventory integrity

The interface flags potential duplicates using similar names, similar purposes, or an exact
provider/model combination. It never merges or rejects records automatically. This is intentionally
a review aid rather than entity-resolution logic.

Synthetic examples cover supervised and autonomous uses, public through restricted information,
internal, vendor, and hybrid delivery, and multiple lifecycle states. Record types distinguish
synthetic examples, temporary submissions, and locally managed inventory.

## Deferred roadmap

Authentication, approval routing, evidence management, integrations, notifications, multi-tenancy,
full lifecycle workflow, migrations beyond the initial local schema, and enterprise persistence are
deferred. Before any shared persistence is introduced, define identity and access, tenant boundaries,
retention and deletion, encryption, audit requirements, schema migration, backup and recovery, and
privacy controls.
