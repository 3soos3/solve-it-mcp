# Multi-Architecture Build Testing

How to test `linux/amd64`, `linux/arm64`, and `linux/arm/v7` Docker builds locally.

## Prerequisites

Install QEMU for cross-architecture emulation:

```bash
# Ubuntu/Debian
sudo apt-get install -y qemu-user-static binfmt-support

# Fedora/RHEL
sudo dnf install -y qemu-user-static

# Verify
ls /proc/sys/fs/binfmt_misc/qemu-*
```

Register QEMU (if not already registered):

```bash
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes
# or with Podman:
podman run --rm --privileged multiarch/qemu-user-static --reset -p yes
```

---

## Method 1: QEMU Emulation (Recommended for Local Testing)

### Build for Each Architecture

```bash
# Native (fast)
podman build --platform linux/amd64 -t solve-it-mcp:amd64 .

# Emulated (slower)
podman build --platform linux/arm64 -t solve-it-mcp:arm64 .
podman build --platform linux/arm/v7 -t solve-it-mcp:armv7 .
```

!!! note "Expected build times on x86_64"
    - `linux/amd64`: ~2–5 minutes (native)
    - `linux/arm64`: ~15–30 minutes (emulated)
    - `linux/arm/v7`: ~20–40 minutes (emulated)

### Verify Architecture

```bash
podman inspect solve-it-mcp:amd64 | jq '.[0].Architecture'   # "amd64"
podman inspect solve-it-mcp:arm64 | jq '.[0].Architecture'   # "arm64"
podman inspect solve-it-mcp:armv7 | jq '.[0].Architecture'   # "arm"

podman run --rm solve-it-mcp:amd64 uname -m                  # x86_64
podman run --rm --platform linux/arm64 solve-it-mcp:arm64 uname -m  # aarch64
podman run --rm --platform linux/arm/v7 solve-it-mcp:armv7 uname -m # armv7l
```

### Test the Server

```bash
# Start AMD64 container
podman run --rm -d --name test-amd64 \
  -e MCP_TRANSPORT=http -e HTTP_PORT=8000 \
  -p 8001:8000 solve-it-mcp:amd64

sleep 5
curl http://localhost:8001/healthz
podman stop test-amd64

# Start ARM64 container (emulated — allow more time)
podman run --rm -d --name test-arm64 \
  -e MCP_TRANSPORT=http -e HTTP_PORT=8000 \
  -p 8002:8000 solve-it-mcp:arm64

sleep 15
curl http://localhost:8002/healthz
podman stop test-arm64
```

---

## Method 2: Docker Buildx (Multi-Platform at Once)

```bash
docker buildx create --name mcp-builder --use
docker buildx inspect --bootstrap

# Build all platforms (push to registry required for multi-platform)
docker buildx build \
  --platform linux/amd64,linux/arm64,linux/arm/v7 \
  -t 3soos3/solve-it-mcp:test-multiarch \
  -f Dockerfile \
  --push \
  .
```

---

## Method 3: Podman Manifest Lists

```bash
# Build individual architectures
podman build --platform linux/amd64 -t localhost/solve-it-mcp:amd64 .
podman build --platform linux/arm64 -t localhost/solve-it-mcp:arm64 .
podman build --platform linux/arm/v7 -t localhost/solve-it-mcp:armv7 .

# Create multi-arch manifest
podman manifest create solve-it-mcp:multiarch
podman manifest add solve-it-mcp:multiarch localhost/solve-it-mcp:amd64
podman manifest add solve-it-mcp:multiarch localhost/solve-it-mcp:arm64
podman manifest add solve-it-mcp:multiarch localhost/solve-it-mcp:armv7

# Inspect
podman manifest inspect solve-it-mcp:multiarch

# Push
podman manifest push solve-it-mcp:multiarch docker://3soos3/solve-it-mcp:test
```

---

## Full Build Verification Script

```bash
#!/bin/bash
set -e

PLATFORMS=("linux/amd64" "linux/arm64" "linux/arm/v7")
IMAGE="solve-it-mcp-test"

for PLATFORM in "${PLATFORMS[@]}"; do
    ARCH=$(echo "$PLATFORM" | sed 's|linux/||;s|/|-|g')
    echo "Building $PLATFORM..."
    podman build --platform "$PLATFORM" -t "${IMAGE}:${ARCH}" -f Dockerfile . \
      || { echo "Build failed for $PLATFORM"; exit 1; }
    echo "Build succeeded for $PLATFORM"
done

echo "All builds completed."
podman images | grep "$IMAGE"
```

---

## Troubleshooting

### "exec format error"

QEMU is not registered. Run:

```bash
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes
```

### ARM build fails with missing dependencies

Some packages need ARM-specific native build deps in the builder stage. Check the Dockerfile — the builder stage already installs `build-base libffi-dev openssl-dev cargo rust`.

### Verify QEMU status

```bash
cat /proc/sys/fs/binfmt_misc/qemu-aarch64
cat /proc/sys/fs/binfmt_misc/qemu-arm

# Test emulation directly
podman run --rm --platform linux/arm64 alpine uname -m   # aarch64
podman run --rm --platform linux/arm/v7 alpine uname -m  # armv7l
```

---

## Quick Reference

```bash
# Build
podman build --platform linux/amd64 -t solve-it-mcp:amd64 .
podman build --platform linux/arm64 -t solve-it-mcp:arm64 .
podman build --platform linux/arm/v7 -t solve-it-mcp:armv7 .

# Verify architecture
podman run --rm solve-it-mcp:amd64 uname -m
podman run --rm --platform linux/arm64 solve-it-mcp:arm64 uname -m
podman run --rm --platform linux/arm/v7 solve-it-mcp:armv7 uname -m
```
