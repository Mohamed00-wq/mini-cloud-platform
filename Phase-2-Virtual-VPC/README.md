# Virtual VPC Lab — Networking Project

A hands-on simulation of a cloud VPC (subnets, routing, NAT, isolation) built locally using **KVM/QEMU**, **libvirt**, and **virt-manager** on Debian.

## 🎯 Objective
Recreate core VPC networking concepts — public/private subnets, routing, and NAT — using virtual machines and isolated virtual networks, without relying on any cloud provider.

---

## 🧱 Architecture


[ Internet ]
                     │
                     │ (NAT via host)
                     ▼
             ┌───────────────┐
             │   Router VM    │
             │  10.0.1.1      │  ← NIC1 (Vpc-public)
             │  10.0.2.1      │  ← NIC2 (Vpc-private)
             └───────┬───────┘
          ┌──────────┴──────────┐
          │                     │
┌─────────▼─────────┐  ┌────────▼─────────┐
│   Vpc-public        │  │   Vpc-private      │
│   10.0.1.0/24        │  │   10.0.2.0/24        │
│   (NAT enabled)      │  │   (isolated)         │
└─────────┬─────────┘  └────────┬─────────┘
          │                     │
 ┌────────▼────────┐   ┌────────▼────────┐
 │   Public VM       │   │   Private VM      │
 │   10.0.1.10         │   │   10.0.2.10         │
 │   (web server)       │   │   (database)         │
 └───────────────────┘   └───────────────────┘




 ---

## 🛠️ Tech Stack
- **Hypervisor:** KVM / QEMU
- **Management:** libvirt + virt-manager
- **Guest OS:** Ubuntu Server
- **Host OS:** Debian

---

## ✅ Steps Completed

### 1. Host Preparation
Installed required virtualization packages:
```bash
sudo apt install qemu-kvm libvirt-daemon-system virt-manager bridge-utils
```
> Note: on Debian 13 (Trixie), `qemu-kvm` resolves to `qemu-system-x86`.

Verified installation and services:
```bash
dpkg -l | grep -E "qemu-kvm|libvirt-daemon-system|virt-manager|bridge-utils"
systemctl status libvirtd --no-pager
```

Added user to required groups (to run `virsh`/`virt-manager` without `sudo`):
```bash
sudo adduser $USER libvirt
sudo adduser $USER kvm
```

---

### 2. Environment Cleanup
Removed pre-existing test VMs to start from a clean state:
```bash
virsh destroy <vm-name>
virsh undefine <vm-name> --remove-all-storage
```

Removed libvirt's default NAT network (`192.168.122.0/24`):
```bash
sudo virsh net-destroy default
sudo virsh net-undefine default
```

---

### 3. VPC Design (on paper)

| Component | CIDR | Internet Access |
|---|---|---|
| VPC | `10.0.0.0/16` | — |
| Public Subnet | `10.0.1.0/24` | ✅ via NAT |
| Private Subnet | `10.0.2.0/24` | ❌ isolated |

| Device | IP | Role |
|---|---|---|
| Router VM (NIC1) | `10.0.1.1` | Gateway — public side |
| Router VM (NIC2) | `10.0.2.1` | Gateway — private side |
| Public VM | `10.0.1.10` | Web server |
| Private VM | `10.0.2.10` | Database |

---

### 4. Virtual Networks Created

**Vpc-public** — NAT-enabled network:
```xml
<network>
  <name>Vpc-public</name>
  <forward mode='nat'/>
  <bridge name='virbr-pub' stp='on' delay='0'/>
  <ip address='10.0.1.1' netmask='255.255.255.0'>
    <dhcp>
      <range start='10.0.1.100' end='10.0.1.200'/>
    </dhcp>
  </ip>
</network>
```

**Vpc-private** — Isolated network (no forward mode = no internet route):
```xml
<network>
  <name>Vpc-private</name>
  <bridge name='virbr-priv' stp='on' delay='0'/>
  <ip address='10.0.2.1' netmask='255.255.255.0'/>
</network>
```

Defined and started both:
```bash
sudo virsh net-define <file>.xml
sudo virsh net-start <network-name>
sudo virsh net-autostart <network-name>
```

Verified:
```bash
sudo virsh net-list --all
```

---

### 5. Router VM Created
- OS: Ubuntu Server
- Specs: 1 vCPU, 1 GB RAM, 8–10 GB disk
- **2 NICs attached:**
  - NIC1 → `Vpc-public`
  - NIC2 → `Vpc-private`

Confirmed both interfaces after install:
```bash
ip a
```
Result:
| Interface | DHCP IP | Network |
|---|---|---|
| `enp1s0` | `10.0.1.222/24` | Vpc-public |
| `enp7s0` | `10.0.2.208/24` | Vpc-private |

---

### 6. Static IP Configuration (Netplan)
Configured static IPs on the Router VM to match the design:

```yaml
network:
  version: 2
  ethernets:
    enp1s0:
      dhcp4: no
      addresses:
        - 10.0.1.1/24
    enp7s0:
      dhcp4: no
      addresses:
        - 10.0.2.1/24
```

Applied:
```bash
sudo netplan apply
```

Verified:
```bash
ip a
```

---

## 🔜 Next Steps
- [ ] Enable IP forwarding on Router VM
- [ ] Add NAT (MASQUERADE) rule so `Vpc-private` traffic routes out via `Vpc-public`
- [ ] Install and configure Public VM (`10.0.1.10`)
- [ ] Install and configure Private VM (`10.0.2.10`)
- [ ] Set default gateways on Public/Private VMs
- [ ] Add firewall rules (ufw/iptables) — simulate Security Groups
- [ ] Full connectivity test matrix (public↔internet, private↔internet, public↔private)

---

## 📚 Concepts Demonstrated
- Virtual Private Cloud (VPC) segmentation
- Public vs private subnets
- NAT Gateway behavior (via Router VM)
- Network isolation
- Routing between subnets
- (Planned) Security Groups via host-based firewalling