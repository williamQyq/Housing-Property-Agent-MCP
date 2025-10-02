#!/usr/bin/env python3
"""
Quick test client for the Master MCP Server /chat endpoint.

Usage:
  python3 scripts/test_chat.py --prompt "Leaking faucet in kitchen"

Options:
  --base http://localhost:8000   # override base URL
  or set env MASTER_URL          # e.g., export MASTER_URL=http://localhost:8000
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
import urllib.error

from dotenv import load_dotenv
load_dotenv()

def main() -> int:
    parser = argparse.ArgumentParser(description="Test POST /chat on master server")
    parser.add_argument("--prompt", required=True, help="Prompt to send to the assistant")
    parser.add_argument("--base", default=os.environ.get("MASTER_URL", "http://localhost:8000"), help="Base URL (default: http://localhost:8000 or env MASTER_URL)")
    args = parser.parse_args()

    base = args.base.rstrip("/")
    url = f"{base}/chat"
    payload = {"prompt": args.prompt}
    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode("utf-8")
            print(f"Status: {resp.status}")
            try:
                parsed = json.loads(body)
                print(json.dumps(parsed, indent=2))
            except json.JSONDecodeError:
                print(body)
            return 0
    except urllib.error.HTTPError as e:
        print(f"HTTPError: {e.code}")
        try:
            print(e.read().decode("utf-8"))
        except Exception:
            pass
        return 1
    except urllib.error.URLError as e:
        print(f"URLError: {e.reason}")
        return 2


if __name__ == "__main__":
    sys.exit(main())

