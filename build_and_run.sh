#!/bin/bash
set -e
IMAGE_NAME=thucs2pl-app
IMAGE_PREFIX=ccr.ccs.tencentyun.com/thucs2/
CONTAINER_NAME=thucs2pl-container
PORT=8000
TAG=$(git rev-parse --short=8 HEAD)
FULL_IMAGE_NAME="$IMAGE_PREFIX$IMAGE_NAME:$TAG"

echo "Building Docker image with tag $TAG..."
docker build -t $FULL_IMAGE_NAME .

echo "Pushing Docker image to remote registry..."
docker push $FULL_IMAGE_NAME
