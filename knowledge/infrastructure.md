# FranLab Infrastructure — Container List

Proxmox host: 192.168.1.150 (node: fran). All containers on vmbr0 bridge, gateway 192.168.1.1.

| CTID | Name | IP | Ports | Purpose |
|------|------|----|-------|---------|
| 103 | jellyfin | 192.168.1.50 | 8096 | Media server |
| 104 | iptv-vpn-proxy | 192.168.1.51 | 8898 | IPTV proxy via VPN |
| 105 | qbit-vpn | 192.168.1.52 | 8080 | qBittorrent via VPN |
| 106 | arr-stack | 192.168.1.53 | 8989/7878/9696/6767/5055 | Sonarr/Radarr/Prowlarr/Bazarr/Jellyseerr |
| 107 | open-webui | 192.168.1.54 | 3000 | Chat UI for local LLMs |
| 109 | n8n | 192.168.1.56 | 5678 | Workflow automation |
| 110 | searxng | 192.168.1.57 | 8080 | Private search engine |
| 111 | open-brain | 192.168.1.55 | 8010 | RAG knowledge base |
| 112 | invidious | 192.168.1.59 | 3000/3001 | YouTube frontend |
| 113 | immich | 192.168.1.60 | 2283 | Photo library |
| 114 | agno | 192.168.1.61 | 3000/7777 | AI agent UI |
| 200 | monitoring | 192.168.1.151 | 19999/61208 | Netdata + Glances |
| 201 | dashboard | 192.168.1.152 | 3000 | Homepage dashboard |
| 202 | npm | 192.168.1.102 | 80/443/81 | Nginx Proxy Manager |
| 203 | adguard | 192.168.1.101 | 53/80 | DNS + ad blocking |
| 204 | uptime-kuma | 192.168.1.153 | 3001 | Uptime monitoring |
| 205 | pbs | 192.168.1.154 | 8007 | Proxmox Backup Server |

Resource totals: 28 vCPU / 26.25 GB RAM allocated. All containers onboot=1.
