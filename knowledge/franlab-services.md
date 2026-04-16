# FranLab Home Server Services

All services are on the local network at `192.168.1.x` and accessible via `*.franlab.uk` subdomains (LAN only via AdGuard DNS + Tailscale for remote access).

## Infrastructure

| Service | URL | LAN IP | Purpose |
|---------|-----|--------|---------|
| Proxmox | https://proxmox.franlab.uk | 192.168.1.150:8006 | Hypervisor / host management |
| NPM | https://npm.franlab.uk | 192.168.1.102:81 | Nginx Proxy Manager — reverse proxy for all services |
| AdGuard | https://adguard.franlab.uk | 192.168.1.101:80 | DNS + ad blocking |
| PBS | https://pbs.franlab.uk | 192.168.1.154:8007 | Proxmox Backup Server — daily container backups |
| Uptime Kuma | https://uptime.franlab.uk | 192.168.1.153:3001 | Service uptime monitoring |
| Netdata | https://netdata.franlab.uk | 192.168.1.151:19999 | Host + container metrics |
| Glances | https://glances.franlab.uk | 192.168.1.150:61208 | System resource overview |
| Router | https://router.franlab.uk | 192.168.1.1 | GL.iNet Opal router admin |
| Dashboard | http://192.168.1.152:3000 | 192.168.1.152:3000 | Homepage dashboard |

## Media

| Service | URL | LAN IP | Purpose |
|---------|-----|--------|---------|
| Jellyfin | https://jellyfin.franlab.uk | 192.168.1.50:8096 | Media server — movies, TV, music |
| Jellyseerr | https://jellyseerr.franlab.uk | 192.168.1.53:5055 | Media request management |
| IPTV | https://iptv.franlab.uk | 192.168.1.51:8898 | IPTV proxy (via VPN) |
| Immich | https://immich.franlab.uk | 192.168.1.60:2283 | Photo library / Google Photos alternative |
| Invidious | https://invidious.franlab.uk | 192.168.1.59:3000 | Privacy-friendly YouTube frontend |
| Materialious | https://materialious.franlab.uk | 192.168.1.59:3001 | Alternative Invidious UI |

## AI

| Service | URL | LAN IP | Purpose |
|---------|-----|--------|---------|
| Open WebUI | https://openwebui.franlab.uk | 192.168.1.54:3000 | Chat UI — connects to Ollama on Mac Mini |
| Open Brain | https://openbrain.franlab.uk | 192.168.1.55:8010 | RAG knowledge base / personal AI assistant |
| Agno | http://192.168.1.61:3000 | 192.168.1.61:3000 | Agno agent UI (this service) |

## ARR Stack (Media Automation)

| Service | URL | LAN IP | Purpose |
|---------|-----|--------|---------|
| Sonarr | https://sonarr.franlab.uk | 192.168.1.53:8989 | TV show automation |
| Radarr | https://radarr.franlab.uk | 192.168.1.53:7878 | Movie automation |
| Prowlarr | https://prowlarr.franlab.uk | 192.168.1.53:9696 | Indexer management |
| Bazarr | https://bazarr.franlab.uk | 192.168.1.53:6767 | Subtitle management |
| qBittorrent | https://qbit.franlab.uk | 192.168.1.52:8080 | Torrent client (via VPN) |

## Automation

| Service | URL | LAN IP | Purpose |
|---------|-----|--------|---------|
| n8n | https://n8n.franlab.uk | 192.168.1.56:5678 | Workflow automation |
| SearXNG | https://searxng.franlab.uk | 192.168.1.57:8080 | Private meta search engine |

## LLM Models (Ollama on Mac Mini — 192.168.1.246:11434)

- `qwen2.5:7b-instruct-q4_K_M` — main chat model (4 GB)
- `qwen2.5:3b-instruct-q4_K_M` — lightweight chat (1 GB)
- `phi4-mini:3.8b` — fast reasoning (2 GB)
- `phi3:latest` — general (2 GB)
- `nomic-embed-text:latest` — embeddings (~274 MB)
- `CognitiveComputations/dolphin-gemma2:2b` — uncensored (1 GB)
