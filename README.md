# fam-mcp

MCP server that gives an AI assistant read-only access to a student's data on the FAM (Faculdade de Americana) academic portal: grades, absences, assignments, schedule, exams, inbox, finances and more.

## Setup

```bash
cp .env.example .env   # then fill FAM_USERNAME (CPF, digits only) and FAM_PASSWORD
uv run fam-mcp         # stdio transport
```

Register it in Claude Code:

```bash
claude mcp add fam -- uv --directory /path/to/fam-mcp run fam-mcp
```

## Tools

| Area | Tools |
|---|---|
| Student | `get_student_profile` |
| Academics | `list_courses`, `get_class_schedule`, `get_grades`, `get_term_results`, `get_absences`, `get_transcript`, `get_degree_progress`, `get_exam_calendar` |
| Assignments | `list_activities`, `get_activity`, `download_activity_material`, `get_agenda` |
| Communication | `get_inbox`, `get_inbox_mail`, `list_forums`, `get_forum`, `list_surveys` |
| Finance and requests | `get_financial_status`, `list_requests`, `get_complementary_hours` |

All tools are read-only. Notes on side effects of the portal itself: opening a message with `get_inbox_mail` marks it as read, and `get_forum` may mark replies as seen.

`get_sent_mail` is not implemented: the portal reports the number of sent messages but never renders the rows.

## Errors

Every failure reaches the client as JSON:

```json
{"error": {"code": "PT-003", "message": "Portal is currently unavailable. Test again later.", "retryable": true, "tool": "get_grades"}}
```

Invalid arguments (`AR-001`) add a `details` field. Codes are defined in `src/fam_mcp/constants.py`; the translation lives in `src/fam_mcp/middleware.py`. The real cause is logged to stderr and never sent to the model.

## Layout

- `server.py`: FastMCP instance, instructions, middleware, lifespan.
- `portal.py`: async session with login, automatic re-login and ISO-8859-1 decoding.
- `tools/`: one module per tool, registered on import.
- `data/`: dataclasses returned by the tools, grouped by area.
- `utils.py`: parsing helpers (dates, numbers, masking, `require`).
