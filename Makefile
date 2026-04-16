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

UV          := uv
HOST        := 0.0.0.0
MCP_PORT    := 8080
MCP_ENV     ?= dev
DEV_MODE    ?= 1
NGROK_DOMAIN ?=

## =======
## Targets
## =======

.PHONY: start check-env style release test test-sandbox test-openai test-openai-sandbox test-codex test-codex-sandbox try-claude try-claude-sandbox test-docker-compose-up

## Check that python3 and uv are available, with OS-specific install hints
check-env:
	@bash scripts/check-env.sh

.venv/pyvenv.cfg:
	$(UV) venv

.install.stamp: requirements.txt .venv/pyvenv.cfg
	$(UV) pip install -r requirements.txt
	@touch .install.stamp

## Setup the local environment and start the server (exposes a public ngrok URL if ngrok is installed)
## Set NGROK_DOMAIN=your-name.ngrok-free.app for a stable URL across restarts.
start: check-env .install.stamp
	@MCP_PORT=$(MCP_PORT) HOST=$(HOST) MCP_ENV=$(MCP_ENV) DEV_MODE=$(DEV_MODE) NGROK_DOMAIN=$(NGROK_DOMAIN) bash scripts/start.sh

## Run lightweight style checks for Python and shell scripts
style: check-env
	@uvx ruff format --check .
	@uvx ruff check .
	@bash -lc 'command -v shellcheck >/dev/null 2>&1 || { echo "shellcheck not found. Install it from https://www.shellcheck.net/ or your package manager."; exit 1; }; shellcheck $$(git ls-files "*.sh")'

## Start local MCP server and open Claude interactively - production (requires: export OPENAPI_TOKEN=your_token)
try-claude: check-env .install.stamp
	@bash scripts/try-claude.sh

## Start local MCP server and open Claude interactively - sandbox (requires: export OPENAPI_SANDBOX_TOKEN=your_token)
try-claude-sandbox: check-env .install.stamp
	@SANDBOX=1 bash scripts/try-claude.sh

## ==============
## Git Operations
## ==============

dev-push:
	@git config credential.helper 'cache --timeout=3600'
	@git add .
	@git commit -m "chore: update code" || true
	@git push


## =======
## Release
## =======

## Build the package and publish it to PyPI (requires: uv, PyPI credentials)
release:
	rm -rf dist/
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
