# Quick Deploy Guide - 5 Minutes to Production

Get your Vibehuntr agent running in production in 5 minutes.

## Prerequisites (2 minutes)

1. **Get API Keys**:
   - [Gemini API Key](https://makersuite.google.com/app/apikey) - Get your Gemini API key from Google AI Studio
   - [Google Places API Key](https://console.cloud.google.com/apis/credentials) - Create a Places API key in GCP Console

2. **Install Required Tools** (if not installed):
   ```bash
   # gcloud CLI
   curl https://sdk.cloud.google.com | bash
   exec -l $SHELL
   
   # Firebase CLI
   npm install -g firebase-tools
   ```
   
   Or follow the official installation guides:
   - [gcloud CLI Installation](https://cloud.google.com/sdk/docs/install)
   - [Firebase CLI Installation](https://firebase.google.com/docs/cli)

## Deploy (3 minutes)

### Step 1: Set Project ID

```bash
export GCP_PROJECT_ID="your-project-id"
```

### Step 2: Authenticate

```bash
# Authenticate with GCP
gcloud auth login
gcloud config set project $GCP_PROJECT_ID

# Authenticate with Firebase
firebase login
```

### Step 3: Create Secrets

```bash
# Replace with your actual API keys
echo "your-gemini-api-key" | gcloud secrets create GEMINI_API_KEY --data-file=-
echo "your-places-api-key" | gcloud secrets create GOOGLE_PLACES_API_KEY --data-file=-

# Grant access to Cloud Run
PROJECT_NUMBER=$(gcloud projects describe $GCP_PROJECT_ID --format='value(projectNumber)')
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Step 4: Deploy Everything

```bash
chmod +x scripts/deploy-production.sh
./scripts/deploy-production.sh
```

That's it! The script will:
- ✅ Enable required GCP APIs
- ✅ Deploy backend to Cloud Run
- ✅ Build and deploy frontend to Firebase Hosting
- ✅ Configure CORS and caching
- ✅ Verify deployment

## Access Your App

After deployment completes, you'll see:

```
Frontend URL: https://YOUR-PROJECT.web.app
Alternative URL: https://YOUR-PROJECT.firebaseapp.com
Backend URL: https://vibehuntr-backend-xxx.run.app
```

## Verify Deployment

```bash
# Check backend health
curl $BACKEND_URL/health

# Should return:
# {"status":"healthy","service":"Vibehuntr Agent API","version":"1.0.0","environment":"production"}
```

## What's Next?

- 📊 **Monitor**: View logs at https://console.cloud.google.com/run
- 🌐 **Custom Domain**: See PRODUCTION_DEPLOYMENT.md for setup
- 💰 **Budget Alerts**: Set up in GCP Console
- 🚀 **CI/CD**: Automate future deployments

## Troubleshooting

### "Permission denied" errors
```bash
# Re-authenticate
gcloud auth application-default login
```

### "Secret not found" errors
```bash
# Verify secrets exist
gcloud secrets list
```

### Backend not starting
```bash
# Check logs
gcloud run logs read vibehuntr-backend --region us-central1 --limit 50
```

### Frontend not loading
```bash
# Check Firebase Hosting status
firebase hosting:channel:list --project $GCP_PROJECT_ID

# View deployment history
firebase hosting:releases:list --project $GCP_PROJECT_ID
```

## Cost Estimate

Expected monthly cost for low-medium traffic: **$10-50**

- Cloud Run: $5-20 (scales to zero)
- Firebase Hosting: $0-5 (10GB free tier, then pay per use)
- Gemini API: Variable (pay per use)
- Places API: Variable (pay per use)

## Full Documentation

For detailed information, see:
- **PRODUCTION_DEPLOYMENT.md** - Complete deployment guide
- **PRODUCTION_READINESS.md** - Production readiness assessment
- **backend/README.md** - Backend documentation
- **frontend/README.md** - Frontend documentation

## Support

Need help? Check:
1. Logs: `gcloud run logs read vibehuntr-backend --region us-central1`
2. Health: `curl $BACKEND_URL/health`
3. Troubleshooting section in PRODUCTION_DEPLOYMENT.md
