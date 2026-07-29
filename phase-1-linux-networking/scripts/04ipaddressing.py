#!/usr/bin/env python3
"""
04ipaddressing.py - Stage 3 of the mini-cloud platform: IP addressing.

Wraps the commands you used manually, run inside each namespace:

    Inside ns1:
        ip addr add 10.0.1.1/24 dev veth1
        ip link set lo up
        ip link set veth1 up

    Inside ns2:
        ip addr add 10.0.1.2/24 dev veth2
        ip link set lo up
        ip link set veth2 up

Usage:
    # Assign an IP to an interface inside a namespace
    sudo python3 04ipaddressing.py assign ns1 veth1 10.0.1.1/24

    # Bring an interface up inside a namespace
    sudo python3 04ipaddressing.py up ns1 lo
    sudo python3 04ipaddressing.py up ns1 veth1

    # Or do all 3 steps (assign IP + bring up lo + bring up the interface) at once
    sudo python3 04ipaddressing.py setup ns1 veth1 10.0.1.1/24
    sudo python3 04ipaddressing.py setup ns2 veth2 10.0.1.2/24

    # Check the result
    python3 04ipaddressing.py show ns1
    python3 04ipaddressing.py show ns2

    # Test connectivity between the two namespaces
    sudo python3 04ipaddressing.py ping ns1 10.0.1.2

Note: assign/up/setup/ping need root privileges (run with sudo).
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


def cmd_assign(args):
    """ip netns exec <namespace> ip addr add <ip> dev <iface>"""
    run(["sudo", "ip", "netns", "exec", args.namespace,
         "ip", "addr", "add", args.ip, "dev", args.iface])
    print(f"[+] Assigned {args.ip} to '{args.iface}' inside '{args.namespace}'")


def cmd_up(args):
    """ip netns exec <namespace> ip link set <iface> up"""
    run(["sudo", "ip", "netns", "exec", args.namespace,
         "ip", "link", "set", args.iface, "up"])
    print(f"[+] Interface '{args.iface}' is up inside '{args.namespace}'")


def cmd_setup(args):
    """Full pipeline: assign IP, bring up loopback, bring up the interface."""
    run(["sudo", "ip", "netns", "exec", args.namespace,
         "ip", "addr", "add", args.ip, "dev", args.iface])
    run(["sudo", "ip", "netns", "exec", args.namespace,
         "ip", "link", "set", "lo", "up"])
    run(["sudo", "ip", "netns", "exec", args.namespace,
         "ip", "link", "set", args.iface, "up"])
    print(f"[+] '{args.namespace}' ready: {args.iface} = {args.ip}, lo and {args.iface} are up")


def cmd_show(args):
    """Show interfaces and IPs inside a namespace."""
    run(["sudo", "ip", "netns", "exec", args.namespace, "ip", "addr", "show"], check=False)


def cmd_ping(args):
    """Ping a target IP from inside a namespace, to test connectivity."""
    count = str(args.count)
    run(["sudo", "ip", "netns", "exec", args.namespace,
         "ping", "-c", count, args.target], check=False)


def main():
    parser = argparse.ArgumentParser(description="Assign IPs and bring up interfaces inside namespaces.")
    sub = parser.add_subparsers(dest="action", required=True)

    p_assign = sub.add_parser("assign", help="Assign an IP address to an interface inside a namespace")
    p_assign.add_argument("namespace", help="Namespace name (e.g. ns1)")
    p_assign.add_argument("iface", help="Interface name (e.g. veth1)")
    p_assign.add_argument("ip", help="IP address with CIDR (e.g. 10.0.1.1/24)")
    p_assign.set_defaults(func=cmd_assign)

    p_up = sub.add_parser("up", help="Bring an interface up inside a namespace")
    p_up.add_argument("namespace", help="Namespace name (e.g. ns1)")
    p_up.add_argument("iface", help="Interface name (e.g. lo, veth1)")
    p_up.set_defaults(func=cmd_up)

    p_setup = sub.add_parser("setup", help="Assign IP + bring up lo + bring up the interface, in one step")
    p_setup.add_argument("namespace", help="Namespace name (e.g. ns1)")
    p_setup.add_argument("iface", help="Interface name (e.g. veth1)")
    p_setup.add_argument("ip", help="IP address with CIDR (e.g. 10.0.1.1/24)")
    p_setup.set_defaults(func=cmd_setup)

    p_show = sub.add_parser("show", help="Show interfaces/IPs inside a namespace")
    p_show.add_argument("namespace", help="Namespace name (e.g. ns1)")
    p_show.set_defaults(func=cmd_show)

    p_ping = sub.add_parser("ping", help="Ping a target from inside a namespace")
    p_ping.add_argument("namespace", help="Namespace to ping from (e.g. ns1)")
    p_ping.add_argument("target", help="Target IP to ping (e.g. 10.0.1.2)")
    p_ping.add_argument("-c", "--count", type=int, default=3, help="Number of pings (default: 3)")
    p_ping.set_defaults(func=cmd_ping)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()