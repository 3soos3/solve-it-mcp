#!/usr/bin/env bash
# build-and-push.sh - Local build and push script for SOLVE-IT MCP Docker images
# Builds multi-architecture images and pushes to Docker Hub
#
# Usage:
#   ./scripts/build-and-push.sh [OPTIONS]
#
# Options:
#   --no-push         Build only, don't push to registry
#   --platform ARCH   Build for specific platform (default: linux/amd64,linux/arm64,linux/arm/v7)
#   --tag TAG         Additional tag to apply (can be used multiple times)
#   --latest          Tag as 'latest' (default: no)
#   --help            Show this help message
#
# Examples:
#   # Build and push with default tags
#   ./scripts/build-and-push.sh
#
#   # Build only for local testing (no push)
#   ./scripts/build-and-push.sh --no-push
#
#   # Build for specific architecture
#   ./scripts/build-and-push.sh --platform linux/amd64 --no-push
#
#   # Build and tag as latest
#   ./scripts/build-and-push.sh --latest

set -euo pipefail

# Configuration
DOCKER_REPO="3soos3/solve-it-mcp"
PLATFORMS="linux/amd64,linux/arm64,linux/arm/v7"
PUSH=true
TAG_LATEST=false
ADDITIONAL_TAGS=()

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-push)
            PUSH=false
            shift
            ;;
        --platform)
            PLATFORMS="$2"
            shift 2
            ;;
        --tag)
            ADDITIONAL_TAGS+=("$2")
            shift 2
            ;;
        --latest)
            TAG_LATEST=true
            shift
            ;;
        --help)
            grep '^#' "$0" | sed 's/^# \?//'
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Run with --help for usage information"
            exit 1
            ;;
    esac
done

# Get git information
GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
GIT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
VERSION="stable"

echo "========================================="
echo "SOLVE-IT MCP Docker Build Script"
echo "========================================="
echo "Repository:  ${DOCKER_REPO}"
echo "Platforms:   ${PLATFORMS}"
echo "Git Commit:  ${GIT_COMMIT}"
echo "Git Branch:  ${GIT_BRANCH}"
echo "Build Date:  ${BUILD_DATE}"
echo "Version:     ${VERSION}"
echo "Push:        ${PUSH}"
echo "========================================="

# Ensure buildx is available
if ! docker buildx version >/dev/null 2>&1; then
    echo "ERROR: docker buildx is not available"
    echo "Please install Docker with buildx support"
    exit 1
fi

# Create builder if it doesn't exist
BUILDER_NAME="solveit-mcp-builder"
if ! docker buildx inspect "${BUILDER_NAME}" >/dev/null 2>&1; then
    echo "Creating buildx builder: ${BUILDER_NAME}"
    docker buildx create --name "${BUILDER_NAME}" --use
else
    echo "Using existing buildx builder: ${BUILDER_NAME}"
    docker buildx use "${BUILDER_NAME}"
fi

# Build tag arguments
TAG_ARGS=()
TAG_ARGS+=("--tag" "${DOCKER_REPO}:${VERSION}")
TAG_ARGS+=("--tag" "${DOCKER_REPO}:sha-${GIT_COMMIT}")

if [ "${TAG_LATEST}" = true ]; then
    TAG_ARGS+=("--tag" "${DOCKER_REPO}:latest")
fi

for tag in "${ADDITIONAL_TAGS[@]}"; do
    TAG_ARGS+=("--tag" "${DOCKER_REPO}:${tag}")
done

# Build arguments
BUILD_ARGS=(
    "--platform" "${PLATFORMS}"
    "--build-arg" "BUILD_DATE=${BUILD_DATE}"
    "--build-arg" "VCS_REF=${GIT_COMMIT}"
    "--build-arg" "VERSION=${VERSION}"
    "--build-arg" "SOLVE_IT_SOURCE=github"
    "--build-arg" "SOLVE_IT_VERSION=main"
)

# Output argument (push or load)
if [ "${PUSH}" = true ]; then
    BUILD_ARGS+=("--push")
    echo "Building and pushing to Docker Hub..."
else
    # Note: --load only works with single platform
    if [[ "${PLATFORMS}" == *","* ]]; then
        echo "WARNING: Multi-platform build without push (images will not be loaded locally)"
        echo "To test locally, use: --platform linux/amd64 --no-push"
    else
        BUILD_ARGS+=("--load")
    fi
    echo "Building locally (no push)..."
fi

# Build the image
echo ""
echo "Running docker buildx build..."
echo ""

docker buildx build \
    "${BUILD_ARGS[@]}" \
    "${TAG_ARGS[@]}" \
    -f Dockerfile \
    .

echo ""
echo "========================================="
echo "Build completed successfully!"
echo "========================================="

if [ "${PUSH}" = true ]; then
    echo "Images pushed to Docker Hub:"
    for arg in "${TAG_ARGS[@]}"; do
        if [[ "${arg}" == "${DOCKER_REPO}:"* ]]; then
            echo "  - ${arg}"
        fi
    done
else
    echo "Images built locally (not pushed)"
fi

echo ""
echo "To test the image:"
echo "  docker run -p 8000:8000 ${DOCKER_REPO}:${VERSION}"
echo ""
