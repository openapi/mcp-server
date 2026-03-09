#!make

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#                                                                             #
#      ____                               _                                   #
#     / __ \____  ___  ____  ____ _____  (_) ®                                #
#    / / / / __ \/ _ \/ __ \/ __ `/ __ \/ /                                   #
#   / /_/ / /_/ /  __/ / / / /_/ / /_/ / /                                    #
#   \____/ .___/\___/_/ /_/\__,_/ .___/_/                                     #
#       /_/                    /_/                                            #
#                                                                             #
#   The Largest Certified API Marketplace                                     #
#   Accelerate Digital Transformation • Simplify Processes • Lead Industry    #
#                                                                             #
#   ═══════════════════════════════════════════════════════════════════════   #
#                                                                             #
#   Project:        mcp-server                                                #
#   Version:        0.1.0                                                     #
#   Author:         Simone Desantis (@SimoneOpenapi)                          #
#   Copyright:      (c) 2026 Openapi®. All rights reserved.                   #
#   License:        MIT                                                       #
#   Maintainer:     Francesco Bianco                                          #
#   Contact:        https://openapi.com/                                      #
#   Repository:     https://github.com/openapi/mcp-server                     #
#   Documentation:  https://console.openapi.com/                              #
#                                                                             #
#   ═══════════════════════════════════════════════════════════════════════   #
#                                                                             #
#   "Truth lies at the source of the stream."                                 #
#                                  — English Proverb                          #
#                                                                             #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

## =========
## Variables
## =========

UV   := uv
HOST := 0.0.0.0
PORT := 8080

## =======
## Targets
## =======

.PHONY: start check-env release test test-sandbox test-openai test-openai-sandbox test-codex test-codex-sandbox try-claude try-claude-sandbox test-docker-compose-up

## Check that python3 and uv are available, with OS-specific install hints
check-env:
	@bash scripts/check-env.sh

.venv/pyvenv.cfg:
	$(UV) venv

.install.stamp: requirements.txt .venv/pyvenv.cfg
	$(UV) pip install -r requirements.txt
	@touch .install.stamp

## Setup the local environment and start the server
start: check-env .install.stamp
	PYTHONPATH=src $(UV) run uvicorn openapi_mcp_sdk.main:app --host $(HOST) --port $(PORT)

## Start local MCP server and open Claude interactively - production (requires: export OPENAPI_TOKEN=your_token)
try-claude: check-env .install.stamp
	@bash scripts/try-claude.sh

## Start local MCP server and open Claude interactively - sandbox (requires: export OPENAPI_SANDBOX_TOKEN=your_token)
try-claude-sandbox: check-env .install.stamp
	@SANDBOX=1 bash scripts/try-claude.sh

## =========
## Release
## =========

## Build the package and publish it to PyPI (requires: uv, PyPI credentials)
release:
	$(UV) build
	$(UV) publish

## =======
## Testing
## =======

## Smoke-test the docker compose stack (latest image, no token required)
test-docker-compose-up:
	@bash tests/docker/test-compose-up.sh

## Run integration tests via Claude Code - production (requires: export OPENAPI_TOKEN=your_token)
test: check-env .install.stamp
	@bash tests/integration/run-vs-claude.sh

## Run integration tests via Claude Code - sandbox (requires: export OPENAPI_SANDBOX_TOKEN=your_token)
test-sandbox: check-env .install.stamp
	@SANDBOX=1 bash tests/integration/run-vs-claude.sh

## Run integration tests via OpenAI - production (requires: OPENAI_API_KEY, OPENAPI_TOKEN, MCP_URL)
test-openai: check-env .install.stamp
	@bash tests/integration/run-vs-openai.sh

## Run integration tests via OpenAI - sandbox (requires: OPENAI_API_KEY, OPENAPI_SANDBOX_TOKEN, MCP_URL)
test-openai-sandbox: check-env .install.stamp
	@SANDBOX=1 bash tests/integration/run-vs-openai.sh

## Run integration tests via OpenAI Codex CLI - production (requires: OPENAI_API_KEY, OPENAPI_TOKEN)
test-codex: check-env .install.stamp
	@bash tests/integration/run-vs-codex.sh

## Run integration tests via OpenAI Codex CLI - sandbox (requires: OPENAI_API_KEY, OPENAPI_SANDBOX_TOKEN)
test-codex-sandbox: check-env .install.stamp
	@SANDBOX=1 bash tests/integration/run-vs-codex.sh