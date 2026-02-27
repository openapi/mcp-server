# mcp.openapi.com MCP Gateway

This project implements a **Model Context Protocol (MCP)** server that acts as a secure, unified gateway for accessing authenticated openapi.com services. The server is designed to integrate with AI environments such as VS Code, Claude Desktop, and other MCP hosts.

## Features

- **Secure proxy**: Pass-through of the Bearer Token provided by the client, without direct handling of sensitive credentials.
- **Extensible**: Easily add new tools/APIs by creating modules in [`/apis/`](apis/).
- **MCP-compatible**: Designed according to MCP protocol best practices.
- **Modular**: All API call logic and tool registration is centralized in [`mcp_core.py`](mcp_core.py).

---

## Prerequisites

- Python 3.9+
- [uv](https://github.com/astral-sh/uv) (for dependency management)
- Internet connection
- **(Optional)** [Docker](https://www.docker.com/) for containerized execution

---

## Installation (Local Environment)

1. **Clone the repository**
   ```bash
   git clone <REPO_URL>
   cd mcp.openapi.com
   ```

2. **Create and activate a virtual environment**
   ```bash
   uv venv
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   uv pip install -r requirements.txt
   # or, using uv:
   uv add "fastmcp" requests pydantic
   ```

---

## Starting the Server

```bash
python main.py
```

The server will be available at `http://0.0.0.0:8080`.

---

## Running with Docker

1. **Build the Docker image**
   ```bash
   docker build -t mcp-openapi .
   ```

2. **Start the container**
   ```bash
   docker run -it --rm -p 8080:8080 mcp-openapi
   ```

The server will be accessible at `http://localhost:8080`.

---

## Debug and Development

- The server prints details of every request to the console, including headers and parameters.
- To view logs, start the server from a terminal:
  ```bash
  python main.py
  ```
- You can modify the `make_api_call` function in [`mcp_core.py`](mcp_core.py) to add additional print statements or logging.
- Use tools like [httpie](https://httpie.io/) or `curl` to manually test endpoints:
  ```bash
  curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8080/mcp/
  ```

### Hot Reload (optional)

For rapid development, you can use [watchdog](https://pypi.org/project/watchdog/) or [entr](https://eradman.com/entrproject/) to restart the server on every file change:
```bash
pip install watchdog
watchmedo auto-restart --pattern="*.py" -- python main.py
```

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

- [`main.py`](main.py): FastAPI + MCP server entry point.
- [`mcp_core.py`](mcp_core.py): MCP initialization, API call helpers, error handling.
- [`/apis/`](apis/): Python modules defining MCP tools (one per API/scope).
- [`requirements.txt`](requirements.txt): Python dependencies.
- [`docs/`](docs/): Documentation and example configurations.
- [`Dockerfile`](Dockerfile): Docker container build and start.

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