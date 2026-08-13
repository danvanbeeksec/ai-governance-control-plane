# Streamlit Community Cloud Deployment Guide

## Purpose and boundary

This guide deploys the synthetic demonstration to Streamlit Community Cloud. It does not create
a production governance service. The hosted app must remain limited to fictional and synthetic
information and must not be represented as an approval, compliance, legal, residual-risk, or
control-effectiveness determination.

## Deployment prerequisites

Before creating an app, confirm:

- `main` contains only reviewed changes and all GitHub checks pass;
- the framework dependency and `data/framework-source.yaml` pin the same exact commit;
- the packaged framework passes digest, schema, version, count, ID, and reference validation;
- every bundled synthetic assessment completes successfully;
- no secret, credential, personal data, nonpublic data, employer material, or client material is
  present in the repository, commit history intended for deployment, fixtures, screenshots, or
  documentation;
- the README, application disclaimers, license, references, and public claims have received a
  point-of-use review;
- the downloaded JSON contains only the submitted synthetic case and documented provenance;
- `CONTROL_PLANE_DATA_MODE` is unset or explicitly set to `demo`, never `local`;
- the intended app URL and initial sharing state are recorded.

## Create an initial hosted review instance

1. Sign in to Streamlit Community Cloud with the GitHub account that administers the repository.
2. Create an app from `danvanbeeksec/ai-governance-control-plane`.
3. Select branch `main` and entrypoint `app.py`.
4. Select Python 3.12.
5. Do not configure secrets. The demonstration has no secret-backed integration.
6. Choose a clear, portfolio-appropriate subdomain.
7. Keep the app unannounced while completing the hosted verification checklist.

Community Cloud obtains the separate framework during dependency installation from the exact
commit in `requirements.txt`. The application then verifies the packaged artifact against
`data/framework-source.yaml`. A mismatch prevents assessment execution.

## Hosted verification checklist

- The page title, favicon, sidebar, definitions, disclaimers, and repository links render.
- The sidebar reports framework version 0.1.0 and 35 verified controls.
- Each bundled synthetic example loads its own intake values.
- Every example produces its documented baseline, final tier, and risk elevation rules.
- The control categories account for every framework control exactly once.
- Required controls, unresolved applicability decisions, and enterprise dependencies appear in
  the intended order with the intended guidance.
- Human-readable explanations contain no internal field names or machine-readable values.
- The JSON download opens, contains the expected versions and provenance, and contains no data
  from another browser session.
- Invalid or unavailable framework data fails closed without displaying internal error details.
- Desktop and mobile layouts remain readable, including the longest control requirements and
  human-confirmation questions.
- Refreshing the page does not preserve an earlier assessment result.
- A new submission appears only in the current session and never creates a SQLite file.

## Publication decision

Do not publish or promote the URL until the hosted checklist and the repository's point-of-use
review are complete. Record the reviewed commit and date. Public sharing is approval to expose
that reviewed demonstration only, not future commits or new data sources.

## Update and rollback

Streamlit Community Cloud follows the configured repository branch. Merge only reviewed changes
to `main` and repeat the hosted checks after material changes.

If a deployment is defective or unsuitable for public access:

1. Change the app to private or remove the public link from portfolio surfaces.
2. Revert the defective repository change through a reviewed pull request, or temporarily point
   the app to the last reviewed commit or recovery branch.
3. Confirm the hosted app reflects the recovery version.
4. Repeat the complete hosted verification checklist before restoring public access.
5. Delete the Community Cloud app if safe recovery cannot be established promptly.

No rollback procedure should preserve or restore user-submitted information because public Demo
Mode has no intentional persistence. SQLite is reserved for explicitly configured local developer
and testing use.
