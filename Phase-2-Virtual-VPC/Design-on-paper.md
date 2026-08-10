# VPC Design (on paper)

| Component | CIDR | Internet Access |
|---|---|---|
| VPC | `10.0.0.0/16` | — |
| Public Subnet | `10.0.1.0/24` | ✅ via NAT |
| Private Subnet | `10.0.2.0/24` | ❌ isolated |

| Device | IP | Role |
|---|---|---|
| Vpc-public bridge (libvirt) | `10.0.1.1` | Host-owned NAT gateway |
| Router VM — `enp1s0` | `10.0.1.2` | Public-facing NIC |
| Router VM — `enp7s0` | `10.0.2.1` | Private-facing NIC / gateway |
| Public VM | `10.0.1.10` | Web server |
| Private VM | `10.0.2.10` | Database |

> Design originally planned Router VM at `10.0.1.1` / `10.0.2.1` on both NICs — revised after Problem #1 below.
