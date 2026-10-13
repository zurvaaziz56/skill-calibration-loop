# skill-calibration-loop

A system that makes AI writing agents (Claude Code "skills") improve from real human edits, safely.

Every draft an agent produces is captured, along with the final version a human actually sent. A weekly job compares them and writes proposed rule changes, each with its evidence. Nothing changes until a person approves, and every approved change has to pass a regression check. It is also watched on probation and can be rolled back with one command.

## The problem it solves

Calibrated writing agents drift. Clients' tastes change, editors keep making the same correction, and the agent keeps making the same mistake, because nobody writes the lesson back into its rules. When people do write lessons back, they tend to pile rules on until the prompt is over-constrained and quality drops. This loop makes improvement routine, evidence-based and reversible.

## What's in this repo

| File | What it is |
|---|---|
| `calibration-gate.py` | A Claude Code **Stop hook**. It makes no model calls and decides deterministically: it only steps in when a tracked skill actually ran in the current turn, then checks the capture happened. It fails open on any error. |
| `docs/calibration-loop-build-spec.md` | The full design: capture, weekly sweep, proposals, apply lane, risks and mitigations. |
| `docs/calibration-capture-protocol.md` | Where drafts and finals are stored, the register schema, and the closing rules for open rows. |
| `docs/calibration-apply-lane-runbook.md` | The gates a change must pass before it's applied, plus probation and rollback. |

## How it works

1. **Capture.** When a tracked skill delivers a draft, it saves `input.md`, `draft.md` (`draft-v2.md`, `draft-v3.md` for revisions, never overwritten) and `meta.json`, and appends a row to a register. The final sent version is stored as `final.md` when known.
2. **Enforce.** `calibration-gate.py` runs when Claude Code tries to end a turn. If a tracked skill ran and no capture happened recently, it blocks the turn with a fix-it message.
3. **Sweep (weekly, read-only).** It diffs draft against final across recent deliverables and writes a proposals file. It never edits a skill.
4. **Apply (only on a human "apply").** Gates:
   - leave protected sections untouched
   - cite evidence from 2–3 or more separate deliverables
   - keep the skill file under 3,000 words (consolidate or retire a rule to add one)
   - stay inside the baseline style envelope
   - pass a golden-set regression with an independent judge
   - pass a consistency sweep

   Then it bumps the version, puts the skill on probation for its next 2 deliverables, and keeps a one-command rollback ready.

## Setup

1. Copy `calibration-gate.py` somewhere stable, e.g. `.claude/hooks/` in your project.
2. Edit the `ENROLLED` list at the top to the names of the skills you want tracked. The register folder defaults to `Calibration Loop/` in the project root; set `CALIBRATION_LOOP_DIR` to use a different one.
3. Register it as a Stop hook in `.claude/settings.json`:

```json
{
  "hooks": {
    "Stop": [
      { "hooks": [ { "type": "command", "command": "python3 .claude/hooks/calibration-gate.py" } ] }
    ]
  }
}
```

4. Add the capture block from `docs/calibration-capture-protocol.md` to each tracked skill's `SKILL.md`.

## Limits

- The weekly sweep and the apply lane are written as runbooks for an AI session to follow, not as standalone code.

Built with Claude Code.
