# Private VM
- Ubuntu Server, **1 NIC only** → `Vpc-private`
- Static IP via netplan:
```yaml
network:
  version: 2
  ethernets:
    enp1s0:
      dhcp4: no
      addresses:
        - 10.0.2.10/24
      routes:
        - to: default
          via: 10.0.2.1
      nameservers:
        addresses: [8.8.8.8, 8.8.4.4]
```

> ⚠️ **Problem encountered:** `ping 10.0.2.1` (its own gateway) failed with `Destination Host Unreachable` — 100% packet loss, even though the netplan config and `Vpc-private` network were correctly set up.
> **Root cause:** `router-vm` (which owns `10.0.2.1`) was **shut off** at the time — nothing on the subnet could answer ARP for that gateway IP.
> **Fix:**
> ```bash
> # on the host
> sudo virsh list --all        # confirmed router-vm: shut off
> sudo virsh start router-vm
> ```
> After starting router-vm, connectivity from private-vm was restored.

**Diagnostic commands used to isolate the issue:**
```bash
sudo virsh list --all                 # check VM power states
sudo virsh domiflist private-vm       # confirm correct network attachment
sudo virsh net-list --all             # confirm Vpc-private is active
ip a show virbr2                      # confirm bridge is up on host
```

**Test results (after fix):**
```bash
ping -c 4 10.0.2.1      # ✅ gateway reachable
ping -c 4 8.8.8.8        # ✅ NAT through router-vm working
ping -c 4 google.com     # ✅ DNS + internet working
```
