#!/usr/bin/env python3
"""
network_tester.py
Stage 9 - Network Connectivity Tester

Tests connectivity between Linux namespaces.

Usage:

    sudo python3 network_tester.py \
        --source ns1 \
        --target 10.0.0.2

Example:

    sudo python3 network_tester.py \
        --source ns1 \
        --target 10.0.0.2

"""

import argparse
import subprocess
import sys


def run_ping(namespace, target, count=2):

    cmd = [
        "sudo",
        "ip",
        "netns",
        "exec",
        namespace,
        "ping",
        "-c",
        str(count),
        target,
    ]

    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    return result.returncode == 0


def print_result(name, success):

    symbol = "✓" if success else "✗"

    print(f"{symbol} {name}")


def main():

    parser = argparse.ArgumentParser(
        description="Network Connectivity Tester"
    )

    parser.add_argument(
        "--source",
        required=True,
        help="Source namespace",
    )

    parser.add_argument(
        "--target",
        required=True,
        help="Target IP address",
    )

    args = parser.parse_args()

    ok = run_ping(args.source, args.target)

    print_result(f"{args.source} -> {args.target}", ok)

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()