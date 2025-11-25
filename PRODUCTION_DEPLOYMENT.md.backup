# Production Deployment Guide

This guide covers deploying the Vibehuntr agent to Google Cloud Platform (GCP) for production use.

## Architecture Overview

The production deployment consists of:
- **Backend**: FastAPI application on Cloud Run (auto-scaling, serverless)
- **Frontend**: React SPA hosted on Cloud Storage (static hosting)
- **Secrets**: API keys stored in Secret Manager
- **Monitoring**: Cloud Logging, Cloud Trace (OpenTelemetry)

## Prerequisites

### 1. GCP Project Setup

```bash
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="us-central1"
```

### 2. Required API Keys

You'll need:
- **Gemini API Key**: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
- **Google Places API Key**: Get from [GCP Console](https://console.cloud.google.com/apis/credentials)

### 3. Install Required Tools

```bash
# gcloud CLI
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Node.js and npm (if not installed)
# Visit: https://nodejs.org/
```

**Installation Links**:
- [gcloud CLI Installation](https://cloud.google.com/sdk/docs/install)
- [uv Installation Guide](https://docs.astral.sh/uv/getting-started/installation/)
- [Node.js Downloads](https://nodejs.org/)

### 4. Authenticate with GCP

```bash
gcloud auth login
gcloud config set project $GCP_PROJECT_ID
gcloud auth application-default login
```

## Quick Deploy (Automated)

The fastest way to deploy is using the automated script:

```bash
# Set your project ID
export GCP_PROJECT_ID="your-project-id"

# Create secrets (first time only)
echo "your-gemini-api-key" | gcloud secrets create GEMINI_API_KEY --data-file=-
echo "your-places-api-key" | gcloud secrets create GOOGLE_PLACES_API_KEY --data-file=-

# Grant Cloud Run access to secrets
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:$(gcloud projects describe $GCP_PROJECT_ID --format='value(projectNumber)')-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Deploy everything
chmod +x scripts/deploy-production.sh
./scripts/deploy-production.sh
```

The script will:
1. Enable required GCP APIs
2. Deploy backend to Cloud Run
3. Build and deploy frontend to Cloud Storage
4. Configure CORS and caching
5. Verify deployment health

## Manual Deployment Steps

If you prefer to deploy manually or need more control:

### 1. Enable Required APIs

```bash
gcloud services enable \
  run.googleapis.com \
  storage.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  aiplatform.googleapis.com \
  --project=$GCP_PROJECT_ID
```

### 2. Create Secrets in Secret Manager

```bash
# Create Gemini API key secret
echo "your-gemini-api-key" | gcloud secrets create GEMINI_API_KEY \
  --data-file=- \
  --replication-policy="automatic" \
  --project=$GCP_PROJECT_ID

# Create Google Places API key secret
echo "your-places-api-key" | gcloud secrets create GOOGLE_PLACES_API_KEY \
  --data-file=- \
  --replication-policy="automatic" \
  --project=$GCP_PROJECT_ID

# Grant Cloud Run service account access to secrets
PROJECT_NUMBER=$(gcloud projects describe $GCP_PROJECT_ID --format='value(projectNumber)')
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### 3. Deploy Backend to Cloud Run

Cloud Run will automatically build from source using buildpacks (no Dockerfile needed):

```bash
cd backend

gcloud run deploy vibehuntr-backend \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars PROJECT_ID=$GCP_PROJECT_ID,LOCATION=us-central1,ENVIRONMENT=production \
  --set-secrets GEMINI_API_KEY=GEMINI_API_KEY:latest,GOOGLE_PLACES_API_KEY=GOOGLE_PLACES_API_KEY:latest \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 0 \
  --port 8080 \
  --project=$GCP_PROJECT_ID

cd ..
```

**Note**: Cloud Run uses Google Cloud Buildpacks to automatically detect Python and build your application. It will:
- Detect `requirements.txt`
- Install dependencies with pip
- Run the application with gunicorn (detected from FastAPI)

### 4. Get Backend URL

```bash
export BACKEND_URL=$(gcloud run services describe vibehuntr-backend \
  --region us-central1 \
  --format 'value(status.url)' \
  --project=$GCP_PROJECT_ID)

echo "Backend deployed at: $BACKEND_URL"
```

### 5. Update Backend CORS Settings

Update `backend/app/core/config.py` to include your production frontend URL in CORS origins, then redeploy:

```python
# In production, add your frontend URL
cors_origins: str = "https://storage.googleapis.com,https://your-custom-domain.com"
```

### 6. Build and Deploy Frontend

```bash
cd frontend

# Set backend URL for build
export VITE_API_URL=$BACKEND_URL

# Install dependencies and build
npm ci
npm run build

# Create Cloud Storage bucket (first time only)
gsutil mb -p $GCP_PROJECT_ID -c STANDARD -l us-central1 gs://$GCP_PROJECT_ID-vibehuntr-frontend

# Make bucket publicly readable
gsutil iam ch allUsers:objectViewer gs://$GCP_PROJECT_ID-vibehuntr-frontend

# Configure bucket for website hosting
gsutil web set -m index.html -e index.html gs://$GCP_PROJECT_ID-vibehuntr-frontend

# Upload built files
gsutil -m rsync -r -d dist/ gs://$GCP_PROJECT_ID-vibehuntr-frontend

# Set cache control headers for optimal performance
gsutil -m setmeta -h "Cache-Control:public, max-age=31536000, immutable" "gs://$GCP_PROJECT_ID-vibehuntr-frontend/assets/**" || true
gsutil -m setmeta -h "Cache-Control:public, max-age=3600" "gs://$GCP_PROJECT_ID-vibehuntr-frontend/index.html"

cd ..
```

### 7. Access Your Application

```bash
echo "Frontend URL: https://storage.googleapis.com/$GCP_PROJECT_ID-vibehuntr-frontend/index.html"
echo "Backend URL: $BACKEND_URL"
echo "API Docs: $BACKEND_URL/docs"
echo "Health Check: $BACKEND_URL/health"
```

## Production Configuration

### Backend Environment Variables

These are configured in Cloud Run via `--set-env-vars` and `--set-secrets`:

| Variable | Source | Description |
|----------|--------|-------------|
| `PROJECT_ID` | Environment | Your GCP project ID |
| `LOCATION` | Environment | GCP region (e.g., us-central1) |
| `ENVIRONMENT` | Environment | Set to "production" |
| `GEMINI_API_KEY` | Secret Manager | Gemini API key for LLM |
| `GOOGLE_PLACES_API_KEY` | Secret Manager | Google Places API key |

### Frontend Environment Variables

Set during build time (before `npm run build`):

| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_API_URL` | Backend Cloud Run URL | https://vibehuntr-backend-xxx.run.app |

### CORS Configuration

The backend automatically configures CORS based on the `ENVIRONMENT` variable:

- **Development**: Allows `localhost:5173`, `localhost:3000`
- **Production**: Uses `CORS_ORIGINS` environment variable

To add your production frontend URL:

```bash
# Update Cloud Run service with CORS origins
gcloud run services update vibehuntr-backend \
  --region us-central1 \
  --update-env-vars CORS_ORIGINS="https://storage.googleapis.com,https://your-domain.com"
```

Or update `backend/app/core/config.py` and redeploy.

## Monitoring and Observability

### View Logs

```bash
# Stream backend logs
gcloud run logs tail vibehuntr-backend --region us-central1

# View recent logs
gcloud run logs read vibehuntr-backend --region us-central1 --limit 50

# Filter by severity
gcloud run logs read vibehuntr-backend --region us-central1 --log-filter="severity>=ERROR"
```

### Cloud Console Monitoring

1. **Cloud Run Metrics**: [Cloud Run Console](https://console.cloud.google.com/run)
   - Request count, latency, error rate
   - CPU and memory utilization
   - Instance count and scaling

2. **Cloud Trace**: [Trace Console](https://console.cloud.google.com/traces)
   - Request traces with OpenTelemetry
   - Latency analysis
   - Service dependencies

3. **Cloud Logging**: [Logging Console](https://console.cloud.google.com/logs)
   - Structured logs
   - Log-based metrics
   - Error reporting

### Health Checks

```bash
# Check backend health
curl $BACKEND_URL/health

# Check API documentation
curl $BACKEND_URL/docs

# Test a simple request
curl -X POST $BACKEND_URL/api/sessions
```

## Custom Domain Setup (Optional)

For a custom domain like `vibehuntr.yourdomain.com`:

### 1. Set up Cloud Load Balancer

```bash
# Reserve a static IP
gcloud compute addresses create vibehuntr-ip --global

# Get the IP address
gcloud compute addresses describe vibehuntr-ip --global --format="value(address)"
```

### 2. Create SSL Certificate

```bash
# Create managed SSL certificate
gcloud compute ssl-certificates create vibehuntr-cert \
  --domains=vibehuntr.yourdomain.com \
  --global
```

### 3. Configure Load Balancer

```bash
# Create backend service pointing to Cloud Run
gcloud compute backend-services create vibehuntr-backend-service \
  --global

# Create URL map
gcloud compute url-maps create vibehuntr-lb \
  --default-service vibehuntr-backend-service

# Create HTTPS proxy
gcloud compute target-https-proxies create vibehuntr-https-proxy \
  --url-map=vibehuntr-lb \
  --ssl-certificates=vibehuntr-cert

# Create forwarding rule
gcloud compute forwarding-rules create vibehuntr-https-rule \
  --address=vibehuntr-ip \
  --global \
  --target-https-proxy=vibehuntr-https-proxy \
  --ports=443
```

### 4. Update DNS

Point your domain to the reserved IP address:
- Type: A
- Name: vibehuntr (or @)
- Value: [IP from step 1]

### 5. Update CORS

```bash
gcloud run services update vibehuntr-backend \
  --region us-central1 \
  --update-env-vars CORS_ORIGINS="https://vibehuntr.yourdomain.com"
```

## Cost Optimization

### Current Architecture Costs

- **Cloud Run Backend**: 
  - Scales to zero when not in use (no idle costs)
  - ~$0.00002400 per request (2.4¢ per 1000 requests)
  - 2GB memory, 2 vCPU configuration
  
- **Cloud Storage Frontend**:
  - ~$0.026 per GB/month storage
  - ~$0.12 per GB egress (first 1GB free)
  - Very cheap for static sites
  
- **Gemini API**:
  - Pay per token (input + output)
  - Gemini 2.0 Flash: ~$0.075 per 1M input tokens
  
- **Google Places API**:
  - Pay per request
  - ~$0.017 per request (varies by request type)

### Cost Reduction Tips

1. **Enable Cloud CDN** for frontend (reduces egress costs)
2. **Set min-instances=0** for Cloud Run (already configured)
3. **Use Gemini Flash models** instead of Pro (already configured)
4. **Implement request caching** for Places API
5. **Set up budget alerts** in GCP Console

### Set Up Budget Alerts

```bash
# Create a budget alert
gcloud billing budgets create \
  --billing-account=YOUR_BILLING_ACCOUNT_ID \
  --display-name="Vibehuntr Monthly Budget" \
  --budget-amount=100 \
  --threshold-rule=percent=50 \
  --threshold-rule=percent=90 \
  --threshold-rule=percent=100
```

## Rollback and Version Management

### List Revisions

```bash
gcloud run revisions list \
  --service vibehuntr-backend \
  --region us-central1
```

### Rollback to Previous Version

```bash
# Get previous revision name
PREVIOUS_REVISION=$(gcloud run revisions list \
  --service vibehuntr-backend \
  --region us-central1 \
  --format="value(name)" \
  --limit=2 | tail -1)

# Route 100% traffic to previous revision
gcloud run services update-traffic vibehuntr-backend \
  --to-revisions $PREVIOUS_REVISION=100 \
  --region us-central1
```

### Gradual Rollout (Canary Deployment)

```bash
# Route 10% to new version, 90% to old
gcloud run services update-traffic vibehuntr-backend \
  --to-revisions NEW_REVISION=10,OLD_REVISION=90 \
  --region us-central1

# After validation, route 100% to new version
gcloud run services update-traffic vibehuntr-backend \
  --to-latest \
  --region us-central1
```

## Security Best Practices

### 1. Restrict API Access

```bash
# Remove public access (require authentication)
gcloud run services remove-iam-policy-binding vibehuntr-backend \
  --region us-central1 \
  --member="allUsers" \
  --role="roles/run.invoker"

# Add specific users/service accounts
gcloud run services add-iam-policy-binding vibehuntr-backend \
  --region us-central1 \
  --member="user:your-email@example.com" \
  --role="roles/run.invoker"
```

### 2. Rotate Secrets

```bash
# Update secret with new value
echo "new-api-key" | gcloud secrets versions add GEMINI_API_KEY --data-file=-

# Cloud Run will automatically use the latest version
```

### 3. Enable VPC Connector (Optional)

For private network access:

```bash
# Create VPC connector
gcloud compute networks vpc-access connectors create vibehuntr-connector \
  --region us-central1 \
  --range 10.8.0.0/28

# Update Cloud Run to use connector
gcloud run services update vibehuntr-backend \
  --region us-central1 \
  --vpc-connector vibehuntr-connector
```

## Troubleshooting

### Backend Not Starting

```bash
# Check logs for errors
gcloud run logs read vibehuntr-backend --region us-central1 --limit 100

# Common issues:
# - Missing secrets: Verify Secret Manager permissions
# - Port mismatch: Ensure app listens on PORT env var (Cloud Run sets this)
# - Memory limits: Increase memory if OOM errors
```

### Frontend Not Loading

```bash
# Check if bucket exists and is public
gsutil ls gs://$GCP_PROJECT_ID-vibehuntr-frontend

# Verify public access
gsutil iam get gs://$GCP_PROJECT_ID-vibehuntr-frontend

# Check CORS on backend
curl -H "Origin: https://storage.googleapis.com" \
  -H "Access-Control-Request-Method: POST" \
  -X OPTIONS $BACKEND_URL/api/chat -v
```

### High Costs

```bash
# Check Cloud Run metrics
gcloud run services describe vibehuntr-backend \
  --region us-central1 \
  --format="value(status.url)"

# View billing reports in console
# https://console.cloud.google.com/billing
```

## CI/CD Integration

### GitHub Actions Example

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - id: auth
        uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}
      
      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy vibehuntr-backend \
            --source ./backend \
            --region us-central1 \
            --project ${{ secrets.GCP_PROJECT_ID }}
```

## Production Readiness Checklist

Before going live:

- [ ] All tests passing (`uv run pytest backend/tests/`)
- [ ] Secrets created in Secret Manager
- [ ] CORS configured for production domain
- [ ] Health check endpoint responding
- [ ] Monitoring and alerts configured
- [ ] Budget alerts set up
- [ ] SSL certificate configured (if using custom domain)
- [ ] Error tracking enabled
- [ ] Backup and disaster recovery plan
- [ ] Load testing completed
- [ ] Security review completed

## Support and Resources

- **GCP Documentation**: [Cloud Run Documentation](https://cloud.google.com/run/docs)
- **FastAPI Documentation**: [FastAPI Official Docs](https://fastapi.tiangolo.com/)
- **Google ADK Documentation**: [Agent Development Kit Docs](https://cloud.google.com/agent-development-kit/docs)
- **Project Issues**: [GitHub Issues](https://github.com/your-org/vibehuntr-agent/issues)

## Next Steps

1. Test your deployment thoroughly
2. Set up monitoring dashboards
3. Configure custom domain (optional)
4. Enable Cloud CDN for better performance
5. Set up CI/CD pipeline
6. Plan for scaling and optimization
