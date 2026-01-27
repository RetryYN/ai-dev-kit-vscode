## 5. OS設定（Linux）

### システムチューニング

```bash
# /etc/sysctl.conf

# ネットワーク
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_keepalive_time = 300
net.ipv4.ip_local_port_range = 1024 65535

# ファイル
fs.file-max = 2097152
fs.inotify.max_user_watches = 524288

# メモリ
vm.swappiness = 10
vm.overcommit_memory = 1
```

### ファイルディスクリプタ

```bash
# /etc/security/limits.conf
* soft nofile 65535
* hard nofile 65535
* soft nproc 65535
* hard nproc 65535
```

### ファイアウォール（UFW）

```bash
# SSH
ufw allow 22/tcp

# HTTP/HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# 有効化
ufw enable
```

---

## 6. モニタリング

### ヘルスチェック

```typescript
// /health エンドポイント
app.get('/health', async (req, res) => {
  const health = {
    status: 'ok',
    timestamp: new Date().toISOString(),
    checks: {
      database: await checkDb(),
      redis: await checkRedis(),
      memory: process.memoryUsage(),
    }
  }
  res.json(health)
})

async function checkDb(): Promise<string> {
  try {
    await prisma.$queryRaw`SELECT 1`
    return 'ok'
  } catch {
    return 'error'
  }
}
```

### メトリクス収集

```yaml
# docker-compose.yml に追加
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
    volumes:
      - grafana_data:/var/lib/grafana
```

### ログ集約

```yaml
# Fluentd/Loki
  loki:
    image: grafana/loki
    ports:
      - "3100:3100"
    
  promtail:
    image: grafana/promtail
    volumes:
      - /var/log:/var/log
      - ./promtail-config.yml:/etc/promtail/config.yml
```

---

## 7. デプロイ

### CI/CD（GitHub Actions）

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Build and push Docker image
        run: |
          docker build -t myapp:${{ github.sha }} .
          docker push myregistry/myapp:${{ github.sha }}
      
      - name: Deploy to server
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.HOST }}
          username: ${{ secrets.USERNAME }}
          key: ${{ secrets.SSH_KEY }}
          script: |
            cd /app
            docker-compose pull
            docker-compose up -d
```

### ゼロダウンタイムデプロイ

```yaml
# docker-compose.yml
services:
  app:
    deploy:
      replicas: 2
      update_config:
        parallelism: 1
        delay: 10s
        order: start-first
      rollback_config:
        parallelism: 1
        delay: 10s
```

---

