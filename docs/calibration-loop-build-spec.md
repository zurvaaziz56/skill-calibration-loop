# Skill Calibration Loop — Build Spec v1

**Status:** SPEC — written 2026-08-21 from the design conversation with Zurva. Build starts on her go. Nothing in this doc is implemented yet.
**Owner of decisions:** Zurva. **Builder:** Claude (Fable main thread for all skill/rubric writing; Opus subagents for sweeps and diffs — standing economy rules).

---

## 1. Purpose and logic

Every client/voice skill is a compressed model of "what gets approved," calibrated from a fixed sample set at one moment. Reality drifts (client preferences, editor pushback, Zurva's own taste) and Zurva edits drafts before sending — each edit is a labeled signal: *this is what the output should have been.* Today that signal is captured only when Zurva remembers to open a session and run the Factory's Calibrate mode.

The loop automates detection → diff → proposal (and, later and selectively, the patch itself), so skills sharpen from real use without manual sessions. **Objective metric:** percent-of-draft-changed per skill over time. Falling = working. Flat or rising = the loop is not earning its keep for that skill.

It does NOT change how a skill improves (same Factory Calibrate logic, same finals-win rule). It changes who does the bookkeeping and stops signals evaporating between sessions.

## 2. Zurva's decisions (2026-08-21)

1. **Propose-only to start.** Weekly Calibration Proposals file; nothing changes until she says "apply." Auto-apply later, selectively, per category, only after a clean track record.
2. **All voice/client skills enrolled.** Enrollment is universal; *execution is activity-driven* (see §4): dormant skills cost nothing and cannot produce proposals until they are used again.
3. Quality gates (§6) are built BEFORE the first patch is ever applied.

## 3. Components

### 3.1 Draft Register (the hinge)
`Calibration Loop/Draft Register.md` (+ machine copy `draft-register.jsonl`). One row per generated draft:
`date · skill · skill_version · client · deliverable_title · draft_path (stored copy) · target (Drive file ID / local path / "chat-only") · author_of_final (Zurva / client / editor / unknown) · status (drafted / final_detected / diffed / proposed / applied / ignored)`
**Capture hook:** every enrolled skill appends its row at generation time. Drafts stored under `Calibration Loop/drafts/<skill>/<date> - <title>.md`.

### 3.2 Per-skill Calibration Profile (one-time, built now for every enrolled skill)
`Calibration Loop/profiles/<skill>.md`:
- **Golden set** — the approved samples the skill was built from (+ later approved finals), frozen; inputs + approved outputs.
- **Baseline fingerprint** — measured ranges and signature patterns from the build (word counts, structure, allowed/banned patterns). Immutable unless Zurva explicitly re-baselines.
- **Protected sections** — client hard constraints, claiming firewall, policy rules: never auto-changed; any touch → flagged.
- **Rule budget** — max size/rule count for SKILL.md; patches must consolidate or retire to add.
- **Version + metric history** — version, date, evidence, %-changed trend.

### 3.3 Weekly sweep — scheduled task `skill-calibration-sweep`
Sunday evening local time (before `vault-weekly-net`). Steps:
1. Read register → select skills with rows since last run (**activity gate** — everything else skipped).
2. For each candidate row: fetch the current final (READ-ONLY Drive connector by file ID / local file). Changed beyond threshold + stable for N days → `final_detected`.
3. Diff draft vs final; classify edits: mechanical · structure · voice · facts · client-rule. Check Drive revision metadata for author where available.
4. Pattern test: a candidate rule needs recurrence across **≥2–3 separate deliverables** (one-offs logged, not proposed).
5. Pre-check each candidate against the golden set (independent judge agent: "would this rule have hurt any approved sample?").
6. Write `Calibration Loop/proposals/Calibration Proposals - <date>.md` — per skill: evidence (deliverables, diffs), pattern, exact proposed SKILL.md change (as a diff), risk class, judge verdict, %-changed metric update.
7. Notify: one line in the morning deck / Hermes nudge; daily-log entry. No skill is modified by this task.
Delegation: sweep + diff + judge = Opus subagents; proposal authoring reviewed before write.

### 3.4 Apply lane
Zurva says "apply calibrations" (or names specific proposals) → Fable session runs Factory **Calibrate mode** on the approved items: golden-set regression test (patched skill regenerates golden inputs → judge scores vs approved outputs; **score drops → patch rejected**) → versioned in-place patch + changelog citing evidence → consistency sweep across skill files → rule-budget check → rebuild `.skill` installer → register rows → `applied` → git commit + push → probation flag on the skill (next 2 deliverables watched; %-changed rises → auto-flag for rollback).
Project skills load from `.claude/skills/` so a patch is live in this workspace immediately; installers are for other machines.

### 3.5 Auto-apply (later, per category, Zurva's go)
Eligible only for categories with a clean proposal record (e.g., recurring wording preferences inside one skill). Never for protected sections, never for facts/claims. Always notified, always revertible (git).

## 4. Enrollment (universal) and activity (computed)

| Skill | Signal | Current activity |
|---|---|---|
| `newsletter-agent-leadership-consultant` | The leadership consultant's edited finals | dormant until next brief |
| `magazine-agent-wellness-publisher` (newest version only) | The magazine's publisher's edited packages | dormant (closed, door open) |
| `post-writer-executive-a`, `post-writer-executive-b` | posted vs drafted | dormant (GTM paused) |
| `pr-qa-pipeline-pr-agency` (current version only) | Agency-editor and contributor feedback patterns | dormant (PR agency paused) |
| `personal-post-writer` | Zurva's edited launch drafts | dormant until posting starts (v0.5 → v0.9 at ~5 edited posts) |
| Not enrolled | — | Factory, engagement/comment batches, utilities. |

Dormant skills: profile built now, capture hook installed now, zero runtime until a draft is generated. They re-enter automatically.

## 5. Build order

- **Phase 1 — foundation (first):** Draft Register + drafts store; Calibration Profiles + capture hooks for all enrolled skills (one-time); **backfill** from existing draft-vs-final pairs as the baseline + diff-engine test. Hygiene: one live version per skill — archive the wellness magazine v1.0/v1.1 and older PR-pipeline variants (installed duplicates cause trigger collisions).
- **Phase 2 — detector:** `skill-calibration-sweep` weekly task, propose-only; first proposals reviewed with Zurva.
- **Phase 3 — apply lane + metrics:** Calibrate-mode application on approval, golden-set gate live, %-changed chart (later a lane in a Skill Stack board). After ~1 month clean: discuss auto-apply for low-risk categories.

## 6. Quality gates (why skills cannot quietly get worse)

| Degradation path | Gate |
|---|---|
| One-off edits become rules | recurrence threshold ≥2–3 deliverables |
| Rule bloat (over-constrained prompt) | rule budget; consolidate-or-retire to add |
| Drift from approved voice | frozen baseline fingerprint; patches refine inside the envelope |
| Regression (fix A, break B) | golden-set regression test with independent judge; score drop = reject |
| Wrong attribution (client reformat read as voice) | edit classification + revision-author check |
| Hard rules loosen | protected sections flagged, never auto-changed |
| Bad patch slips through | versioned (git), probation on next 2 deliverables, one-command rollback |

No self-updating system guarantees quality; these gates make degradation detectable, bounded, and reversible — and Zurva remains the approval step in propose-only mode.

## 7. Open questions for Zurva
1. Sweep day/time — Sunday ~20:00 local time proposed.
2. Notification surface — Hermes Discord nudge, morning deck, or both.
