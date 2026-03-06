#!/bin/bash
# ════════════════════════════════════════════════════
# deploy.sh — PA Studio → Google Cloud Run
# ════════════════════════════════════════════════════
set -e

PROJECT_ID="YOUR_PROJECT_ID"       # ← เปลี่ยนเป็น project จริง
SERVICE_NAME="pa-studio"
REGION="asia-southeast1"
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "🔨 Building image..."
gcloud builds submit --tag ${IMAGE} --project ${PROJECT_ID}

echo "🚀 Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE} \
  --platform managed \
  --region ${REGION} \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --concurrency 10 \
  --min-instances 0 \
  --max-instances 5 \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
  --allow-unauthenticated \
  --project ${PROJECT_ID}

echo "✅ Deploy สำเร็จ!"
gcloud run services describe ${SERVICE_NAME} \
  --region ${REGION} --format="value(status.url)"
