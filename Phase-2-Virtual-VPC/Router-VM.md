# Router VM Created
- OS: Ubuntu Server
- Specs: 1 vCPU, 1 GB RAM, 8–10 GB disk
- **2 NICs attached:**
  - `enp1s0` → `Vpc-public`
  - `enp7s0` → `Vpc-private`

> ⚠️ **Problem encountered:** the VM was initially created *without* the second NIC (forgot to add it during the "customize before install" step).
> **Fix:** added the missing NIC afterward, while the VM was shut off:
> - virt-manager → open VM → hardware details (ⓘ icon) → **Add Hardware** → Network → set Network source to `Virtual network 'Vpc-private': Isolated` → Finish

Confirmed both interfaces after install (DHCP-assigned at this point):
```bash
ip a
```
| Interface | DHCP IP | Network |
|---|---|---|
| `enp1s0` | `10.0.1.222/24` | Vpc-public |
| `enp7s0` | `10.0.2.208/24` | Vpc-private |

---

# Static IP Configuration (Netplan) — Router VM

**Original (broken) config** — caused an IP conflict with the `Vpc-public` bridge, which also owns `10.0.1.1`:
```yaml
network:
  version: 2
  ethernets:
    enp1s0:
      dhcp4: no
      addresses:
        - 10.0.1.1/24     # ❌ conflicts with libvirt bridge
    enp7s0:
      dhcp4: no
      addresses:
        - 10.0.2.1/24
```

> ⚠️ **Problem #1 — IP conflict:** both the `Vpc-public` bridge (host-owned, automatic NAT gateway) and the Router VM's `enp1s0` were assigned `10.0.1.1`. This broke routing and internet access from the Router VM entirely.

**Final corrected config:**
```yaml
network:
  version: 2
  ethernets:
    enp1s0:
      dhcp4: no
      addresses:
        - 10.0.1.2/24
      routes:
        - to: default
          via: 10.0.1.1
      nameservers:
        addresses: [8.8.8.8, 8.8.4.4]
    enp7s0:
      dhcp4: no
      addresses:
        - 10.0.2.1/24
```

Applied:
```bash
sudo netplan apply
```

> ⚠️ **Problem #2 — netplan file conflict:** after editing and applying, `ip a` still showed the *old* `10.0.1.1/24` address instead of the new `10.0.1.2/24`. Root cause: Ubuntu Server auto-generates `/etc/netplan/50-cloud-init.yaml` via cloud-init on first boot, and edits were made to a different/duplicate netplan file, so the old config kept winning.
> **Fix:**
> ```bash
> ls -la /etc/netplan/
> # identified the actual active file (e.g. 50-cloud-init.yaml)
> sudo nano /etc/netplan/50-cloud-init.yaml   # edited THIS file directly
> sudo netplan apply
> ```
> Also cleaned up a leftover bad manual route from troubleshooting:
> ```bash
> sudo ip route del default via 10.0.1.245 dev enp1s0
> ```

Verified after fix:
```bash
ip a
ip route
```
Result:
enp1s0: inet 10.0.1.2/24
enp7s0: inet 10.0.2.1/24
default via 10.0.1.1 dev enp1s0 proto static

---

# IP Forwarding + NAT (Router VM)

Enabled forwarding:
```bash
sudo sysctl -w net.ipv4.ip_forward=1
echo "net.ipv4.ip_forward=1" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

Added NAT + forwarding rules:
```bash
sudo iptables -t nat -A POSTROUTING -s 10.0.2.0/24 -o enp1s0 -j MASQUERADE
sudo iptables -A FORWARD -i enp7s0 -o enp1s0 -j ACCEPT
sudo iptables -A FORWARD -i enp1s0 -o enp7s0 -m state --state RELATED,ESTABLISHED -j ACCEPT
```

Made rules persistent:
```bash
sudo apt install iptables-persistent -y
sudo netfilter-persistent save
```

> ⚠️ **Minor issue encountered:** `sudo iptables -t FORWARD -L -v -n` failed with `table 'FORWARD' does not exist` — this was a syntax mistake (`FORWARD` is a **chain**, not a table).
> **Fix:** used the correct syntax:
> ```bash
> sudo iptables -L FORWARD -v -n
> ```

Verified (final working state):
```bash
sudo iptables -t nat -L -v -n
# POSTROUTING: MASQUERADE all -- * enp1s0  10.0.2.0/24  0.0.0.0/0

sudo iptables -L FORWARD -v -n
# ACCEPT all -- enp7s0 enp1s0  0.0.0.0/0  0.0.0.0/0
# ACCEPT all -- enp1s0 enp7s0  0.0.0.0/0  0.0.0.0/0  state RELATED,ESTABLISHED
```