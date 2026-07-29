#!/usr/bin/env python3
"""
veth_manager.py - Stage 2 of the mini-cloud platform: veth pairs.

Wraps the commands you used manually:
    sudo ip link add veth1 type veth peer name veth2
    sudo ip link set veth1 netns ns1
    sudo ip link set veth2 netns ns2

Usage:
    # Create the veth pair (both ends still in the host namespace)
    sudo python3 veth_manager.py create veth1 veth2

    # Move one end into a namespace
    sudo python3 veth_manager.py attach veth1 ns1
    sudo python3 veth_manager.py attach veth2 ns2

    # Or do all three steps in one go
    sudo python3 veth_manager.py setup veth1 ns1 veth2 ns2

    # List links (on host, or inside a namespace)
    python3 veth_manager.py list
    python3 veth_manager.py list --netns ns1

    # Delete a veth pair (deleting one end removes its peer too)
    sudo python3 veth_manager.py delete veth1
    sudo python3 veth_manager.py delete veth1 --netns ns1

Note: create/attach/setup/delete need root privileges (run with sudo).
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


def cmd_create(args):
    """sudo ip link add <veth1> type veth peer name <veth2>"""
    run(["sudo", "ip", "link", "add", args.veth1, "type", "veth", "peer", "name", args.veth2])
    print(f"[+] veth pair created: {args.veth1} <-> {args.veth2}")


def cmd_attach(args):
    """sudo ip link set <veth> netns <namespace>"""
    run(["sudo", "ip", "link", "set", args.veth, "netns", args.namespace])
    print(f"[+] '{args.veth}' moved into namespace '{args.namespace}'")


def cmd_setup(args):
    """Full pipeline: create the pair, then move each end into its namespace."""
    run(["sudo", "ip", "link", "add", args.veth1, "type", "veth", "peer", "name", args.veth2])
    run(["sudo", "ip", "link", "set", args.veth1, "netns", args.ns1])
    run(["sudo", "ip", "link", "set", args.veth2, "netns", args.ns2])
    print(f"[+] Done: {args.veth1} -> {args.ns1}, {args.veth2} -> {args.ns2}")


def cmd_list(args):
    """ip link list, optionally inside a namespace."""
    if args.netns:
        cmd = ["sudo", "ip", "netns", "exec", args.netns, "ip", "link", "list"]
    else:
        cmd = ["ip", "link", "list"]
    run(cmd, check=False)


def cmd_delete(args):
    """
    Delete a veth interface. Deleting one end automatically removes its peer.
    Pass --netns if the interface currently lives inside a namespace.
    """
    if args.netns:
        cmd = ["sudo", "ip", "netns", "exec", args.netns, "ip", "link", "delete", args.veth]
    else:
        cmd = ["sudo", "ip", "link", "delete", args.veth]
    run(cmd)
    print(f"[+] '{args.veth}' (and its peer) deleted.")


def main():
    parser = argparse.ArgumentParser(description="Manage veth pairs between namespaces.")
    sub = parser.add_subparsers(dest="action", required=True)

    p_create = sub.add_parser("create", help="Create a veth pair on the host")
    p_create.add_argument("veth1", help="First interface name (e.g. veth1)")
    p_create.add_argument("veth2", help="Second interface name (e.g. veth2)")
    p_create.set_defaults(func=cmd_create)

    p_attach = sub.add_parser("attach", help="Move one veth end into a namespace")
    p_attach.add_argument("veth", help="Interface name (e.g. veth1)")
    p_attach.add_argument("namespace", help="Target namespace (e.g. ns1)")
    p_attach.set_defaults(func=cmd_attach)

    p_setup = sub.add_parser("setup", help="Create the pair and attach both ends in one step")
    p_setup.add_argument("veth1", help="First interface name (e.g. veth1)")
    p_setup.add_argument("ns1", help="Namespace for veth1 (e.g. ns1)")
    p_setup.add_argument("veth2", help="Second interface name (e.g. veth2)")
    p_setup.add_argument("ns2", help="Namespace for veth2 (e.g. ns2)")
    p_setup.set_defaults(func=cmd_setup)

    p_list = sub.add_parser("list", help="List links on host or inside a namespace")
    p_list.add_argument("--netns", help="List links inside this namespace instead of the host")
    p_list.set_defaults(func=cmd_list)

    p_delete = sub.add_parser("delete", help="Delete a veth interface (removes its peer too)")
    p_delete.add_argument("veth", help="Interface name to delete (e.g. veth1)")
    p_delete.add_argument("--netns", help="Namespace the interface currently lives in")
    p_delete.set_defaults(func=cmd_delete)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()