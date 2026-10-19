# Self-Hosting & Production Deployment Guide

Aieval Console is designed for simple, local-first self-hosting with minimal operational overhead.

---

## 1. Quick Docker Compose Deployment

Run the unified monolith with persistent volume storage:

```bash
docker compose up -d
```

Verify service readiness:
```bash
curl http://127.0.0.1:8000/health
```

Expected output:
```json
{"status":"ok","app_version":"0.1.0","aieval_version":"0.2.0"}
```

---

## 2. Persistent Storage & Backups

All state (contracts, versions, runs, and review notes) is stored in a single SQLite database inside the persistent volume at `/app/data/aieval.db`.

### Backing Up the Database
Because SQLite supports atomic online backups, you can create a safe snapshot of the database while the application is actively running:

```bash
docker exec aieval-console sqlite3 /app/data/aieval.db ".backup '/app/data/backup_$(date +%Y%m%d_%H%M%S).db'"
```

### Restoring from Backup
To restore a backup, stop the container, replace `data/aieval.db`, and restart:

```bash
docker compose stop
cp backup_20261019.db data/aieval.db
docker compose start
```

---

## 3. Reverse Proxy Configuration

In production environments, place Aieval Console behind a TLS-terminating reverse proxy.
The console does not provide user authentication. Do not expose it to untrusted networks
unless the reverse proxy (or another trusted network boundary) enforces authentication
for every path, including `/api/`, `/docs`, and `/openapi.json`.

### Caddy (Recommended)
Add the following to your `Caddyfile`:

```caddy
eval.yourcompany.com {
    basic_auth {
        {$EVAL_USERNAME} {$EVAL_PASSWORD_HASH}
    }

    reverse_proxy 127.0.0.1:8000 {
        header_up X-Real-IP {remote_host}
        header_up X-Forwarded-For {remote_host}
        header_up X-Forwarded-Proto {scheme}
    }
}
```

### Nginx
```nginx
server {
    listen 80;
    server_name eval.yourcompany.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name eval.yourcompany.com;

    ssl_certificate /etc/letsencrypt/live/eval.yourcompany.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/eval.yourcompany.com/privkey.pem;

    auth_basic "Aieval Console";
    auth_basic_user_file /etc/nginx/.htpasswd;
    client_max_body_size 1M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 4. Security & Hardening Checklist

1. **Local Network Binding:** Ensure `docker-compose.yml` binds to `127.0.0.1:8000` rather than `0.0.0.0:8000` if no reverse proxy is used.
2. **Payload Protection:** Requests exceeding `MAX_PAYLOAD_BYTES` (default 500 KB) are automatically rejected with `413 Request Entity Too Large`.
3. **No Dynamic Execution:** Contracts cannot invoke shell commands, dynamic imports, or arbitrary Python scripts.
4. **Log Privacy:** Application request logs record timestamps, HTTP status codes, and durations, but omit AI prompt inputs and completion outputs.
5. **Access Control:** Configure authentication at the reverse proxy before exposing the service beyond a trusted local network.
