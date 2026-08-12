# Public VM

- Ubuntu Server, **1 NIC only** → `Vpc-public`
- Static IP via netplan (edited the existing cloud-init file directly, avoiding the netplan conflict from Router VM):
```yaml
network:
  version: 2
  ethernets:
    enp1s0:
      dhcp4: no
      addresses:
        - 10.0.1.10/24
      routes:
        - to: default
          via: 10.0.1.1
      nameservers:
        addresses: [8.8.8.8, 8.8.4.4]
```

**Test results:**
```bash
ping -c 4 10.0.1.1     # ✅ 0% packet loss
ping -c 4 8.8.8.8       # ✅ 0% packet loss
ping -c 4 google.com    # ✅ 0% packet loss, DNS resolved
```

### 9. Firewall Rules (Security Groups Equivalent) — Public VM

Allow only SSH and HTTP inbound:
```bash
sudo apt install ufw -y
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw enable
sudo ufw status verbose
```
