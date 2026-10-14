<h1 align="center">🎓 fam-mcp</h1>

<br>

<h3 align="center">An MCP server for the FAM student portal.<br>It reads the portal so an assistant can answer what the portal makes you click for</h3>

<p align="center">
  <a href="https://pypi.org/project/fam-mcp/"><img alt="PyPI version" src="https://img.shields.io/pypi/v/fam-mcp?logo=pypi&logoColor=white" /></a> <a href="https://github.com/Petri-Hub/fam-mcp/actions/workflows/build.yml"><img alt="Build" src="https://github.com/Petri-Hub/fam-mcp/actions/workflows/build.yml/badge.svg?branch=main" /></a> <a href="https://github.com/Petri-Hub/fam-mcp/stargazers"><img alt="GitHub stars" src="https://img.shields.io/github/stars/Petri-Hub/fam-mcp?style=social" /></a> <img alt="Python 3.14+" src="https://img.shields.io/badge/python-3.14%2B-3776AB?logo=python&logoColor=white" /> <a href="LICENSE.md"><img alt="License" src="https://img.shields.io/github/license/Petri-Hub/fam-mcp" /></a> <img alt="Time spent" src="https://img.shields.io/endpoint?url=https%3A%2F%2Flab-wakapi.petri.zip%2Fapi%2Fcompat%2Fshields%2Fv1%2FPetri%2Fproject%3Afam-mcp%2Finterval%3Aall_time&label=time%20spent&logo=wakatime&logoColor=white&color=blue&cacheSeconds=3600" />
</p>

<br>

## About

> **TL;DR:** a read-only MCP server that gives an AI assistant access to a student's data on the portal of FAM (Faculdade de Americana): grades, absences, assignments, schedule, exams, inbox, forums, finances and complementary hours. The portal has no API, so the server signs in as the student, reads the pages and hands back clean, typed JSON. It does not write anything back.

## Why it exists

The portal does its job, but it was built for a browser and a patient person. There is no API, every screen is a full page rendered on the server that takes seconds to load, and the answer to a simple question is usually spread over several of them. *What do I have to deliver this week?* means the assignments, the forums, the exam calendar and the finance page.

With this server the assistant opens those pages for me, and I just ask. Some things I use it for:

- *"What is due this week?"* reads the assignments, exams, forums and invoices in one go
- *"Can I still miss class in this course?"* checks the absences against the allowed maximum
- *"What do I need on the last exam to pass?"* reads the averages together with the portal's own grading rules
- *"How much of the degree is left?"* adds up the transcript

## How it works

<p align="center">
  <img src="assets/how-it-works.svg" alt="You ask an AI assistant a question. It calls a tool in the local fam-mcp server, which reads FAM portal pages over HTTPS, parses the HTML and returns structured data to the assistant. Access is read-only." />
</p>

Every tool is a small module. It asks the portal client for one or more pages, parses the HTML into a typed model, and returns it. The portal client keeps a single session for the whole run: it signs in when the server starts, notices when the portal sends it back to the login page, signs in again once and retries the request. Calls that arrive together share that one login.

## What it can do

### Student

| Tools | What they do |
|---|---|
| `get_student_profile` | Who is signed in: name, RA, class, term and masked contact data |

### Academics

| Tools | What they do |
|---|---|
| `list_courses`<br>`get_class_schedule`<br>`get_grades`<br>`get_term_results`<br>`get_absences`<br>`get_transcript`<br>`get_degree_progress`<br>`get_exam_calendar` | The courses of a term, with teachers and teaching-plan status<br>What happens on each weekday<br>Scores per evaluation stage: N1, N2 and N3<br>Averages, grading rules and the absences used so far<br>How many classes can still be missed, month by month<br>The full grade history, semester by semester<br>How much of the degree is done and what comes next<br>When the exams are |

### Assignments

| Tools | What they do |
|---|---|
| `list_activities`<br>`get_activity`<br>`download_activity_material`<br>`get_agenda` | Assignments with deadline, status and whether they were delivered<br>One assignment in full: instructions, materials and the delivery<br>Saves an attached file so the assistant can read it<br>Everything with a date in the next days, in one sorted list |

### Communication

| Tools | What they do |
|---|---|
| `get_inbox`<br>`get_inbox_mail`<br>`list_forums`<br>`get_forum`<br>`list_surveys` | Inbox messages, filtered by unread or sender<br>One message in full, with its attachments<br>The course forums and whether they are still open<br>A forum's instructions and replies<br>The institutional surveys and which ones were answered |

### Finance and requests

| Tools | What they do |
|---|---|
| `get_financial_status`<br>`list_requests`<br>`get_complementary_hours` | Open and paid invoices, with the bank data to check them against<br>The requests opened at the secretariat<br>Complementary activity hours, by status |

## Installation

FAM MCP is a local **stdio** server published on PyPI. It requires Python 3.14 or newer. Most MCP clients can launch it with [`uvx`](https://docs.astral.sh/uv/guides/tools/):

```json
{
  "mcpServers": {
    "fam": {
      "command": "uvx",
      "args": ["fam-mcp"],
      "env": {
        "FAM_USERNAME": "YOUR_CPF",
        "FAM_PASSWORD": "YOUR_FAM_PASSWORD"
      }
    }
  }
}
```

### What you will need

- [`uv`](https://docs.astral.sh/uv/getting-started/installation/), which provides the `uvx` command.
- Python 3.14 or newer.
- Your FAM portal credentials: `FAM_USERNAME` is your CPF (digits only), and `FAM_PASSWORD` is your portal password.

Replace the example values with your credentials. Keep populated user configuration files private, and never commit real credentials to a repository.

### Client-specific instructions

The examples below cover Claude Code, Claude Desktop, OpenAI Codex, OpenCode, Gemini CLI, Grok Build, DeepSeek Harness, Cursor, VS Code with GitHub Copilot, Zed, Cline, Roo Code, and Continue. Claude.ai and ChatGPT in a browser are covered too; they require a remote MCP server, while FAM MCP currently runs locally over stdio.

<details>
<summary>Claude Code</summary>

Run this in a terminal. The `user` scope makes FAM available in all your Claude Code projects:

```sh
claude mcp add --transport stdio --scope user \
  --env "FAM_USERNAME=YOUR_CPF" \
  --env "FAM_PASSWORD=YOUR_FAM_PASSWORD" \
  fam -- uvx fam-mcp
```

Check the connection with `claude mcp get fam` or `/mcp` inside Claude Code. See the [Claude Code MCP guide](https://code.claude.com/docs/en/mcp).

</details>

<details>
<summary>Claude Desktop</summary>

Open **Settings → Developer → Edit Config** and add this entry inside `mcpServers`:

```json
{
  "mcpServers": {
    "fam": {
      "command": "uvx",
      "args": ["fam-mcp"],
      "env": {
        "FAM_USERNAME": "YOUR_CPF",
        "FAM_PASSWORD": "YOUR_FAM_PASSWORD"
      }
    }
  }
}
```

Restart Claude Desktop after saving. See [Claude Desktop local MCP setup](https://support.claude.com/en/articles/10949351-getting-started-with-local-mcp-servers-on-claude-desktop).

</details>

<details>
<summary>OpenAI Codex</summary>

Add this to `~/.codex/config.toml`. The same user config is used by Codex CLI and its IDE integrations:

```toml
[mcp_servers.fam]
command = "uvx"
args = ["fam-mcp"]
env = { FAM_USERNAME = "YOUR_CPF", FAM_PASSWORD = "YOUR_FAM_PASSWORD" }
```

Restart Codex, then check the server with `codex mcp list`. See the [Codex configuration reference](https://developers.openai.com/codex/config-reference/).

</details>

<details>
<summary>OpenCode</summary>

Add this server under `mcp` in your user `~/.config/opencode/opencode.json` or project `opencode.json`:

```json
{
  "mcp": {
    "fam": {
      "type": "local",
      "command": ["uvx", "fam-mcp"],
      "environment": {
        "FAM_USERNAME": "YOUR_CPF",
        "FAM_PASSWORD": "YOUR_FAM_PASSWORD"
      },
      "enabled": true
    }
  }
}
```

See the [OpenCode MCP server guide](https://opencode.ai/docs/mcp-servers/).

</details>

<details>
<summary>Gemini CLI</summary>

Run:

```sh
gemini mcp add --scope user \
  --env "FAM_USERNAME=YOUR_CPF" \
  --env "FAM_PASSWORD=YOUR_FAM_PASSWORD" \
  fam uvx fam-mcp
```

Check with `gemini mcp list`. See the [Gemini CLI MCP guide](https://github.com/google-gemini/gemini-cli/blob/main/docs/tools/mcp-server.md).

</details>

<details>
<summary>Grok Build</summary>

Add this to `~/.grok/config.toml`:

```toml
[mcp_servers.fam]
command = "uvx"
args = ["fam-mcp"]
env = { FAM_USERNAME = "YOUR_CPF", FAM_PASSWORD = "YOUR_FAM_PASSWORD" }
enabled = true
```

Reload the MCP list in Grok Build after saving. See the [Grok Build MCP guide](https://github.com/xai-org/grok-build/blob/main/crates/codegen/xai-grok-pager/docs/user-guide/07-mcp-servers.md).

</details>

<details>
<summary>DeepSeek Harness</summary>

Add this MCP client entry to your DeepSeek Harness Cordis profile. Start the harness with `FAM_USERNAME` and `FAM_PASSWORD` set in its environment:

```yaml
- id: mcp-fam
  name: '@deepseek-ai/dsh-mcp-client'
  config:
    serverName: fam
    transport: stdio
    command: uvx
    args: [fam-mcp]
    env:
      FAM_USERNAME: !!js process.env.FAM_USERNAME
      FAM_PASSWORD: !!js process.env.FAM_PASSWORD
```

See the [DeepSeek Harness MCP client guide](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/mcp/mcp-client/README.md).

</details>

<details>
<summary>Cursor</summary>

Add this entry under `mcpServers` in `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "fam": {
      "command": "uvx",
      "args": ["fam-mcp"],
      "env": {
        "FAM_USERNAME": "YOUR_CPF",
        "FAM_PASSWORD": "YOUR_FAM_PASSWORD"
      }
    }
  }
}
```

See the [Cursor MCP guide](https://cursor.com/docs/context/mcp).

</details>

<details>
<summary>VS Code with GitHub Copilot</summary>

Create or edit `.vscode/mcp.json`:

```json
{
  "servers": {
    "fam": {
      "type": "stdio",
      "command": "uvx",
      "args": ["fam-mcp"],
      "env": {
        "FAM_USERNAME": "YOUR_CPF",
        "FAM_PASSWORD": "YOUR_FAM_PASSWORD"
      }
    }
  }
}
```

Start the server from the MCP Servers view in Copilot Chat. See [VS Code MCP setup](https://code.visualstudio.com/docs/agent-customization/mcp-servers).

</details>

<details>
<summary>Zed</summary>

Add this entry under `context_servers` in Zed's `settings.json`:

```json
{
  "context_servers": {
    "fam": {
      "command": "uvx",
      "args": ["fam-mcp"],
      "env": {
        "FAM_USERNAME": "YOUR_CPF",
        "FAM_PASSWORD": "YOUR_FAM_PASSWORD"
      }
    }
  }
}
```

See the [Zed MCP guide](https://zed.dev/docs/ai/mcp).

</details>

<details>
<summary>Cline and Roo Code</summary>

In either extension's MCP settings, add a **local stdio** server with command `uvx`, argument `fam-mcp`, and environment variables `FAM_USERNAME` and `FAM_PASSWORD`. Both provide an MCP settings editor in the extension UI. See the [Cline MCP guide](https://github.com/cline/cline/blob/main/docs/mcp/mcp-overview.mdx) and [Roo Code MCP guide](https://roocodeinc.github.io/Roo-Code/features/mcp/using-mcp-in-roo/).

</details>

<details>
<summary>Continue</summary>

Create `.continue/mcpServers/fam.yaml`:

```yaml
name: FAM MCP
version: 1.0.0
schema: v1
mcpServers:
  - name: FAM
    command: uvx
    args:
      - fam-mcp
    env:
      FAM_USERNAME: YOUR_CPF
      FAM_PASSWORD: YOUR_FAM_PASSWORD
```

See the [Continue MCP guide](https://docs.continue.dev/customize/deep-dives/mcp).

</details>

<details>
<summary>Claude.ai and ChatGPT in a browser</summary>

These web apps connect to **remote** MCP servers. FAM MCP currently runs locally over stdio and does not publish a remote endpoint, so you cannot paste `uvx fam-mcp` into their connector settings. Connecting a web app requires a separately hosted or securely tunneled remote MCP endpoint. See [Claude remote connectors](https://support.claude.com/en/articles/11175166-get-started-with-custom-connectors-using-remote-mcp) and [ChatGPT MCP connectors](https://help.openai.com/en/articles/12584461-developer-mode-and-full-mcp-connectors-in-chatgpt).

</details>

## Philosophy

**Read-only, always.**  
It never submits, posts or answers anything on the portal. The only side effect comes from the portal itself: opening a message in the inbox marks it as read.

**Questions, not screens.**  
The tools follow what a student actually asks, not how the portal's menu is organized. One question about what's coming up replaces four pages, and finding out how far along the degree is replaces adding up a transcript by hand.

**Private by default.**  
Personal documents like the CPF and the RG come back hidden, other students' names and registration numbers are removed from forum replies, and the login stays in the environment instead of showing up in any answer.

**Failures that explain themselves.**  
When something goes wrong, the assistant gets a clear answer: what happened, whether trying again makes sense and which tool it was. A portal that is down is told apart from a page that changed its layout, and the technical details stay in the log instead of reaching the assistant.

**Gentle with a fragile site.**  
There is one shared session, renewed only when it expires. A call takes from a few seconds to about twenty, and doing several at once barely helps. The server doesn't hide that, and tells the assistant up front.

**Shaped for the assistant.**  
Dates and numbers always come in the same format, and every id the assistant needs comes from a previous answer. The server also says where to start, so the assistant spends its calls on the answer instead of finding its way around.

## What's inside

```sh
├── assets/             # the How it works diagram, as an editable Excalidraw file and its SVG
├── src/fam_mcp
│   ├── server.py       # the MCP server: instructions, middleware and the login at startup
│   ├── portal.py       # the session with the portal: login, re-login, retries, decoding
│   ├── middleware.py   # turns every failure into the JSON error
│   ├── errors.py       # the error hierarchy, one class per failure
│   ├── constants.py    # the error codes and their messages
│   ├── utils.py        # parsing helpers: dates, numbers, masking
│   ├── data/           # what the tools return, as dataclasses, one module per area
│   └── tools/          # one file per tool, registered automatically on import
└── pyproject.toml
```

## Technologies

| &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; | Technology | Used for |
|:---:|---|---|
| <img src="https://cdn.simpleicons.org/modelcontextprotocol/9198A1" width="20" height="20" alt="" /> | [Model Context Protocol](https://modelcontextprotocol.io) | The protocol that lets an assistant call the tools |
| <img src="https://gofastmcp.com/assets/brand/blue-logo.png" height="20" alt="" /> | [FastMCP](https://gofastmcp.com) | The MCP framework: tool registration, input validation, middleware and the startup lifecycle |
| <img src="https://cdn.simpleicons.org/python" width="20" height="20" alt="" /> | [Python](https://docs.python.org/3/) | The language, with `asyncio` so calls don't block each other |
| <img src="https://www.python-httpx.org/img/butterfly.png" height="20" alt="" /> | [httpx](https://www.python-httpx.org) | The async HTTP client behind the portal session |
| <img src="https://www.crummy.com/software/BeautifulSoup/10.1.jpg" height="20" alt="" /> | [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) | Reads the portal's HTML, which is often malformed |
| <img src="https://cdn.simpleicons.org/uv" width="20" height="20" alt="" /> | [uv](https://docs.astral.sh/uv/) | Dependencies and running the project |

## Roadmap

What's already in place:

- ✅ A portal client that signs in, survives an expired session and shares one login between parallel calls
- ✅ 21 read-only tools across the student's profile, academics, assignments, communication and finances
- ✅ Published on PyPI as `fam-mcp`, with `uvx` installation instructions above
- ✅ Errors as JSON with a code, a retryable flag and the tool that raised them
- ✅ Masked personal data, and forum replies stripped of other students' identifiers
- ✅ Paid invoice history alongside open invoices
- ✅ Every tool checked against the live portal, including its error cases
- ✅ Server instructions that tell the assistant where to start

## References

- [Model Context Protocol](https://modelcontextprotocol.io): the specification the server speaks
- [FastMCP](https://gofastmcp.com): the framework the server is built on
- [httpx](https://www.python-httpx.org): the HTTP client
- [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/): the HTML parser
- [uv](https://docs.astral.sh/uv/): how the project is run
- [FAM](https://www.famportal.com.br): the portal this server reads

## Starred by students

<!-- stargazers:start -->
<table align="center">
  <tbody>
    <tr>
      <td align="center" valign="top"><a href="https://github.com/jntmelgar"><img src="https://avatars.githubusercontent.com/u/147103279?v=4" width="64" height="64" alt="@jntmelgar" /><br /><sub>@jntmelgar</sub></a></td>
      <td align="center" valign="top"><a href="https://github.com/Melodypl"><img src="https://avatars.githubusercontent.com/u/167656139?v=4" width="64" height="64" alt="@Melodypl" /><br /><sub>@Melodypl</sub></a></td>
      <td align="center" valign="top"><a href="https://github.com/Petri-Hub"><img src="https://avatars.githubusercontent.com/u/80995990?v=4" width="64" height="64" alt="@Petri-Hub" /><br /><sub>@Petri-Hub</sub></a></td>
    </tr>
  </tbody>
</table>
<!-- stargazers:end -->

## Disclaimer

This project is unofficial. It is not made by, affiliated with or endorsed by FAM.

## License

MIT, in [`LICENSE.md`](LICENSE.md).

