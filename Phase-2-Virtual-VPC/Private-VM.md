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

Install SSH (needed for management + Security Group testing):
```bash
sudo apt update
sudo apt install openssh-server -y
sudo systemctl enable ssh
sudo systemctl start ssh
sudo systemctl status ssh
sudo ss -tlnp | grep :22
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

**Test results (after fix):**
```bash
ping -c 4 10.0.2.1      # ✅ gateway reachable
ping -c 4 8.8.8.8        # ✅ NAT through router-vm working
ping -c 4 google.com     # ✅ DNS + internet working
```

### 9. Firewall Rules (Security Groups Equivalent) — Private VM

Allow DB port only from Public VM, SSH only from Router VM:
```bash
sudo apt install ufw -y
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow from 10.0.1.10 to any port 3306 proto tcp
sudo ufw allow from 10.0.2.1 to any port 22 proto tcp
sudo ufw enable
sudo ufw status verbose
```

**Test from Router VM (should succeed):**
```bash
nc -zv 10.0.2.10 22
```

**Test from Public VM (should be blocked/timeout):**
```bash
nc -zv -w 3 10.0.2.10 22
```

**Confirm Private VM still has outbound internet (only inbound is restricted):**
```bash
ping -c 4 8.8.8.8
```
