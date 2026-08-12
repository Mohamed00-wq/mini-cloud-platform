# 📐 IP & Subnet Plan

| Component | CIDR / IP | Notes |
|---|---|---|
| VPC (overall) | `10.0.0.0/16` | Logical container |
| Public Subnet | `10.0.1.0/24` | NAT-enabled via libvirt |
| Private Subnet | `10.0.2.0/24` | Fully isolated, no libvirt NAT |
| Vpc-public bridge (libvirt) | `10.0.1.1` | Auto NAT gateway, host-owned |
| Router VM — `enp1s0` | `10.0.1.2` | Public-facing interface |
| Router VM — `enp7s0` | `10.0.2.1` | Private-facing interface / gateway |
| Public VM | `10.0.1.10` | Gateway: `10.0.1.1` |
| Private VM | `10.0.2.10` | Gateway: `10.0.2.1` (Router VM only) |
