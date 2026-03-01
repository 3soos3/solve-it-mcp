#!/bin/bash
# Quick Multi-Architecture Test
# Fast test to verify QEMU and build one ARM image

set -e

echo "🔧 Quick Multi-Architecture Test"
echo "================================="
echo ""

# Step 1: Check QEMU
echo "Step 1: Checking QEMU emulation..."
if [ ! -f /proc/sys/fs/binfmt_misc/qemu-aarch64 ]; then
    echo "⚠️  QEMU not detected. Registering..."
    podman run --rm --privileged multiarch/qemu-user-static --reset -p yes
    echo "✅ QEMU registered"
else
    echo "✅ QEMU already registered"
fi
echo ""

# Step 2: Test QEMU works
echo "Step 2: Testing QEMU emulation..."
echo "Running ARM64 Alpine container..."
ARCH=$(podman run --rm --platform linux/arm64 alpine:latest uname -m)
if [ "$ARCH" = "aarch64" ]; then
    echo "✅ QEMU emulation works! Detected: $ARCH"
else
    echo "❌ QEMU emulation failed. Expected 'aarch64', got: $ARCH"
    exit 1
fi
echo ""

# Step 3: Quick build test (AMD64 only - fast)
echo "Step 3: Building AMD64 image (native - fast)..."
cd "$(dirname "$0")"
podman build --platform linux/amd64 -t solve-it-mcp:quick-test-amd64 -f Dockerfile . || {
    echo "❌ AMD64 build failed"
    exit 1
}
echo "✅ AMD64 build successful"
echo ""

# Step 4: Verify and test
echo "Step 4: Testing AMD64 image..."
podman run --rm solve-it-mcp:quick-test-amd64 python3 --version
podman run --rm solve-it-mcp:quick-test-amd64 uname -m
echo "✅ AMD64 image works"
echo ""

# Step 5: Optional ARM64 test (slow!)
read -p "🐢 Build and test ARM64? (slow, ~10-20 min) [y/N]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Step 5: Building ARM64 image (emulated - SLOW)..."
    echo "⏳ This will take 10-20 minutes..."
    START=$(date +%s)
    
    podman build --platform linux/arm64 -t solve-it-mcp:quick-test-arm64 -f Dockerfile . || {
        echo "❌ ARM64 build failed"
        exit 1
    }
    
    END=$(date +%s)
    DURATION=$((END - START))
    echo "✅ ARM64 build successful (took ${DURATION}s)"
    echo ""
    
    echo "Testing ARM64 image..."
    podman run --rm --platform linux/arm64 solve-it-mcp:quick-test-arm64 python3 --version
    podman run --rm --platform linux/arm64 solve-it-mcp:quick-test-arm64 uname -m
    echo "✅ ARM64 image works"
else
    echo ""
    echo "⏭️  Skipping ARM64 test"
fi

echo ""
echo "================================="
echo "✅ All tests passed!"
echo ""
echo "Your system can build multi-architecture images."
echo ""
echo "Next steps:"
echo "  • Run full test: ./test-multiarch.sh"
echo "  • Read guide: cat MULTIARCH_TESTING.md"
echo "  • Clean up: podman rmi solve-it-mcp:quick-test-amd64"
echo ""
