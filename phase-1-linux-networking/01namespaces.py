#!/usr/bin/env python3
"""
netns_manager.py - Simple network namespace manager for a mini-cloud platform.

Wraps the `ip netns` commands you were running manually:
    sudo ip netns add ns1
    ip netns list
    sudo ip netns exec ns1 bash
    sudo ip netns del ns1

Usage:
    sudo python3 01namespaces.py create ns1
    python3 01namespaces.py list
    sudo python3 01namespaces.py exec ns1
    sudo python3 01namespaces.py exec ns1 -- ping -c 3 8.8.8.8
    sudo python3 01namespaces.py delete ns1
    python3 01namespaces.py exists ns1

Note: create/exec/delete need root privileges (run with sudo).
      list/exists work without sudo.
"""

import argparse
import subprocess
import sys


def run(cmd, check=True):
    """Run a shell command, streaming output live, and return the result."""
    print(f"[+] Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    if check and result.returncode != 0:
        print(f"[!] Command failed with exit code {result.returncode}", file=sys.stderr)
        sys.exit(result.returncode)
    return result


def list_namespaces():
    """Return a list of existing namespace names."""
    result = subprocess.run(["ip", "netns", "list"], capture_output=True, text=True)
    names = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if line:
            # ip netns list sometimes prints "ns1 (id: 0)"
            names.append(line.split()[0])
    return names


def cmd_create(args):
    if args.name in list_namespaces():
        print(f"[!] Namespace '{args.name}' already exists.")
        return
    run(["sudo", "ip", "netns", "add", args.name])
    print(f"[+] Namespace '{args.name}' created.")


def cmd_delete(args):
    if args.name not in list_namespaces():
        print(f"[!] Namespace '{args.name}' does not exist.")
        return
    run(["sudo", "ip", "netns", "del", args.name])
    print(f"[+] Namespace '{args.name}' deleted.")


def cmd_list(args):
    names = list_namespaces()
    if not names:
        print("No namespaces found.")
        return
    print("Namespaces:")
    for n in names:
        print(f"  - {n}")


def cmd_exists(args):
    exists = args.name in list_namespaces()
    print(f"'{args.name}' exists: {exists}")
    sys.exit(0 if exists else 1)


def cmd_exec(args):
    if args.name not in list_namespaces():
        print(f"[!] Namespace '{args.name}' does not exist.")
        sys.exit(1)
    # Default to an interactive bash shell if no command given
    inner_cmd = args.command if args.command else ["bash"]
    full_cmd = ["sudo", "ip", "netns", "exec", args.name] + inner_cmd
    run(full_cmd, check=False)


def main():
    parser = argparse.ArgumentParser(description="Manage Linux network namespaces.")
    sub = parser.add_subparsers(dest="action", required=True)

    p_create = sub.add_parser("create", help="Create a new namespace")
    p_create.add_argument("name", help="Namespace name")
    p_create.set_defaults(func=cmd_create)

    p_delete = sub.add_parser("delete", help="Delete an existing namespace")
    p_delete.add_argument("name", help="Namespace name")
    p_delete.set_defaults(func=cmd_delete)

    p_list = sub.add_parser("list", help="List all namespaces")
    p_list.set_defaults(func=cmd_list)

    p_exists = sub.add_parser("exists", help="Check if a namespace exists")
    p_exists.add_argument("name", help="Namespace name")
    p_exists.set_defaults(func=cmd_exists)

    p_exec = sub.add_parser("exec", help="Execute a command inside a namespace (default: bash)")
    p_exec.add_argument("name", help="Namespace name")
    p_exec.add_argument("command", nargs=argparse.REMAINDER,
                         help="Command to run inside the namespace (default: bash). "
                              "Use '--' before the command, e.g. exec ns1 -- ping -c 3 8.8.8.8")
    p_exec.set_defaults(func=cmd_exec)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()