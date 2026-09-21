# DR-0010: Local research path attachment boundary

Status: Accepted
Date: 2026-09-20
Scope: Integration / Authority / Research

## Decision

A chat may inspect a user-supplied local Windows path without first creating a MAR task or MAR workspace.

Ownership is split by intent:

- ChatCode owns local path resolution, project reuse/registration, and read/research access.
- MAR owns isolated development execution only after the user intent changes to product/source mutation.
- Read attachment never implies mutation authority.

## Canonical flow

1. Resolve the supplied path through D:\ChatCode\Automations\attach-local-path.ps1.
2. If the resolver returns EXISTING_PROJECT, reuse the returned ChatCode alias.
3. If it returns NEEDS_REGISTRATION, call ChatCode add_project with path=attach_root and alias=suggested_alias.
4. Research using bounded ChatCode read capabilities.
5. Do not create a MAR workspace for read-only inspection.
6. If the user later requests implementation, compile that intent into the normal CADS/MAR development flow.

## Resolver contract

Schema: chatcode-local-path-attach-v1

Semantic states:
- EXISTING_PROJECT
- NEEDS_REGISTRATION

A file input attaches its parent directory and returns relative_target.

The resolver reads ChatCode projects.json only to resolve existing roots. It never edits the registry. Registration remains exclusively through ChatCode add_project.

## Acceptance evidence

Verified on 2026-09-20:

- New unregistered path D:\_chat_attach_e2e_20260920 was registered through ChatCode add_project.
- ChatCode read_file immediately returned ATTACH_LOCAL_PATH_E2E_OK.
- No MAR task or MAR workspace was created for that read-only research flow.
- Existing project resolution: D:\Story Auto -> EXISTING_PROJECT / story-auto.
- New path resolution: D:\_chat_attach_unregistered_probe -> NEEDS_REGISTRATION.
- File path resolution: D:\_chat_attach_e2e_20260920\PROBE.txt -> attach-e2e-20260920 with relative_target=PROBE.txt.
- Resolver SHA-256: 2fa1c35cb557be48b04964f9eef4c736b70a49647de4d938bb98772b4846ce47
- Operational workflow: D:\ChatCode\Knowledge\LOCAL_PATH_ATTACH_WORKFLOW.md

## Product limitation

ChatCode 2.1.5 does not expose a native single-call attach_local_path capability or custom-capability registration API. The accepted implementation composes existing supported capabilities.

A future native implementation should preserve this contract and remain idempotent for already-registered roots.

## Safety

- Missing paths fail before registration.
- Existing roots are reused.
- Resolver does not mutate user files or ChatCode registry state.
- add_project remains the registration authority.
- Research attachment does not widen write, Git, remote, deploy, or MAR authority.
