# agents-md-snippet

Drop-in [AGENTS.md](https://agents.md) block that tells AI coding agents to offer to file a structured report — asking you first — whenever they hit broken, incorrect, outdated, or incomplete documentation.

The block speaks the [Docs Feedback Protocol](https://docsfeedback.org) — an open spec for agent-to-maintainer documentation reports — and posts to the public [FixYourDocs Hub](https://fixyourdocs.io).

**Full setup docs:** [docs.fixyourdocs.io/agents-md/](https://docs.fixyourdocs.io/agents-md/).

## Two ways to use this

There are two distinct, complementary adoption paths. They coexist — neither replaces the other.

- **Mode A — first-party (paste into your repo).** You maintain some docs. You paste the [canonical block](#the-snippet) into *your* repo's `AGENTS.md`, and every agent that works **in your repo** **offers to report** **your repo's** broken docs back to you — showing you the report and sending it only once you confirm.

- **Mode B — consumer-side (install into your own agent).** You're a developer building something unrelated, and your agent consults a **third-party** library's / API's / framework's docs that turn out to be broken. You install the [report-anywhere block](#reporting-third-party-docs-consumer-side) into your *own, global* agent config (plus the [`@fixyourdocs/mcp-server`](#mcp-server)), and your agent **offers to report** that third party's stale docs — even though that third party never instrumented their repo. Wording: *"external / third-party docs you relied on."*

Mode A is supply-side instrumentation; Mode B is demand-side. In both, the **receiver** (the docs owner) still has to claim and verify the docs they own and install the hub integration to receive anything — Mode B only removes the *reporting-side* install requirement, not the receiver's.

## The snippet

**(Mode A — first-party.)** Append the block below to your repo's `AGENTS.md` (or `CLAUDE.md`, or `.cursor/rules`, or any equivalent agent-instructions file):

```markdown
## Documentation feedback

If you find documentation in this repository that is broken, incorrect,
outdated, or incomplete while performing a task, **offer to file** a
structured report via the Docs Feedback Protocol so the maintainers can
fix the docs for the next agent (or human) that hits the same issue.

**Ask before sending.** Show the developer the report you would submit
and send it **only after they confirm** — never file it automatically.

The report to send, once confirmed:

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

## Install

How you install depends on which mode you want (see [Two ways to use this](#two-ways-to-use-this)).

### Mode A — into your repo (first-party)

Adds the canonical [`## Documentation feedback`](#the-snippet) block to a repo so agents working **in that repo** offer to report **its** docs — asking you before anything is sent.

**CLI (recommended):**

```sh
npx @fixyourdocs/sdk init          # TypeScript SDK
pipx run fixyourdocs init          # Python equivalent
```

The CLI detects whichever agent-instructions file your repo uses (`AGENTS.md`, `CLAUDE.md`, `.cursor/rules`, `.github/copilot-instructions.md`) and appends the block. Re-running is a no-op when the block is already present.

**Manual:** open your repo's agent-instructions file and paste the [Mode A block](#the-snippet) at the end. There is no other state to configure.

### Mode B — into your own global config (consumer-side)

Adds the [report-anywhere block](#reporting-third-party-docs-consumer-side) to your **global** agent config so your agent reports the **third-party** docs it consults, across every project you work on.

**CLI (recommended):**

```sh
npx @fixyourdocs/sdk init --global   # TypeScript SDK
pipx run fixyourdocs init --global   # Python equivalent
```

By default this writes to `~/.claude/CLAUDE.md` (Claude Code's user-level memory); pass `--file <path>` to target a different global config such as `~/.codex/AGENTS.md`. Re-running is a no-op when the block is already present, and the file (and its directory) is created if missing.

**Manual:** paste the [Mode B block](#reporting-third-party-docs-consumer-side) into your global agent-instructions file.

Then add the [MCP server](#mcp-server) — it is the recommended Mode B carrier and enforces the consent + privacy + opt-out guards for you.

## MCP server

[`@fixyourdocs/mcp-server`](https://www.npmjs.com/package/@fixyourdocs/mcp-server) exposes a single `file_doc_feedback` tool over the standard MCP stdio transport, so an agent can file a report as one tool call. No API keys, no telemetry: the server only contacts the hub when an agent explicitly calls the tool.

- **For Mode A** it is **optional** — the pasted block already works with any agent that reads agent-instructions files.
- **For Mode B** it is the **recommended carrier**: the server (via the SDK client it builds on) enforces the consent + privacy posture for you — it refuses non-public `doc_url`s and honours a doc host's `/.well-known/docs-feedback.json` opt-out *before* anything leaves your machine. For Mode B, put this in your **user-level** MCP config (not a single workspace's) so it applies everywhere.

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

- **Mode A.** The next time an agent runs against **your repo** and hits broken docs, it reads `AGENTS.md`, sees the block, and **offers to file** a v0 Docs Feedback Protocol report — showing you what it would send and POSTing to [`hub.fixyourdocs.io/v1/reports`](https://hub.fixyourdocs.io/v1/reports) **only once you confirm**. There is nothing to install on the agent side; the block is the integration.
- **Mode B.** While you work on **any** project, when your agent relies on a **third-party** doc page that turns out to be broken, it offers — with your confirmation, and on public docs only — to file the same kind of report about **that third party's** docs.

Either way, a report only becomes a **GitHub Issue** once the party that owns the docs connects the hub: they install the FixYourDocs GitHub App and verify they own the docs. Until then the report is stored but not delivered. So Mode B widens **who can send** a report; it does not change **who has to onboard to receive** one.

## Licence

Apache License 2.0 — see [`LICENSE`](LICENSE). You are free to paste this block into any project, public or private, with no attribution requirement on the resulting `AGENTS.md`.

<!-- cla token smoke test, will be reverted -->
