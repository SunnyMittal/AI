#!/bin/bash
# Setup k6 for Performance Testing
# Automated installation script for Linux/macOS

set -e

echo "========================================"
echo "k6 Installation Script"
echo "========================================"

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Detected: Linux"

    # Check if it's Debian/Ubuntu
    if [ -f /etc/debian_version ]; then
        echo "Installing k6 for Debian/Ubuntu..."

        # Install GPG key
        sudo gpg -k
        sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg \
            --keyserver hkp://keyserver.ubuntu.com:80 \
            --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69

        # Add k6 repository
        echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | \
            sudo tee /etc/apt/sources.list.d/k6.list

        # Update and install
        sudo apt-get update
        sudo apt-get install k6

    else
        echo "Unsupported Linux distribution"
        echo "Please install k6 manually from: https://k6.io/docs/getting-started/installation/"
        exit 1
    fi

elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Detected: macOS"

    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        echo "ERROR: Homebrew is not installed"
        echo "Install Homebrew from: https://brew.sh/"
        exit 1
    fi

    echo "Installing k6 via Homebrew..."
    brew install k6

else
    echo "Unsupported operating system: $OSTYPE"
    echo "Please install k6 manually from: https://k6.io/docs/getting-started/installation/"
    exit 1
fi

# Verify installation
echo ""
echo "Verifying k6 installation..."
if k6 version; then
    echo ""
    echo "========================================"
    echo "✓ k6 installed successfully!"
    echo "========================================"
else
    echo ""
    echo "========================================"
    echo "✗ k6 installation failed"
    echo "========================================"
    exit 1
fi
