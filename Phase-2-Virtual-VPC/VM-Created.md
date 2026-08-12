# Virtual Networks Created

### 3. Virtual Networks

**Vpc-public** — NAT-enabled:
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

**Vpc-private** — fully isolated (no `<ip>` block — only the Router VM owns an address here):
```xml
<network>
  <name>Vpc-private</name>
  <bridge name='virbr-priv' stp='on' delay='0'/>
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

> ⚠️ **Problem encountered:** `Vpc-private` was originally created *with* `<ip address='10.0.2.1' netmask='255.255.255.0'/>` on the bridge. Later, the Router VM's `enp7s0` was also assigned `10.0.2.1` — same address on both the host bridge and the VM, causing a silent IP conflict on the private subnet.
> **Fix:**
> ```bash
> sudo virsh net-destroy Vpc-private
> sudo virsh net-edit Vpc-private
> # deleted the entire <ip>...</ip> block, leaving only name/bridge/mac
> sudo virsh net-start Vpc-private
> sudo virsh net-autostart Vpc-private
> ```
> Now only the Router VM owns `10.0.2.1` — the bridge itself holds no address on the private subnet.
