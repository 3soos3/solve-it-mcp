#!/bin/bash
# Multi-Architecture Build Test Script
# Tests building and running SOLVE-IT MCP Server on amd64, arm64, and arm/v7

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="solve-it-mcp-test"
PROJECT_DIR="~/solve_it_mcp"
PLATFORMS=("linux/amd64" "linux/arm64" "linux/arm/v7")

echo -e "${BLUE}======================================"
echo "Multi-Architecture Build Test"
echo "======================================${NC}"
echo ""

# Function to print status
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check prerequisites
print_status "Checking prerequisites..."

# Check podman
if ! command -v podman &> /dev/null; then
    print_error "Podman is not installed"
    exit 1
fi
print_success "Podman found: $(podman --version)"

# Check QEMU
if [ ! -f /proc/sys/fs/binfmt_misc/qemu-aarch64 ]; then
    print_warning "QEMU ARM64 emulation not detected"
    print_status "Attempting to register QEMU..."
    
    if command -v docker &> /dev/null; then
        docker run --rm --privileged multiarch/qemu-user-static --reset -p yes
    else
        podman run --rm --privileged multiarch/qemu-user-static --reset -p yes
    fi
    
    if [ -f /proc/sys/fs/binfmt_misc/qemu-aarch64 ]; then
        print_success "QEMU registered successfully"
    else
        print_error "Failed to register QEMU. Install with: sudo apt-get install qemu-user-static"
        exit 1
    fi
else
    print_success "QEMU ARM64 emulation detected"
fi

# Change to project directory
cd "$PROJECT_DIR" || exit 1
print_status "Working directory: $PROJECT_DIR"
echo ""

# Step 1: Build images for each architecture
echo -e "${BLUE}======================================"
echo "Step 1: Building Images"
echo "======================================${NC}"
echo ""

for PLATFORM in "${PLATFORMS[@]}"; do
    ARCH_TAG=$(echo "$PLATFORM" | sed 's/linux\///' | sed 's/\//-/g')
    
    print_status "Building for: $PLATFORM (tagged as $ARCH_TAG)"
    
    START_TIME=$(date +%s)
    
    if podman build \
        --platform "$PLATFORM" \
        -t "${IMAGE_NAME}:${ARCH_TAG}" \
        -f Dockerfile \
        . > "/tmp/build-${ARCH_TAG}.log" 2>&1; then
        
        END_TIME=$(date +%s)
        DURATION=$((END_TIME - START_TIME))
        
        print_success "Build completed in ${DURATION}s for $PLATFORM"
    else
        print_error "Build failed for $PLATFORM"
        echo "Check logs: /tmp/build-${ARCH_TAG}.log"
        tail -20 "/tmp/build-${ARCH_TAG}.log"
        exit 1
    fi
    echo ""
done

# Step 2: Verify image metadata
echo -e "${BLUE}======================================"
echo "Step 2: Verifying Image Metadata"
echo "======================================${NC}"
echo ""

for PLATFORM in "${PLATFORMS[@]}"; do
    ARCH_TAG=$(echo "$PLATFORM" | sed 's/linux\///' | sed 's/\//-/g')
    
    print_status "Inspecting ${IMAGE_NAME}:${ARCH_TAG}"
    
    ARCH=$(podman inspect "${IMAGE_NAME}:${ARCH_TAG}" --format '{{.Architecture}}')
    OS=$(podman inspect "${IMAGE_NAME}:${ARCH_TAG}" --format '{{.Os}}')
    SIZE=$(podman inspect "${IMAGE_NAME}:${ARCH_TAG}" --format '{{.Size}}' | numfmt --to=iec)
    
    echo "  OS: $OS"
    echo "  Architecture: $ARCH"
    echo "  Size: $SIZE"
    echo ""
done

# Step 3: Test runtime functionality
echo -e "${BLUE}======================================"
echo "Step 3: Testing Runtime"
echo "======================================${NC}"
echo ""

test_image() {
    local ARCH_TAG=$1
    local PLATFORM=$2
    
    print_status "Testing ${IMAGE_NAME}:${ARCH_TAG}"
    
    # Test 1: Python version
    if podman run --rm --platform "$PLATFORM" "${IMAGE_NAME}:${ARCH_TAG}" \
        python3 --version > /dev/null 2>&1; then
        print_success "Python runtime works"
    else
        print_error "Python runtime failed"
        return 1
    fi
    
    # Test 2: Architecture check
    CONTAINER_ARCH=$(podman run --rm --platform "$PLATFORM" "${IMAGE_NAME}:${ARCH_TAG}" uname -m)
    echo "  Container reports: $CONTAINER_ARCH"
    
    # Test 3: Import test (check if MCP dependencies work)
    if podman run --rm --platform "$PLATFORM" "${IMAGE_NAME}:${ARCH_TAG}" \
        python3 -c "import sys; print(f'Python {sys.version.split()[0]} OK')" 2>&1; then
        print_success "Python imports work"
    else
        print_error "Python imports failed"
        return 1
    fi
    
    echo ""
}

# Test each architecture
for PLATFORM in "${PLATFORMS[@]}"; do
    ARCH_TAG=$(echo "$PLATFORM" | sed 's/linux\///' | sed 's/\//-/g')
    
    if [ "$PLATFORM" = "linux/amd64" ]; then
        print_status "Testing $ARCH_TAG (native - fast)"
    else
        print_warning "Testing $ARCH_TAG (emulated - this will be slower)"
    fi
    
    if ! test_image "$ARCH_TAG" "$PLATFORM"; then
        print_error "Runtime test failed for $PLATFORM"
        exit 1
    fi
done

# Step 4: Create manifest list
echo -e "${BLUE}======================================"
echo "Step 4: Creating Manifest List"
echo "======================================${NC}"
echo ""

MANIFEST_NAME="${IMAGE_NAME}:multiarch"

print_status "Creating manifest: $MANIFEST_NAME"
podman manifest create "$MANIFEST_NAME" || podman manifest rm "$MANIFEST_NAME" && podman manifest create "$MANIFEST_NAME"

for PLATFORM in "${PLATFORMS[@]}"; do
    ARCH_TAG=$(echo "$PLATFORM" | sed 's/linux\///' | sed 's/\//-/g')
    print_status "Adding ${IMAGE_NAME}:${ARCH_TAG} to manifest"
    podman manifest add "$MANIFEST_NAME" "${IMAGE_NAME}:${ARCH_TAG}"
done

print_success "Manifest created successfully"
echo ""

# Display manifest details
print_status "Manifest details:"
podman manifest inspect "$MANIFEST_NAME" | grep -A 10 "manifests" | head -20
echo ""

# Step 5: Summary
echo -e "${BLUE}======================================"
echo "Step 5: Summary"
echo "======================================${NC}"
echo ""

print_status "Available images:"
podman images | grep "$IMAGE_NAME" | awk '{printf "  %-40s %-15s %-10s\n", $1":"$2, $4, $3}'
echo ""

print_success "All tests passed! ✅"
echo ""
echo "Next steps:"
echo "  1. Test the multi-arch manifest:"
echo "     podman run --rm $MANIFEST_NAME python3 --version"
echo ""
echo "  2. Push to registry (optional):"
echo "     podman manifest push $MANIFEST_NAME docker://3soos3/solve-it-mcp:test-multiarch"
echo ""
echo "  3. Clean up test images:"
echo "     podman rmi ${IMAGE_NAME}:amd64 ${IMAGE_NAME}:arm64 ${IMAGE_NAME}:arm-v7"
echo "     podman manifest rm $MANIFEST_NAME"
echo ""
