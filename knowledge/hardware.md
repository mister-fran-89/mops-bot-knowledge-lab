# Host Hardware

| Component | Detail |
|-----------|--------|
| CPU | Intel Core i5-8500T @ 2.10 GHz — 6 cores |
| RAM | 32 GB |
| NVMe (OS) | 238.5 GB Samsung → / (OS + LVM thin pool local-lvm) |
| SSD media | 931.5 GB Crucial CT1000BX500SSD1 → /mnt/media |
| SSD portable | 931.5 GB SanDisk Extreme — Immich external library + personal files (97% full) |
| USB backup | 116.4 GB Toshiba TransMemory — FRAN-BACKUP, ext4, auto-mounted read-only at /mnt/fran-backup |
| Proxmox | VE 9.1.1, kernel 6.17.2-1-pve |

## Local devices
- Mac Mini: 192.168.1.246 — runs Ollama on port 11434 (local LLM backend)
  - Models: qwen2.5:7b-instruct-q4_K_M, qwen2.5:3b, phi4-mini:3.8b, phi3, nomic-embed-text, dolphin-gemma2:2b

## Storage pools
- local: ~82 GB at /var/lib/vz
- local-lvm: ~141 GB LVM thin pool (container rootfs)
- backup-media: 916 GB at /mnt/media/proxmox-backups
- pbs: PBS LXC 205, datastore "main"
