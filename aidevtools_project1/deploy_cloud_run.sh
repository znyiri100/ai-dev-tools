#!/bin/bash

# Cloud Run Deployment Script
# Usage: ./deploy_cloud_run.sh [PROJECT_ID] [REGION]

PROJECT_ID=${1:-$(gcloud config get-value project)}
REGION=${2:-"us-central1"}
BACKEND_SERVICE="aidevtools-backend"
FRONTEND_SERVICE="aidevtools-frontend"

if [ -z "$PROJECT_ID" ]; then
    echo "Error: PROJECT_ID is not set. Please provide it as the first argument or run 'gcloud config set project <PROJECT_ID>'."
    exit 1
fi

echo "=================================================="
echo "Deploying to Project: $PROJECT_ID"
echo "Region: $REGION"
echo "=================================================="

# 1. Deploy Backend
echo "PROMPT: Deploy Backend Service? [y/N]"
read -r deploy_backend
if [[ "$deploy_backend" =~ ^[Yy]$ ]]; then
    echo ">>> Deploying Backend ($BACKEND_SERVICE) from ./backend ..."
    
    # Note: We do not set secrets here to avoid command history leaks.
    # Users should set secrets via Secret Manager or the Cloud Console for production.
    # For now, we deploy and rely on env vars being set later or via .env file logic if added.
    gcloud run deploy $BACKEND_SERVICE \
        --project $PROJECT_ID \
        --region $REGION \
        --source ./backend \
        --allow-unauthenticated \
        --port 8080
    
    # Capture URL
    BACKEND_URL=$(gcloud run services describe $BACKEND_SERVICE --project $PROJECT_ID --region $REGION --format 'value(status.url)')
    echo ">>> Backend deployed at: $BACKEND_URL"
else
    echo "Skipping Backend deployment."
    # Try to fetch existing URL if skipped
    BACKEND_URL=$(gcloud run services describe $BACKEND_SERVICE --project $PROJECT_ID --region $REGION --format 'value(status.url)' 2>/dev/null || echo "")
fi

# 2. Deploy Frontend
echo "PROMPT: Deploy Frontend Service? [y/N]"
read -r deploy_frontend
if [[ "$deploy_frontend" =~ ^[Yy]$ ]]; then
    if [ -z "$BACKEND_URL" ]; then
        echo "WARNING: Backend URL not found or deployment skipped. You may need to manually configure API_BASE_URL."
        echo "Enter Backend URL (or press Enter to skip env var setting):"
        read -r input_url
        BACKEND_URL=${input_url:-$BACKEND_URL}
    fi

    echo ">>> Deploying Frontend ($FRONTEND_SERVICE) from ./frontend_nicegui ..."
    
    # Copy docs folder to frontend directory for build context
    echo ">>> Copying ./docs to ./frontend_nicegui/docs for deployment..."
    cp -r ./docs ./frontend_nicegui/docs

    deploy_cmd="gcloud run deploy $FRONTEND_SERVICE \
        --project $PROJECT_ID \
        --region $REGION \
        --source ./frontend_nicegui \
        --allow-unauthenticated \
        --port 8080"

    # Only set API_BASE_URL if we have it
    if [ ! -z "$BACKEND_URL" ]; then
        deploy_cmd="$deploy_cmd --set-env-vars API_BASE_URL=$BACKEND_URL"
    fi

    echo "Running: $deploy_cmd"
    eval $deploy_cmd

    # Clean up copied docs
    echo ">>> Removing ./frontend_nicegui/docs..."
    rm -rf ./frontend_nicegui/docs
    
    FRONTEND_URL=$(gcloud run services describe $FRONTEND_SERVICE --project $PROJECT_ID --region $REGION --format 'value(status.url)')
    echo ">>> Frontend deployed at: $FRONTEND_URL"
else
    echo "Skipping Frontend deployment."
fi

echo "=================================================="
echo "Deployment logic finished."
echo "IMPORTANT: Ensure your database environment variables (POSTGRES_HOST, etc.) are set for the Backend service!"
echo "Use: gcloud run services update $BACKEND_SERVICE --update-env-vars KEY=VALUE,..."
echo "=================================================="
