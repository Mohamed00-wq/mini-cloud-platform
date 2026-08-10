# 🐛 Full Problem Log (Summary)

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
