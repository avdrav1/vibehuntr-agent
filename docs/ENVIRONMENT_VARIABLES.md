# Environment Variables Reference

This document provides a comprehensive reference for all environment variables used in the Vibehuntr React + FastAPI application.

## Backend Environment Variables

### Required Variables

| Variable | Description | Example | Where to Set |
|----------|-------------|---------|--------------|
| `PROJECT_ID` | GCP Project ID | `vibehuntr-prod-123` | Cloud Run environment |
| `LOCATION` | GCP Region | `us-central1` | Cloud Run environment |
| `GEMINI_API_KEY` | Gemini API key for LLM | `AIza...` | Secret Manager |
| `GOOGLE_PLACES_API_KEY` | Google Places API key | `AIza...` | Secret Manager |

### Optional Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `ENVIRONMENT` | Environment name | `development` | `production` |
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated) | `http://localhost:5173` | `https://vibehuntr.com,https://www.vibehuntr.com` |
| `LOG_LEVEL` | Logging level | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `MAX_INSTANCES` | Maximum Cloud Run instances | `10` | `20` |
| `MIN_INSTANCES` | Minimum Cloud Run instances | `0` | `1` |
| `TIMEOUT` | Request timeout in seconds | `300` | `600` |
| `MEMORY` | Container memory | `2Gi` | `4Gi` |
| `CPU` | Container CPU | `2` | `4` |

### Backend Configuration Files

#### Development: `backend/.env`
```env
PROJECT_ID=vibehuntr-dev
LOCATION=us-central1
GEMINI_API_KEY=your-dev-key
GOOGLE_PLACES_API_KEY=your-dev-key
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
ENVIRONMENT=development
LOG_LEVEL=DEBUG
```

#### Production: `backend/.env.production`
```env
PROJECT_ID=vibehuntr-prod
LOCATION=us-central1
GEMINI_API_KEY=${GEMINI_API_KEY}  # From Secret Manager
GOOGLE_PLACES_API_KEY=${GOOGLE_PLACES_API_KEY}  # From Secret Manager
CORS_ORIGINS=https://vibehuntr.com
ENVIRONMENT=production
LOG_LEVEL=INFO
```

## Frontend Environment Variables

### Required Variables

| Variable | Description | Example | Where to Set |
|----------|-------------|---------|--------------|
| `VITE_API_URL` | Backend API URL | `https://api.vibehuntr.com` | `.env.production` |

### Optional Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `VITE_ENVIRONMENT` | Environment name | `development` | `production` |
| `VITE_ENABLE_ANALYTICS` | Enable analytics | `false` | `true` |
| `VITE_SENTRY_DSN` | Sentry error tracking DSN | - | `https://...@sentry.io/...` |

### Frontend Configuration Files

#### Development: `frontend/.env`
```env
VITE_API_URL=http://localhost:8000
VITE_ENVIRONMENT=development
```

#### Production: `frontend/.env.production`
```env
VITE_API_URL=https://vibehuntr-backend-xxxxx-uc.a.run.app
VITE_ENVIRONMENT=production
```

## Setting Environment Variables

### Local Development

1. **Backend**: Create `backend/.env` file
   ```bash
   cp backend/.env.example backend/.env
   # Edit backend/.env with your values
   ```

2. **Frontend**: Create `frontend/.env` file
   ```bash
   cp frontend/.env.example frontend/.env
   # Edit frontend/.env with your values
   ```

### Cloud Run (Backend)

#### Method 1: Using gcloud CLI
```bash
gcloud run services update vibehuntr-backend \
  --set-env-vars PROJECT_ID=vibehuntr-prod,LOCATION=us-central1 \
  --region us-central1
```

#### Method 2: Using Secret Manager
```bash
# Create secret
echo -n "your-api-key" | gcloud secrets create GEMINI_API_KEY --data-file=-

# Mount secret in Cloud Run
gcloud run services update vibehuntr-backend \
  --set-secrets GEMINI_API_KEY=GEMINI_API_KEY:latest \
  --region us-central1
```

#### Method 3: Using Cloud Console
1. Go to Cloud Run → Select service → Edit & Deploy New Revision
2. Go to "Variables & Secrets" tab
3. Add environment variables or mount secrets

### Frontend Build

Environment variables are embedded at build time:

```bash
# Development build
npm run dev

# Production build
VITE_API_URL=https://api.vibehuntr.com npm run build
```

## Security Best Practices

### DO ✅

- Store sensitive values in Secret Manager
- Use different secrets for different environments
- Rotate secrets regularly (quarterly)
- Use IAM to control secret access
- Never commit `.env` files to version control
- Use `.env.example` files as templates (without actual values)

### DON'T ❌

- Hardcode secrets in code
- Commit `.env` files to git
- Share secrets via email or chat
- Use production secrets in development
- Log secret values
- Expose secrets in error messages

## Accessing Environment Variables

### Backend (Python)

```python
import os

# Direct access
project_id = os.getenv("PROJECT_ID")

# With default value
log_level = os.getenv("LOG_LEVEL", "INFO")

# Using settings class (recommended)
from app.core.config import settings

project_id = settings.PROJECT_ID
```

### Frontend (TypeScript)

```typescript
// Vite automatically exposes VITE_* variables
const apiUrl = import.meta.env.VITE_API_URL;

// With fallback
const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Type-safe access (recommended)
interface ImportMetaEnv {
  readonly VITE_API_URL: string;
  readonly VITE_ENVIRONMENT: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
```

## Troubleshooting

### Backend Issues

**Problem**: Environment variable not found
```bash
# Check what variables are set
gcloud run services describe vibehuntr-backend \
  --region us-central1 \
  --format="value(spec.template.spec.containers[0].env)"
```

**Problem**: Secret not accessible
```bash
# Check IAM permissions
gcloud secrets get-iam-policy GEMINI_API_KEY

# Grant access to service account
gcloud secrets add-iam-policy-binding GEMINI_API_KEY \
  --member="serviceAccount:SERVICE_ACCOUNT_EMAIL" \
  --role="roles/secretmanager.secretAccessor"
```

### Frontend Issues

**Problem**: Environment variable undefined in production
- Ensure variable starts with `VITE_`
- Rebuild the application after changing `.env.production`
- Check that the variable is set before running `npm run build`

**Problem**: Wrong API URL in production
```bash
# Verify the built files contain correct URL
grep -r "VITE_API_URL" frontend/dist/
```

## Environment Variable Validation

### Backend Validation

Add validation in `backend/app/core/config.py`:

```python
from pydantic import BaseSettings, validator

class Settings(BaseSettings):
    PROJECT_ID: str
    LOCATION: str
    GEMINI_API_KEY: str
    
    @validator('PROJECT_ID')
    def project_id_not_empty(cls, v):
        if not v:
            raise ValueError('PROJECT_ID must be set')
        return v
    
    class Config:
        env_file = '.env'

settings = Settings()
```

### Frontend Validation

Add validation in `frontend/src/config.ts`:

```typescript
function getRequiredEnv(key: string): string {
  const value = import.meta.env[key];
  if (!value) {
    throw new Error(`Missing required environment variable: ${key}`);
  }
  return value;
}

export const config = {
  apiUrl: getRequiredEnv('VITE_API_URL'),
  environment: import.meta.env.VITE_ENVIRONMENT || 'development',
};
```

## Migration Checklist

When moving from development to production:

- [ ] Update `PROJECT_ID` to production project
- [ ] Update `LOCATION` to production region
- [ ] Create production secrets in Secret Manager
- [ ] Update `CORS_ORIGINS` to production domain
- [ ] Update `VITE_API_URL` to production backend URL
- [ ] Set `ENVIRONMENT=production`
- [ ] Set `LOG_LEVEL=INFO` (not DEBUG)
- [ ] Configure `MIN_INSTANCES` based on traffic
- [ ] Set appropriate `TIMEOUT` and `MEMORY` values
- [ ] Verify all secrets are accessible
- [ ] Test the application with production configuration

## Additional Resources

- [Cloud Run Environment Variables](https://cloud.google.com/run/docs/configuring/environment-variables)
- [Secret Manager Documentation](https://cloud.google.com/secret-manager/docs)
- [Vite Environment Variables](https://vitejs.dev/guide/env-and-mode.html)
- [Pydantic Settings](https://pydantic-docs.helpmanual.io/usage/settings/)
