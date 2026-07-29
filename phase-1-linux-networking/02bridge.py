#!/usr/bin/env python3
"""
bridge_manager.py - Stage 5 of the mini-cloud platform: Linux Bridge (virtual switch).

Wraps the commands you used manually:
    sudo ip link add br0 type bridge
    sudo ip link set br0 up
    sudo ip link set <veth-end> master br0   (attach a veth end to the bridge)

Instead of a direct cable (veth <-> veth) between two namespaces, every namespace
now connects to a shared bridge (a virtual switch), so any number of namespaces
can talk to each other through it.

This script also keeps a small state file (bridge_topology.json) in the current
directory, so that every time you run it, it prints an updated ASCII diagram
of the current topology in the terminal - no need to ask for it separately.

Usage:
    # Create the bridge and bring it up
    sudo python3 02bridge.py create br0
    sudo python3 02bridge.py up br0

    # Attach an interface to the bridge (mention which namespace it belongs
    # to with --namespace so the diagram is meaningful; it's optional)
    sudo python3 02bridge.py attach veth1-br br0 --namespace ns1
    sudo python3 02bridge.py attach veth2-br br0 --namespace ns2

    # Detach an interface from the bridge
    sudo python3 02bridge.py detach veth1-br

    # Show raw bridge info from the kernel
    python3 02bridge.py show br0

    # Just (re)draw the diagram from the last known state
    python3 02bridge.py diagram

Note: create/up/attach/detach need root privileges (run with sudo).
"""

import argparse
import json
import os
import subprocess
import sys

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bridge_topology.json")


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
    return {"bridge": None, "links": {}}  # links: {iface: namespace_or_null}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def draw_diagram(state):
    """Print an ASCII diagram of the current bridge topology."""
    bridge = state.get("bridge")
    links = state.get("links", {})

    if not bridge:
        print("(no bridge created yet)")
        return
    if not links:
        print(f"(bridge '{bridge}' created but nothing attached yet)")
        return

    columns = []
    for iface, ns in links.items():
        top_label = ns if ns else "(host)"
        columns.append((top_label, iface))

    col_width = max(max(len(top), len(iface)) for top, iface in columns) + 4

    top_line = "".join(top.center(col_width) for top, iface in columns)
    bar_line = "".join("|".center(col_width) for _ in columns)
    iface_line = "".join(iface.center(col_width) for top, iface in columns)

    total_width = col_width * len(columns)
    bridge_label = f" {bridge} (bridge) "
    box_width = max(total_width, len(bridge_label) + 4)
    border = "+" + "-" * (box_width - 2) + "+"
    bridge_line = "|" + bridge_label.center(box_width - 2) + "|"

    print()
    print(top_line)
    print(bar_line)
    print(iface_line)
    print(bar_line)
    print(border)
    print(bridge_line)
    print(border)
    print()


def cmd_create(args):
    """sudo ip link add <bridge> type bridge"""
    run(["sudo", "ip", "link", "add", args.bridge, "type", "bridge"])
    state = load_state()
    state["bridge"] = args.bridge
    state.setdefault("links", {})
    save_state(state)
    print(f"[+] Bridge '{args.bridge}' created.")
    draw_diagram(state)


def cmd_up(args):
    """sudo ip link set <bridge> up"""
    run(["sudo", "ip", "link", "set", args.bridge, "up"])
    print(f"[+] Bridge '{args.bridge}' is up.")
    draw_diagram(load_state())


def cmd_attach(args):
    """sudo ip link set <iface> master <bridge>"""
    run(["sudo", "ip", "link", "set", args.iface, "master", args.bridge])
    run(["sudo", "ip", "link", "set", args.iface, "up"], check=False)
    state = load_state()
    state["bridge"] = args.bridge
    state.setdefault("links", {})
    state["links"][args.iface] = args.namespace
    save_state(state)
    print(f"[+] '{args.iface}' attached to bridge '{args.bridge}'"
          + (f" (namespace: {args.namespace})" if args.namespace else ""))
    draw_diagram(state)


def cmd_detach(args):
    """sudo ip link set <iface> nomaster"""
    run(["sudo", "ip", "link", "set", args.iface, "nomaster"])
    state = load_state()
    state.get("links", {}).pop(args.iface, None)
    save_state(state)
    print(f"[+] '{args.iface}' detached from the bridge.")
    draw_diagram(state)


def cmd_show(args):
    """Show kernel-level bridge info."""
    run(["bridge", "link", "show"], check=False)
    print()
    run(["ip", "-d", "link", "show", args.bridge], check=False)


def cmd_diagram(args):
    """Just redraw the diagram from the saved state."""
    draw_diagram(load_state())


def main():
    parser = argparse.ArgumentParser(description="Manage a Linux bridge (virtual switch) for namespaces.")
    sub = parser.add_subparsers(dest="action", required=True)

    p_create = sub.add_parser("create", help="Create a bridge")
    p_create.add_argument("bridge", help="Bridge name (e.g. br0)")
    p_create.set_defaults(func=cmd_create)

    p_up = sub.add_parser("up", help="Bring a bridge up")
    p_up.add_argument("bridge", help="Bridge name (e.g. br0)")
    p_up.set_defaults(func=cmd_up)

    p_attach = sub.add_parser("attach", help="Attach an interface to a bridge")
    p_attach.add_argument("iface", help="Interface name (e.g. veth1-br)")
    p_attach.add_argument("bridge", help="Bridge name (e.g. br0)")
    p_attach.add_argument("--namespace", help="Namespace this interface leads to, for the diagram (e.g. ns1)")
    p_attach.set_defaults(func=cmd_attach)

    p_detach = sub.add_parser("detach", help="Detach an interface from its bridge")
    p_detach.add_argument("iface", help="Interface name (e.g. veth1-br)")
    p_detach.set_defaults(func=cmd_detach)

    p_show = sub.add_parser("show", help="Show kernel-level info about the bridge")
    p_show.add_argument("bridge", help="Bridge name (e.g. br0)")
    p_show.set_defaults(func=cmd_show)

    p_diagram = sub.add_parser("diagram", help="Redraw the topology diagram from saved state")
    p_diagram.set_defaults(func=cmd_diagram)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()