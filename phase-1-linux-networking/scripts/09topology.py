#!/usr/bin/env python3
"""
09topology.py - End-to-end mini-cloud topology: two subnets routed together + NAT to internet.

Builds the full Phase-1 stack in one shot on the HOST:

    ns1 (10.0.1.1)                ns2 (10.0.2.1)
      10.0.1.0/24                   10.0.2.0/24
        veth1                          veth2
          │                              │
          └──────────────┐  ┌────────────┘
                     ┌───┴──┴───┐
                     │  router  │  eth0 = 10.0.1.254, eth1 = 10.0.2.254
                     │          │  eth2 = 10.0.99.1,  ip_forward=1
                     └───┬──┬───┘
                         │
                  veth-host (10.0.99.254)
                         │
                   ┌─────┴─────┐
                   │   host    │  MASQUERADE 10.0.0.0/8 -> <internet iface>
                   └─────┬─────┘
                         │
                      Internet

What it demonstrates (matching scripts 01-06):
    network namespaces, veth pairs, IP addressing, routing, IP forwarding,
    MASQUERADE (NAT), and FORWARD-chain rules.

Usage:
    sudo python3 09topology.py up      # build the whole topology + run tests
    sudo python3 09topology.py test    # only re-run the connectivity tests
    sudo python3 09topology.py down    # tear everything down (idempotent)
    python3 09topology.py diagram      # print the ASCII topology

Note: up/test/down need root privileges (run with sudo).
"""

import argparse
import os
import shutil
import subprocess
import sys

NS1, NS2, ROUTER = "ns1", "ns2", "router"
UPLINK = "10.0.99.0/24"
UPLINK_HOST = "10.0.99.254/24"
UPLINK_ROUTER = "10.0.99.1/24"

TESTS = [
    ("ns1 -> ns2 (10.0.2.1, cross-subnet via router)", NS1, "10.0.2.1"),
    ("ns2 -> ns1 (10.0.1.1, cross-subnet via router)", NS2, "10.0.1.1"),
    ("ns1 -> internet (8.8.8.8, host NAT)", NS1, "8.8.8.8"),
    ("ns2 -> internet (8.8.8.8, host NAT)", NS2, "8.8.8.8"),
]


def run(cmd, check=True):
    """Run a shell command, streaming output live, and return the result."""
    if not shutil.which(cmd[0]):
        print (f"[!] Required command not found: {cmd[0]}", file=sys.stderr)
        if check:
            sys.exit(127)
        return None
    print(f"[+] Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"[!] Command failed with exit code {result.returncode}: {' '.join(cmd)}",
              file=sys.stderr)
        print(result.stderr.strip(), file=sys.stderr)
        sys.exit(result.returncode)
    return result


def ns(name, *cmd):
    """Prefix a command so it runs inside a network namespace."""
    return ["ip", "netns", "exec", name] + list(cmd)


def root_check():
    if os.geteuid() != 0:
        print("[!] This script needs root privileges. Run with sudo.", file=sys.stderr)
        sys.exit(1)


def internet_iface():
    """Return the host's default-route interface, or None if there is none."""
    result = run(["ip", "-o", "-4", "route", "show", "default"], check=False)
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 5 and parts[3] == "dev":
            return parts[4]
    return None


def setup_namespace(name, iface, ip):
    """Bring up loopback + an interface and assign an IP inside a namespace."""
    run(ns(name, "ip", "link", "set", "lo", "up"))
    run(ns(name, "ip", "addr", "add", ip, "dev", iface))
    run(ns(name, "ip", "link", "set", iface, "up"))


def ping_ok(name, target, count=2):
    """Ping a target from inside a namespace; return True on success."""
    result = run(ns(name, "ping", "-c", str(count), "-W", "2", target), check=False)
    return result is not None and result.returncode == 0


def draw_diagram():
    print()
    print("  ns1 (10.0.1.1)                    ns2 (10.0.2.1)")
    print("   10.0.1.0/24                       10.0.2.0/24")
    print("     veth1                              veth2")
    print("       |                                  |")
    print("       +---------------+  +---------------+")
    print("                     +--+--+")
    print("                     |router| eth0=10.0.1.254 eth1=10.0.2.254")
    print("                     |      | eth2=10.0.99.1  ip_forward=1")
    print("                     +--+--+")
    print("                        |")
    print("                 veth-host (10.0.99.254)")
    print("                        |")
    print("                    +---+---+")
    print("                    |  host  | MASQUERADE 10.0.0.0/8 -> <internet iface>")
    print("                    +---+---+")
    print("                        |")
    print("                     Internet")
    print()


def cmd_up(args):
    root_check()
    print("== Tearing down any leftover state ==")
    cmd_down(args)

    print("== Creating namespaces ==")
    run(["ip", "netns", "add", NS1])
    run(["ip", "netns", "add", NS2])
    run(["ip", "netns", "add", ROUTER])

    print("== Creating veth pairs ==")
    run(["ip", "link", "add", "veth1", "type", "veth", "peer", "name", "veth1-r"])
    run(["ip", "link", "add", "veth2", "type", "veth", "peer", "name", "veth2-r"])
    run(["ip", "link", "add", "veth-r", "type", "veth", "peer", "name", "veth-host"])

    print("== Moving veth ends into namespaces ==")
    run(["ip", "link", "set", "veth1", "netns", NS1])
    run(["ip", "link", "set", "veth1-r", "netns", ROUTER])
    run(["ip", "link", "set", "veth2", "netns", NS2])
    run(["ip", "link", "set", "veth2-r", "netns", ROUTER])
    run(["ip", "link", "set", "veth-r", "netns", ROUTER])

    print("== Naming router interfaces ==")
    run(ns(ROUTER, "ip", "link", "set", "veth1-r", "name", "eth0"))
    run(ns(ROUTER, "ip", "link", "set", "veth2-r", "name", "eth1"))
    run(ns(ROUTER, "ip", "link", "set", "veth-r", "name", "eth2"))

    print("== Assigning IPs ==")
    setup_namespace(NS1, "veth1", "10.0.1.1/24")
    setup_namespace(NS2, "veth2", "10.0.2.1/24")
    setup_namespace(ROUTER, "eth0", "10.0.1.254/24")
    setup_namespace(ROUTER, "eth1", "10.0.2.254/24")
    setup_namespace(ROUTER, "eth2", UPLINK_ROUTER)
    run(["ip", "addr", "add", UPLINK_HOST, "dev", "veth-host"])
    run(["ip", "link", "set", "veth-host", "up"])

    print("== Adding routes ==")
    run(ns(NS1, "ip", "route", "add", "default", "via", "10.0.1.254"))
    run(ns(NS2, "ip", "route", "add", "default", "via", "10.0.2.254"))
    run(ns(ROUTER, "ip", "route", "add", "default", "via", "10.0.99.254"))

    print("== Enabling IP forwarding ==")
    run(ns(ROUTER, "sysctl", "-w", "net.ipv4.ip_forward=1"))
    run(["sysctl", "-w", "net.ipv4.ip_forward=1"])

    print("== Setting up host NAT ==")
    iface = internet_iface()
    if iface and shutil.which("iptables"):
        print(f"[i] Internet-facing interface detected: {iface}")
        run(["iptables", "-t", "nat", "-A", "POSTROUTING",
             "-s", "10.0.0.0/8", "-o", iface, "-j", "MASQUERADE"])
        run(["iptables", "-A", "FORWARD", "-i", "veth-host", "-o", iface, "-j", "ACCEPT"])
        run(["iptables", "-A", "FORWARD", "-i", iface, "-o", "veth-host",
             "-m", "state", "--state", "ESTABLISHED,RELATED", "-j", "ACCEPT"])
    elif not iface:
        print("[!] No default route found on the host — skipping NAT "
              "(the internet tests below will fail).")
    else:
        print("[!] 'iptables' not found on the host — skipping NAT "
              "(the internet tests below will fail). Install it or use nftables manually.)")

    print()
    cmd_test(args)


def cmd_test(args):
    root_check()
    failed = False
    for label, src, target in TESTS:
        ok = ping_ok(src, target)
        print(f"{'OK ' if ok else 'FAIL'} {label}")
        failed = failed or not ok
    print()
    print("All tests passed." if not failed else "Some tests FAILED.")
    sys.exit(0 if not failed else 1)


def cmd_down(args):
    root_check()
    iface = internet_iface()
    if iface and shutil.which("iptables"):
        run(["iptables", "-t", "nat", "-D", "POSTROUTING",
             "-s", "10.0.0.0/8", "-o", iface, "-j", "MASQUERADE"], check=False)
        run(["iptables", "-D", "FORWARD", "-i", "veth-host", "-o", iface, "-j", "ACCEPT"], check=False)
        run(["iptables", "-D", "FORWARD", "-i", iface, "-o", "veth-host",
             "-m", "state", "--state", "ESTABLISHED,RELATED", "-j", "ACCEPT"], check=False)
    # Deleting a namespace destroys its interfaces (and, transitively, their veth peers).
    for name in (ROUTER, NS1, NS2):
        run(["ip", "netns", "del", name], check=False)
    run(["ip", "link", "del", "veth-host"], check=False)
    print("[+] Cleanup done.")


def cmd_diagram(args):
    draw_diagram()


def main():
    parser = argparse.ArgumentParser(
        description="Build, test, and tear down the full Phase-1 mini-cloud topology.")
    sub = parser.add_subparsers(dest="action", required=True)

    sub.add_parser("up", help="Build the whole topology and run connectivity tests").set_defaults(func=cmd_up)
    sub.add_parser("test", help="Only re-run the connectivity tests").set_defaults(func=cmd_test)
    sub.add_parser("down", help="Tear down the whole topology (idempotent)").set_defaults(func=cmd_down)
    sub.add_parser("diagram", help="Print the ASCII topology").set_defaults(func=cmd_diagram)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
