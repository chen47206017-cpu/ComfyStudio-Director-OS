# H3 Upgrade Manifest

## Delivery status

**PARTIAL: evidence and planning controls are complete; production H3 installation is blocked.**

This manifest records exactly what happened in this iteration. It does not imply that any plugin was installed or that an H3 video was generated.

## Installation state

| Item | Before | After |
| --- | --- | --- |
| Production ComfyUI path | G:\ComfyUI | Unchanged |
| ComfyUI core | 0.27.0 | Unchanged |
| Motion Context custom-node directory | Absent | Absent |
| MiniMax H3 Extender custom-node directory | Absent | Absent |
| Plugin dependencies | Not installed | Not installed |
| ComfyUI process | Existing loopback PID recorded | Not stopped or restarted |
| Models, inputs, outputs, workflows | Existing production assets | Unchanged |
| Infinite-Canvas | Existing application | Unchanged |

## Candidate ledger

| Component | Upstream identity | License / dependencies | Install decision |
| --- | --- | --- | --- |
| ComfyUI-H3-Motion-Context current | v0.6.1, d6fb99813863ce7c3cf3bdd09cd43cd9bfdc3e0a | GPL-3.0; no standalone requirements file declared | Blocked: requires ComfyUI >=0.34.0. |
| ComfyUI-H3-Motion-Context legacy | v0.3.1, 725a731e644c669601799da1eb63f4e7497c628f | GPL-3.0; upstream directs 0.33.4 or older to it | Blocked: it cannot supply the absent native H3 node, and no local import/runtime test occurred. |
| ComfyUI_MiniMax_H3_Extender | 88cc10d4db3d51f88e6a3fe097f5a750edf05ab3 | Audit-only alternative | Not installed or activated; excluded by the one-owner rule. |

The upstream repository audit is saved in reports/h3/upstream_motion_context_audit.json. The direct source fetch failed at the Windows Schannel credential layer, so no unpinned archive, checkout, or dependency set was added to the production host.

## Files created by this iteration

- docs/H3_UPGRADE_AUDIT.md
- docs/H3_MODEL_INVENTORY.md
- docs/H3_UPGRADE_MANIFEST.md
- docs/H3_EXTENDER_API_SCHEMA.md
- docs/H3_RESUME_TEST.md
- docs/H3_CONTINUITY_QC_REPORT.md
- docs/H3_FINAL_ACCEPTANCE_REPORT.md
- reports/h3/upstream_motion_context_audit.json
- reports/h3/runtime_baseline_summary.json
- reports/h3/runtime-subject.json
- reports/h3/install_manifest.json
- reports/h3/static_import_dependency_check.json

No file outside the project documentation and reports/h3 evidence area was intentionally created or modified by this iteration.

## Installation and rollback procedure

No production rollback is required because no production modification occurred.

For a later, separately authorized installation, the minimum reversible unit is one pinned plugin directory under G:\ComfyUI\custom_nodes. Before changing it, capture the existing core revision, requirements, custom-node revisions, startup command, and a fresh API baseline. If the compatibility test fails, remove only the newly added plugin directory and restore the pre-install startup configuration. Do not restore over, delete, or overwrite existing models, workflows, inputs, outputs, or unrelated custom nodes.

## Claim boundary

The following are deliberately not claimed: plugin import success, node registration after installation, H3 model loading, Clip generation, continuity, audio continuity, latent persistence, Trim, Assembly, Resume, or final MP4 output.
