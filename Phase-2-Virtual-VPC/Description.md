# Virtual VPC Lab — Networking Project

A hands-on simulation of a cloud VPC (subnets, routing, NAT, isolation) built locally using **KVM/QEMU**, **libvirt**, and **virt-manager** on Debian.

## 🎯 Objective
Recreate core VPC networking concepts — public/private subnets, routing, and NAT — using virtual machines and isolated virtual networks, without relying on any cloud provider.

---

> ⚠️ Note the Router VM's public IP is `10.0.1.2`, **not** `10.0.1.1` — this was changed after a real conflict we hit (see Problem #1 in Full Problem Log).

---

## 🛠️ Tech Stack
- **Hypervisor:** KVM / QEMU (`qemu-system-x86` on Debian 13)
- **Management:** libvirt + virt-manager
- **Guest OS:** Ubuntu Server
- **Host OS:** Debian (user: `theriepper`)

---

## ✅ Steps Completed

# Host Preparation
```bash
sudo apt install qemu-kvm libvirt-daemon-system virt-manager bridge-utils
```
> On Debian 13 (Trixie), `qemu-kvm` resolves to `qemu-system-x86` automatically — this is expected, not an error.

Verify installation and services:
```bash
dpkg -l | grep -E "qemu-kvm|libvirt-daemon-system|virt-manager|bridge-utils"
systemctl status libvirtd --no-pager
```

Allow running `virsh`/`virt-manager` without `sudo`:
```bash
sudo adduser $USER libvirt
sudo adduser $USER kvm
```
(log out/in for group changes to apply)

---

# Environment Cleanup
Removed pre-existing test VMs:
```bash
virsh destroy <vm-name>
virsh undefine <vm-name> --remove-all-storage
```

Removed libvirt's default NAT network (`192.168.122.0/24`):
```bash
sudo virsh net-destroy default
sudo virsh net-undefine default
```

> ⚠️ **Problem encountered:** the `default` network kept reappearing after certain libvirt operations (e.g. after defining new networks or restarting libvirtd).
> **Fix:** re-run the destroy/undefine commands any time it shows up again in `virsh net-list --all`. There's no permanent one-time fix — libvirt can recreate it on daemon restart if the XML template still exists in `/etc/libvirt/qemu/networks/autostart/`. Check that folder if it keeps returning.

---

## 🔜 Remaining Work
- [ ] Confirm Public VM **cannot** directly reach Private VM (isolation test)
- [ ] Permanently prevent `default` libvirt network from reappearing
- [ ] Add `ufw`/`iptables` rules on Public VM and Private VM to simulate **Security Groups**
  - Public VM: allow SSH (22), HTTP (80) only
  - Private VM: allow traffic only from Public VM's IP, deny direct internet inbound
- [ ] Full connectivity test matrix (all combinations)
- [ ] Final documentation and lessons-learned writeup

---

## 📚 Concepts Demonstrated
- VPC-style network segmentation (public/private subnets)
- NAT Gateway simulation via a dedicated Router VM
- IP forwarding and Linux routing
- Network isolation using libvirt isolated networks (no `<ip>` on bridge)
- iptables MASQUERADE and stateful FORWARD rules
- Netplan static IP configuration and cloud-init file conflicts
- Real-world debugging: IP conflicts, VM power-state issues, and syntax errors