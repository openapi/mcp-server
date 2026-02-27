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

.PHONY: start check-env

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
	$(UV) run uvicorn openapi_mcp_server.main:app --host $(HOST) --port $(PORT)