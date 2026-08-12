# 🐛 Full Problem Log

| # | Problem | Root Cause | Fix |
|---|---|---|---|
| 1 | Router VM lost internet access after netplan change | `enp1s0` and `Vpc-public` bridge both assigned `10.0.1.1` | Changed Router VM's `enp1s0` to `10.0.1.2` |
| 2 | Private subnet had a second silent IP conflict | `Vpc-private` bridge and Router VM's `enp7s0` both owned `10.0.2.1` | Removed `<ip>` block from `Vpc-private` network XML entirely |
| 3 | Static IP edit didn't apply after `netplan apply` | Duplicate/incorrect netplan file edited instead of the active `50-cloud-init.yaml` | Identified and edited the correct file directly |
| 4 | Leftover bad default route | Manual troubleshooting route (`via 10.0.1.245`) never removed | `sudo ip route del default via 10.0.1.245 dev enp1s0` |
| 5 | `iptables -t FORWARD -L` failed | Wrong syntax — `FORWARD` is a chain, not a table | Used `sudo iptables -L FORWARD -v -n` |
| 6 | Router VM created without second NIC | Missed "Customize before install" NIC step | Added second NIC afterward via virt-manager hardware details |
| 7 | `default` libvirt network kept reappearing | Autostart template still present in libvirt config | Re-ran `net-destroy` / `net-undefine` as needed |
| 8 | Private VM couldn't reach its own gateway (`10.0.2.1`) | `router-vm` was shut off | Started `router-vm` via `sudo virsh start router-vm` |
| 9 | `nc -zv` test from Private VM to itself gave false result | Test was run from Private VM against itself instead of from Public/Router VM | Always test connectivity *from the source* to the *target*, never from a host to itself |
| 10 | `nc` from Router VM showed "connection refused" on port 22 | `openssh-server` was never installed on Private VM — nothing was listening | Installed and started `openssh-server` on Private VM |
| 11 | Private VM lost internet access again (100% packet loss to `8.8.8.8`, DNS failed) | `net.ipv4.ip_forward` had reset to `0` on Router VM (not persisted correctly) | Re-set `net.ipv4.ip_forward=1`, confirmed it's saved in `/etc/sysctl.conf`, ran `sudo sysctl -p` |

## ✅ Connectivity Test Matrix (Final)

| From | To | Expected | Status |
|---|---|---|---|
| Router VM | `10.0.2.1` (self) | ✅ Success | Confirmed |
| Router VM | `8.8.8.8` / `google.com` | ✅ Success | Confirmed |
| Public VM | `10.0.1.1` (gateway) | ✅ Success | Confirmed |
| Public VM | `8.8.8.8` / `google.com` | ✅ Success | Confirmed |
| Private VM | `10.0.2.1` (gateway) | ✅ Success | Confirmed |
| Private VM | `8.8.8.8` / `google.com` (via NAT) | ✅ Success | Confirmed (after fixing ip_forward) |
| Router VM | Private VM port 22 (allowed) | ✅ Success | Confirmed |
| Public VM | Private VM port 22 (blocked) | ❌ Blocked (expected) | Confirmed |
| Public VM | Private VM `10.0.2.10` (isolation) | ❌ Blocked (expected) | Pending final confirmation |
