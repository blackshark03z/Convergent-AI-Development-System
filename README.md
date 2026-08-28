# Build OS — simplified consequential-boundary guard

Build OS leaves normal development to Git, editors, tests, CI and the Worker.
It deterministically checks explicit consequential boundaries.

Normal work stays native:

```text
understand -> inspect -> edit -> focused test -> ordinary commit -> continue
```

No task lifecycle, grant, adoption or continuation operation is required for
ordinary development.

## Public surface

Read current Git and external-effect truth without writes:

```powershell
python scripts/ai.py --root D:\path\to\repo inspect
```

Check a declared boundary against the live base-to-HEAD and dirty delta:

```powershell
python scripts/ai.py --root D:\path\to\repo check `
  --base <commit-or-ref> --boundary R3 `
  --expected app.py --strict app.py --prohibited "secrets/**"
```

`expected` deviations are `WARN`. `strict` or `prohibited` violations are
`BLOCK`. A clean pre-existing descendant commit receives no special authority.
Tracked `.buildos/**` changes always block.

Use a repo-local policy when the caller wants path intent in a file. It is read
fresh on every invocation and is never migrated or adopted:

```json
{
  "expected_paths": ["src/**"],
  "strict_paths": ["src/**", "tests/**", ".buildos-scope.json"],
  "prohibited_paths": ["secrets/**"]
}
```

```powershell
python scripts/ai.py --root D:\path\to\repo check `
  --base <commit> --boundary R3 --policy .buildos-scope.json
```

For one explicitly declared high-cost local action:

```powershell
python scripts/ai.py --root D:\path\to\repo high-cost `
  --base <commit> --strict "src/**" -- python focused_tool.py
```

Build OS does not classify the command. It re-observes exact Git state at the
last practical point, uses native argv without a shell, and either returns
`BLOCK_STALE_STATE` or invokes the command once.

## External effects

External dispatch is available only through the narrow Python API
`buildos.external_effect.execute_external_effect(...)`, where an explicit
integration supplies one known dispatcher callable. There is no generic remote
command, provider plugin system or automatic retry.

Exact intent is durable before dispatch. The record becomes
`DISPATCH_UNCERTAIN` before the one provider call. A crash or ambiguous response
therefore cannot be mistaken for no dispatch.

Inspect or reconcile durable effect truth:

```powershell
python scripts/ai.py --root D:\path\to\repo effect list
python scripts/ai.py --root D:\path\to\repo effect inspect --effect-id <id>
python scripts/ai.py --root D:\path\to\repo effect retry-check --effect-id <id>
python scripts/ai.py --root D:\path\to\repo reconcile `
  --effect-id <id> --outcome NO_EFFECT_CONFIRMED `
  --evidence "canonical provider lookup proves absence"
```

Ambiguous effects are never redispatched automatically. Retry is only reported
safe when exact provider-enforced idempotency or positive no-effect evidence is
present.

Effect records live under the repository's common Git administration directory
(`buildos/effects`), not product history. This is the only default durable
runtime state in the simplified architecture.

## Repository map

- [AGENTS.md](AGENTS.md): short operating map for a fresh Worker.
- [ARCHITECTURE.md](ARCHITECTURE.md): durable ownership and safety invariants.
- [TASK.md](TASK.md): current goal and progress only.
- [docs/EFFECT_SAFETY.md](docs/EFFECT_SAFETY.md): effect contract and recovery semantics.
- [docs/LEGACY_V125.md](docs/LEGACY_V125.md): historical compatibility boundary.

Run active tests with:

```powershell
python scripts/self_test.py
```

Historical v1.25 lifecycle sources remain repository evidence during the
transition, but they are disconnected from the default CLI and are not active
task authority. The v1.26 executor-lifecycle candidate was experimental and was
not adopted into this architecture.
