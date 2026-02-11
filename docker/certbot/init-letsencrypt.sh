#!/bin/bash

# Initialize Let's Encrypt certificate using Certbot
# Usage: ./init-letsencrypt.sh DOMAIN_NAME EMAIL

set -e

DOMAIN_NAME="${1:-example.com}"
EMAIL="${2:-admin@example.com}"
CERTBOT_CONTAINER="certbot"
NGINX_CONTAINER="nginx"

echo "==========================================="
echo "Let's Encrypt Certificate Initialization"
echo "==========================================="
echo "Domain: $DOMAIN_NAME"
echo "Email: $EMAIL"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if containers exist
if ! docker ps -a --format '{{.Names}}' | grep -q "^${NGINX_CONTAINER}$"; then
    echo "❌ Nginx container not found. Please run 'docker-compose up -d' first."
    exit 1
fi

echo "📝 Creating certbot www directory..."
mkdir -p $(dirname "$0")/www

echo "📝 Creating initial certificate..."
docker run --rm \
    -v $(cd $(dirname "$0")/.. && pwd)/certbot/www:/var/www/certbot \
    -v $(docker inspect $NGINX_CONTAINER --format='{{json .Mounts}}' | grep certbot_etc | grep -o '/var/lib/docker[^"]*') \
    certbot/certbot certonly \
    --webroot \
    -w /var/www/certbot \
    --email $EMAIL \
    -d $DOMAIN_NAME \
    --agree-tos \
    --non-interactive \
    --dry-run

if [ $? -eq 0 ]; then
    echo ""
    echo "🔄 Running without dry-run..."
    docker run --rm \
        -v $(cd $(dirname "$0")/.. && pwd)/certbot/www:/var/www/certbot \
        certbot/certbot certonly \
        --webroot \
        -w /var/www/certbot \
        --email $EMAIL \
        -d $DOMAIN_NAME \
        --agree-tos \
        --non-interactive
fi

echo ""
echo "✅ Certificate initialization completed!"
echo ""
echo "📝 IMPORTANT: Update nginx configuration"
echo "   Replace 'DOMAIN_NAME' in /docker/nginx/default.conf with: $DOMAIN_NAME"
echo ""
echo "🔄 Then reload nginx:"
echo "   docker-compose exec nginx nginx -s reload"
echo ""
