# Integration Testing

This project uses a shell-based integration testing system that verifies the full chain:
**AI agent → MCP server → openapi.com APIs → response with real data.**

---

## The openapi CLI

The `openapi` CLI is the official command-line client for openapi.com APIs. It is used during test development to call APIs directly and verify expected response values **without** the MCP server in the loop.

### Installation

Install via Cargo (Rust):

```bash
cargo install openapi-cli-rs
```

See: https://crates.io/crates/openapi-cli-rs

### Configuration

The CLI reads credentials from environment variables:

```bash
export OPENAPI_USERNAME=your@email.com
export OPENAPI_KEY=your_production_key
export OPENAPI_SANDBOX_KEY=your_sandbox_key
```

### Verifying API responses before writing tests

Use the CLI to discover the exact data returned by an API endpoint, then use that data as the expected pattern in `expect.txt`:

```bash
# Check exchange rates
openapi exchange-rate get

# Look up a company by VAT (sandbox)
openapi --sandbox company start --code 02120220419

# Generate a token for a specific set of scopes
openapi token create --scopes "company,exchange-rate"
openapi token create --sandbox --scopes "company,exchange-rate"

# Verify your current configuration
openapi info
```

---

## Test Structure

```
tests/integration/
  run-vs-claude.sh       # runner using Claude Code CLI
  run-vs-openai.sh       # runner using OpenAI Responses API
  cases/
    00_sanity_check/     # verifies the test framework itself (no MCP involved)
    01_exchange_rates/   # calls get_today_exchange_rates via MCP
    02_company_lookup/   # calls get_company_IT_start via MCP
```

Each test case contains:
- `prompt.txt` — the natural-language prompt sent to the AI agent
- `expect.txt` — patterns (one per line) that must appear in the response

Lines starting with `#` in `expect.txt` are treated as comments.

---

## Running Tests

### Environment variables

| Variable | Required by | Description |
|---|---|---|
| `OPENAPI_TOKEN` | all runners | Production Bearer token |
| `OPENAPI_SANDBOX_TOKEN` | sandbox mode | Sandbox Bearer token |
| `OPENAI_API_KEY` | OpenAI runner | OpenAI API key |
| `MCP_URL` | OpenAI runner | Public URL of the MCP server |
| `SANDBOX=1` | all runners | Switch to sandbox mode |

### Via Claude Code

Claude Code connects to the MCP server locally via `.mcp.json` (auto-generated, gitignored).

```bash
# Production
export OPENAPI_TOKEN=your_token
make test

# Sandbox
export OPENAPI_SANDBOX_TOKEN=your_sandbox_token
make test-sandbox
```

### Via OpenAI

OpenAI's Responses API calls the MCP server from the cloud, so the server must be
publicly accessible. Expose it with [ngrok](https://ngrok.com/):

```bash
# Terminal 1 — start the server
make start

# Terminal 2 — expose it
ngrok http 8080
# copy the https URL, e.g. https://abcd1234.ngrok-free.app

# Terminal 3 — run tests
export OPENAI_API_KEY=sk-...
export OPENAPI_SANDBOX_TOKEN=your_sandbox_token
MCP_URL=https://abcd1234.ngrok-free.app SANDBOX=1 make test-openai-sandbox
```

---

## Production vs Sandbox

| | Production | Sandbox |
|---|---|---|
| API endpoints | `company.openapi.com` | `test.company.openapi.com` |
| Token scope | limited (depends on plan) | full |
| Data | real | simulated |
| Token variable | `OPENAPI_TOKEN` | `OPENAPI_SANDBOX_TOKEN` |

The MCP server switches between production and sandbox based on the `K_SERVICE` environment
variable (handled automatically by the test runners).

---

## Adding a New Test Case

1. Create a directory under `tests/integration/cases/`, e.g. `03_email_check/`
2. **Verify the expected response first** using the CLI:
   ```bash
   openapi --sandbox trust email-start --email test@example.com
   ```
3. Write `prompt.txt` with a natural-language question that requires the MCP tool
4. Write `expect.txt` with patterns from the verified API response
