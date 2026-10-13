#!/usr/bin/env python3
"""Calibration-capture gate (Stop hook), deterministic two-stage design.

Stage 1 (this script, no LLM): approve instantly unless an ENROLLED skill was
actually invoked in the current turn. Detection is strict - a Skill tool_use
with a matching skill name, or a <command-name> launch tag - so merely talking
about a skill never triggers the gate.

Stage 2 (mechanical): if an enrolled skill ran, verify the calibration capture
happened (register files touched recently). Failures exit 2 with the standard
remediation message; everything else exits 0 silently.

Fail-open on ANY parsing error or missing infrastructure: a gate that breaks
sessions is worse than a missed capture.
"""
import json
import os
import re
import sys
import time

ENROLLED = [
    "newsletter-agent-leadership-consultant",
    "magazine-agent-wellness-publisher",
    "personal-post-writer",
    "post-writer-executive-a",
    "post-writer-executive-b",
    "pr-qa-pipeline-pr-agency",
]

CAPTURE_MSG = (
    "Calibration capture missing. Store input.md, draft.md (or draft-vN.md for a "
    "revision) and meta.json under Calibration Loop/drafts/<skill>/<date> - <title>/, "
    "and append or update the row in "
    "Draft Register.md plus draft-register.jsonl, per Calibration Capture "
    "Protocol.md. If the user moved on to a NEW job or brief for this same skill, "
    "first close the previous open row: copy its latest draft-vN.md to final.md "
    "with final_source: inferred_next_job and status: final_captured."
)

REGISTER_FRESH_SECONDS = 45 * 60


def approve():
    sys.exit(0)


def block(msg):
    sys.stderr.write(msg)
    sys.exit(2)


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        approve()

    if payload.get("stop_hook_active"):
        approve()

    transcript_path = payload.get("transcript_path", "")
    if not transcript_path or not os.path.isfile(transcript_path):
        approve()

    # Read a bounded tail of the transcript.
    try:
        size = os.path.getsize(transcript_path)
        with open(transcript_path, "rb") as f:
            if size > 2_000_000:
                f.seek(-2_000_000, os.SEEK_END)
            raw = f.read().decode("utf-8", errors="replace")
        lines = raw.splitlines()
    except Exception:
        approve()

    # Locate the last genuine user prompt (not hook feedback, not tool results).
    entries = []
    for line in lines:
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            entries.append(json.loads(line))
        except Exception:
            continue

    last_user_idx = -1
    for i, e in enumerate(entries):
        if e.get("type") != "user" or e.get("isMeta"):
            continue
        msg = e.get("message") or {}
        content = msg.get("content")
        text = ""
        if isinstance(content, str):
            text = content
        elif isinstance(content, list):
            has_tool_result = any(
                isinstance(b, dict) and b.get("type") == "tool_result" for b in content
            )
            if has_tool_result:
                continue
            text = " ".join(
                b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"
            )
        if not text:
            continue
        if text.lstrip().startswith("Stop hook feedback"):
            continue
        last_user_idx = i

    if last_user_idx < 0:
        approve()

    turn = entries[last_user_idx:]

    # Strict detection: Skill tool_use with an enrolled name, or a launch tag.
    invoked = set()
    turn_text_parts = []
    for e in turn:
        msg = e.get("message") or {}
        content = msg.get("content")
        if isinstance(content, str):
            turn_text_parts.append(content)
            m = re.findall(r"<command-name>/?([a-z0-9:-]+)</command-name>", content)
            for name in m:
                short = name.split(":")[-1]
                if short in ENROLLED:
                    invoked.add(short)
        elif isinstance(content, list):
            for b in content:
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "text":
                    turn_text_parts.append(b.get("text", ""))
                    m = re.findall(r"<command-name>/?([a-z0-9:-]+)</command-name>", b.get("text", ""))
                    for name in m:
                        short = name.split(":")[-1]
                        if short in ENROLLED:
                            invoked.add(short)
                elif b.get("type") == "tool_use" and b.get("name") == "Skill":
                    skill = str((b.get("input") or {}).get("skill", ""))
                    short = skill.split(":")[-1]
                    if short in ENROLLED:
                        invoked.add(short)
                elif b.get("type") == "tool_result":
                    inner = b.get("content")
                    if isinstance(inner, str):
                        turn_text_parts.append(inner)
                    elif isinstance(inner, list):
                        for ib in inner:
                            if isinstance(ib, dict) and ib.get("type") == "text":
                                turn_text_parts.append(ib.get("text", ""))

    if not invoked:
        approve()

    # Stage 2a: capture check via register freshness.
    cwd = payload.get("cwd") or os.path.expanduser("~/workspace")
    loop_dir = os.environ.get("CALIBRATION_LOOP_DIR") or os.path.join(cwd, "Calibration Loop")
    if not os.path.isdir(loop_dir):
        approve()  # second seat / other machine: protocol degrades to row-in-chat

    now = time.time()
    fresh = False
    for reg in ("draft-register.jsonl", "Draft Register.md"):
        p = os.path.join(loop_dir, reg)
        try:
            if now - os.path.getmtime(p) < REGISTER_FRESH_SECONDS:
                fresh = True
        except OSError:
            pass
    if not fresh:
        block(CAPTURE_MSG)

    approve()


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        sys.exit(0)
