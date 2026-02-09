# Deployment Guide

## Production Deployment

This guide covers deploying the Focus ST Telemetry system to production.

## Prerequisites

- Linux server (Ubuntu 20.04+ or similar)
- Python 3.12+
- Nginx (for reverse proxy)
- Domain name (optional but recommended)
- SSL certificate (Let's Encrypt recommended)

## Deployment Steps

### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.12 python3-pip python3-venv nginx

# Create application user
sudo useradd -m -s /bin/bash focusst
sudo su - focusst
```

### 2. Application Setup

```bash
# Clone repository
git clone https://github.com/SaltProphet/ST.git
cd ST

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env  # Edit configuration
```

### 3. Configuration

Edit `.env` with production settings:

```env
HOST=127.0.0.1
PORT=8000
DEBUG=false

# Generate a secure secret key
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# Database
DATABASE_URL=sqlite:///./telemetry.db

# Telemetry
ROLLING_BUFFER_SECONDS=600
SAMPLE_RATE_HZ=10

# Enable features as needed
ENABLE_EMAIL_ALERTS=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ALERT_EMAIL_TO=alerts@example.com

ENABLE_CLOUD_SYNC=false

# OBD Configuration
SIMULATION_MODE=true  # Set to false for real hardware
```

### 4. Create Systemd Service

Create `/etc/systemd/system/focusst-telemetry.service`:

```ini
[Unit]
Description=Focus ST Telemetry Service
After=network.target

[Service]
Type=simple
User=focusst
WorkingDirectory=/home/focusst/ST
Environment="PATH=/home/focusst/ST/venv/bin"
ExecStart=/home/focusst/ST/venv/bin/python /home/focusst/ST/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable focusst-telemetry
sudo systemctl start focusst-telemetry
sudo systemctl status focusst-telemetry
```

### 5. Nginx Configuration

Create `/etc/nginx/sites-available/focusst`:

```nginx
upstream focusst_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name telemetry.yourdomain.com;

    client_max_body_size 20M;

    location / {
        proxy_pass http://focusst_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support
    location /ws/ {
        proxy_pass http://focusst_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/focusst /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 6. SSL Configuration (Let's Encrypt)

```bash
# Install certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d telemetry.yourdomain.com

# Auto-renewal is configured automatically
```

### 7. Firewall Configuration

```bash
# Allow HTTP, HTTPS, and SSH
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 focusst && chown -R focusst:focusst /app
USER focusst

EXPOSE 8000

CMD ["python", "app.py"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  telemetry:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./telemetry.db:/app/telemetry.db
      - ./.env:/app/.env
    restart: unless-stopped
    environment:
      - HOST=0.0.0.0
      - PORT=8000
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - telemetry
    restart: unless-stopped
```

Deploy with Docker Compose:

```bash
docker-compose up -d
docker-compose logs -f
```

## Security Checklist

- [ ] Change default admin password immediately
- [ ] Use a strong, randomly generated SECRET_KEY
- [ ] Enable HTTPS with valid SSL certificate
- [ ] Configure firewall to allow only necessary ports
- [ ] Set DEBUG=false in production
- [ ] Use environment variables for sensitive data
- [ ] Regular security updates: `apt update && apt upgrade`
- [ ] Configure database backups
- [ ] Implement rate limiting if exposed to internet
- [ ] Review and limit user permissions

## Backup Strategy

### Manual Backup

```bash
# Backup database
cp telemetry.db telemetry.db.backup.$(date +%Y%m%d)

# Backup configuration
cp .env .env.backup.$(date +%Y%m%d)
```

### Automated Backups

Add to crontab:

```bash
# Daily backup at 2 AM
0 2 * * * cd /home/focusst/ST && cp telemetry.db /backups/telemetry.db.$(date +\%Y\%m\%d)

# Weekly cleanup (keep 30 days)
0 3 * * 0 find /backups -name "telemetry.db.*" -mtime +30 -delete
```

## Monitoring

### Check Service Status

```bash
sudo systemctl status focusst-telemetry
journalctl -u focusst-telemetry -f
```

### Health Check

```bash
curl http://localhost:8000/health
```

### Monitor Logs

```bash
# Application logs
journalctl -u focusst-telemetry -n 100 -f

# Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

## Performance Tuning

### Database Optimization

```bash
# Periodic vacuum to optimize database
sqlite3 telemetry.db "VACUUM;"

# Clean old data
python cli.py cleanup --days 30
```

### System Resources

Monitor resource usage:

```bash
# CPU and memory
htop

# Disk usage
df -h

# Database size
du -h telemetry.db
```

## Troubleshooting

### Service Won't Start

```bash
# Check logs
journalctl -u focusst-telemetry -n 50

# Check configuration
cd /home/focusst/ST
source venv/bin/activate
python app.py  # Run manually to see errors
```

### WebSocket Connection Issues

- Ensure Nginx proxy_pass includes WebSocket headers
- Check firewall allows WebSocket traffic
- Verify proxy_read_timeout is sufficient

### Database Locked Errors

```bash
# Check for hung processes
ps aux | grep python

# Restart service
sudo systemctl restart focusst-telemetry
```

## Scaling

### Horizontal Scaling

For high-traffic deployments:

1. Use PostgreSQL instead of SQLite
2. Deploy multiple app instances behind load balancer
3. Use Redis for session storage
4. Implement separate WebSocket server

### Vertical Scaling

- Increase server resources (CPU, RAM)
- Optimize database with indexes
- Implement caching layer
- Use CDN for static assets

## Maintenance

### Regular Tasks

- [ ] Weekly: Review logs for errors
- [ ] Monthly: Update dependencies
- [ ] Monthly: Clean up old telemetry data
- [ ] Quarterly: Review and rotate secrets
- [ ] Yearly: Review security configuration

### Update Procedure

```bash
# Backup first
cp telemetry.db telemetry.db.backup

# Update code
git pull origin main

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt

# Restart service
sudo systemctl restart focusst-telemetry
```

## Support

For issues or questions:
- GitHub Issues: https://github.com/SaltProphet/ST/issues
- Documentation: See README.md and API.md
