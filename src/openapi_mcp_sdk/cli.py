import argparse
import sys


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
        from .main import run
        run()
    else:
        parser.print_help()
        sys.exit(1)
