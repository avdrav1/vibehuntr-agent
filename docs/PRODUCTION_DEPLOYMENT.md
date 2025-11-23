# Production Deployment Guide

This guide covers deploying the React + FastAPI Vibehuntr application to Google Cloud Platform (GCP).

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Production Setup                         │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Cloud CDN + Cloud Storage (Frontend)                  │ │
│  │  - Static React build (HTML, JS, CSS)                  │ │
│  │  - HTTPS with custom domain                            │ │
│  │  - Global edge caching                                 │ │
│  └────────────────┬───────────────────────────────────────┘ │
│                   │ HTTPS API calls                          │
│  ┌────────────────▼───────────────────────────────────────┐ │
│  │  Cloud Run (Backend)                                   │ │
│  │  - FastAPI application                                 │ │
│  │  - Auto-scaling containers                             │ │
│  │  - HTTPS endpoint                                      │ │
│  │  - Environment variables from Secret Manager          │ │
│  └────────────────┬───────────────────────────────────────┘ │
│                   │                                          │
│  ┌────────────────▼───────────────────────────────────────┐ │
│  │  Vertex AI / ADK Agent                                 │ │
│  │  - Agent logic and tools                               │ │
│  │  - Session management                                  │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

- GCP Project with billing enabled
- `gcloud` CLI installed and authenticated
- Docker installed (for backend deployment)
- Node.js 18+ and npm (for frontend build)
- Required GCP APIs enabled:
  - Cloud Run API
  - Cloud Storage API
  - Cloud Build API
  - Secret Manager API
  - Vertex AI API

### Enable Required APIs

```bash
gcloud services enable \
  run.googleapis.com \
  storage.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  aiplatform.googleapis.com
```

## Part 1: Backend Deployment (Cloud Run)

### Step 1: Prepare Backend for Production

Create a `Dockerfile` in the `backend/` directory:

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy parent app directory for agent code
COPY ../app /app/app

# Expose port (Cloud Run uses PORT env var)
ENV PORT=8080
EXPOSE 8080

# Run the application
CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
```

Create a `.dockerignore` file:

```
# backend/.dockerignore
__pycache__
*.pyc
*.pyo
*.pyd
.pytest_cache
.coverage
htmlcov
dist
build
*.egg-info
.env
.venv
venv
tests
```

### Step 2: Configure Environment Variables

Create production environment configuration in Secret Manager:

```bash
# Set your GCP project
export PROJECT_ID="your-project-id"
export REGION="us-central1"

# Create secrets for sensitive values
echo -n "your-gemini-api-key" | gcloud secrets create GEMINI_API_KEY --data-file=-
echo -n "your-google-places-api-key" | gcloud secrets create GOOGLE_PLACES_API_KEY --data-file=-

# Create a secret for the full .env file
gcloud secrets create backend-env-file --data-file=backend/.env.production
```

Create `backend/.env.production` with production values:

```env
# backend/.env.production
GEMINI_API_KEY=${GEMINI_API_KEY}
GOOGLE_PLACES_API_KEY=${GOOGLE_PLACES_API_KEY}
PROJECT_ID=your-project-id
LOCATION=us-central1
CORS_ORIGINS=https://your-domain.com
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### Step 3: Build and Deploy Backend to Cloud Run

```bash
# Navigate to backend directory
cd backend

# Build and deploy using Cloud Build
gcloud run deploy vibehuntr-backend \
  --source . \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --set-env-vars PROJECT_ID=${PROJECT_ID},LOCATION=${REGION},ENVIRONMENT=production \
  --set-secrets GEMINI_API_KEY=GEMINI_API_KEY:latest,GOOGLE_PLACES_API_KEY=GOOGLE_PLACES_API_KEY:latest \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 0 \
  --port 8080

# Get the service URL
gcloud run services describe vibehuntr-backend --region ${REGION} --format 'value(status.url)'
```

### Step 4: Configure CORS for Production

Update `backend/app/core/config.py` to use environment-based CORS:

```python
# backend/app/core/config.py
import os
from typing import List

class Settings:
    PROJECT_ID: str = os.getenv("PROJECT_ID", "")
    LOCATION: str = os.getenv("LOCATION", "us-central1")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # CORS configuration
    CORS_ORIGINS: List[str] = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://localhost:3000"
    ).split(",")
    
    # API Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GOOGLE_PLACES_API_KEY: str = os.getenv("GOOGLE_PLACES_API_KEY", "")

settings = Settings()
```

### Step 5: Set Up Custom Domain (Optional)

```bash
# Map custom domain to Cloud Run service
gcloud run domain-mappings create \
  --service vibehuntr-backend \
  --domain api.your-domain.com \
  --region ${REGION}

# Follow instructions to configure DNS records
```

### Step 6: Configure Health Checks

Ensure your FastAPI app has a health endpoint (already in `backend/app/main.py`):

```python
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

## Part 2: Frontend Deployment (Cloud Storage + CDN)

### Step 1: Create Cloud Storage Bucket

```bash
# Create bucket for frontend hosting
export BUCKET_NAME="${PROJECT_ID}-vibehuntr-frontend"

gsutil mb -p ${PROJECT_ID} -c STANDARD -l ${REGION} gs://${BUCKET_NAME}

# Make bucket publicly readable
gsutil iam ch allUsers:objectViewer gs://${BUCKET_NAME}

# Configure bucket for website hosting
gsutil web set -m index.html -e index.html gs://${BUCKET_NAME}
```

### Step 2: Configure Frontend for Production

Create `frontend/.env.production`:

```env
# frontend/.env.production
VITE_API_URL=https://vibehuntr-backend-xxxxx-uc.a.run.app
VITE_ENVIRONMENT=production
```

Update `frontend/vite.config.ts` for production builds:

```typescript
// frontend/vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: process.env.VITE_API_URL || 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
        }
      }
    }
  }
})
```

Update `frontend/src/services/api.ts` to use environment variable:

```typescript
// frontend/src/services/api.ts
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Rest of the file remains the same
```

### Step 3: Build and Deploy Frontend

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm ci

# Build for production
npm run build

# Deploy to Cloud Storage
gsutil -m rsync -r -d dist/ gs://${BUCKET_NAME}

# Set cache control headers
gsutil -m setmeta -h "Cache-Control:public, max-age=31536000" gs://${BUCKET_NAME}/**/*.js
gsutil -m setmeta -h "Cache-Control:public, max-age=31536000" gs://${BUCKET_NAME}/**/*.css
gsutil -m setmeta -h "Cache-Control:public, max-age=3600" gs://${BUCKET_NAME}/index.html
```

### Step 4: Set Up Cloud CDN (Optional but Recommended)

```bash
# Create a backend bucket
gcloud compute backend-buckets create vibehuntr-frontend-backend \
  --gcs-bucket-name=${BUCKET_NAME} \
  --enable-cdn

# Reserve a static IP
gcloud compute addresses create vibehuntr-frontend-ip \
  --global

# Get the IP address
gcloud compute addresses describe vibehuntr-frontend-ip \
  --global \
  --format="value(address)"

# Create URL map
gcloud compute url-maps create vibehuntr-frontend-url-map \
  --default-backend-bucket=vibehuntr-frontend-backend

# Create HTTP(S) target proxy
gcloud compute target-https-proxies create vibehuntr-frontend-https-proxy \
  --url-map=vibehuntr-frontend-url-map \
  --ssl-certificates=your-ssl-cert

# Create forwarding rule
gcloud compute forwarding-rules create vibehuntr-frontend-https-rule \
  --address=vibehuntr-frontend-ip \
  --global \
  --target-https-proxy=vibehuntr-frontend-https-proxy \
  --ports=443
```

### Step 5: Configure SSL Certificate

```bash
# Option 1: Use Google-managed SSL certificate
gcloud compute ssl-certificates create vibehuntr-ssl-cert \
  --domains=your-domain.com \
  --global

# Option 2: Upload your own certificate
gcloud compute ssl-certificates create vibehuntr-ssl-cert \
  --certificate=path/to/cert.pem \
  --private-key=path/to/key.pem \
  --global
```

### Step 6: Configure DNS

Point your domain to the reserved IP address:

```
Type: A
Name: @ (or subdomain)
Value: [IP from step 4]
TTL: 3600
```

## Part 3: Environment Configuration

### Backend Environment Variables

Required environment variables for Cloud Run:

| Variable | Description | Example |
|----------|-------------|---------|
| `PROJECT_ID` | GCP Project ID | `my-project-123` |
| `LOCATION` | GCP Region | `us-central1` |
| `ENVIRONMENT` | Environment name | `production` |
| `CORS_ORIGINS` | Allowed origins (comma-separated) | `https://your-domain.com` |
| `GEMINI_API_KEY` | Gemini API key (from Secret Manager) | `secret:latest` |
| `GOOGLE_PLACES_API_KEY` | Google Places API key (from Secret Manager) | `secret:latest` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Frontend Environment Variables

Required environment variables for frontend build:

| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API URL | `https://api.your-domain.com` |
| `VITE_ENVIRONMENT` | Environment name | `production` |

### Secret Management Best Practices

1. **Never commit secrets to version control**
2. **Use Secret Manager for sensitive values**
3. **Rotate secrets regularly**
4. **Use different secrets for different environments**
5. **Grant minimal IAM permissions**

```bash
# Grant Cloud Run service account access to secrets
export SERVICE_ACCOUNT=$(gcloud run services describe vibehuntr-backend \
  --region ${REGION} \
  --format 'value(spec.template.spec.serviceAccountName)')

gcloud secrets add-iam-policy-binding GEMINI_API_KEY \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding GOOGLE_PLACES_API_KEY \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/secretmanager.secretAccessor"
```

## Part 4: CI/CD Pipeline (Optional)

### GitHub Actions Workflow

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches:
      - main

env:
  PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}
  REGION: us-central1
  BACKEND_SERVICE: vibehuntr-backend
  FRONTEND_BUCKET: ${{ secrets.GCP_PROJECT_ID }}-vibehuntr-frontend

jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - id: auth
        uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}
      
      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v1
      
      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy ${{ env.BACKEND_SERVICE }} \
            --source ./backend \
            --platform managed \
            --region ${{ env.REGION }} \
            --allow-unauthenticated

  deploy-frontend:
    runs-on: ubuntu-latest
    needs: deploy-backend
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      
      - name: Build
        env:
          VITE_API_URL: ${{ secrets.VITE_API_URL }}
        run: |
          cd frontend
          npm run build
      
      - id: auth
        uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}
      
      - name: Deploy to Cloud Storage
        run: |
          gsutil -m rsync -r -d frontend/dist/ gs://${{ env.FRONTEND_BUCKET }}
```

## Part 5: Monitoring and Logging

### Enable Cloud Logging

Logs are automatically collected from Cloud Run. View them:

```bash
# View backend logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=vibehuntr-backend" \
  --limit 50 \
  --format json

# Stream logs in real-time
gcloud alpha logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=vibehuntr-backend"
```

### Set Up Monitoring Dashboard

1. Go to Cloud Console > Monitoring > Dashboards
2. Create a new dashboard
3. Add charts for:
   - Request count
   - Request latency
   - Error rate
   - Container CPU utilization
   - Container memory utilization

### Set Up Alerts

```bash
# Create alert for high error rate
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="High Error Rate" \
  --condition-display-name="Error rate > 5%" \
  --condition-threshold-value=0.05 \
  --condition-threshold-duration=300s
```

## Part 6: Rollback Procedures

### Backend Rollback

```bash
# List revisions
gcloud run revisions list \
  --service vibehuntr-backend \
  --region ${REGION}

# Rollback to previous revision
gcloud run services update-traffic vibehuntr-backend \
  --to-revisions REVISION_NAME=100 \
  --region ${REGION}
```

### Frontend Rollback

```bash
# Keep previous builds
mv frontend/dist frontend/dist.backup

# Restore previous build
gsutil -m rsync -r -d frontend/dist.backup/ gs://${BUCKET_NAME}
```

## Part 7: Performance Optimization

### Backend Optimizations

1. **Enable Cloud Run concurrency**:
   ```bash
   gcloud run services update vibehuntr-backend \
     --concurrency 80 \
     --region ${REGION}
   ```

2. **Configure minimum instances** (reduces cold starts):
   ```bash
   gcloud run services update vibehuntr-backend \
     --min-instances 1 \
     --region ${REGION}
   ```

3. **Enable HTTP/2**:
   Already enabled by default on Cloud Run

### Frontend Optimizations

1. **Enable compression** in Cloud Storage
2. **Use CDN caching** (configured in Step 4)
3. **Optimize bundle size**:
   ```bash
   npm run build -- --analyze
   ```

## Part 8: Security Checklist

- [ ] HTTPS enabled for both frontend and backend
- [ ] CORS properly configured with specific origins
- [ ] Secrets stored in Secret Manager, not in code
- [ ] IAM permissions follow principle of least privilege
- [ ] Cloud Run service uses custom service account
- [ ] API rate limiting configured
- [ ] Input validation on all endpoints
- [ ] Security headers configured (CSP, HSTS, etc.)
- [ ] Regular dependency updates
- [ ] Vulnerability scanning enabled

## Part 9: Cost Optimization

### Backend (Cloud Run)

- Use minimum instances = 0 for development
- Set maximum instances to prevent runaway costs
- Monitor request patterns and adjust CPU/memory allocation

### Frontend (Cloud Storage + CDN)

- Enable CDN caching to reduce egress costs
- Use lifecycle policies to delete old versions
- Compress assets before uploading

### Estimated Monthly Costs

- Cloud Run (low traffic): $5-20/month
- Cloud Storage: $1-5/month
- Cloud CDN: $5-50/month (depending on traffic)
- **Total**: ~$10-75/month for low to moderate traffic

## Troubleshooting

### Backend Issues

**Issue**: Service won't start
```bash
# Check logs
gcloud logging read "resource.type=cloud_run_revision" --limit 50

# Check service status
gcloud run services describe vibehuntr-backend --region ${REGION}
```

**Issue**: CORS errors
- Verify CORS_ORIGINS environment variable includes your frontend domain
- Check that preflight requests are handled correctly

### Frontend Issues

**Issue**: 404 errors on refresh
- Ensure `gsutil web set` was run with `-e index.html`
- Configure URL rewriting in Cloud CDN

**Issue**: API calls failing
- Verify VITE_API_URL is set correctly
- Check CORS configuration on backend
- Verify backend service is running

## Additional Resources

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud Storage Static Website Hosting](https://cloud.google.com/storage/docs/hosting-static-website)
- [Cloud CDN Documentation](https://cloud.google.com/cdn/docs)
- [Secret Manager Documentation](https://cloud.google.com/secret-manager/docs)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)
- [Vite Production Build](https://vitejs.dev/guide/build.html)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review Cloud Run logs
3. Check the GitHub repository issues
4. Contact the development team
