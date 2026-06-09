# agents-md-snippet

Drop-in [AGENTS.md](https://agents.md) block that tells AI coding agents to file a structured report whenever they hit broken, incorrect, outdated, or incomplete documentation.

The block speaks the [Docs Feedback Protocol](https://docsfeedback.org) — an open spec for agent-to-maintainer documentation reports — and posts to the public [FixYourDocs Hub](https://fixyourdocs.io).

**Full setup docs:** [docs.fixyourdocs.io/agents-md/](https://docs.fixyourdocs.io/agents-md/).

## Two ways to use this

There are two distinct, complementary adoption paths. They coexist — neither replaces the other.

- **Mode A — first-party (paste into your repo).** You maintain some docs. You paste the [canonical block](#the-snippet) into *your* repo's `AGENTS.md`, and every agent that works **in your repo** reports **your repo's** broken docs back to you. This is what the rest of this README, the `fixyourdocs init` CLI, and the SDKs are built around. Wording: *"documentation in **this repository**."*

- **Mode B — consumer-side (install into your own agent).** You're a developer building something unrelated, and your agent consults a **third-party** library's / API's / framework's docs that turn out to be broken. You install the [report-anywhere block](#reporting-third-party-docs-consumer-side) into your *own, global* agent config (plus the [`@fixyourdocs/mcp-server`](#mcp-server)), and your agent **offers to report** that third party's stale docs — even though that third party never instrumented their repo. Wording: *"external / third-party docs you relied on."*

Mode A is supply-side instrumentation; Mode B is demand-side. In both, the **receiver** (the docs owner) still has to claim and DNS-verify their domain and install the hub integration to receive anything — Mode B only removes the *reporting-side* install requirement, not the receiver's.

## Why

Agents already read `AGENTS.md` (Cursor, Claude Code, Codex, Devin, Gemini CLI, Copilot, …). One paste-ready block is enough to turn every agent run on your repo into a free, structured signal about what is wrong with your docs — without changing any agent.

## The snippet

**(Mode A — first-party.)** Append the block below to your repo's `AGENTS.md` (or `CLAUDE.md`, or `.cursor/rules`, or any equivalent agent-instructions file):

```markdown
## Documentation feedback

If you find documentation in this repository that is broken, incorrect,
outdated, or incomplete while performing a task, file a structured report
via the Docs Feedback Protocol. This helps the maintainers fix the docs
for the next agent (or human) that hits the same issue.

How to file a report:

    curl -X POST https://hub.fixyourdocs.io/v1/reports \
      -H 'Content-Type: application/json' \
      -d '{
        "protocol_version": "0",
        "doc_url": "<URL or path of the doc you were reading>",
        "agent":   { "name": "<your agent id, e.g. claude-code>" },
        "report":  {
          "kind":    "<broken | incorrect | outdated | missing | unclear | other>",
          "summary": "<one-line description of the problem>",
          "details": "<what you expected vs. what the doc said (optional)>"
        }
      }'

Spec: https://docsfeedback.org
```

The block is the canonical wording. Other repositories (the FixYourDocs CLI, the SDKs, the docs-platform integrations) embed this same text by SHA-pinned drift check rather than by hand-copy — see the [snippet-drift workflow](.github/workflows/snippet-drift.yml).

## Reporting third-party docs (consumer side)

**(Mode B.)** The block above is repo-scoped on purpose — it says *"documentation in **this repository**."* If instead you want **your own agent** to report the broken third-party docs it stumbles on while you build something else, install the block below into your *global* agent config — `~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md`, your global Cursor rules, or wherever your client reads global instructions — rather than into any one project's `AGENTS.md`:

```text
## Reporting stale third-party docs

While working on this project, if you rely on a **third-party / external**
documentation page — a library, API, framework, or hosted docs site you
consulted, *not* this project's own docs, and never an internal, private,
`localhost`, or login-gated page — and you find it broken, incorrect,
outdated, or incomplete, **offer to file a structured report** via the
Docs Feedback Protocol so its maintainers can fix it for the next agent
(or human) that hits the same issue.

Rules:

- **Ask before sending.** Offer to file the report; only send once the
  developer confirms.
- **Public docs only.** Only report a page served over public `https://`.
  Never report `localhost`, internal, private, or login-gated URLs.
- **Never include private context.** No private code, secrets, internal
  URLs, or transcript excerpts from this project.

Prefer the `file_doc_feedback` MCP tool from `@fixyourdocs/mcp-server`
if available; otherwise POST to `https://hub.fixyourdocs.io/v1/reports`
per https://docsfeedback.org.
```

Unlike the Mode A block, this one is **not** drift-locked across the SDKs (it has no `fixyourdocs init` paste path yet); this README is its single source of truth. The matching consent + privacy behaviour — refusing non-public `doc_url`s and honouring a doc host's `/.well-known/docs-feedback.json` opt-out **before** anything leaves your machine — is enforced for you by the [`@fixyourdocs/mcp-server`](#mcp-server) and the SDK clients it builds on, so the MCP tool is the recommended carrier for Mode B.

## Install

There are two paths. Both produce the same final `AGENTS.md`.

### CLI (recommended)

```sh
npx @fixyourdocs/sdk init
```

The CLI ships with the [TypeScript SDK](https://github.com/fixyourdocs/sdk-typescript). It detects whichever agent-instructions file your repo uses (`AGENTS.md`, `CLAUDE.md`, `.cursor/rules`, `.github/copilot-instructions.md`) and appends the block. Re-running is a no-op when the block is already present.

The Python equivalent:

```sh
pipx run fixyourdocs init
```

ships with the [Python SDK](https://github.com/fixyourdocs/sdk-python).

### Manual

Open your repo's agent-instructions file and paste the block above at the end. That's it — there is no other state to configure.

## MCP server

The snippet works with any agent that reads agent-instructions files. For MCP-aware clients there is also the [`@fixyourdocs/mcp-server`](https://www.npmjs.com/package/@fixyourdocs/mcp-server) — it exposes a single `file_doc_feedback` tool over the standard MCP stdio transport, so an agent can file a report as one tool call. No API keys, no telemetry: the server only contacts the hub when an agent explicitly calls the tool.

It runs via `npx`, so there is nothing to install up front — your client launches it on demand. Add one of the blocks below to your client's MCP config.

**Claude Desktop** — `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```jsonc
{
  "mcpServers": {
    "fixyourdocs": {
      "command": "npx",
      "args": ["-y", "@fixyourdocs/mcp-server"]
    }
  }
}
```

**Cursor** — `~/.cursor/mcp.json` (or your workspace's `.cursor/mcp.json`): the same `mcpServers` block as above.

**Codex** — `~/.codex/config.toml`:

```toml
[mcp_servers.fixyourdocs]
command = "npx"
args = ["-y", "@fixyourdocs/mcp-server"]
```

See the [`@fixyourdocs/mcp-server` README](https://github.com/fixyourdocs/fixyourdocs/tree/main/mcp-server) for the full tool schema and environment variables.

## What happens after install

The next time an AI agent runs against your repo and hits broken docs, it reads `AGENTS.md`, sees the block, and POSTs a v0 Docs Feedback Protocol report to [`hub.fixyourdocs.io/v1/reports`](https://hub.fixyourdocs.io/v1/reports). When you connect the hub to your repo — install the FixYourDocs GitHub App and verify you own the doc's domain (a DNS-TXT record) — each report for that domain shows up as a GitHub Issue. There is nothing to install on the agent side; the snippet is the integration.

## Licence

Apache License 2.0 — see [`LICENSE`](LICENSE). You are free to paste this block into any project, public or private, with no attribution requirement on the resulting `AGENTS.md`.
