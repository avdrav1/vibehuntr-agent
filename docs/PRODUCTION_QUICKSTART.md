# Production Deployment Quick Start

This is a condensed guide for deploying Vibehuntr to production. For detailed instructions, see [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md).

## Prerequisites

- GCP project with billing enabled
- `gcloud` CLI installed and authenticated
- Docker installed
- Node.js 18+ installed

## 5-Minute Deployment

### 1. Set Environment Variables

```bash
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="us-central1"
```

### 2. Create Secrets

```bash
# Create API key secrets
echo -n "your-gemini-api-key" | gcloud secrets create GEMINI_API_KEY --data-file=-
echo -n "your-places-api-key" | gcloud secrets create GOOGLE_PLACES_API_KEY --data-file=-
```

### 3. Deploy Backend

```bash
cd backend

gcloud run deploy vibehuntr-backend \
  --source . \
  --platform managed \
  --region ${GCP_REGION} \
  --allow-unauthenticated \
  --set-env-vars PROJECT_ID=${GCP_PROJECT_ID},LOCATION=${GCP_REGION},ENVIRONMENT=production \
  --set-secrets GEMINI_API_KEY=GEMINI_API_KEY:latest,GOOGLE_PLACES_API_KEY=GOOGLE_PLACES_API_KEY:latest \
  --memory 2Gi \
  --cpu 2 \
  --port 8080

# Get backend URL
export BACKEND_URL=$(gcloud run services describe vibehuntr-backend \
  --region ${GCP_REGION} \
  --format 'value(status.url)')

echo "Backend deployed at: ${BACKEND_URL}"
```

### 4. Deploy Frontend

```bash
cd ../frontend

# Build and deploy to Firebase Hosting
npm ci
VITE_API_URL=${BACKEND_URL} npm run build
firebase deploy --only hosting --project ${GCP_PROJECT_ID}

echo "Frontend deployed at: https://${GCP_PROJECT_ID}.web.app"
```

### 5. Update CORS

```bash
# Update backend CORS to allow Firebase Hosting domains
gcloud run services update vibehuntr-backend \
  --set-env-vars CORS_ORIGINS=https://${GCP_PROJECT_ID}.web.app,https://${GCP_PROJECT_ID}.firebaseapp.com \
  --region ${GCP_REGION}
```

## Automated Deployment

Use the provided script for automated deployment:

```bash
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="us-central1"
./scripts/deploy-production.sh
```

## Verify Deployment

```bash
# Test backend
curl ${BACKEND_URL}/health

# Test frontend
curl https://${GCP_PROJECT_ID}.web.app
```

## Next Steps

1. **Set up custom domain** (optional)
   - Add custom domain in Firebase Console
   - Update DNS records
   - SSL certificates are automatic

2. **Configure monitoring**
   - Set up Cloud Logging alerts
   - Create monitoring dashboard
   - Configure error notifications

3. **Optimize performance**
   - CDN is included with Firebase Hosting
   - Adjust Cloud Run settings
   - Monitor and optimize costs

## Rollback

If something goes wrong:

```bash
./scripts/rollback-production.sh
```

## Troubleshooting

### Backend won't start
```bash
# Check logs
gcloud logging read "resource.type=cloud_run_revision" --limit 50
```

### Frontend not loading
```bash
# Check Firebase Hosting status
firebase hosting:channel:list --project ${GCP_PROJECT_ID}

# View deployment history
firebase hosting:releases:list --project ${GCP_PROJECT_ID}
```

### CORS errors
```bash
# Check CORS configuration
gcloud run services describe vibehuntr-backend \
  --region ${GCP_REGION} \
  --format="value(spec.template.spec.containers[0].env)"
```

## Documentation

- [Full Deployment Guide](PRODUCTION_DEPLOYMENT.md)
- [Deployment Checklist](PRODUCTION_CHECKLIST.md)
- [Environment Variables](ENVIRONMENT_VARIABLES.md)
- [Development Setup](DEVELOPMENT_SETUP.md)

## Support

For issues:
1. Check logs: `gcloud logging read`
2. Review [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md)
3. Use rollback script if needed
4. Contact development team
