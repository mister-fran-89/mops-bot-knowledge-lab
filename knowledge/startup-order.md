# Container Startup Order

Containers start in this sequence on boot:

1. AdGuard 203 (`order=1,up=15`)
2. NPM 202 (`order=2,up=15`) · Uptime Kuma 204 (`order=2,up=15`) · PBS 205 (`order=2,up=15`)
3. iptv-vpn-proxy 104 (`order=3,up=25`) · qbit-vpn 105 (`order=3,up=25`)
4. jellyfin 103 (`order=4,up=20`) · searxng 110 (`order=4,up=20`) · open-brain 111 (`order=4,up=20`) · invidious 112 (`order=4,up=20`)
5. open-webui 107 (`order=5,up=15`) · arr-stack 106 (`order=5,up=15`)
6. n8n 109 (`order=6,up=10`)
7. monitoring 200 (`order=7,up=10`)
8. dashboard 201 (`order=8,up=0`)

## Why AdGuard starts first

All containers use AdGuard (192.168.1.101) as their DNS resolver, set via `nameserver:` in each container's `.conf`. If AdGuard is not up when other containers start, DNS resolution fails and services cannot reach the internet or each other by hostname. AdGuard itself uses 1.1.1.1 as upstream.

NPM (reverse proxy) starts second because it needs DNS to resolve upstream proxy targets. All other services depend on both DNS and the reverse proxy being available.
