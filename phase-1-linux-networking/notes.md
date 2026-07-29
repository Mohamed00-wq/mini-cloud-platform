# Phase 1 – Linux Networking: Learning Notes

## What I Learned

### Linux Network Namespaces

* Learned how Linux **Network Namespaces** work and how they provide isolated network environments.
* Understood that each namespace has its own network stack, including interfaces, routing tables, ARP table, and firewall rules.
* Used namespaces to simulate multiple hosts and routers on a single Linux machine.

### IP Addressing

* Learned how to assign IPv4 addresses to network interfaces.
* Understood the purpose of subnet masks and how IP addressing enables communication between network devices.
* Configured network interfaces manually using Linux networking tools.

### Routing

* Learned how packets are forwarded between different networks.
* Understood the role of routing tables and default gateways.
* Configured static routes and observed how Linux makes forwarding decisions.

### Building a Virtual Network

* Built the fundamental components of a virtual network using Linux namespaces.
* Connected isolated namespaces using virtual Ethernet (veth) pairs.
* Simulated a small network topology without requiring multiple physical machines.

### Network Automation with Python

* Learned how to automate Linux networking tasks using Python.
* Used the `subprocess` module to execute Linux networking commands.
* Built command-line tools with `argparse` to simplify repetitive networking operations.
* Gained a better understanding of how automation can improve infrastructure management.

## Key Takeaways

* I now understand how Linux networking works behind the scenes.
* I can manually configure network interfaces, IP addresses, and routing.
* I understand the relationship between namespaces, virtual interfaces, and routing.
* I can automate networking tasks using Python instead of executing every command manually.
* This phase provided the foundation required for more advanced topics such as bridges, NAT, Docker networking, Kubernetes networking, and cloud networking.

## Next Goal

Continue building a complete virtual cloud environment by expanding the networking infrastructure and automating the remaining components.
