#!/bin/bash
# =============================================================================
# DROPLET SETUP SCRIPT
# Run this once on a fresh DigitalOcean droplet with Docker pre-installed
# =============================================================================

set -e  # Exit on error

echo "🚀 Setting up Automations server..."

# Update system
apt-get update && apt-get upgrade -y

# Install Docker Compose (if not already)
if ! command -v docker-compose &> /dev/null; then
    echo "📦 Installing Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Create app directory
mkdir -p /opt/automations
cd /opt/automations

# Clone repo (replace with your repo URL)
if [ ! -d ".git" ]; then
    echo "📥 Cloning repository..."
    git clone https://github.com/YOUR_USERNAME/automations.git .
else
    echo "📥 Pulling latest..."
    git pull origin main
fi

# Create .env file if not exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cat > .env << 'EOF'
# Redis connection (from DigitalOcean managed Redis)
REDIS_URL=rediss://default:YOUR_PASSWORD@YOUR_HOST.db.ondigitalocean.com:25061

# API Keys
OPENAI_API_KEY=your_openai_key
APIFY_API_KEY=your_apify_key
FIRECRAWL_API_KEY=your_firecrawl_key

# Add more as needed
EOF
    echo "⚠️  Edit .env with your actual values: nano /opt/automations/.env"
fi

# Build and start
echo "🔨 Building containers..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

# Show status
echo ""
echo "✅ Setup complete!"
echo ""
docker-compose ps
echo ""
echo "📊 Dashboard: http://$(curl -s ifconfig.me):9181"
echo "🔌 API: http://$(curl -s ifconfig.me):8000"
echo "📚 API Docs: http://$(curl -s ifconfig.me):8000/docs"
echo ""
echo "⚠️  Don't forget to:"
echo "   1. Edit .env with your API keys: nano /opt/automations/.env"
echo "   2. Add GitHub secrets for auto-deploy:"
echo "      - DROPLET_IP: $(curl -s ifconfig.me)"
echo "      - SSH_PRIVATE_KEY: (your SSH private key)"
