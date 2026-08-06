# Mini Cloud Platform

A practical project to build a miniature cloud platform using Linux Networking, Docker, Terraform, and Ansible.

## Goals

- Learn Linux Networking
- Build a virtual cloud
- Deploy microservices
- Automate infrastructure
- Practice DevOps workflows

## Roadmap

### Phase 0 — Git & GitHub
- Create the repository
- Learn Git basics (add, commit, branch, merge, push)
- Document the project in the README
- Organize files and folders

### Phase 1 — Linux Networking
- Network Namespaces
- Linux Bridges
- veth Pairs
- IP Addressing
- Routing
- NAT
- iptables / nftables
- Test connectivity between networks

**Goal:** Build a complete virtual network inside Linux.

### Phase 2 — Virtual VPC
- Create multiple VMs using KVM/QEMU
- Router VM
- Public Subnet
- Private Subnet
- Bastion Host
- SSH with key-based auth
- Design the network diagram

**Goal:** Simulate a mini VPC.

### Phase 3 — Docker & Microservices
- Docker
- Docker Compose
- Multiple services (Frontend, Backend, Database)
- Volumes
- Networks
- Service Discovery

**Goal:** Run a full application inside the network.

### Phase 4 — Security
- Firewall
- Security Groups (simulated)
- ACLs
- Network isolation
- User and permission management

### Phase 5 — Infrastructure as Code
- Terraform
- Ansible
- Automate server setup
- Recreate the environment with a few commands

### Phase 6 — Monitoring & Logging
- Prometheus
- Grafana
- Node Exporter
- Resource usage monitoring
- Log collection

### Phase 7 — CI/CD
- GitHub Actions
- Automatic Docker image builds
- Automated tests
- Automated service deployment

### Phase 8 — Final Project
Combine everything above to build a **Mini Cloud Platform** resembling a small-scale AWS environment, including:

- VPC
- Public & Private Subnets
- NAT Gateway
- Bastion Host
- Microservices
- Monitoring
- CI/CD
- Infrastructure as Code

## License

This project is open-source for educational purposes.