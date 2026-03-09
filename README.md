# openapi-mcp-sdk

**`openapi-mcp-sdk`** is the official [openapi.com](https://openapi.com/) MCP SDK.
It ships as a Python package on [PyPI](https://pypi.org/project/openapi-mcp-sdk/) and
can be used in two ways:

- **Ready-to-use server** — run the MCP gateway directly from the package with a
  single command, no cloning or setup required.
- **Python library** — import `openapi_mcp_server` in your own project to build a
  custom MCP server that wraps openapi.com APIs with your own logic, tools, or auth
  layer on top.

---

## Features

- **Secure proxy**: Pass-through of the Bearer Token provided by the client, without direct handling of sensitive credentials.
- **Extensible**: Easily add new tools/APIs by creating modules in [`/apis/`](src/openapi_mcp_server/apis/).
- **MCP-compatible**: Designed according to MCP protocol best practices.
- **Modular**: All API call logic and tool registration is centralized in [`mcp_core.py`](src/openapi_mcp_server/mcp_core.py).

---

## Quick Start — run from PyPI (recommended)

No cloning, no virtual environment. Start the server in one command:

```bash
uvx openapi-mcp-sdk server
```

The server starts immediately at `http://localhost:8080`.

### Other runtimes

```bash
# pipx (ephemeral run, no install needed — similar to uvx)
pipx run openapi-mcp-sdk server

# pip (installs the package, then run the command)
pip install openapi-mcp-sdk && openapi-mcp-sdk server

# pip3 on systems where python3 is the default
pip3 install openapi-mcp-sdk && openapi-mcp-sdk server
```

### CLI reference

```
openapi-mcp-sdk <command>

Commands:
  server   Start the MCP server (HTTP/SSE, default port 8080)
  ping     Ping the openapi.com APIs and report latency       [coming soon]
  token    Generate or inspect an openapi.com Bearer token    [coming soon]
```

---

## Local launcher script

Copy the block below, paste it into your terminal, and press Enter. It will
create a `mcp-server.sh` file in the current directory and launch the server:

```bash
cat > mcp-server.sh << 'EOF'
#!/bin/bash
# ============================================================
# Openapi.com MCP Server — local launcher
# Edit the variables below, then run: bash mcp-server.sh
# ============================================================

export PORT="${PORT:-8080}"
export SERVICES_CREDENTIALS="${SERVICES_CREDENTIALS:-{}}"

uvx openapi-mcp-sdk server
EOF
bash mcp-server.sh
```

Next time, just run:

```bash
bash mcp-server.sh
```

---

## Running with Docker

The project ships a single [`compose.yml`](compose.yml) with the `mcp` service.

```bash
# Build and start (production-like image)
docker compose up --build

# Run in background
docker compose up --build -d

# Follow logs
docker compose logs -f mcp
```

The server will be accessible at `http://localhost:8080`.

---

## Debug and Development

### Local development (without Docker)

The fastest iteration loop runs the server directly with `uvicorn`:

```bash
make start
```

This sets `PYTHONPATH=src` and starts `uvicorn` with auto-reload disabled. The
server listens on `http://0.0.0.0:8080`.

To test endpoints manually:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8080/mcp/
```

The server prints request headers and parameters to stdout — no extra
configuration needed.

---

### Remote debugging with VS Code and Docker (one click)

The repository is pre-configured for a **single-click** debug experience.
No manual steps, no editing compose files, no terminal commands.

#### How it works

| File | Role |
|---|---|
| [`docker/dev/Dockerfile`](docker/dev/Dockerfile) | Debug image — adds `debugpy`, exposes port 5678 |
| [`compose.yml`](compose.yml) | Compose config — dev image, debug ports, bind mount |
| [`.vscode/tasks.json`](.vscode/tasks.json) | VS Code tasks — starts/stops the container automatically |
| [`.vscode/launch.json`](.vscode/launch.json) | Launch config — ties everything together under F5 |

#### Workflow

1. **Set your breakpoints** anywhere in `src/`.
2. **Open Run and Debug** (`Ctrl+Shift+D` / `⌘+Shift+D`).
3. **Select `MCP: Debug (Docker)`** from the dropdown.
4. **Press F5.**

VS Code will:

- Build the debug image (`docker/dev/Dockerfile`) if needed.
- Start the container via `compose.yml` (debug image + bind mount).
- Wait automatically until the server logs `Server FastAPI+MCP ready`.
- Attach `debugpy` — your breakpoints are now live.

When you press **⇧F5** (Stop), VS Code detaches and tears down the container.

> **Keep the container alive after detaching?**
> Remove the `"postDebugTask"` line from `.vscode/launch.json`. You can then
> re-attach at any time by pressing F5 again without rebuilding.

#### Live code reload

`compose.yml` bind-mounts `./src` into `/app/src` inside the container.
Edits to files under `src/` are reflected **immediately** — no image rebuild
required. Just send a new request and the updated code runs.

#### Path mapping reference

| | Host | Container |
|---|---|---|
| Source code | `./src` | `/app/src` |
| MCP server | `localhost:8080` | `0.0.0.0:8080` |
| debugpy listener | `localhost:5678` | `0.0.0.0:5678` |

---

## MCP Client Configuration (VS Code)

1. **Generate a Bearer Token**
   From the portal https://console.openapi.com/oauth, create a token with the required scopes.

2. **Create the `.vscode/mcp.json` file**
   Example:
   ```json
   {
     "servers": {
       "openapi.com": {
         "type": "http",
         "url": "http://YOUR_SERVER_IP:8080/mcp/",
         "headers": {
           "Authorization": "Bearer YOUR_PRODUCTION_BEARER_TOKEN"
         }
       }
     }
   }
   ```

3. **Test the integration**
   - Reload VS Code.
   - Open the Copilot chat and type `@workspace`.
   - Use the tools exposed by the MCP server.

---

## Project Structure

- [`src/openapi_mcp_server/main.py`](src/openapi_mcp_server/main.py): FastAPI + MCP server entry point.
- [`src/openapi_mcp_server/mcp_core.py`](src/openapi_mcp_server/mcp_core.py): MCP initialization, API call helpers, error handling.
- [`src/openapi_mcp_server/apis/`](src/openapi_mcp_server/apis/): Python modules defining MCP tools (one per API/scope).
- [`requirements.txt`](requirements.txt): Python dependencies.
- [`compose.yml`](compose.yml): Docker Compose (production image by default; see comments to switch to debug).
- [`docker/latest/Dockerfile`](docker/latest/Dockerfile): Production Docker image.
- [`docker/dev/Dockerfile`](docker/dev/Dockerfile): Development image with `debugpy` for VS Code remote debugging.
- [`.vscode/launch.json`](.vscode/launch.json): VS Code debug configuration (attach to debugpy).
- [`docs/`](docs/): Documentation and example configurations.

---

## Adding New Tools/APIs

1. Create or modify a file in [`/apis/`](apis/), following this pattern:
   ```python
   from fastmcp import Context
   from typing import Any
   from mcp_core import make_api_call, mcp

   @mcp.tool
   async def tool_name(parameters..., ctx: Context) -> Any:
       # ...logic...
       return make_api_call(ctx, "GET", url, params=params)
   ```
2. Restart the server to apply the changes.

---

## Security Notes

- **Never** hardcode credentials or tokens in the code.
- The server expects the Bearer Token to be provided by the client via HTTP headers.
- All API calls are proxied using the token provided by the client.

---

## Useful Resources

- [MCP Documentation](https://github.com/anthropics/model-context-protocol)
- [fastmcp](https://pypi.org/project/fastmcp/)
- [openapi.com](https://openapi.com/)

---

## Contributing

Contributions are always welcome! Whether you want to report bugs, suggest new features, improve documentation, or contribute code, your help is appreciated.

See [docs/contributing.md](docs/contributing.md) for detailed instructions on how to get started. Please make sure to follow this project's [docs/code-of-conduct.md](docs/code-of-conduct.md) to help maintain a welcoming and collaborative environment.

## Authors

Meet the project authors:

- Simone Desantis ([@SimoneDesantis](https://github.com/SimoneDesantis))
- Marco Prosperi ([@MarcoProsperi](https://github.com/MarcoProsperi))
- Francesco Bianco ([@francescobianco](https://github.com/frabcescobianco))
- Openapi Team ([@openapi-it](https://github.com/openapi-it))

## Partners

Meet our partners using Openapi or contributing to this SDK:

- [Blank](https://www.blank.app/)
- [Credit Safe](https://www.creditsafe.com/)
- [Deliveroo](https://deliveroo.it/)
- [Gruppo MOL](https://molgroupitaly.it/it/)
- [Jakala](https://www.jakala.com/)
- [Octotelematics](https://www.octotelematics.com/)
- [OTOQI](https://otoqi.com/)
- [PWC](https://www.pwc.com/)
- [QOMODO S.R.L.](https://www.qomodo.me/)
- [SOUNDREEF S.P.A.](https://www.soundreef.com/)

## License

This project is licensed under the [MIT License](LICENSE).

The MIT License is a permissive open-source license that allows you to freely use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the software, provided that the original copyright notice and this permission notice are included in all copies or substantial portions of the software.

In short, you are free to use this SDK in your personal, academic, or commercial projects, with minimal restrictions. The project is provided "as-is", without any warranty of any kind, either expressed or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose, and non-infringement.

For more details, see the full license text at the [MIT License page](https://choosealicense.com/licenses/mit/).