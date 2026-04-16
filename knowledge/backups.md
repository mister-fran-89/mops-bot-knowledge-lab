# Backup Strategy

## Layer 1 — PBS (daily container backups)
- Schedule: daily vzdump at 03:00, snapshot mode, zstd compression
- Retention: keep-last=3 per container
- Covers: LXC 103,104,105,106,107,109,110,111,112,113,200,201,202,203,204
- Excludes: LXC 205 (PBS itself — circular)
- Storage: PBS LXC 205 at 192.168.1.154:8007, datastore "main", bind-mounted from /mnt/media/pbs-datastore
- GC: daily at 01:00 UTC

## Layer 2 — FRAN-BACKUP USB (daily)
- Drive: Toshiba 116 GB USB at /mnt/fran-backup (ext4, auto-mounted read-only)
- Schedule: daily at 04:00 via root crontab
- Script: /usr/local/bin/fran-backup.sh
- Backs up: PBS datastore chunks, Immich postgres dump, Open Brain vault, host configs, host scripts
- Monitoring: push heartbeat to Uptime Kuma monitor ID 24
- Recovery guide: /mnt/fran-backup/README.md

## Warning
PBS datastore, host config backups, and /mnt/media are all on the same physical disk (sda). Single disk failure loses all three. Mitigated by daily rsync to FRAN-BACKUP USB.
