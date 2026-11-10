# CLAUDE.md

Read `AGENTS.md` for the project layout. It is out of date (see #94): where it disagrees with the code or `README.md`, trust the code.

The agreed target architecture, open decisions (D1 to D5) and task order are in `docs/architecture.md`. Read it before starting an issue.

## How work is tracked

- Every change starts from a GitHub issue. Stories are parent issues; tasks are their sub-issues, in the order they should be done.
- Issues are short: an imperative title, two or three sentences on what is wrong and what should be true, an **Acceptance criteria** checklist, and an optional **Agents** section with where to start, how to check and what to leave alone.
- Labels: `enhancement` or `bug`.
- One task per branch and per pull request. Never commit to `main`.

## Commits and pull requests

- A commit message is one line, in the imperative, with no body.
- No `Co-Authored-By` or other trailers in commits.
- Pull requests are written for a human reviewer: what changed and why, how it was checked, and anything a human must do (Coolify, DNS, secrets). Link the issue with `Closes #N`.
- Only a human merges. Agents never merge, approve, enable auto-merge or push to `main`.

## Before pushing

Run the checks CI runs for each package you touched:

- Python (`expenses-api/`, `expenses-agent/`, `expenses-mcp/`): `uv run ruff check . && uv run ruff format --check . && uv run pyright .`, plus `uv run pytest` where tests exist.
- Go (`expenses-auth/`): `test -z "$(gofmt -l .)" && go vet ./... && go test ./...`
- UI (`ui/`): `pnpm run lint && pnpm run check:types`

Never skip or disable a failing test to get CI green; report it instead.

## Rules for the code

- Every query is scoped to the acting user. A missing user id never means "all users".
- Logs never contain message text, prompts, model output, tool arguments, amounts, merchants, tokens, passwords, emails or `Authorization` headers.
- Keep the existing `# type: ignore` and `# pyright: ignore` comments; langgraph and ag-ui-langgraph have no type stubs.
- Infrastructure (Coolify, DNS, secrets) needs a human. List the changes required in the pull request instead of guessing.
