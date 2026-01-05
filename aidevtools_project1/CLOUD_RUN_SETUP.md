# Cloud Run Setup & Deployment Guide

This project is configured for deployment on **Google Cloud Run**.

## Prerequisites
- Google Cloud CLI (`gcloud`) installed and authenticated (`gcloud auth login`).
- A Google Cloud Project created and billing enabled.
- **Secret Manager API** enabled:
  ```bash
  gcloud services enable secretmanager.googleapis.com
  ```

## 1. Quick Deploy Script
We have provided a helper script to deploy both services:

```bash
PROJECT_ID=$(gcloud config get-value project)
REGION=us-central1
./deploy_cloud_run.sh $PROJECT_ID $REGION
```
*   `PROJECT_ID`: Your Google Cloud Project ID (defaults to current config).
*   `REGION`: e.g., `us-central1` (default).

Run this script to build and deploy your containers. It will output the URLs for your Backend and Frontend.

## 2. Configuration (Environment Variables)

You can configure your services using either **Plain Environment Variables** (easiest) or **Google Secret Manager** (recommended for production).

### Option A: Google Secret Manager (Secure)

Using Secret Manager ensures your credentials (API keys, DB passwords) are encrypted and not visible in the Cloud Run console.

#### 1. Setup Script

First, export your secrets as environment variables in your current shell (e.g. `export POSTGRES_PASSWORD=...`).

Then run the following commands to create the secrets, grant access to the Cloud Run service account, and update the backend service:

```bash
printf "$POSTGRES_HOST" | gcloud secrets create postgres-host --data-file=-
printf "$POSTGRES_USER" | gcloud secrets create postgres-user --data-file=-
printf "$POSTGRES_PASSWORD" | gcloud secrets create postgres-password --data-file=-
printf "$POSTGRES_DATABASE" | gcloud secrets create postgres-db --data-file=-
printf "$YOUTUBE_API_KEY" | gcloud secrets create youtube-api-key --data-file=-
printf "$GOOGLE_API_KEY" | gcloud secrets create google-api-key --data-file=-
printf "$HTTP_PROXY_USER" | gcloud secrets create http-proxy-user --data-file=-
printf "$HTTP_PROXY_PASS" | gcloud secrets create http-proxy-pass --data-file=-

PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format="value(projectNumber)")
SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/secretmanager.secretAccessor"

gcloud run services update aidevtools-backend \
    --region us-central1 \
    --update-secrets POSTGRES_HOST=postgres-host:latest,POSTGRES_USER=postgres-user:latest,POSTGRES_PASSWORD=postgres-password:latest,POSTGRES_DATABASE=postgres-db:latest
gcloud run services update aidevtools-backend --region us-central1 --update-secrets YOUTUBE_API_KEY=youtube-api-key:latest
gcloud run services update aidevtools-backend --region us-central1 --update-secrets GOOGLE_API_KEY=google-api-key:latest
gcloud run services update aidevtools-backend --region us-central1 --update-secrets HTTP_PROXY_USER=http-proxy-user:latest
gcloud run services update aidevtools-backend --region us-central1 --update-secrets HTTP_PROXY_PASS=http-proxy-pass:latest
```

### Option B: Plain Environment Variables (Quick)

If you strictly want to test quickly and don't mind secrets being visible in the Cloud Console configuration:

```bash
gcloud run services update aidevtools-backend \
  --region us-central1 \
  --update-env-vars POSTGRES_HOST=db.example.com,POSTGRES_USER=postgres,POSTGRES_PASSWORD=secret,POSTGRES_DATABASE=postgres,YOUTUBE_API_KEY=your_key
```

---

### Frontend Configuration
The frontend mainly needs to know where the backend is.

```bash
gcloud run services update aidevtools-frontend \
  --region us-central1 \
  --update-env-vars API_BASE_URL=https://aidevtools-backend-xyz-uc.a.run.app
```
