#!/bin/bash

# k6 Installation Script
# Detects OS and installs k6 using the appropriate package manager

set -e

echo "k6 Installation Script"
echo "======================"

# Detect OS
OS="$(uname -s)"
case "$OS" in
    Linux*)
        echo "Detected: Linux"

        # Check if running in WSL
        if grep -qi microsoft /proc/version 2>/dev/null; then
            echo "Running in WSL (Windows Subsystem for Linux)"
        fi

        # Detect distribution
        if [ -f /etc/os-release ]; then
            . /etc/os-release
            DISTRO=$ID
        else
            DISTRO="unknown"
        fi

        echo "Distribution: $DISTRO"

        case "$DISTRO" in
            ubuntu|debian)
                echo "Installing k6 for Debian/Ubuntu..."
                sudo gpg -k || true
                sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg \
                    --keyserver hkp://keyserver.ubuntu.com:80 \
                    --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
                echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | \
                    sudo tee /etc/apt/sources.list.d/k6.list
                sudo apt-get update
                sudo apt-get install -y k6
                ;;
            fedora|centos|rhel)
                echo "Installing k6 for Fedora/CentOS/RHEL..."
                sudo dnf install -y https://dl.k6.io/rpm/repo.rpm
                sudo dnf install -y k6
                ;;
            arch)
                echo "Installing k6 for Arch Linux..."
                sudo pacman -Sy k6
                ;;
            *)
                echo "Unsupported Linux distribution: $DISTRO"
                echo "Please install k6 manually from https://k6.io/docs/get-started/installation/"
                exit 1
                ;;
        esac
        ;;

    Darwin*)
        echo "Detected: macOS"
        if ! command -v brew &> /dev/null; then
            echo "Error: Homebrew is required but not installed"
            echo "Please install Homebrew from https://brew.sh/"
            exit 1
        fi
        echo "Installing k6 via Homebrew..."
        brew install k6
        ;;

    MINGW*|MSYS*|CYGWIN*)
        echo "Detected: Windows (Git Bash/MSYS)"
        echo "For Windows, please use one of the following methods:"
        echo ""
        echo "1. Using Chocolatey:"
        echo "   choco install k6"
        echo ""
        echo "2. Using winget:"
        echo "   winget install k6"
        echo ""
        echo "3. Download installer from:"
        echo "   https://dl.k6.io/msi/k6-latest-amd64.msi"
        echo ""
        exit 1
        ;;

    *)
        echo "Unsupported operating system: $OS"
        echo "Please install k6 manually from https://k6.io/docs/get-started/installation/"
        exit 1
        ;;
esac

# Verify installation
echo ""
echo "Verifying k6 installation..."
if command -v k6 &> /dev/null; then
    K6_VERSION=$(k6 version)
    echo "✓ k6 installed successfully: $K6_VERSION"
else
    echo "✗ k6 installation failed"
    exit 1
fi

echo ""
echo "Installation complete!"
echo "You can now run performance tests using: make perf-test"
