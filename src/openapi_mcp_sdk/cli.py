import argparse
import os
import platform
import sys


_BANNER = r"""
     ____                               _
    / __ \____  ___  ____  ____ _____  (_) ®
   / / / / __ \/ _ \/ __ \/ __ `/ __ \/ /
  / /_/ / /_/ /  __/ / / / /_/ / /_/ / /
  \____/ .___/\___/_/ /_/\__,_/ .___/_/
      /_/                    /_/
                        mcp sdk
"""


def _print_banner(port: int) -> None:
    try:
        from importlib.metadata import version
        ver = version("openapi-mcp-sdk")
    except Exception:
        ver = "dev"

    py_ver   = platform.python_version()
    os_name  = platform.system()
    os_rel   = platform.release()
    arch     = platform.machine()
    node     = platform.node()

    sep = "─" * 54

    sys.stderr.write(_BANNER)
    sys.stderr.write(f"  The official openapi.com MCP SDK\n")
    sys.stderr.write(f"  {sep}\n")
    sys.stderr.write(f"  version   {ver}\n")
    sys.stderr.write(f"  listen    http://0.0.0.0:{port}\n")
    sys.stderr.write(f"  python    {py_ver}\n")
    sys.stderr.write(f"  platform  {os_name} {os_rel}  {arch}\n")
    sys.stderr.write(f"  host      {node}\n")
    sys.stderr.write(f"  {sep}\n\n")
    sys.stderr.flush()


def main():
    parser = argparse.ArgumentParser(
        prog="openapi-mcp-sdk",
        description=(
            "Openapi.com MCP SDK — run as a ready-to-use MCP server "
            "or import as a library to build your own."
        ),
    )

    subparsers = parser.add_subparsers(dest="command", metavar="<command>")

    subparsers.add_parser(
        "server",
        help="Start the MCP server (HTTP/SSE, default port 8080)",
    )

    # Future commands — uncomment and implement when ready:
    # subparsers.add_parser("ping",  help="Ping the openapi.com APIs and report latency")
    # subparsers.add_parser("token", help="Generate or inspect an openapi.com Bearer token")

    args = parser.parse_args()

    if args.command == "server":
        import warnings
        warnings.filterwarnings("ignore", category=DeprecationWarning)

        port = int(os.environ.get("PORT", 8080))
        _print_banner(port)

        from .main import run
        run()
    else:
        parser.print_help()
        sys.exit(1)
