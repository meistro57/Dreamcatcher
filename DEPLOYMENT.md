<div align="center">
  <img src="Dreamcatcher_logo.png" alt="Dreamcatcher Logo" width="150" />
</div>

# Dreamcatcher Deployment Guide

*From idea to reality - set up your personal AI idea factory*

## Prerequisites

- Linux server (Ubuntu 20.04+ recommended)
- Docker and Docker Compose installed
- Domain name pointing to your server
- SSL certificate capability (Let's Encrypt works great)
- At least 2GB RAM and 10GB storage
- Internet connection for AI API calls

## Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/dreamcatcher.git
   cd dreamcatcher
   ```

2. **Set your domain**
   ```bash
   export DOMAIN="yourdomain.com"
   export SUBDOMAIN="dreamcatcher"
   export EMAIL="admin@yourdomain.com"
   ```

3. **Run deployment script**
   ```bash
   sudo ./deploy.sh
   ```

4. **Configure API keys**
   ```bash
   nano .env
   # Add your ANTHROPIC_API_KEY and OPENAI_API_KEY
   ```

5. **Start the system**
   ```bash
   sudo systemctl start dreamcatcher
   ```

Your Dreamcatcher will be available at `https://dreamcatcher.yourdomain.com`

## Manual Setup

### 1. Environment Configuration

Create a `.env` file with your settings:

```bash
# Domain Configuration
DOMAIN=yourdomain.com
SUBDOMAIN=dreamcatcher
FULL_DOMAIN=dreamcatcher.yourdomain.com
SSL_EMAIL=admin@yourdomain.com

# AI API Keys
ANTHROPIC_API_KEY=your_claude_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Database
DB_PASSWORD=your_secure_password_here

# Security
SECRET_KEY=your_secret_key_here

# Optional: ComfyUI Integration
COMFY_API_URL=http://localhost:8188
COMFYUI_ENABLED=true
```

### 2. SSL Certificate Setup

Using Let's Encrypt:

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Generate certificate
sudo certbot certonly --standalone \
  --email admin@yourdomain.com \
  --agree-tos \
  --no-eff-email \
  -d dreamcatcher.yourdomain.com
```

### 3. Docker Deployment

```bash
cd docker
docker-compose -f docker-compose.prod.yml up -d
```

### 4. Systemd Service

Create `/etc/systemd/system/dreamcatcher.service`:

```ini
[Unit]
Description=Dreamcatcher AI Idea Factory
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/path/to/dreamcatcher/docker
ExecStart=/usr/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/bin/docker-compose -f docker-compose.prod.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable dreamcatcher
sudo systemctl start dreamcatcher
```

## Configuration Options

### Voice Processing

- **Whisper Model**: Set `WHISPER_MODEL=base` (or `small`, `medium`, `large`)
- **Offline Voice**: Set `ENABLE_OFFLINE_VOICE=true` for local processing
- **Voice Timeout**: Configure in agent settings

### ComfyUI Integration

1. Install ComfyUI separately
2. Set `COMFY_API_URL` in environment
3. Configure visual generation models
4. Test connection with health check

### Database Options

- **PostgreSQL**: Default, recommended for production
- **Backup**: Automated daily backups to `/opt/dreamcatcher/backups/`
- **Retention**: 30 days by default

## Monitoring

### Health Checks

Check system status:
```bash
curl https://dreamcatcher.yourdomain.com/api/health
```

### Logs

View application logs:
```bash
docker-compose -f docker/docker-compose.prod.yml logs -f
```

System logs:
```bash
tail -f /var/log/dreamcatcher/monitor.log
```

### Container Status

```bash
docker ps --filter "name=dreamcatcher"
```

## Troubleshooting

### Common Issues

1. **SSL Certificate Errors**
   - Check domain DNS settings
   - Verify certificate files exist
   - Restart nginx container

2. **API Connection Issues**
   - Verify API keys in `.env`
   - Check internet connectivity
   - Review rate limiting

3. **Voice Capture Not Working**
   - Check microphone permissions
   - Verify Whisper model loading
   - Test audio file upload

4. **Database Connection Errors**
   - Check PostgreSQL container status
   - Verify database credentials
   - Review connection string

### Debug Mode

Enable debug logging:
```bash
echo "DEBUG=true" >> .env
docker-compose -f docker/docker-compose.prod.yml restart backend
```

## Maintenance

### Updates

```bash
sudo /path/to/dreamcatcher/scripts/update.sh
```

### Backups

Manual backup:
```bash
sudo /path/to/dreamcatcher/scripts/backup.sh
```

### SSL Renewal

Automatic renewal is configured, but manual renewal:
```bash
sudo certbot renew
```

## Security

### Firewall

```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### API Rate Limiting

Nginx configuration includes rate limiting:
- API: 10 requests/second
- Uploads: 2 requests/second

### Data Protection

- All data stored locally
- Encrypted database connections
- API keys stored securely
- Regular security updates

## Scaling

### Multiple Instances

Deploy multiple agent containers:
```bash
docker-compose -f docker-compose.prod.yml up -d --scale backend=3
```

### Load Balancing

Add load balancer to nginx configuration for high availability.

### Performance Monitoring

Enable metrics collection:
```bash
echo "ENABLE_METRICS=true" >> .env
```

## Support

- Check logs first: `/var/log/dreamcatcher/`
- Review health endpoints: `/api/health`
- Monitor resource usage: `docker stats`
- Test individual components

Your personal AI idea factory is now operational! 🚀

*Remember: This system runs in your basement, thinks about your ideas 24/7, and never forgets a spark of genius.*