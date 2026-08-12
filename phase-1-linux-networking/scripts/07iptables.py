#!/usr/bin/env python3
"""
07iptables.py
Stage 8 - Linux Firewall (iptables)

Features:
    - Allow ICMP (ping)
    - Block SSH (port 22)
    - Allow SSH
    - List firewall rules
    - Flush INPUT rules (scoped to the INPUT chain only, never the
      whole filter table / NAT rules)

Examples:

    sudo python3 07iptables.py allow-ping

    sudo python3 07iptables.py block-ssh

    sudo python3 07iptables.py allow-ssh

    sudo python3 07iptables.py list

    sudo python3 07iptables.py flush
"""

import argparse
import subprocess
import sys


def run(cmd):
    full = ["sudo"] + cmd
    print("[+] " + " ".join(full))
    subprocess.run(full, check=True)


def allow_ping():
    run([
        "iptables",
        "-A",
        "INPUT",
        "-p",
        "icmp",
        "-j",
        "ACCEPT"
    ])


def block_ssh():
    run([
        "iptables",
        "-A",
        "INPUT",
        "-p",
        "tcp",
        "--dport",
        "22",
        "-j",
        "DROP"
    ])


def allow_ssh():
    run([
        "iptables",
        "-A",
        "INPUT",
        "-p",
        "tcp",
        "--dport",
        "22",
        "-j",
        "ACCEPT"
    ])


def list_rules():
    run([
        "iptables",
        "-L",
        "-n",
        "-v"
    ])


def flush():
    run([
        "iptables",
        "-F",
        "INPUT"
    ])


def main():

    parser = argparse.ArgumentParser(
        description="Linux iptables manager"
    )

    sub = parser.add_subparsers(dest="command")

    sub.add_parser("allow-ping")
    sub.add_parser("block-ssh")
    sub.add_parser("allow-ssh")
    sub.add_parser("list")
    sub.add_parser("flush")

    args = parser.parse_args()

    if args.command == "allow-ping":
        allow_ping()

    elif args.command == "block-ssh":
        block_ssh()

    elif args.command == "allow-ssh":
        allow_ssh()

    elif args.command == "list":
        list_rules()

    elif args.command == "flush":
        flush()

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()