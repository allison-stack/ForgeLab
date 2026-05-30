"""forgelab start — launch the ForgeLab server from any target repo root."""
import argparse
import subprocess
import sys


def main() -> None:
    parser = argparse.ArgumentParser(prog="forgelab")
    sub = parser.add_subparsers(dest="command")

    start = sub.add_parser("start", help="Start the ForgeLab server")
    start.add_argument("--port", type=int, default=8000, help="Port (default: 8000)")
    start.add_argument("--host", default="127.0.0.1", help="Host (default: 127.0.0.1)")
    start.add_argument("--reload", action="store_true", help="Enable auto-reload (dev mode)")

    args = parser.parse_args()

    if args.command == "start":
        cmd = [
            sys.executable, "-m", "uvicorn",
            "forgelab.api:app",
            "--host", args.host,
            "--port", str(args.port),
        ]
        if args.reload:
            cmd.append("--reload")
        subprocess.run(cmd, check=True)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
