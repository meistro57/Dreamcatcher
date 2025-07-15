#!/bin/bash

# Dreamcatcher Deployment Script
# Deploys the AI-powered idea factory to your basement server

set -e

echo "🚀 Starting Dreamcatcher deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOMAIN=${DOMAIN:-"unitthirty2.com"}
SUBDOMAIN=${SUBDOMAIN:-"dreamcatcher"}
FULL_DOMAIN="${SUBDOMAIN}.${DOMAIN}"
EMAIL=${EMAIL:-"admin@${DOMAIN}"}
DATA_DIR="/opt/dreamcatcher"
LOG_DIR="/var/log/dreamcatcher"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    log_info "Checking system requirements..."
    
    # Check if running as root
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root"
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check available disk space (need at least 2GB)
    available_space=$(df / | tail -1 | awk '{print $4}')
    if [[ $available_space -lt 2097152 ]]; then
        log_warning "Low disk space. Consider freeing up space before deployment."
    fi
    
    log_success "System requirements check passed"
}

setup_directories() {
    log_info "Setting up directories..."
    
    # Create data directories
    mkdir -p $DATA_DIR/{postgres,redis,storage/audio,storage/images,storage/logs}
    mkdir -p $LOG_DIR
    
    # Set permissions
    chown -R 1000:1000 $DATA_DIR
    chmod -R 755 $DATA_DIR
    
    log_success "Directories created"
}

setup_environment() {
    log_info "Setting up environment configuration..."
    
    # Check if .env already exists
    if [[ -f .env ]]; then
        log_warning ".env file already exists. Backing up to .env.backup"
        cp .env .env.backup
    fi
    
    # Create .env file
    cat > .env << EOF
# Database Configuration
DB_PASSWORD=$(openssl rand -base64 32)

# Domain Configuration
DOMAIN=${DOMAIN}
SUBDOMAIN=${SUBDOMAIN}
FULL_DOMAIN=${FULL_DOMAIN}
SSL_EMAIL=${EMAIL}

# AI API Keys (you'll need to set these)
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-your_claude_api_key_here}
OPENAI_API_KEY=${OPENAI_API_KEY:-your_openai_api_key_here}

# ComfyUI Integration
COMFY_API_URL=${COMFY_API_URL:-http://localhost:8188}

# Security
SECRET_KEY=$(openssl rand -base64 32)

# Voice Processing
WHISPER_MODEL=base
ENABLE_OFFLINE_VOICE=true

# Development
DEBUG=false
LOG_LEVEL=INFO

# Optional: Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090

# Data directories
DATA_DIR=${DATA_DIR}
LOG_DIR=${LOG_DIR}
EOF
    
    log_success "Environment configuration created"
    
    if [[ "${ANTHROPIC_API_KEY:-your_claude_api_key_here}" == "your_claude_api_key_here" ]]; then
        log_warning "Don't forget to set your ANTHROPIC_API_KEY in .env"
    fi
    
    if [[ "${OPENAI_API_KEY:-your_openai_api_key_here}" == "your_openai_api_key_here" ]]; then
        log_warning "Don't forget to set your OPENAI_API_KEY in .env"
    fi
}

setup_ssl() {
    log_info "Setting up SSL certificates..."
    
    # Install certbot if not present
    if ! command -v certbot &> /dev/null; then
        log_info "Installing certbot..."
        apt-get update
        apt-get install -y certbot python3-certbot-nginx
    fi
    
    # Create SSL directory
    mkdir -p docker/ssl
    
    # Generate SSL certificate
    if [[ ! -f "docker/ssl/${FULL_DOMAIN}.crt" ]]; then
        log_info "Generating SSL certificate for ${FULL_DOMAIN}..."
        
        # Stop nginx if running
        systemctl stop nginx 2>/dev/null || true
        
        # Generate certificate
        certbot certonly --standalone \
            --email $EMAIL \
            --agree-tos \
            --no-eff-email \
            -d $FULL_DOMAIN
        
        # Copy certificates
        cp /etc/letsencrypt/live/${FULL_DOMAIN}/fullchain.pem docker/ssl/${FULL_DOMAIN}.crt
        cp /etc/letsencrypt/live/${FULL_DOMAIN}/privkey.pem docker/ssl/${FULL_DOMAIN}.key
        
        log_success "SSL certificate generated"
    else
        log_info "SSL certificate already exists"
    fi
}

setup_nginx_config() {
    log_info "Setting up Nginx configuration..."
    
    cat > docker/nginx-production.conf << EOF
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    # Rate limiting
    limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone \$binary_remote_addr zone=upload:10m rate=2r/s;

    # Redirect HTTP to HTTPS
    server {
        listen 80;
        server_name ${FULL_DOMAIN};
        return 301 https://\$server_name\$request_uri;
    }

    # Main HTTPS server
    server {
        listen 443 ssl http2;
        server_name ${FULL_DOMAIN};

        # SSL configuration
        ssl_certificate /etc/nginx/ssl/${FULL_DOMAIN}.crt;
        ssl_certificate_key /etc/nginx/ssl/${FULL_DOMAIN}.key;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;

        # Frontend
        location / {
            proxy_pass http://frontend:3000;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }

        # API with rate limiting
        location /api {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://backend:8000;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }

        # WebSocket support
        location /api/ws {
            proxy_pass http://backend:8000;
            proxy_http_version 1.1;
            proxy_set_header Upgrade \$http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }

        # File uploads with special rate limiting
        location /api/capture/voice {
            limit_req zone=upload burst=5 nodelay;
            client_max_body_size 10M;
            proxy_pass http://backend:8000;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }

        # Storage files
        location /storage {
            proxy_pass http://backend:8000;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }
    }
}
EOF
    
    log_success "Nginx configuration created"
}

update_docker_compose() {
    log_info "Updating Docker Compose for production..."
    
    # Update docker-compose.yml for production
    cat > docker/docker-compose.prod.yml << EOF
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: dreamcatcher-db
    environment:
      POSTGRES_DB: dreamcatcher
      POSTGRES_USER: dreamcatcher
      POSTGRES_PASSWORD: \${DB_PASSWORD}
    volumes:
      - ${DATA_DIR}/postgres:/var/lib/postgresql/data
    restart: unless-stopped
    networks:
      - dreamcatcher-network

  redis:
    image: redis:7-alpine
    container_name: dreamcatcher-redis
    volumes:
      - ${DATA_DIR}/redis:/data
    command: redis-server --appendonly yes
    restart: unless-stopped
    networks:
      - dreamcatcher-network

  backend:
    build:
      context: ../backend
      dockerfile: Dockerfile
    container_name: dreamcatcher-backend
    environment:
      - DATABASE_URL=postgresql://dreamcatcher:\${DB_PASSWORD}@postgres:5432/dreamcatcher
      - REDIS_URL=redis://redis:6379
      - ANTHROPIC_API_KEY=\${ANTHROPIC_API_KEY}
      - OPENAI_API_KEY=\${OPENAI_API_KEY}
      - COMFY_API_URL=\${COMFY_API_URL}
      - SECRET_KEY=\${SECRET_KEY}
      - DEBUG=false
      - LOG_LEVEL=INFO
    depends_on:
      - postgres
      - redis
    volumes:
      - ${DATA_DIR}/storage:/app/storage
      - ${LOG_DIR}:/app/logs
    restart: unless-stopped
    networks:
      - dreamcatcher-network

  frontend:
    build:
      context: ../frontend
      dockerfile: Dockerfile
    container_name: dreamcatcher-frontend
    restart: unless-stopped
    networks:
      - dreamcatcher-network

  nginx:
    image: nginx:alpine
    container_name: dreamcatcher-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx-production.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
      - ${LOG_DIR}/nginx:/var/log/nginx
    depends_on:
      - backend
      - frontend
    restart: unless-stopped
    networks:
      - dreamcatcher-network

  scheduler:
    build:
      context: ../backend
      dockerfile: Dockerfile.scheduler
    container_name: dreamcatcher-scheduler
    environment:
      - DATABASE_URL=postgresql://dreamcatcher:\${DB_PASSWORD}@postgres:5432/dreamcatcher
      - REDIS_URL=redis://redis:6379
      - ANTHROPIC_API_KEY=\${ANTHROPIC_API_KEY}
      - OPENAI_API_KEY=\${OPENAI_API_KEY}
      - LOG_LEVEL=INFO
    depends_on:
      - postgres
      - redis
    volumes:
      - ${DATA_DIR}/storage:/app/storage
      - ${LOG_DIR}:/app/logs
    restart: unless-stopped
    networks:
      - dreamcatcher-network

networks:
  dreamcatcher-network:
    driver: bridge
EOF
    
    log_success "Production Docker Compose configuration created"
}

setup_systemd_service() {
    log_info "Setting up systemd service..."
    
    cat > /etc/systemd/system/dreamcatcher.service << EOF
[Unit]
Description=Dreamcatcher AI Idea Factory
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/mark/Dreamcatcher/docker
ExecStart=/usr/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/bin/docker-compose -f docker-compose.prod.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable dreamcatcher
    
    log_success "Systemd service configured"
}

setup_monitoring() {
    log_info "Setting up monitoring and log rotation..."
    
    # Log rotation configuration
    cat > /etc/logrotate.d/dreamcatcher << EOF
${LOG_DIR}/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 root root
}
EOF
    
    # Simple monitoring script
    cat > /usr/local/bin/dreamcatcher-monitor.sh << 'EOF'
#!/bin/bash
# Simple monitoring script for Dreamcatcher

LOG_FILE="/var/log/dreamcatcher/monitor.log"
HEALTH_URL="http://localhost:8000/api/health"

check_health() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    if curl -s -f $HEALTH_URL > /dev/null; then
        echo "[$timestamp] Health check: OK" >> $LOG_FILE
        return 0
    else
        echo "[$timestamp] Health check: FAILED" >> $LOG_FILE
        return 1
    fi
}

# Check if containers are running
check_containers() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local containers=(
        "dreamcatcher-db"
        "dreamcatcher-redis"
        "dreamcatcher-backend"
        "dreamcatcher-frontend"
        "dreamcatcher-nginx"
        "dreamcatcher-scheduler"
    )
    
    for container in "${containers[@]}"; do
        if docker ps --filter "name=$container" --filter "status=running" | grep -q $container; then
            echo "[$timestamp] Container $container: Running" >> $LOG_FILE
        else
            echo "[$timestamp] Container $container: NOT RUNNING" >> $LOG_FILE
        fi
    done
}

# Main monitoring
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting health check" >> $LOG_FILE
check_health
check_containers
EOF
    
    chmod +x /usr/local/bin/dreamcatcher-monitor.sh
    
    # Add to crontab for regular monitoring
    (crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/dreamcatcher-monitor.sh") | crontab -
    
    log_success "Monitoring configured"
}

deploy_application() {
    log_info "Deploying Dreamcatcher application..."
    
    cd docker
    
    # Build and start services
    docker-compose -f docker-compose.prod.yml build
    docker-compose -f docker-compose.prod.yml up -d
    
    # Wait for services to be ready
    log_info "Waiting for services to start..."
    sleep 30
    
    # Check if services are running
    if docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
        log_success "Services started successfully"
    else
        log_error "Some services failed to start"
        docker-compose -f docker-compose.prod.yml logs
        exit 1
    fi
    
    cd ..
}

setup_ssl_renewal() {
    log_info "Setting up SSL certificate auto-renewal..."
    
    # Create renewal hook
    cat > /etc/letsencrypt/renewal-hooks/deploy/dreamcatcher.sh << EOF
#!/bin/bash
# Copy renewed certificates to Docker volume
cp /etc/letsencrypt/live/${FULL_DOMAIN}/fullchain.pem /home/mark/Dreamcatcher/docker/ssl/${FULL_DOMAIN}.crt
cp /etc/letsencrypt/live/${FULL_DOMAIN}/privkey.pem /home/mark/Dreamcatcher/docker/ssl/${FULL_DOMAIN}.key

# Reload nginx
docker exec dreamcatcher-nginx nginx -s reload
EOF
    
    chmod +x /etc/letsencrypt/renewal-hooks/deploy/dreamcatcher.sh
    
    log_success "SSL auto-renewal configured"
}

main() {
    log_info "🧠 Dreamcatcher Deployment Starting..."
    
    check_requirements
    setup_directories
    setup_environment
    setup_ssl
    setup_nginx_config
    update_docker_compose
    setup_systemd_service
    setup_monitoring
    deploy_application
    setup_ssl_renewal
    
    log_success "🎉 Dreamcatcher deployed successfully!"
    log_info "🌐 Access your idea factory at: https://${FULL_DOMAIN}"
    log_info "📊 Monitor logs at: ${LOG_DIR}"
    log_info "🔧 Manage service with: systemctl {start|stop|restart|status} dreamcatcher"
    
    echo ""
    echo "Next steps:"
    echo "1. Set your API keys in .env file"
    echo "2. Test voice capture functionality"
    echo "3. Configure ComfyUI if needed"
    echo "4. Check logs: docker-compose -f docker/docker-compose.prod.yml logs"
    echo ""
    echo "The basement never sleeps. Neither does your idea factory. 🚀"
}

# Run main function
main "$@"