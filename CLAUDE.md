# CLAUDE.md

Read `AGENTS.md` for the project layout. It is out of date (see #94): where it disagrees with the code or `README.md`, trust the code.

The agreed target architecture, decisions and task order are in `docs/architecture.md`. Read it before starting an issue.

## Decisions

All five are made. Do not reopen them in a pull request; raise an issue instead.

- **D1:** The agent, MCP server and REST API merge into one Python app. No zero-trust microservice setup.
- **D2:** Production data is important and must not be lost. Back it up and rehearse any migration on a copy. Never write to or delete from the production MySQL yourself.
- **D3:** An expense's currency is the user's default, unless the message names one. A new user is offered USD and must confirm it before anything is saved. Existing users' expenses are RWF.
- **D4:** External MCP clients can log expenses through the app's `/mcp`. The app's own chat calls the same tool functions directly, not through MCP.
- **D5:** Sign-in moves to WorkOS AuthKit, replacing `expenses-auth`. Any MCP client that follows the MCP authorization spec must be able to sign in.

## How work is tracked

- Every change starts from a GitHub issue. Stories are parent issues; tasks are their sub-issues, in the order they should be done.
- Issues are short: an imperative title, two or three sentences on what is wrong and what should be true, an **Acceptance criteria** checklist, and an optional **Agents** section with where to start, how to check and what to leave alone.
- Labels: `enhancement` or `bug`.
- One task per branch and per pull request. Never commit to `main`.

## Commits and pull requests

- A commit message is one line, in the imperative, with no body.
- Commits are never authored or committed as Claude. Before the first commit, set `user.name` and `user.email` in the checkout to the repository owner's (Blaise-Shyaka), as on their commits on `main` (`git log origin/main --format='%an <%ae>'`).
- No `Co-Authored-By` or other trailers in commits.
- Pull requests are written for a human reviewer: what changed and why, how it was checked, and anything a human must do (Coolify, DNS, secrets). Link the issue with `Closes #N`.
- Pull request descriptions carry no "Generated with Claude Code" line, session link or other AI attribution.
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
