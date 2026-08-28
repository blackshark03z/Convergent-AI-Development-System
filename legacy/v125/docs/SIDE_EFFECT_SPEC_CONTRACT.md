# Side-effect design/spec contract

This contract closes a design-layer gap that ordinary code checks cannot
close: a project may have multiple local status fields, provider outcomes,
replay validators and retry gates that appear individually reasonable while
disagreeing about whether an external effect is possible, confirmed, or safe
to repeat.

The contract is provider-neutral and project-neutral. It formalizes four
things before implementation:

1. Independent state dimensions and their named states.
2. Every dangerous, externally visible, destructive, billable, or
   non-idempotent action and its canonical authority predicate.
3. Crash points, possible effect state, retry authority, and recovery action.
4. Current, verified-equivalent legacy, and unmigratable schemas.

Enable it in `.buildos-policy.json`:

```json
{
  "side_effect_contract": {
    "enabled": true,
    "path": "SIDE_EFFECT_CONTRACT.json"
  }
}
```

Start from `templates/project-lifecycle/SIDE_EFFECT_CONTRACT.json.tmpl` and
validate through the lifecycle policy check or directly:

```powershell
python skills/project-lifecycle-bootstrap/scripts/project_lifecycle.py --root <repo> check
python skills/project-lifecycle-bootstrap/scripts/side_effect_contract.py <repo>/SIDE_EFFECT_CONTRACT.json
```

## Mandatory semantics

- Unknown effect state is a queue barrier, never retry authority.
- A non-idempotent action cannot claim an idempotent retry policy.
- A retry labelled `POSITIVE_NO_EFFECT_PROOF_ONLY` must name the semantic proof
  used by every retry/replay path.
- Every semantic consumer names its dangerous `action_id` and role
  (`AUTHORITY`, `RETRY`, `REPLAY`, or `RECOVERY`). Retry, replay and recovery
  roles bind directly to that action's one `positive_no_effect_proof`; a
  globally reused but weaker predicate is rejected.
- If an effect is possible or confirmed, crash recovery forbids retry and
  requires reconciliation.
- Every dangerous action has crash-recovery coverage.
- Exactly one schema is current. A legacy schema is accepted only through an
  explicit deterministic verifier; otherwise it is unmigratable.

Provider request IDs, HTTP codes, local flags, timestamps, filenames and
newest-item heuristics may contribute evidence. None of them independently
becomes canonical no-effect proof unless the contract says so and the verifier
enforces the same semantic predicate everywhere.

The validator continues to accept the original single-action consumer names
as a verified legacy-equivalent shape. Multi-action or newly authored
contracts use explicit action/role bindings so consumer meaning cannot be
inferred from descriptive text.

## Compatibility and migration

An additive optional field may retain the current schema identifier when old
records remain semantically readable. An incompatible state shape requires an
explicit migration operation: detect the source schema, validate the source,
write a new immutable generation and migration receipt, verify it, then swap
the canonical pointer. Never edit historical records in place or silently
coerce an unknown legacy shape into current state.
