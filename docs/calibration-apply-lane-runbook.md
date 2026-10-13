# Apply Lane Runbook — how a calibration proposal becomes a skill patch

**Trigger:** Zurva says "apply calibrations" / "apply 1 and 3, skip 2" in a session. Until then, proposals stay pending and are re-surfaced at every session start (CLAUDE.md standing rule). Nothing is applied by the weekly task — ever.
**Who runs it:** Fable main thread (skill writing is Fable's job). Opus subagents may run the judge/regression steps.

## Gates — in order, any failure stops the patch
1. **Protected sections untouched.** Compare the proposed change against the skill's profile (`profiles/<skill>.md` → Protected). Any overlap → reject, tell Zurva why.
2. **Evidence threshold.** The proposal cites ≥2–3 separate deliverables (or Zurva's explicit instruction). One-off → reject/log.
3. **Rule budget.** SKILL.md ≤ 3,000 words; references ≤ 3 files. The proposal must state its net word delta; growth without consolidation → reject.
4. **Baseline envelope.** The change refines inside the profile's baseline fingerprint (ranges, structure, signature patterns). Moving the envelope requires Zurva's explicit re-baseline decision.
5. **Golden-set regression.** Apply the patch to a COPY of the skill. Regenerate the golden inputs (or the fixtures) with the patched copy; an independent judge agent scores patched vs current outputs against the approved originals/rubric. Any score drop → reject.
6. **Consistency sweep.** The Factory's Calibrate consistency pass across all files of the skill (no rule contradicts another after the patch).

## Apply steps
1. Patch SKILL.md / references in place. Bump `version:` in frontmatter and add a Version History entry citing the proposal id and evidence rows.
2. Rebuild the installer: `cd "<parent of skill folder>" && zip -qr "<homebase>/<skill>.skill" "<skill>/"` (layout: the skill folder is the zip's top-level directory). If the skill is inside zurva-ops, patch the plugin copy too, bump `plugin.json` version, rebuild `zurva-ops.plugin`. Tell Zurva which installed copies need re-install via Save.
3. Update the Draft Register rows → `applied`; update `profiles/<skill>.md` version + metric history; mark the proposal file item "APPLIED <date>".
4. `git add -A && git commit -m "calibrate <skill> v<x> (proposal <id>)" && git push`.
5. Start probation: the skill's next 2 register rows are watched; if %-changed rises above the skill's trailing average, the next sweep writes a rollback proposal.

## Rollback (one command)
`git log --oneline -- ".claude/skills/<skill>/"` → `git checkout <previous-commit> -- ".claude/skills/<skill>/"` → rebuild installer → commit. Profiles and register note the rollback.

## Metric
%-changed per draft = edit distance(draft.md, final.md) / len(draft.md), recorded in the profile's metric history. Falling = the loop is working for that skill.
