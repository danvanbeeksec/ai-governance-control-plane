# Candidate rollout checklist

Merge the reviewed Framework change first, followed by the Control Plane, then the Assistant and Copilot kit. The dependency pins identify exact commits, so preserve those commits when merging or update dependent pins after a squash or rebase. Do not move existing release tags.

1. Verify CI and the clean installed-wheel check on the exact candidate commit.
2. Confirm package metadata, source manifest, universal lock, generated requirements, compatibility tables, and generated bundles agree.
3. Merge only after owner review. Rebuild the hosted demo from the approved revision.
4. Verify Framework integrity, a complete synthetic assessment, design comparison, review-brief download, and inventory reassessment in the hosted app.
5. Confirm Demo Mode remains session-only. Do not enable SQLite persistence on the anonymous public demo.
6. Create reviewed release tags and release notes only after the appropriate verification. The package distribution and authoritative library have separate versions: Framework package 1.2.1 still carries control library 1.2.0.
7. Retain the prior approved revision as a rollback target. Revert or redeploy the prior compatible dependency chain if verification fails; never bypass a digest check.

Local source and browser verification are not confirmation of hosted deployment. The Assistant container remains subject to its Docker and HTTP CI checks; Microsoft and Claude surfaces require their own actual conversation validation.
