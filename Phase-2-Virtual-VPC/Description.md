# 🌐 Virtual VPC Lab — On-Prem Networking Simulation

A fully virtualized simulation of a cloud **VPC (Virtual Private Cloud)** — built entirely on-premises using **KVM/QEMU**, **libvirt**, and **virt-manager**, without any cloud provider. This project recreates core cloud networking concepts: subnetting, routing, NAT, network isolation, and security groups, using real Linux networking tools.

> ⚠️ Note the Router VM's public IP is `10.0.1.2`, **not** `10.0.1.1` — this was changed after a real conflict we hit (see Problem #1 in the Full Problem Log).

## 🎯 Project Goal

Simulate an AWS-style VPC architecture locally to learn:

- Public vs private subnet design
- NAT Gateway behavior
- Inter-subnet routing via a dedicated router
- Network isolation and traffic control
- Security Group simulation via host-based firewalls (ufw)
- Real-world debugging of virtualized networking

## 🛠️ Tech Stack

| Layer | Tool |
|---|---|
| Hypervisor | KVM / QEMU (`qemu-system-x86` on Debian 13) |
| VM Management | libvirt + virt-manager |
| Guest OS | Ubuntu Server |
| Host OS | Debian (user: `theriepper`) |
| Networking | netplan, iptables, IP forwarding |
| Firewalling | ufw (Security Groups equivalent) |

## ✅ Setup Steps

### 1. Host Preparation (Debian)

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

### 2. Environment Cleanup

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

## 📚 Concepts Demonstrated

- VPC-style network segmentation (public/private subnets)
- NAT Gateway simulation via a dedicated Router VM
- IP forwarding and Linux routing
- Network isolation using libvirt isolated networks (no `<ip>` on bridge)
- iptables MASQUERADE and stateful FORWARD rules
- Netplan static IP configuration and cloud-init file conflicts
- Security Groups simulated via `ufw` source-IP restrictions
- Real-world debugging: IP conflicts, VM power-state issues, syntax errors, and forwarding resets

## 🔜 Remaining Work

- [ ] Final confirmation: Public VM cannot reach Private VM directly (`10.0.2.10`)
- [ ] Permanently prevent `default` libvirt network from reappearing
- [ ] Full end-to-end connectivity test matrix re-run after all fixes
- [ ] Document final lessons learned

## 🖥️ Host Environment

- **Host OS:** Debian
- **Username:** `theriepper`
- **Virtualization:** KVM/QEMU + libvirt + virt-manager
- **Guest OS (all VMs):** Ubuntu Server
