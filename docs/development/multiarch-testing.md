# Multi-Architecture Build Testing Guide

This guide shows you how to test multi-architecture Docker/Podman builds locally for amd64, arm64, and arm/v7.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Method 1: QEMU Emulation (Recommended)](#method-1-qemu-emulation-recommended)
- [Method 2: Buildx Multi-Platform Builds](#method-2-buildx-multi-platform-builds)
- [Method 3: Podman Manifest Lists](#method-3-podman-manifest-lists)
- [Testing Each Architecture](#testing-each-architecture)
- [Verification and Debugging](#verification-and-debugging)
- [CI/CD Integration](#cicd-integration)

---

## Prerequisites

### Your Current Setup
- **Host Architecture**: x86_64 (amd64)
- **Container Runtime**: Podman 5.7.1
- **Project**: `~/solve_it_mcp`

### Required Tools

**Install QEMU for multi-arch emulation:**

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y qemu-user-static binfmt-support

# Fedora/RHEL
sudo dnf install -y qemu-user-static

# Verify QEMU is registered
ls -la /proc/sys/fs/binfmt_misc/qemu-*
```

**Verify multi-arch support:**

```bash
# Check registered emulators
cat /proc/sys/fs/binfmt_misc/qemu-aarch64  # For arm64
cat /proc/sys/fs/binfmt_misc/qemu-arm      # For arm/v7
```

---

## Method 1: QEMU Emulation (Recommended)

This is the **easiest method** for local testing. Build images for different architectures using QEMU emulation.

### Step 1: Enable QEMU Support

```bash
# Register QEMU binaries (if not already done)
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes

# Or with Podman
podman run --rm --privileged multiarch/qemu-user-static --reset -p yes
```

### Step 2: Build for Specific Architecture

```bash
cd ~/solve_it_mcp

# Build for AMD64 (native on your machine)
podman build \
  --platform linux/amd64 \
  -t solve-it-mcp:amd64 \
  -f Dockerfile .

# Build for ARM64 (using QEMU emulation)
podman build \
  --platform linux/arm64 \
  -t solve-it-mcp:arm64 \
  -f Dockerfile .

# Build for ARMv7 (using QEMU emulation)
podman build \
  --platform linux/arm/v7 \
  -t solve-it-mcp:armv7 \
  -f Dockerfile .
```

**Note**: ARM builds will be slower due to emulation (can take 5-10x longer).

### Step 3: Verify Images

```bash
# List images
podman images | grep solve-it-mcp

# Inspect architecture
podman inspect solve-it-mcp:amd64 | grep Architecture
podman inspect solve-it-mcp:arm64 | grep Architecture
podman inspect solve-it-mcp:armv7 | grep Architecture
```

### Step 4: Test Each Image

```bash
# Test AMD64 (native)
podman run --rm -it solve-it-mcp:amd64 python3 --version

# Test ARM64 (emulated)
podman run --rm -it --platform linux/arm64 solve-it-mcp:arm64 python3 --version

# Test ARMv7 (emulated)
podman run --rm -it --platform linux/arm/v7 solve-it-mcp:armv7 python3 --version
```

---

## Method 2: Buildx Multi-Platform Builds

Docker Buildx can build multiple architectures in one command. **Podman equivalent**: Use `buildah` with manifests.

### Using Docker Buildx

```bash
# Create a new builder instance
docker buildx create --name multiarch --use
docker buildx inspect --bootstrap

# Build all architectures at once
docker buildx build \
  --platform linux/amd64,linux/arm64,linux/arm/v7 \
  -t solve-it-mcp:multiarch \
  -f Dockerfile \
  --load \
  .

# Note: --load only works with single platform
# For multiple platforms, use --push to registry or --output type=image,push=false
```

### Multi-Platform Build and Push

```bash
# Build and push to Docker Hub (all architectures)
docker buildx build \
  --platform linux/amd64,linux/arm64,linux/arm/v7 \
  -t 3soos3/solve-it-mcp:test-multiarch \
  -f Dockerfile \
  --push \
  .
```

---

## Method 3: Podman Manifest Lists

Podman supports creating manifest lists that reference multiple architecture images.

### Step 1: Build Individual Architectures

```bash
cd ~/solve_it_mcp

# Build for each platform
podman build --platform linux/amd64 -t localhost/solve-it-mcp:amd64 .
podman build --platform linux/arm64 -t localhost/solve-it-mcp:arm64 .
podman build --platform linux/arm/v7 -t localhost/solve-it-mcp:armv7 .
```

### Step 2: Create Manifest List

```bash
# Create manifest that points to all arch-specific images
podman manifest create solve-it-mcp:multiarch

# Add each architecture to the manifest
podman manifest add solve-it-mcp:multiarch localhost/solve-it-mcp:amd64
podman manifest add solve-it-mcp:multiarch localhost/solve-it-mcp:arm64
podman manifest add solve-it-mcp:multiarch localhost/solve-it-mcp:armv7
```

### Step 3: Inspect and Test Manifest

```bash
# Inspect the manifest
podman manifest inspect solve-it-mcp:multiarch

# Should show all three architectures:
# - linux/amd64
# - linux/arm64
# - linux/arm/v7

# Test (Podman auto-selects correct architecture)
podman run --rm solve-it-mcp:multiarch python3 --version
```

### Step 4: Push Manifest to Registry

```bash
# Push manifest to Docker Hub (includes all architectures)
podman manifest push solve-it-mcp:multiarch docker://3soos3/solve-it-mcp:test-multiarch
```

---

## Testing Each Architecture

### 1. Build Verification Test

Create a simple test script:

```bash
cat > /tmp/test-multiarch.sh << 'EOF'
#!/bin/bash
set -e

PLATFORMS=("linux/amd64" "linux/arm64" "linux/arm/v7")
IMAGE_NAME="solve-it-mcp-test"

for PLATFORM in "${PLATFORMS[@]}"; do
    ARCH_TAG=$(echo $PLATFORM | sed 's/linux\///' | sed 's/\//-/g')
    
    echo "======================================"
    echo "Building for: $PLATFORM"
    echo "======================================"
    
    podman build \
        --platform "$PLATFORM" \
        -t "${IMAGE_NAME}:${ARCH_TAG}" \
        -f Dockerfile \
        . || {
            echo "❌ Build failed for $PLATFORM"
            exit 1
        }
    
    echo "✅ Build successful for $PLATFORM"
    echo ""
done

echo "======================================"
echo "All builds completed successfully!"
echo "======================================"
podman images | grep $IMAGE_NAME
EOF

chmod +x /tmp/test-multiarch.sh
```

Run the test:

```bash
cd ~/solve_it_mcp
/tmp/test-multiarch.sh
```

### 2. Runtime Verification Test

Test that each image actually runs:

```bash
cat > /tmp/test-runtime.sh << 'EOF'
#!/bin/bash
set -e

echo "Testing AMD64 image..."
podman run --rm --platform linux/amd64 solve-it-mcp-test:amd64 \
    python3 -c "import sys; print(f'Python {sys.version} on {sys.platform}')"

echo ""
echo "Testing ARM64 image (emulated)..."
podman run --rm --platform linux/arm64 solve-it-mcp-test:arm64 \
    python3 -c "import sys; print(f'Python {sys.version} on {sys.platform}')"

echo ""
echo "Testing ARMv7 image (emulated)..."
podman run --rm --platform linux/arm-v7 solve-it-mcp-test:arm-v7 \
    python3 -c "import sys; print(f'Python {sys.version} on {sys.platform}')"

echo ""
echo "✅ All runtime tests passed!"
EOF

chmod +x /tmp/test-runtime.sh
/tmp/test-runtime.sh
```

### 3. Application-Specific Test

Test the actual SOLVE-IT MCP server:

```bash
# Test AMD64 (native)
podman run --rm -d --name test-amd64 \
    -e MCP_TRANSPORT=http \
    -e HTTP_PORT=8000 \
    -p 8001:8000 \
    solve-it-mcp-test:amd64

# Wait for startup
sleep 5

# Test health endpoint
curl http://localhost:8001/healthz

# Cleanup
podman stop test-amd64

# Test ARM64 (emulated - slower)
podman run --rm -d --name test-arm64 \
    --platform linux/arm64 \
    -e MCP_TRANSPORT=http \
    -e HTTP_PORT=8000 \
    -p 8002:8000 \
    solve-it-mcp-test:arm64

sleep 10  # Emulation is slower

curl http://localhost:8002/healthz

podman stop test-arm64
```

---

## Verification and Debugging

### 1. Inspect Image Architecture

```bash
# Check architecture metadata
podman inspect solve-it-mcp:amd64 | jq '.[0].Architecture'
podman inspect solve-it-mcp:arm64 | jq '.[0].Architecture'
podman inspect solve-it-mcp:armv7 | jq '.[0].Architecture'

# Expected outputs:
# amd64
# arm64
# arm
```

### 2. Verify Binary Compatibility

```bash
# Run architecture-specific command inside container
podman run --rm solve-it-mcp:amd64 uname -m
# Output: x86_64

podman run --rm --platform linux/arm64 solve-it-mcp:arm64 uname -m
# Output: aarch64

podman run --rm --platform linux/arm/v7 solve-it-mcp:armv7 uname -m
# Output: armv7l
```

### 3. Check Image Size

```bash
# Compare sizes across architectures
podman images solve-it-mcp-test --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}\t{{.Created}}"

# ARM images might be slightly different sizes due to compiled dependencies
```

### 4. Debug Build Failures

If a build fails for a specific architecture:

```bash
# Build with verbose output
podman build \
    --platform linux/arm64 \
    --log-level debug \
    -t solve-it-mcp:arm64-debug \
    -f Dockerfile \
    .

# Check QEMU is working
podman run --rm --platform linux/arm64 alpine:latest uname -m
# Should output: aarch64
```

### 5. Common Issues and Solutions

**Issue: "exec format error"**
```bash
# Solution: QEMU not registered
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes
```

**Issue: ARM build extremely slow**
```bash
# Solution: This is normal - emulation is slow
# ARM64 builds can take 5-10x longer than native
# Consider using CI/CD with native ARM runners for faster builds
```

**Issue: Python package build fails on ARM**
```bash
# Solution: Some packages need additional ARM-specific dependencies
# Add to Dockerfile builder stage:
RUN apt-get install -y --no-install-recommends \
    libffi-dev \
    libssl-dev \
    gcc \
    g++
```

---

## CI/CD Integration

### GitHub Actions Multi-Arch Build

Your repository already has this in `.github/workflows/docker-build.yml`. Here's what it does:

```yaml
- name: Set up QEMU
  uses: docker/setup-qemu-action@v3

- name: Set up Docker Buildx
  uses: docker/setup-buildx-action@v3

- name: Build and push multi-arch
  uses: docker/build-push-action@v5
  with:
    platforms: linux/amd64,linux/arm64,linux/arm/v7
    push: true
    tags: 3soos3/solve-it-mcp:latest
```

### Test Before CI/CD Push

Run local tests to catch issues before pushing:

```bash
# Full test pipeline
cd ~/solve_it_mcp

# 1. Build all architectures
for PLATFORM in linux/amd64 linux/arm64 linux/arm/v7; do
    ARCH=$(echo $PLATFORM | cut -d'/' -f2)
    echo "Building $ARCH..."
    podman build --platform $PLATFORM -t solve-it-mcp:$ARCH . || exit 1
done

# 2. Test basic functionality
for ARCH in amd64 arm64 armv7; do
    echo "Testing $ARCH..."
    podman run --rm solve-it-mcp:$ARCH python3 -c "import sys; print(sys.version)" || exit 1
done

# 3. Create and inspect manifest
podman manifest create solve-it-mcp:test-manifest
podman manifest add solve-it-mcp:test-manifest solve-it-mcp:amd64
podman manifest add solve-it-mcp:test-manifest solve-it-mcp:arm64
podman manifest add solve-it-mcp:test-manifest solve-it-mcp:armv7
podman manifest inspect solve-it-mcp:test-manifest

echo "✅ All tests passed! Ready to push to CI/CD"
```

---

## Quick Reference Commands

### Build Single Architecture
```bash
podman build --platform linux/amd64 -t solve-it-mcp:amd64 .
podman build --platform linux/arm64 -t solve-it-mcp:arm64 .
podman build --platform linux/arm/v7 -t solve-it-mcp:armv7 .
```

### Test Runtime
```bash
podman run --rm solve-it-mcp:amd64 python3 --version
podman run --rm --platform linux/arm64 solve-it-mcp:arm64 python3 --version
podman run --rm --platform linux/arm/v7 solve-it-mcp:armv7 python3 --version
```

### Verify Architecture
```bash
podman inspect solve-it-mcp:amd64 | grep -i arch
podman inspect solve-it-mcp:arm64 | grep -i arch
podman inspect solve-it-mcp:armv7 | grep -i arch
```

### Create Manifest
```bash
podman manifest create solve-it-mcp:multiarch
podman manifest add solve-it-mcp:multiarch solve-it-mcp:amd64
podman manifest add solve-it-mcp:multiarch solve-it-mcp:arm64
podman manifest add solve-it-mcp:multiarch solve-it-mcp:armv7
podman manifest inspect solve-it-mcp:multiarch
```

### Push to Registry
```bash
podman manifest push solve-it-mcp:multiarch docker://3soos3/solve-it-mcp:test
```

---

## Expected Build Times

On a typical x86_64 machine:

| Architecture | Build Time | Speed |
|--------------|------------|-------|
| **linux/amd64** | ~2-5 minutes | Native (1x) |
| **linux/arm64** | ~15-30 minutes | Emulated (~5-8x slower) |
| **linux/arm/v7** | ~20-40 minutes | Emulated (~8-10x slower) |

**Note**: ARM builds are significantly slower due to QEMU emulation. This is normal and expected.

---

## Troubleshooting

### Check QEMU Status
```bash
ls -la /proc/sys/fs/binfmt_misc/qemu-*
cat /proc/sys/fs/binfmt_misc/qemu-aarch64
cat /proc/sys/fs/binfmt_misc/qemu-arm
```

### Re-register QEMU
```bash
podman run --rm --privileged multiarch/qemu-user-static --reset -p yes
```

### Test QEMU Emulation
```bash
podman run --rm --platform linux/arm64 alpine uname -m  # Should output: aarch64
podman run --rm --platform linux/arm/v7 alpine uname -m # Should output: armv7l
```

### Check Podman Multi-Arch Support
```bash
podman info | grep -i arch
```

---

## Summary

**Recommended Workflow for Local Testing:**

1. **Install QEMU**: `sudo apt-get install qemu-user-static`
2. **Register QEMU**: `podman run --rm --privileged multiarch/qemu-user-static --reset -p yes`
3. **Build each arch**: `podman build --platform linux/ARCH -t solve-it-mcp:ARCH .`
4. **Test images**: `podman run --rm solve-it-mcp:ARCH python3 --version`
5. **Create manifest**: Bundle all architectures into one multi-arch image
6. **Push to registry**: `podman manifest push`

This ensures your multi-architecture builds work correctly before pushing to CI/CD or Docker Hub.
