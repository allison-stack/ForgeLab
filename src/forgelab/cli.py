"""forgelab CLI — start the server or run the scripted demo."""
import argparse
import os
import subprocess
import sys


def main() -> None:
    parser = argparse.ArgumentParser(prog="forgelab")
    sub = parser.add_subparsers(dest="command")

    start = sub.add_parser("start", help="Start the ForgeLab server")
    start.add_argument("--port", type=int, default=8000)
    start.add_argument("--host", default="127.0.0.1")
    start.add_argument("--reload", action="store_true")

    demo = sub.add_parser("demo", help="Stream a scripted fixture through the demo server")
    demo.add_argument("--fixture", default="demo/arrow-bug-1148.json",
                      help="Path to fixture JSON (default: demo/arrow-bug-1148.json)")
    demo.add_argument("--speed", type=float, default=1.0,
                      help="Delay multiplier: 0.5 = faster, 2.0 = slower (default: 1.0)")
    demo.add_argument("--port", type=int, default=8000)
    demo.add_argument("--host", default="127.0.0.1")

    benchmark_parser = sub.add_parser("benchmark", help="Run benchmark against SWE-bench Lite tasks")
    benchmark_parser.add_argument(
        "--tasks", default="benchmark/tasks.json",
        help="Path to tasks JSON (default: benchmark/tasks.json)",
    )
    benchmark_parser.add_argument(
        "--output", default="benchmark/results",
        help="Output directory (default: benchmark/results)",
    )

    args = parser.parse_args()

    if args.command == "start":
        cmd = [sys.executable, "-m", "uvicorn", "forgelab.api:app",
               "--host", args.host, "--port", str(args.port)]
        if args.reload:
            cmd.append("--reload")
        subprocess.run(cmd, check=True)

    elif args.command == "demo":
        if not os.path.exists(args.fixture):
            sys.exit(f"Fixture not found: {args.fixture}")
        env = {
            **os.environ,
            "FORGELAB_DEMO_FIXTURE": args.fixture,
            "FORGELAB_DEMO_SPEED": str(args.speed),
        }
        cmd = [sys.executable, "-m", "uvicorn", "forgelab.demo_server:app",
               "--host", args.host, "--port", str(args.port)]
        subprocess.run(cmd, env=env, check=True)

    elif args.command == "benchmark":
        if not os.path.exists(args.tasks):
            sys.exit(f"Tasks file not found: {args.tasks}")
        from forgelab.benchmark_runner import run_benchmark
        run_benchmark(tasks_path=args.tasks, output_dir=args.output)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
