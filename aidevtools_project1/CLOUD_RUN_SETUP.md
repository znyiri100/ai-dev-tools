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
./deploy_cloud_run.sh [PROJECT_ID] [REGION]
```
*   `PROJECT_ID`: Your Google Cloud Project ID (defaults to current config).
*   `REGION`: e.g., `us-central1` (default).

Run this script to build and deploy your containers. It will output the URLs for your Backend and Frontend.

## 2. Configuration (Environment Variables)

You can configure your services using either **Plain Environment Variables** (easiest) or **Google Secret Manager** (recommended for production).

### Option A: Google Secret Manager (Secure)

Using Secret Manager ensures your credentials (API keys, DB passwords) are encrypted and not visible in the Cloud Run console.

#### 1. Create Secrets
Run the following commands to create secrets in your project. Replace `[VALUE]` with your actual secrets.

```bash
# Database Credentials (Supabase)
printf "[VALUE]" | gcloud secrets create postgres-host --data-file=-
printf "[VALUE]" | gcloud secrets create postgres-user --data-file=-
printf "[VALUE]" | gcloud secrets create postgres-password --data-file=-
printf "[VALUE]" | gcloud secrets create postgres-db --data-file=-

# API Keys
printf "[VALUE]" | gcloud secrets create youtube-api-key --data-file=-
printf "[VALUE]" | gcloud secrets create google-api-key --data-file=-
```

#### 2. Grant Access
Give your Cloud Run service account permission to access these secrets.
(The default compute service account is usually `[PROJECT_NUMBER]-compute@developer.gserviceaccount.com`)

```bash
PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format="value(projectNumber)")
SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/secretmanager.secretAccessor"
```

#### 3. Update Backend Service
Map the secrets to environment variables in your Backend service.

```bash
gcloud run services update aidevtools-backend \
    --region us-central1 \
    --update-secrets POSTGRES_HOST=postgres-host:latest,POSTGRES_USER=postgres-user:latest,POSTGRES_PASSWORD=postgres-password:latest,POSTGRES_DATABASE=postgres-db:latest,YOUTUBE_API_KEY=youtube-api-key:latest
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
