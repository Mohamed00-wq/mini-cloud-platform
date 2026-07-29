#!/usr/bin/env python3
"""
06nat.py - Stage 7 of the mini-cloud platform: NAT (Internet access).

Wraps the commands you'd run manually on the HOST (not inside a namespace):

    sudo sysctl -w net.ipv4.ip_forward=1
    sudo iptables -t nat -A POSTROUTING -s 10.0.1.0/24 -o eth0 -j MASQUERADE
    sudo iptables -A FORWARD -i veth-router -o eth0 -j ACCEPT
    sudo iptables -A FORWARD -i eth0 -o veth-router -m state --state ESTABLISHED,RELATED -j ACCEPT

Topology:
    ns1 --> router --> Host --> Internet

The router already forwards packets between ns1/ns2 (Stage 6). Now the HOST
itself needs to:
  1. Allow forwarding at the kernel level.
  2. MASQUERADE (NAT) traffic leaving through its real internet interface
     (e.g. eth0), rewriting the private 10.0.x.x source IPs to the host's
     public/real IP - exactly what an AWS NAT Gateway does for a private
     subnet.
  3. Explicitly allow the FORWARD chain to pass this traffic (some distros
     default FORWARD policy to DROP).

This script also keeps a state file (nat_topology.json) so it can redraw an
ASCII diagram of the current NAT setup after every change. It supports both
iptables (default) and nftables as the backend.

Usage:
    # Enable IP forwarding on the host kernel
    sudo python3 06nat.py enable-forwarding

    # Add MASQUERADE so a subnet can reach the internet through eth0
    sudo python3 06nat.py masquerade add 10.0.1.0/24 eth0
    sudo python3 06nat.py masquerade add 10.0.2.0/24 eth0

    # Allow the FORWARD chain to pass traffic between the router leg and eth0
    sudo python3 06nat.py allow-forward veth-router eth0

    # Remove a masquerade rule
    sudo python3 06nat.py masquerade remove 10.0.1.0/24 eth0

    # List current NAT rules
    python3 06nat.py masquerade list

    # Use nftables instead of iptables
    sudo python3 06nat.py masquerade add 10.0.1.0/24 eth0 --backend nft

    # Test internet access from inside a namespace
    sudo python3 06nat.py test ns1 8.8.8.8

    # Just redraw the diagram
    python3 06nat.py diagram

Note: enable-forwarding/masquerade add|remove/allow-forward/test need root
      privileges (run with sudo).
"""

import argparse
import json
import os
import subprocess
import sys

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nat_topology.json")


def run(cmd, check=True):
    """Run a shell command, streaming output live, and return the result."""
    print(f"[+] Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    if check and result.returncode != 0:
        print(f"[!] Command failed with exit code {result.returncode}", file=sys.stderr)
        sys.exit(result.returncode)
    return result


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"out_iface": None, "subnets": []}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def draw_diagram(state):
    """Print an ASCII diagram of subnets going out through NAT to the internet."""
    subnets = state.get("subnets", [])
    out_iface = state.get("out_iface")

    if not subnets:
        print("(no NAT rules configured yet)")
        return

    labels = [f"[{s}]" for s in subnets]
    col_width = max(len(l) for l in labels) + 4
    top_line = "".join(l.center(col_width) for l in labels)
    slash_line = "".join("\\".center(col_width) if i % 2 == 0 else "/".center(col_width)
                          for i in range(len(labels))) if len(labels) > 1 else "|".center(col_width)

    print()
    print(top_line)
    print(slash_line)
    print("router".center(col_width * max(len(labels), 1)))
    print("|".center(col_width * max(len(labels), 1)))
    host_label = f"Host ({out_iface})" if out_iface else "Host"
    print(f"{host_label}  -- NAT/MASQUERADE --".center(col_width * max(len(labels), 1)))
    print("|".center(col_width * max(len(labels), 1)))
    print("Internet".center(col_width * max(len(labels), 1)))
    print()


def cmd_enable_forwarding(args):
    """sudo sysctl -w net.ipv4.ip_forward=1 (on the HOST, not a namespace)"""
    run(["sudo", "sysctl", "-w", "net.ipv4.ip_forward=1"])
    print("[+] IP forwarding enabled on the host kernel.")


def _masq_cmd(action, subnet, out_iface, backend):
    """Build the masquerade command for iptables or nft."""
    if backend == "nft":
        # Ensure a nat table/chain exists, then add/delete the rule.
        # (Kept simple: uses the legacy-style 'nft add rule' with inet family.)
        if action == "add":
            return ["sudo", "nft", "add", "rule", "ip", "nat", "POSTROUTING",
                     "ip", "saddr", subnet, "oifname", out_iface, "masquerade"]
        else:
            print("[i] For nft, removing a specific rule requires its handle number.")
            print("    Run: sudo nft -a list table ip nat   (to find the handle)")
            print("    Then: sudo nft delete rule ip nat POSTROUTING handle <N>")
            return None
    else:
        flag = "-A" if action == "add" else "-D"
        return ["sudo", "iptables", "-t", "nat", flag, "POSTROUTING",
                "-s", subnet, "-o", out_iface, "-j", "MASQUERADE"]


def cmd_masquerade(args):
    if args.masq_action == "list":
        if args.backend == "nft":
            run(["sudo", "nft", "list", "table", "ip", "nat"], check=False)
        else:
            run(["sudo", "iptables", "-t", "nat", "-L", "POSTROUTING", "-n", "-v"], check=False)
        return

    cmd = _masq_cmd(args.masq_action, args.subnet, args.out_iface, args.backend)
    if cmd is None:
        return
    run(cmd)

    state = load_state()
    state["out_iface"] = args.out_iface
    subnets = set(state.get("subnets", []))
    if args.masq_action == "add":
        subnets.add(args.subnet)
        print(f"[+] MASQUERADE enabled: {args.subnet} -> {args.out_iface}")
    else:
        subnets.discard(args.subnet)
        print(f"[+] MASQUERADE removed: {args.subnet} -> {args.out_iface}")
    state["subnets"] = sorted(subnets)
    save_state(state)
    draw_diagram(state)


def cmd_allow_forward(args):
    """
    Allow the FORWARD chain to pass traffic both ways between the router
    interface and the internet-facing interface. Needed because many
    distros default the FORWARD chain policy to DROP.
    """
    run(["sudo", "iptables", "-A", "FORWARD", "-i", args.in_iface,
         "-o", args.out_iface, "-j", "ACCEPT"])
    run(["sudo", "iptables", "-A", "FORWARD", "-i", args.out_iface,
         "-o", args.in_iface, "-m", "state", "--state", "ESTABLISHED,RELATED",
         "-j", "ACCEPT"])
    print(f"[+] FORWARD chain now allows traffic between '{args.in_iface}' and '{args.out_iface}'")


def cmd_test(args):
    """Ping an external IP from inside a namespace to confirm internet access."""
    run(["sudo", "ip", "netns", "exec", args.namespace,
         "ping", "-c", str(args.count), args.target], check=False)


def cmd_diagram(args):
    draw_diagram(load_state())


def main():
    parser = argparse.ArgumentParser(description="Configure NAT so namespace subnets can reach the internet.")
    sub = parser.add_subparsers(dest="action", required=True)

    p_fwd = sub.add_parser("enable-forwarding", help="Enable IP forwarding on the host kernel")
    p_fwd.set_defaults(func=cmd_enable_forwarding)

    p_masq = sub.add_parser("masquerade", help="Add/remove/list MASQUERADE (NAT) rules")
    masq_sub = p_masq.add_subparsers(dest="masq_action", required=True)

    p_masq_add = masq_sub.add_parser("add", help="Add a MASQUERADE rule for a subnet")
    p_masq_add.add_argument("subnet", help="Private subnet (e.g. 10.0.1.0/24)")
    p_masq_add.add_argument("out_iface", help="Host's internet-facing interface (e.g. eth0)")
    p_masq_add.add_argument("--backend", choices=["iptables", "nft"], default="iptables")
    p_masq_add.set_defaults(func=cmd_masquerade)

    p_masq_del = masq_sub.add_parser("remove", help="Remove a MASQUERADE rule for a subnet")
    p_masq_del.add_argument("subnet", help="Private subnet (e.g. 10.0.1.0/24)")
    p_masq_del.add_argument("out_iface", help="Host's internet-facing interface (e.g. eth0)")
    p_masq_del.add_argument("--backend", choices=["iptables", "nft"], default="iptables")
    p_masq_del.set_defaults(func=cmd_masquerade)

    p_masq_list = masq_sub.add_parser("list", help="List current NAT rules")
    p_masq_list.add_argument("--backend", choices=["iptables", "nft"], default="iptables")
    p_masq_list.set_defaults(func=cmd_masquerade)

    p_allow = sub.add_parser("allow-forward", help="Allow the FORWARD chain between two interfaces")
    p_allow.add_argument("in_iface", help="Interface facing the router (e.g. veth-router)")
    p_allow.add_argument("out_iface", help="Interface facing the internet (e.g. eth0)")
    p_allow.set_defaults(func=cmd_allow_forward)

    p_test = sub.add_parser("test", help="Ping an external target from inside a namespace")
    p_test.add_argument("namespace", help="Namespace to test from (e.g. ns1)")
    p_test.add_argument("target", help="External IP to ping (e.g. 8.8.8.8)")
    p_test.add_argument("-c", "--count", type=int, default=3, help="Number of pings (default: 3)")
    p_test.set_defaults(func=cmd_test)

    p_diagram = sub.add_parser("diagram", help="Redraw the NAT topology diagram from saved state")
    p_diagram.set_defaults(func=cmd_diagram)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()