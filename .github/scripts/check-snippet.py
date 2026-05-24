#!/usr/bin/env python3
"""Self-test for the canonical AGENTS.md block.

Run from the repo root:

    python3 .github/scripts/check-snippet.py

Checks:

1. README.md contains exactly one fenced ```markdown block. That block is
   the canonical AGENTS.md snippet.
2. AGENTS.md (this repo's dogfood file) contains the same block, byte-for-byte
   modulo the fence.
3. The curl example inside the block carries a JSON body that parses as JSON
   and conforms to the v0 Docs Feedback Protocol schema's required shape
   (top-level `protocol_version` / `doc_url` / `agent` / `report`,
   nested `report.kind` + `report.summary`).

The live POST half (against the FixYourDocs Hub) is deferred until the
Hub is deployed. When the Hub goes live, extend this script to substitute
the placeholders, POST the body to a staging endpoint, and assert
`201 Created`.

Exit code 0 on success, 1 on any check failure.
"""

from __future__ import annotations

import json
import pathlib
import re
import sys
import textwrap

ROOT = pathlib.Path(__file__).resolve().parents[2]
README = ROOT / "README.md"
AGENTS = ROOT / "AGENTS.md"


def fail(msg: str) -> "None":
    print(f"snippet-drift: {msg}", file=sys.stderr)
    sys.exit(1)


def extract_markdown_block(path: pathlib.Path) -> str:
    text = path.read_text()
    matches = re.findall(r"```markdown\n(.*?)\n```", text, flags=re.DOTALL)
    if len(matches) != 1:
        fail(
            f"{path.relative_to(ROOT)} must contain exactly one ```markdown ... ``` "
            f"block; found {len(matches)}"
        )
    return matches[0]


def extract_agents_md_block(path: pathlib.Path) -> str:
    """AGENTS.md is the snippet itself (no markdown fence). Return the block
    starting at the canonical heading."""

    text = path.read_text()
    heading = "## Documentation feedback"
    idx = text.find(heading)
    if idx == -1:
        fail(f"{path.relative_to(ROOT)} missing canonical heading '{heading}'")
    block = text[idx:].rstrip() + "\n"
    return block.rstrip("\n")


def extract_curl_json(block: str) -> str:
    match = re.search(r"-d '(\{.*?\})'", block, flags=re.DOTALL)
    if not match:
        fail("could not find `-d '{...}'` JSON payload in the snippet's curl example")
    raw = match.group(1)
    return textwrap.dedent(raw)


def main() -> "None":
    readme_block = extract_markdown_block(README)
    agents_block = extract_agents_md_block(AGENTS)
    if readme_block != agents_block:
        diff_pos = next(
            (i for i, (a, b) in enumerate(zip(readme_block, agents_block)) if a != b),
            min(len(readme_block), len(agents_block)),
        )
        fail(
            "README.md and AGENTS.md disagree on the canonical block "
            f"(first diff at byte {diff_pos}).\n"
            f"README excerpt:  {readme_block[max(0, diff_pos - 20): diff_pos + 60]!r}\n"
            f"AGENTS excerpt:  {agents_block[max(0, diff_pos - 20): diff_pos + 60]!r}"
        )

    raw_json = extract_curl_json(readme_block)
    try:
        payload = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        fail(f"snippet's curl payload is not valid JSON: {exc}")

    required_top = {"protocol_version", "doc_url", "agent", "report"}
    missing_top = required_top - set(payload.keys())
    if missing_top:
        fail(f"snippet payload missing required top-level keys: {sorted(missing_top)}")
    if payload["protocol_version"] != "0":
        fail(
            f"snippet payload protocol_version must equal '0' (v0 spec); "
            f"got {payload['protocol_version']!r}"
        )
    if not isinstance(payload["agent"], dict) or "name" not in payload["agent"]:
        fail("snippet payload agent must be an object with a `name` field")
    report = payload.get("report")
    if not isinstance(report, dict):
        fail("snippet payload report must be an object")
    required_report = {"kind", "summary"}
    missing_report = required_report - set(report.keys())
    if missing_report:
        fail(f"snippet payload report missing required keys: {sorted(missing_report)}")

    print("snippet-drift: README/AGENTS in sync, payload conforms to v0 schema shape.")


if __name__ == "__main__":
    main()
