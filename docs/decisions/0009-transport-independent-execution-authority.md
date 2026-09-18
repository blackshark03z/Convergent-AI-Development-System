# DR-0009: Preserve execution authority across transport availability changes

Status: Accepted
Date: 2026-09-19
Scope: Harness / Transport / Execution Authority

## Context

CADS already requires Goal, authority, acceptance and consequence semantics to survive changes in model, harness, protocol and execution topology. AE-030 explicitly treats protocol lock-in as a failure class.

Owner real-use exposed a concrete transport failure mode: MAR may be healthy, aligned and holding the canonical durable project/task state while a particular Web chat does not expose MAR itself as a callable tool. The absence can come from host-side app attachment, plan/workspace capability, tool discovery or conversation-local connector state. That condition says nothing by itself about whether the MAR task exists, whether it is complete, or whether a new task should be submitted.

On 2026-09-19 an alternate bounded path was proven against the same live MAR authority:

```text
Web Tech Lead -> ChatCode stable gateway -> thin local adapter -> MAR loopback MCP
```

The adapter listed the same six canonical MAR tools and MAR `project/context` returned CADS revision `1a6c4caedda329c9700fcda27e410a0f750bb487`, matching canonical local CADS reality. The MAR-side adapter is recorded at MAR commit `ba0b2dc`.

This evidence supports a transport rule; it does not make ChatCode a CADS dependency or a MAR authority.

## Decision

Preserve execution authority independently of the transport used to reach it.

1. **Direct authority path first.** When MAR is directly callable from the current cognition client, use that direct MAR surface.
2. **Equivalent bounded transport is allowed.** When direct MAR attachment is unavailable, a thin adapter may relay calls only when it reaches the same MAR durable authority and preserves MAR's task/tool semantics.
3. **Transport adapters are non-authoritative.** They may translate or relay calls, but they do not own Goal state, Task/Attempt/Run Epoch, workspace authority, verification, integration, recovery or release truth.
4. **Do not recreate work because a tool disappeared.** Missing direct tool exposure is not evidence that a durable task is absent. Recover current project/task truth through an equivalent authority-preserving path before considering any resubmission.
5. **Do not emulate MAR by direct repository mutation.** If the Goal requires MAR execution/integration authority, a Web Tech Lead must not replace unavailable MAR tooling with ad-hoc filesystem/Git changes and then claim equivalent MAR verification/integration.
6. **Fail closed on unproven equivalence.** If the alternate transport cannot prove that it reaches the intended MAR authority or cannot preserve required semantics, report the transport boundary as unavailable rather than inventing state or widening authority.
7. **Keep protocol mechanics removable.** ChatCode, MCP, provider-native connectors and future protocols are replaceable transport/harness mechanisms. CADS semantics must not depend on their control vocabulary.

## Consequences

- A chat may truthfully say “direct MAR tool is unavailable here” without concluding “MAR task state is unavailable” or resubmitting completed work.
- Transport recovery becomes cheaper: reconnect, alternate adapter or another compatible client may recover the same durable MAR state.
- Existing verified/integrated work remains identified by MAR/Git evidence across chat or connector changes.
- Thin adapters may be introduced or removed without creating a sixth CADS control, a new workflow state, a second task database or a second execution authority.
- Current ChatCode -> MAR adapter evidence is an implementation example, not a permanent architectural dependency.
- Product/engineering work still stops when neither the direct path nor an equivalent authority-preserving path is available.

## Revisit

Revisit if a future execution authority exposes no transport-independent durable identity/state, if representative evidence shows adapters materially alter semantics, or if direct provider-native execution can provide equivalent durable authority and makes the current MAR boundary obsolete.
