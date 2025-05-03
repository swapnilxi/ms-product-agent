#!/bin/bash

# === Config ===
IMAGE_NAME="msproductregistryswapnil01.azurecr.io/ms-product-backend:latest"
RESOURCE_GROUP="ms-product-collabration_group"
APP_NAME="ms-product-backend"
ACR_NAME="msproductregistryswapnil01"

# === Ensure Buildx is Ready ===
echo "🔧 Ensuring Docker buildx builder exists for amd64..."
if ! docker buildx inspect amd64-builder >/dev/null 2>&1; then
  docker buildx create --use --name amd64-builder
fi
docker buildx use amd64-builder
docker buildx inspect --bootstrap

# === Build and Push Image ===
echo "🐳 Building Docker image for linux/amd64 and pushing to ACR..."
docker buildx build --platform linux/amd64 --push -t $IMAGE_NAME .

# === Login to Azure Container Registry ===
echo "🔐 Logging into Azure Container Registry..."
az acr login --name $ACR_NAME

# === Update Azure Container App ===
echo "🚀 Updating Azure Container App image and ingress..."
az containerapp update \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --image $IMAGE_NAME \
  --set configuration.ingress.external=true configuration.ingress.targetPort=8003
