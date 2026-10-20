#!/bin/bash
# X-ops Docker 镜像构建与推送脚本
# 用法：
#   ./deploy/docker-push.sh build                        # 仅构建镜像
#   ./deploy/docker-push.sh push <docker.io用户名> [tag] # 构建 + 推送
# 示例：
#   ./deploy/docker-push.sh push mydockerid latest
set -e

IMAGE_NAME="x-ops-backend"
TAG="${2:-latest}"

build_image() {
    echo "[1/3] 构建前端产物..."
    (cd frontend && npm install --registry=https://registry.npmmirror.com && npm run build)
    mkdir -p deploy/frontend-dist
    cp -r frontend/dist/* deploy/frontend-dist/

    echo "[2/3] 构建 Docker 镜像..."
    docker compose build
    echo "构建完成: $IMAGE_NAME:$TAG"
}

push_image() {
    local USERNAME="$1"
    local FULL_IMAGE="docker.io/$USERNAME/$IMAGE_NAME:$TAG"
    echo "[3/3] 登录并推送 $FULL_IMAGE ..."
    docker login docker.io
    docker tag "$IMAGE_NAME:latest" "$FULL_IMAGE"
    docker push "$FULL_IMAGE"
    echo "推送完成: $FULL_IMAGE"
    echo "他人部署: docker pull $FULL_IMAGE"
}

case "$1" in
    build)
        build_image
        ;;
    push)
        if [ -z "$2" ]; then
            echo "用法: ./deploy/docker-push.sh push <docker.io用户名> [tag]"
            exit 1
        fi
        build_image
        push_image "$2"
        ;;
    *)
        echo "用法:"
        echo "  ./deploy/docker-push.sh build"
        echo "  ./deploy/docker-push.sh push <docker.io用户名> [tag]"
        ;;
esac