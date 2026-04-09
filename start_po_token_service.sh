#!/bin/bash

##############################################################################
# PO Token Provider Service Launcher (Linux/macOS)
#
# Usage:
#   bash start_po_token_service.sh
##############################################################################

set -e

echo "========================================"
echo "  PO Token Provider Service Launcher"
echo "========================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check Node.js
print_info "Checking Node.js..."
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed!"
    echo ""
    echo "Please install Node.js 20+ from: https://nodejs.org/"
    echo "Or use nvm:"
    echo "  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.4/install.sh | bash"
    echo "  nvm install 24"
    exit 1
fi

NODE_VERSION=$(node --version)
NODE_MAJOR=$(echo "$NODE_VERSION" | cut -d'v' -f2 | cut -d'.' -f1)

if [ "$NODE_MAJOR" -lt 20 ]; then
    print_warning "Node.js version is too old: $NODE_VERSION"
    print_error "Node.js 20+ is required"
    exit 1
fi

print_success "Node.js version: $NODE_VERSION"
echo ""

# Check if PO Token Provider exists
if [ ! -d "bgutil-ytdlp-pot-provider" ]; then
    print_info "PO Token Provider not found. Cloning now..."
    echo ""
    git clone --single-branch --branch 1.3.1 https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git
    if [ $? -ne 0 ]; then
        print_error "Failed to clone PO Token Provider!"
        echo ""
        echo "Please clone manually:"
        echo "  git clone --single-branch --branch 1.3.1 https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git"
        exit 1
    fi
    print_success "PO Token Provider cloned successfully"
    echo ""
fi

if [ ! -f "bgutil-ytdlp-pot-provider/server/package.json" ]; then
    print_error "PO Token Provider directory exists but server not found!"
    echo ""
    echo "Please remove and re-clone:"
    echo "  rm -rf bgutil-ytdlp-pot-provider"
    echo "  git clone --single-branch --branch 1.3.1 https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git"
    exit 1
fi

print_success "PO Token Provider found"
echo ""

# Check if already running
if curl -s http://127.0.0.1:4416/ping > /dev/null 2>&1; then
    print_warning "PO Token service is already running on http://127.0.0.1:4416"
    echo ""
    read -p "Do you want to restart it? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Stopping existing service..."
        pkill -f "node build/main.js" 2>/dev/null || true
        sleep 2
    else
        print_info "Keeping existing service running"
        exit 0
    fi
fi

# Start service
print_info "Starting PO Token Provider service..."
print_info "Service will run on: http://127.0.0.1:4416"
print_info "Press Ctrl+C to stop"
echo "========================================"
echo ""

cd bgutil-ytdlp-pot-provider/server
npm ci && npx tsc && node build/main.js

if [ $? -ne 0 ]; then
    echo ""
    print_error "Service failed to start!"
    exit 1
fi
