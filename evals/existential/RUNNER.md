# Existential benchmark runner v1

Run a qualified case with one command from the CADS root:

```powershell
python scripts/run_existential_case.py XP-001
```

The default batch uses R `gpt-6-sol` at high effort (240 seconds per invocation)
and I `gpt-6-luna` at medium effort (600 seconds per invocation). The same
settings apply to all four arms. The runner creates a timestamped disposable
directory under the system temporary directory and prints its location. Pass
`--out D:\path\to\run` to choose another directory outside CADS and the source
repository. An existing runner directory requires `--force`; it is deleted and
recreated. The runner refuses to delete an unmarked directory.

```powershell
python scripts/run_existential_case.py XP-001 --preflight
python scripts/run_existential_case.py XP-001 --probe-models
python scripts/run_existential_case.py XP-001 --r-model gpt-6-sol --i-model gpt-6-luna --r-effort high --i-effort medium --r-seconds 240 --i-seconds 600
python scripts/run_existential_case.py XP-001 --record-sot
```

`--preflight` validates the case manifest, qualified oracle hash, pinned source
revision, prompts, and Codex executable without starting models. `--probe-models`
makes a short, tool-free call to each configured model to check availability and
quota. It does not test whether a model can read the repository. `--codex-cli` selects
a different executable. `--record-sot` writes only `result.json` and `result.md`
under `evals/existential/results/<case>/<run-id>/`; it never commits or pushes.
Full prompts, model events, stderr, diffs, and oracle logs stay in the disposable
run directory. XP-002 is qualified only after its pinned neutral projection and held-out oracle pass the recorded discrimination checks.

Each qualified case has `RUNNER.json` with source candidates, pinned base,
neutralization paths, qualification file/status, qualified neutral tree, and an
oracle command. The runner archives the pinned base, removes only the declared
paths, creates a fresh one-commit neutral repository, and verifies its tree
against the qualified projection. Four independent clones receive only this
neutral tree. R inspects its assigned clone and produces an Implementation Brief; I
works in its assigned disposable clone. R reviews the staged candidate diff and
visible evidence, may issue one repair brief, and then gives a final verdict.
Every invocation is fresh; its needed continuity is included in the persisted
prompt. All four candidates are frozen as Git tree IDs before the held-out oracle
is run on separate evaluation copies. R/I prompts prohibit hidden oracle,
historical reference, sibling-arm access, and external or production effects.

On this Windows machine, Codex CLI `--sandbox read-only` rejects even repository
read commands. Both R and I therefore use the CLI automation/full-access mode.
R's prompt explicitly forbids edits and external effects. Immediately before and
after each R invocation (phase 1, review, and final review), the runner compares
the arm's Git HEAD/index entries and the content of every worktree file, including
untracked files. Any difference invalidates and stops the batch without resetting
the arm, even if R exits with an error or timeout. I may edit only its disposable
arm clone. The neutral clone and prompts contain no hidden oracle or reference;
prompts forbid access to sibling arms and results. Full-access mode is not an
OS-enforced filesystem or network isolation boundary. Use a machine/container
with appropriate external isolation when that stronger property is required.

Statuses: `COMPLETE`, `CASE_NOT_READY`, `NEEDS_AUTH` (quota/auth), `NEEDS_OWNER`
(material Owner ambiguity), and `HARNESS_INVALID` (execution/contract failure).
Exit code is zero only for a complete batch or successful preflight/probe.
An oracle `FAIL` is a scored product outcome, not a harness failure. `READY`
is R's judgment; only the frozen held-out oracle supplies independent outcome
evidence.


## Full-access contamination guard

On this Windows Codex CLI build, the nominal read-only sandbox rejects even repository read commands. R and I therefore execute only inside disposable benchmark clones using Codex automation mode. This is **not** treated as filesystem isolation.

The runner compensates with fail-closed guards:

- every R invocation must leave the Git worktree/index byte-for-byte unchanged;
- prompts forbid external/production effects and hidden/sibling inspection;
- phase traces are scanned for case-specific hidden-reference/oracle markers, the canonical CADS/source paths, and sibling-arm workspace paths;
- any detected contamination is `HARNESS_INVALID`, never a scored arm result.

This trace guard is defense-in-depth, not a claim of perfect OS-level sandboxing.
