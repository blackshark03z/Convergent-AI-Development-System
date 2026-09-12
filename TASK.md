# Goal

Add a narrow, safe path for reusable external specialist Agent Skills without creating a capability-management subsystem: ordinary targeted research remains the default, while a materially useful reusable skill may be vetted, pinned and used as non-authoritative advisory context. Make CADS-owned skills portable through deterministic Agent Skills projections from one canonical source.

# Critical User Journey

AI Tech Lead encounters a material knowledge gap -> performs ordinary targeted investigation -> only when a reusable external specialist skill is materially preferable to ordinary research, evaluates its relevance against the current Goal and active project/version reality -> vets immutable source identity, exact docs-only content, license and instruction conflicts -> persists the exact accepted bytes plus optional provenance lock only when reuse is justified -> activates the pinned skill as advisory context -> continues normal CADS Change / Acceptance / Consequence. Separately, a supported harness can receive deterministic Agent Skills-compatible projections of CADS-owned skills without creating a second canonical knowledge source.

# Acceptance

- Add one conditional `skills/core/external-skill-acquisition.md` method called from existing Knowledge-Gap Responsibility; it must not become a sixth control or generic capability subsystem.
- Ordinary targeted research remains the default. Stack/framework detection is advisory evidence only and cannot by itself authorize persistent skill installation.
- External skills have no independent CADS authority: they cannot redefine Goal/Acceptance, override repository/runtime truth or Decision Records, suppress tests, authorize consequential effects, or claim DONE.
- Initial persistent external-skill support is fail-closed to Markdown/reference-only content. Skills containing executable scripts, opaque/binary assets, or live network-fetching behavior are research-only/deferred until future evidence justifies a stronger boundary.
- When an external skill is persisted for reuse, use an optional project-local provenance lock conforming to `skills/external-skills-lock.schema.json`; no empty lockfile is created for projects that use no external skills.
- Provenance records immutable source revision/path, exact bundle hash, license, content class, selection reason, review time and review method. Hash identity alone is never trust or correctness proof.
- New external skills and changed skill bytes are never automatically persisted/updated from stack detection. A previously vetted pinned skill may be activated automatically when materially relevant.
- Project-local skill adoption does not make a skill CADS-recommended. CADS-wide recommendation requires representative evidence and remains scoped to the evaluated model/harness/version unless cross-harness evidence exists.
- Adopt Agent Skills / `SKILL.md` as a portability target for CADS-owned internal skills via one deterministic projector and explicit routing metadata. Canonical semantic content remains under `skills/core/*.md` and `skills/product/*.md`; generated projections are build/output artifacts, not manually maintained sources.
- The projector must preserve canonical skill body bytes, emit stable `name`/`description` frontmatter, fail clearly on invalid/missing metadata, and support a read-only `--check` mode.
- Preserve the frozen Standard, Five Controls, Thin Guard and existing authority model. Do not add AutoSkills as a dependency, registry/marketplace, resolver, updater, daemon, trust score, skill database or second runtime.
- Add focused tests and keep the full CADS regression suite passing without weakening existing tests.

# Acceptance Fixture / Evidence Basis

1. A React dependency exists in a monorepo but the current Goal is backend-only: detection alone does not persist or activate a React skill.
2. A current FastAPI Goal needs reusable framework-specific guidance: a docs-only skill pinned to an immutable source revision and exact bytes may be persisted after relevance/license/instruction review.
3. A candidate skill contains a shell script or fetches mutable remote instructions: current CADS does not persistently activate it; the AI may inspect its content as ordinary research only.
4. Two safe skills conflict on architecture or testing guidance: project/CADS authority and current Goal decide; popularity or skill order cannot launder one into authority.
5. Skill guidance targets framework version X while the project uses materially different version Y: the skill is not accepted without compatible evidence.
6. A pinned external skill changes upstream: current project keeps exact accepted bytes until an explicit re-vet; no background update occurs.
7. CADS-owned internal skill projection generates deterministic Agent Skills-compatible `SKILL.md` files whose bodies match canonical sources and whose routing descriptions are explicit.
8. A skill improves one model/harness in representative evals: that evidence does not automatically establish CADS-wide value on another harness/version.

# Non-goals

No sixth CADS control, AutoSkills dependency, skill marketplace/registry service, package resolver, sync daemon, background updater, skill database, online trust score, external-skill execution authority, automatic skill installation from stack detection, vendor-specific duplicated CADS standards, executable external-skill support in this slice, model router, or Standard amendment.

# Constraints

Preserve `Reality -> Intent / Design -> Change -> Acceptance -> Consequence`, Knowledge-Gap Responsibility, DR-0003 anti-accretion, DR-0004 trusted-evidence boundaries, DR-0006 acceptance-surface provenance and the frozen Standard. Prefer ordinary research unless persistent reusable specialist instructions materially improve the current Goal. One canonical CADS skill source must remain authoritative; portability outputs are deterministic projections only.

# Material Decisions

- Accept the independent review refinement: the real gap is safe reusable **external specialist instruction acquisition/vetting**, not missing knowledge-gap detection.
- Borrow AutoSkills patterns (weak-signal detection, dry-run thinking, immutable source revision, content hashes, curated/mirrored sources) but do not adopt AutoSkills itself or treat any external registry label as CADS trust proof.
- Adopt Agent Skills / `SKILL.md` as a portability target for CADS-owned skills while keeping canonical semantics in existing CADS Markdown sources.
- External skills are untrusted advisory engineering inputs with zero independent authority in CADS domains.
- v1 persistent external-skill support is docs/reference-only; executable/network-fetching bundles are deferred.
- Persistent project-local external skills use exact provenance; project-local use and CADS-wide recommendation are different claims.

# Progress / Discoveries / Next

- Independent reviewer verdict: `ACCEPT_WITH_CHANGES`.
- Review confirmed a narrow external-skill trust/provenance/portability gap while rejecting a capability-management subsystem.
- Minimum safe scope selected: one conditional acquisition/vetting method, optional provenance schema, one Decision Record, deterministic Agent Skills projection, and focused tests; frozen Standard remains unchanged.

Next: implement the bounded slice, run focused projection/security tests, then full CADS regression before commit/push.
