# Contributing to mcp.openapi.com

Thanks for considering contributing! We welcome all kinds of contributions: bug reports, feature requests, documentation improvements, and code enhancements.

## How to Contribute

1. **Fork the repository** and clone it locally:
   ```bash
   git clone https://github.com/<username>/mcp-server.git
   ```

2. **Create a branch** for your feature or fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes** and commit them:
   ```bash
   git commit -m "Add some feature"
   ```

4. **Push your branch** to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Open a Pull Request** describing your changes.

## Adding a New Tool or API

New tools live in the [`/apis/`](../apis/) directory. Each file groups related tools by API domain. Follow the existing pattern:

```python
from fastmcp import Context
from typing import Any
from mcp_core import make_api_call, mcp

@mcp.tool
async def tool_name(param: str, ctx: Context) -> Any:
    """Tool description shown to the AI."""
    return make_api_call(ctx, "GET", "https://api.openapi.com/endpoint", params={"param": param})
```

After adding a new file, make sure it is imported in [`main.py`](../main.py).

## Guidelines

- Follow the existing **Python coding style** (PEP 8).
- Run `make style` before opening a pull request to check Python formatting/linting and shell scripts.
- Include **tests** for new features or bug fixes when applicable.
- Keep **commit messages clear and concise**.
- Update **documentation** as needed for your changes.
- Never hardcode credentials, tokens, or secrets in the code.

## Reporting Issues

To report bugs or request features, please **open an issue** on GitHub including:

- Clear description of the problem or feature.
- Steps to reproduce (if applicable).
- Relevant logs or screenshots.

Thank you for helping improve mcp.openapi.com!
