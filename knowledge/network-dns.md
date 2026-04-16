# Network and DNS

- All containers on flat network vmbr0, 192.168.1.0/24. No VLANs.
- All containers use AdGuard (192.168.1.101) as DNS resolver.
- AdGuard upstream: 1.1.1.1
- External access domain: franlab.uk (LAN only — no public DNS, no port forwarding)
- All *.franlab.uk subdomains proxied via NPM (192.168.1.102:80/443)
- NPM ACL: allows 192.168.1.0/24 only (defence-in-depth)
- Remote access: Tailscale on host, node "fran" at 100.122.153.112
- Double NAT: GL.iNet Opal router behind ISP modem — no internet-facing exposure

## Key DNS rule
nameserver: 192.168.1.101 must be set in every container .conf for DNS to work.
