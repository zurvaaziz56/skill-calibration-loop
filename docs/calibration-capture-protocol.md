# Calibration Capture Protocol — the hinge of the Skill Calibration Loop

**Purpose:** every enrolled skill records what it produced, so the weekly sweep can later diff the draft against what was actually sent/approved. No capture, no signal. Spec: `Skill Calibration Loop - Build Spec v1.md`.

## Where things live (all inside this folder)
- `Draft Register.md` — human-readable table, one row per generated draft (newest at the bottom).
- `draft-register.jsonl` — machine copy, one JSON object per line, same fields.
- `drafts/<skill>/<YYYY-MM-DD> - <short title>/` — `input.md` (job post / brief / source), `draft.md` (the output exactly as delivered), `final.md` (the sent or approved version, when known), `meta.json`.
- `fixtures/<skill>/` — regression-test inputs; accumulate automatically from `input.md` files (see Apply Lane Runbook).

## Row schema (table and JSONL use the same fields)
`id` (YYYYMMDD-<skill>-NN) · `date` · `skill` · `skill_version` · `client` · `deliverable` · `draft_path` (latest version) · `revisions` (count) · `input_path` · `target` (Drive file ID / local path / "chat-only") · `final_path` · **`final_source`** (`confirmed` | `inferred_next_job` | `inferred_session_end` | `fetched_drive`) · `author_of_final` · `status` · `notes`

**Evidence weight:** `confirmed` and `fetched_drive` finals are full-strength. `inferred_*` finals are weaker: the sweep may use them, but a rule proposal must state how many of its evidence rows are inferred, and a proposal resting ONLY on unmatched inferred finals is capped at MEDIUM risk and flagged.

**Status ladder:** `drafted` → `final_captured` → `diffed` → `proposed` → `applied` | `ignored` | `no_signal`

## When to capture

- **On delivery:** the moment a skill delivers its final output block for a run (not mid-draft thinking). One row per piece of work.
- **On revision:** every revised version in the same session saves as `draft-v2.md`, `draft-v3.md`, … in the same folder, and the row's `revisions` count increases. Never overwrite an earlier version — the revision sequence is the edit signal.
- **On finalisation — three closing rules (Zurva's design, 2026-08-21):**
  1. **Confirmed** — the user supplies the sent/approved text -> `final.md`, `final_source: confirmed`.
  2. **Inferred by next job** — the user starts a NEW job/brief/source for the same skill -> the previous row's latest version is copied to `final.md`, `final_source: inferred_next_job`. Rationale: moving on means the previous piece was finished and used.
  3. **Inferred at session end** — the row is still open when the session ends -> same, `final_source: inferred_session_end`.
  Cases 2 and 3 set `status: final_captured`, `author_of_final: Zurva`. If the user says a piece was never sent or was abandoned -> `status: ignored`; an abandoned draft is never treated as an approved final.
- **Drive-based clients:** the weekly sweep fetches the live doc READ-ONLY by file ID and saves it as `final.md`, `final_source: fetched_drive`. No user action needed.
- **Enforcement:** a project Stop hook (`.claude/settings.json`) checks at turn end that an enrolled skill's delivered draft was captured, and blocks the turn from ending if it was not.

## Graceful degrade (second seat / other workspaces)
If these paths do not exist on the machine running the skill, output the register row as ONE line in chat so it can be logged on the primary seat. Never skip silently.

## The hook block — appended verbatim to every enrolled SKILL.md (between the markers)
<!-- HOOK-BLOCK-START -->
---

## Calibration capture (standing — Skill Calibration Loop)

This skill is enrolled in the Skill Calibration Loop. After delivering a draft (the final output block of a run), before the turn ends:

1. Store the run under `02 Projects/Workflow Automation Hub/Calibration Loop/drafts/<this skill's name>/<YYYY-MM-DD> - <short title>/` as `input.md` (job post, brief, or source material), `draft.md` (the output exactly as delivered), and `meta.json` (skill, version, client, date, target reference).
2. Append one row to `02 Projects/Workflow Automation Hub/Calibration Loop/Draft Register.md` and one JSON line to `draft-register.jsonl` in that folder (schema: `Calibration Capture Protocol.md`). Status `drafted`.
3. If the user supplies the sent or approved version in the same session, save it as `final.md` and set status `final_captured`.

If those paths do not exist on this machine, output the register row as one line in chat so it can be logged on the primary seat. Never skip silently. This hook records what the skill produced; it changes nothing about how the skill writes.
<!-- HOOK-BLOCK-END -->
