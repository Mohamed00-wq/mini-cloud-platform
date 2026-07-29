#!/usr/bin/env python3
"""
router_manager.py - Stage 6 of the mini-cloud platform: Routing between two subnets.

Wraps the commands you used manually:
    sudo ip netns add router
    # eth0 -> subnet1 (10.0.1.0/24), eth1 -> subnet2 (10.0.2.0/24)
    sudo ip netns exec router ip addr add 10.0.1.254/24 dev eth0
    sudo ip netns exec router ip addr add 10.0.2.254/24 dev eth1
    sudo ip netns exec router ip link set eth0 up
    sudo ip netns exec router ip link set eth1 up
    sudo ip netns exec router sysctl -w net.ipv4.ip_forward=1
    # and on each subnet's namespace, a default/route pointing at the router:
    sudo ip netns exec ns1 ip route add 10.0.2.0/24 via 10.0.1.254
    sudo ip netns exec ns2 ip route add 10.0.1.0/24 via 10.0.2.254

Without a router, ns1 (10.0.1.0/24) and ns2 (10.0.2.0/24) are two separate
networks and cannot see each other, even if both are wired into bridges.
The router namespace has one leg in each subnet and forwards packets between
them once IP forwarding is enabled.

This script keeps a small state file (router_topology.json) in the current
directory, so every time you run it, it prints an updated ASCII diagram of
the routed topology in the terminal.

Usage:
    # 1. Create the router namespace
    sudo python3 router_manager.py create-router router

    # 2. Assign an IP to each interface inside the router (also brings it up)
    sudo python3 router_manager.py add-interface router eth0 10.0.1.254/24 --subnet 10.0.1.0/24
    sudo python3 router_manager.py add-interface router eth1 10.0.2.254/24 --subnet 10.0.2.0/24

    # 3. Turn the router into an actual router
    sudo python3 router_manager.py enable-forwarding router

    # 4. Tell each subnet how to reach the other one, via the router
    sudo python3 router_manager.py add-route ns1 10.0.2.0/24 10.0.1.254
    sudo python3 router_manager.py add-route ns2 10.0.1.0/24 10.0.2.254

    # Check routing tables
    python3 router_manager.py show-routes ns1
    python3 router_manager.py show-routes router

    # Test end-to-end connectivity
    sudo python3 router_manager.py ping ns1 10.0.2.1

    # Just redraw the diagram from saved state
    python3 router_manager.py diagram

Note: create-router/add-interface/enable-forwarding/add-route/ping need root
      privileges (run with sudo). The interfaces (eth0, eth1) must already
      exist as veth ends moved into the 'router' namespace - use
      veth_manager.py from Stage 2 to create and attach them first.
"""

import argparse
import json
import os
import subprocess
import sys

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "router_topology.json")


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
    return {"router": None, "interfaces": {}}  # interfaces: {iface: {"ip":.., "subnet":..}}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def draw_diagram(state):
    """Print an ASCII diagram of the router connecting two (or more) subnets."""
    router = state.get("router")
    interfaces = state.get("interfaces", {})

    if not router:
        print("(no router namespace created yet)")
        return
    if not interfaces:
        print(f"(router '{router}' created but has no interfaces yet)")
        return

    columns = []
    for iface, info in interfaces.items():
        subnet = info.get("subnet") or "(subnet unknown)"
        ip = info.get("ip", "")
        columns.append((f"[{subnet}]", f"{iface} ({ip})"))

    col_width = max(max(len(top), len(bottom)) for top, bottom in columns) + 4

    top_line = "".join(top.center(col_width) for top, bottom in columns)
    bar_line = "".join("|".center(col_width) for _ in columns)
    iface_line = "".join(bottom.center(col_width) for top, bottom in columns)

    total_width = col_width * len(columns)
    router_label = f" {router} (router) "
    box_width = max(total_width, len(router_label) + 4)
    border = "+" + "-" * (box_width - 2) + "+"
    router_line = "|" + router_label.center(box_width - 2) + "|"

    print()
    print(top_line)
    print(bar_line)
    print(iface_line)
    print(bar_line)
    print(border)
    print(router_line)
    print(border)
    print()


def cmd_create_router(args):
    """sudo ip netns add <router>"""
    run(["sudo", "ip", "netns", "add", args.router])
    state = load_state()
    state["router"] = args.router
    state.setdefault("interfaces", {})
    save_state(state)
    print(f"[+] Router namespace '{args.router}' created.")
    draw_diagram(state)


def cmd_add_interface(args):
    """
    Assign an IP to an interface inside the router namespace and bring it up.
    Assumes the interface already exists inside that namespace (e.g. the
    router-side end of a veth pair created with veth_manager.py).
    """
    run(["sudo", "ip", "netns", "exec", args.router,
         "ip", "addr", "add", args.ip, "dev", args.iface])
    run(["sudo", "ip", "netns", "exec", args.router,
         "ip", "link", "set", args.iface, "up"])

    state = load_state()
    state["router"] = args.router
    state.setdefault("interfaces", {})
    state["interfaces"][args.iface] = {"ip": args.ip, "subnet": args.subnet}
    save_state(state)

    print(f"[+] '{args.iface}' in '{args.router}' set to {args.ip}"
          + (f" (subnet: {args.subnet})" if args.subnet else ""))
    draw_diagram(state)


def cmd_enable_forwarding(args):
    """sudo ip netns exec <router> sysctl -w net.ipv4.ip_forward=1"""
    run(["sudo", "ip", "netns", "exec", args.router,
         "sysctl", "-w", "net.ipv4.ip_forward=1"])
    print(f"[+] IP forwarding enabled inside '{args.router}'. It is now an actual router.")


def cmd_add_route(args):
    """sudo ip netns exec <namespace> ip route add <destination> via <gateway>"""
    cmd = ["sudo", "ip", "netns", "exec", args.namespace,
           "ip", "route", "add", args.destination, "via", args.gateway]
    if args.dev:
        cmd += ["dev", args.dev]
    run(cmd)
    print(f"[+] Route added in '{args.namespace}': {args.destination} via {args.gateway}")


def cmd_show_routes(args):
    """Show the routing table inside a namespace."""
    run(["sudo", "ip", "netns", "exec", args.namespace, "ip", "route", "show"], check=False)


def cmd_ping(args):
    """Ping a target IP from inside a namespace, to test end-to-end routing."""
    run(["sudo", "ip", "netns", "exec", args.namespace,
         "ping", "-c", str(args.count), args.target], check=False)


def cmd_diagram(args):
    draw_diagram(load_state())


def main():
    parser = argparse.ArgumentParser(description="Manage a router namespace connecting two or more subnets.")
    sub = parser.add_subparsers(dest="action", required=True)

    p_create = sub.add_parser("create-router", help="Create the router namespace")
    p_create.add_argument("router", nargs="?", default="router", help="Router namespace name (default: router)")
    p_create.set_defaults(func=cmd_create_router)

    p_add_if = sub.add_parser("add-interface", help="Assign an IP to an interface inside the router and bring it up")
    p_add_if.add_argument("router", help="Router namespace name (e.g. router)")
    p_add_if.add_argument("iface", help="Interface name inside the router (e.g. eth0)")
    p_add_if.add_argument("ip", help="IP address with CIDR (e.g. 10.0.1.254/24)")
    p_add_if.add_argument("--subnet", help="Subnet this interface belongs to, for the diagram (e.g. 10.0.1.0/24)")
    p_add_if.set_defaults(func=cmd_add_interface)

    p_fwd = sub.add_parser("enable-forwarding", help="Enable IP forwarding inside the router namespace")
    p_fwd.add_argument("router", help="Router namespace name (e.g. router)")
    p_fwd.set_defaults(func=cmd_enable_forwarding)

    p_route = sub.add_parser("add-route", help="Add a route inside a namespace pointing at the router")
    p_route.add_argument("namespace", help="Namespace to add the route in (e.g. ns1)")
    p_route.add_argument("destination", help="Destination subnet (e.g. 10.0.2.0/24)")
    p_route.add_argument("gateway", help="Gateway IP to reach it through (e.g. 10.0.1.254)")
    p_route.add_argument("--dev", help="Optional outgoing interface (e.g. veth1)")
    p_route.set_defaults(func=cmd_add_route)

    p_show = sub.add_parser("show-routes", help="Show the routing table inside a namespace")
    p_show.add_argument("namespace", help="Namespace name (e.g. ns1, router)")
    p_show.set_defaults(func=cmd_show_routes)

    p_ping = sub.add_parser("ping", help="Ping a target from inside a namespace")
    p_ping.add_argument("namespace", help="Namespace to ping from (e.g. ns1)")
    p_ping.add_argument("target", help="Target IP to ping (e.g. 10.0.2.1)")
    p_ping.add_argument("-c", "--count", type=int, default=3, help="Number of pings (default: 3)")
    p_ping.set_defaults(func=cmd_ping)

    p_diagram = sub.add_parser("diagram", help="Redraw the routing diagram from saved state")
    p_diagram.set_defaults(func=cmd_diagram)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()