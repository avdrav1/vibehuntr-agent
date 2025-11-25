# Production Deployment Guide

This guide covers deploying the Vibehuntr agent to Google Cloud Platform (GCP) for production use.

## Architecture Overview

The production deployment consists of:
- **Backend**: FastAPI application on Cloud Run (auto-scaling, serverless)
- **Frontend**: React SPA hosted on Firebase Hosting (static hosting with CDN)
- **Secrets**: API keys stored in Secret Manager
- **Monitoring**: Cloud Logging, Cloud Trace (OpenTelemetry)

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         User Browser                         │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Firebase Hosting (Global CDN)                   │
│  • Automatic SSL certificates                                │
│  • SPA routing (all routes → index.html)                     │
│  • Cache headers (31536000s for assets, 3600s for HTML)     │
│  • URL: https://project-id.web.app                           │
└────────────────────────┬────────────────────────────────────┘
                         │ API Requests
                         │ (CORS configured)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Cloud Run Backend                          │
│  • FastAPI application                                       │
│  • Auto-scaling (min: 0, max: 10)                            │
│  • 2GB memory, 2 vCPU                                        │
│  • Secrets from Secret Manager                               │
│  • OpenTelemetry tracing                                     │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   Gemini    │  │   Google    │  │   Secret    │
│     API     │  │  Places API │  │   Manager   │
└─────────────┘  └─────────────┘  └─────────────┘
```

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

# Firebase CLI
npm install -g firebase-tools

# uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Node.js and npm (if not installed)
# Visit: https://nodejs.org/
```

**Installation Links**:
- [gcloud CLI Installation](https://cloud.google.com/sdk/docs/install)
- [Firebase CLI Installation](https://firebase.google.com/docs/cli)
- [uv Installation Guide](https://docs.astral.sh/uv/getting-started/installation/)
- [Node.js Downloads](https://nodejs.org/)

### 4. Authenticate with GCP and Firebase

```bash
# Authenticate with GCP
gcloud auth login
gcloud config set project $GCP_PROJECT_ID
gcloud auth application-default login

# Authenticate with Firebase
firebase login
```

### 5. Firebase Project Setup (First Time Only)

If this is your first time deploying to Firebase Hosting, you need to set up the Firebase project:

```bash
cd frontend

# Option 1: Use existing Firebase configuration (recommended)
# The repository already includes firebase.json and .firebaserc
# Just verify the project ID is correct
cat .firebaserc

# If the project ID is incorrect or missing, update it:
firebase use $GCP_PROJECT_ID

# Option 2: Initialize Firebase from scratch (only if needed)
# This will create firebase.json and .firebaserc
firebase init hosting

# When prompted:
# - Select "Use an existing project"
# - Choose your GCP project from the list
# - Set public directory to: dist
# - Configure as single-page app: Yes
# - Set up automatic builds with GitHub: No (we use manual deployment)
# - Don't overwrite existing files

cd ..
```

**Verify Firebase Configuration**:

The `frontend/firebase.json` should look like this:
```json
{
  "hosting": {
    "public": "dist",
    "ignore": ["firebase.json", "**/.*", "**/node_modules/**"],
    "rewrites": [
      {
        "source": "**",
        "destination": "/index.html"
      }
    ],
    "headers": [
      {
        "source": "**/*.@(js|css|jpg|jpeg|png|gif|svg|webp|woff|woff2|ttf|eot)",
        "headers": [
          {
            "key": "Cache-Control",
            "value": "public, max-age=31536000, immutable"
          }
        ]
      },
      {
        "source": "index.html",
        "headers": [
          {
            "key": "Cache-Control",
            "value": "public, max-age=3600, must-revalidate"
          }
        ]
      }
    ]
  }
}
```

The `frontend/.firebaserc` should contain:
```json
{
  "projects": {
    "default": "your-project-id"
  }
}
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
3. Build and deploy frontend to Firebase Hosting
4. Configure CORS and caching
5. Verify deployment health

## Manual Deployment Steps

If you prefer to deploy manually or need more control:

### 1. Enable Required APIs

```bash
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  aiplatform.googleapis.com \
  firebasehosting.googleapis.com \
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

The deployment script automatically configures CORS for Firebase Hosting URLs. If you need to add custom domains, update the CORS_ORIGINS environment variable:

```bash
gcloud run services update vibehuntr-backend \
  --region us-central1 \
  --update-env-vars CORS_ORIGINS="https://$GCP_PROJECT_ID.web.app,https://$GCP_PROJECT_ID.firebaseapp.com,https://your-custom-domain.com"
```

### 6. Build and Deploy Frontend

```bash
cd frontend

# Set backend URL for build
export VITE_API_URL=$BACKEND_URL

# Install dependencies and build
npm ci
npm run build

# Deploy to Firebase Hosting
firebase deploy --only hosting --project $GCP_PROJECT_ID

cd ..
```

**Note**: Firebase Hosting automatically:
- Serves content via global CDN
- Provisions SSL certificates
- Applies cache headers from `firebase.json`
- Handles SPA routing

### 7. Access Your Application

```bash
echo "Frontend URL: https://$GCP_PROJECT_ID.web.app"
echo "Alternative URL: https://$GCP_PROJECT_ID.firebaseapp.com"
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

The deployment script automatically configures CORS for Firebase Hosting URLs. To add custom domains:

```bash
# Update Cloud Run service with CORS origins
gcloud run services update vibehuntr-backend \
  --region us-central1 \
  --update-env-vars CORS_ORIGINS="https://$GCP_PROJECT_ID.web.app,https://$GCP_PROJECT_ID.firebaseapp.com,https://your-domain.com"
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

Firebase Hosting makes custom domains easy. For a custom domain like `vibehuntr.yourdomain.com`:

### 1. Add Custom Domain in Firebase Console

```bash
# Add domain via CLI
firebase hosting:channel:deploy production \
  --project $GCP_PROJECT_ID \
  --expires 30d

# Or use Firebase Console:
# 1. Go to Firebase Console > Hosting
# 2. Click "Add custom domain"
# 3. Enter your domain name
# 4. Follow verification steps
```

### 2. Update DNS Records

Firebase will provide DNS records to add to your domain registrar:

**For apex domain (yourdomain.com)**:
- Type: A
- Name: @
- Value: [IP addresses provided by Firebase]

**For subdomain (vibehuntr.yourdomain.com)**:
- Type: CNAME
- Name: vibehuntr
- Value: [hostname provided by Firebase]

### 3. Wait for SSL Provisioning

Firebase automatically provisions SSL certificates (usually takes 24-48 hours).

### 4. Update Backend CORS

```bash
gcloud run services update vibehuntr-backend \
  --region us-central1 \
  --update-env-vars CORS_ORIGINS="https://$GCP_PROJECT_ID.web.app,https://vibehuntr.yourdomain.com"
```

**Documentation**: [Firebase Custom Domain Setup](https://firebase.google.com/docs/hosting/custom-domain)

## Cost Optimization

### Current Architecture Costs

- **Cloud Run Backend**: 
  - Scales to zero when not in use (no idle costs)
  - ~$0.00002400 per request (2.4¢ per 1000 requests)
  - 2GB memory, 2 vCPU configuration
  
- **Firebase Hosting Frontend**:
  - Free tier: 10GB storage, 360MB/day transfer
  - ~$0.026 per GB/month storage (after free tier)
  - ~$0.15 per GB egress (after free tier)
  - Includes global CDN at no extra cost
  
- **Gemini API**:
  - Pay per token (input + output)
  - Gemini 2.0 Flash: ~$0.075 per 1M input tokens
  
- **Google Places API**:
  - Pay per request
  - ~$0.017 per request (varies by request type)

### Cost Reduction Tips

1. **Firebase Hosting includes CDN** at no extra cost (already configured)
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

**Backend (Cloud Run)**:
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

**Frontend (Firebase Hosting)**:
```bash
# Firebase maintains deployment history
firebase hosting:channel:list --project $GCP_PROJECT_ID

# Rollback to previous version
firebase hosting:rollback --project $GCP_PROJECT_ID
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
# Check Firebase Hosting status
firebase hosting:channel:list --project $GCP_PROJECT_ID

# View deployment history
firebase hosting:releases:list --project $GCP_PROJECT_ID

# Check CORS on backend
curl -H "Origin: https://$GCP_PROJECT_ID.web.app" \
  -H "Access-Control-Request-Method: POST" \
  -X OPTIONS $BACKEND_URL/api/chat -v

# Test frontend directly
curl https://$GCP_PROJECT_ID.web.app
```

### Firebase-Specific Issues

#### Firebase CLI Not Authenticated

**Symptom**: `firebase deploy` fails with authentication error

**Solution**:
```bash
# Re-authenticate with Firebase
firebase login --reauth

# Verify authentication
firebase projects:list

# If using CI/CD, use service account
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
firebase deploy --token "$(gcloud auth print-access-token)"
```

#### Firebase Project Not Found

**Symptom**: Error: "Project not found" or "Permission denied"

**Solution**:
```bash
# List available projects
firebase projects:list

# Set correct project
firebase use $GCP_PROJECT_ID

# Verify .firebaserc file
cat frontend/.firebaserc

# If .firebaserc is missing or incorrect, recreate it
cd frontend
firebase use --add
```

#### Build Artifacts Not Found

**Symptom**: Firebase deploy fails with "public directory not found"

**Solution**:
```bash
# Ensure build completed successfully
cd frontend
npm run build

# Verify dist directory exists
ls -la dist/

# Check firebase.json points to correct directory
cat firebase.json | grep public

# Should show: "public": "dist"
```

#### SPA Routes Return 404

**Symptom**: Direct navigation to routes (e.g., `/about`) returns 404

**Solution**:
```bash
# Verify firebase.json has rewrite rules
cat frontend/firebase.json

# Should include:
# "rewrites": [
#   {
#     "source": "**",
#     "destination": "/index.html"
#   }
# ]

# Redeploy if missing
firebase deploy --only hosting --project $GCP_PROJECT_ID
```

#### Cache Headers Not Applied

**Symptom**: Assets not caching properly, slow repeat visits

**Solution**:
```bash
# Check cache headers in browser DevTools Network tab
# Or use curl:
curl -I https://$GCP_PROJECT_ID.web.app/assets/index-abc123.js

# Should see: Cache-Control: public, max-age=31536000, immutable

# If missing, verify firebase.json headers configuration
cat frontend/firebase.json | grep -A 20 headers

# Redeploy to apply changes
firebase deploy --only hosting --project $GCP_PROJECT_ID
```

#### SSL Certificate Pending

**Symptom**: Custom domain shows "SSL certificate pending"

**Solution**:
- SSL provisioning can take 24-48 hours
- Verify DNS records are correctly configured
- Check Firebase Console > Hosting > Custom domains for status
- Ensure domain verification is complete

```bash
# Check domain status
firebase hosting:channel:list --project $GCP_PROJECT_ID

# View SSL certificate status in Firebase Console
# https://console.firebase.google.com/project/$GCP_PROJECT_ID/hosting/sites
```

#### CORS Errors from Frontend

**Symptom**: Browser console shows CORS errors when calling backend API

**Solution**:
```bash
# Verify backend CORS configuration includes Firebase URLs
gcloud run services describe vibehuntr-backend \
  --region us-central1 \
  --format="value(spec.template.spec.containers[0].env)" | grep CORS

# Update CORS origins if needed
gcloud run services update vibehuntr-backend \
  --region us-central1 \
  --update-env-vars CORS_ORIGINS="https://$GCP_PROJECT_ID.web.app,https://$GCP_PROJECT_ID.firebaseapp.com"

# Test CORS with curl
curl -H "Origin: https://$GCP_PROJECT_ID.web.app" \
  -H "Access-Control-Request-Method: POST" \
  -X OPTIONS $BACKEND_URL/api/chat -v

# Should see: Access-Control-Allow-Origin header in response
```

#### Deployment Quota Exceeded

**Symptom**: "Quota exceeded" error during deployment

**Solution**:
- Firebase Hosting has deployment limits (10 per hour for free tier)
- Wait an hour or upgrade to Blaze plan
- Use preview channels for testing: `firebase hosting:channel:deploy preview`

#### Old Version Still Showing

**Symptom**: Deployed new version but old version still appears

**Solution**:
```bash
# Clear browser cache (Ctrl+Shift+R or Cmd+Shift+R)

# Check deployment status
firebase hosting:releases:list --project $GCP_PROJECT_ID

# Verify latest deployment
curl -I https://$GCP_PROJECT_ID.web.app/index.html

# Check Cache-Control header - may need to wait for cache expiry
# index.html has max-age=3600 (1 hour)

# Force cache clear by adding query parameter
# https://$GCP_PROJECT_ID.web.app/?v=timestamp
```

### High Costs

```bash
# Check Cloud Run metrics
gcloud run services describe vibehuntr-backend \
  --region us-central1 \
  --format="value(status.url)"

# View billing reports in console
# https://console.cloud.google.com/billing

# Check Firebase Hosting usage
# https://console.firebase.google.com/project/$GCP_PROJECT_ID/usage
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
