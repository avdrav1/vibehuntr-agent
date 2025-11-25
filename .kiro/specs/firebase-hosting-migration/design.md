# Firebase Hosting Migration Design

## Overview

This design document outlines the migration from Google Cloud Storage static hosting to Firebase Hosting for the Vibehuntr frontend application. Firebase Hosting provides superior developer experience with cleaner URLs, automatic SSL certificates, integrated CDN, and simpler deployment workflows compared to Cloud Storage.

The migration involves:
- Creating Firebase Hosting configuration files
- Updating the deployment script to use Firebase CLI
- Configuring optimal caching and routing rules
- Updating documentation
- Removing Cloud Storage hosting code

## Architecture

### Current Architecture (Cloud Storage)

```
┌─────────────────┐
│  Developer      │
│  Runs Script    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│  deploy-production.sh           │
│  1. npm run build               │
│  2. gsutil mb (create bucket)   │
│  3. gsutil rsync (upload)       │
│  4. gsutil setmeta (headers)    │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Cloud Storage Bucket           │
│  URL: storage.googleapis.com/   │
│       project-id-frontend/      │
│       index.html                │
└─────────────────────────────────┘
```

### New Architecture (Firebase Hosting)

```
┌─────────────────┐
│  Developer      │
│  Runs Script    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│  deploy-production.sh           │
│  1. npm run build               │
│  2. firebase deploy --only      │
│     hosting                     │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Firebase Hosting               │
│  - Global CDN                   │
│  - Automatic SSL                │
│  - URL: project-id.web.app      │
│  - Custom domain support        │
└─────────────────────────────────┘
```

### Integration Points

1. **Frontend Build Process**: Remains unchanged (Vite builds to `dist/`)
2. **Backend API**: No changes required; frontend continues to use `VITE_API_URL` environment variable
3. **Deployment Script**: Modified to use Firebase CLI instead of gsutil
4. **CORS Configuration**: Backend CORS settings must include new Firebase Hosting URLs

## Components and Interfaces

### 1. Firebase Configuration Files

#### firebase.json

Location: `frontend/firebase.json`

```json
{
  "hosting": {
    "public": "dist",
    "ignore": [
      "firebase.json",
      "**/.*",
      "**/node_modules/**"
    ],
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

**Configuration Explanation**:
- `public`: Specifies `dist/` as the directory containing build artifacts
- `rewrites`: Implements SPA routing by serving `index.html` for all routes
- `headers`: Sets aggressive caching for immutable assets, shorter cache for HTML

#### .firebaserc

Location: `frontend/.firebaserc`

```json
{
  "projects": {
    "default": "${PROJECT_ID}"
  }
}
```

**Note**: This file will be generated dynamically or use environment variable substitution.

### 2. Deployment Script Updates

#### Modified deploy-production.sh

Key changes to `scripts/deploy-production.sh`:

**Remove**:
- `gsutil mb` (bucket creation)
- `gsutil iam ch` (public access)
- `gsutil web set` (website configuration)
- `gsutil rsync` (file upload)
- `gsutil setmeta` (cache headers)

**Add**:
- Firebase CLI installation check
- Firebase authentication verification
- `firebase deploy --only hosting` command
- Firebase project initialization (if needed)

**Function Signature**:
```bash
deploy_frontend() {
    # Input: None (uses environment variables)
    # Environment: PROJECT_ID, VITE_API_URL
    # Output: Deployed frontend URL
    # Side effects: Deploys to Firebase Hosting
}
```

### 3. Firebase CLI Integration

#### Installation Check

```bash
check_firebase_cli() {
    if ! command -v firebase &> /dev/null; then
        print_error "Firebase CLI not installed"
        print_info "Install with: npm install -g firebase-tools"
        exit 1
    fi
}
```

#### Authentication Check

```bash
check_firebase_auth() {
    if ! firebase projects:list &> /dev/null; then
        print_error "Not authenticated with Firebase"
        print_info "Run: firebase login"
        exit 1
    fi
}
```

#### Deployment Command

```bash
firebase deploy \
    --only hosting \
    --project "${PROJECT_ID}" \
    --non-interactive
```

### 4. Backend CORS Updates

The backend must allow requests from Firebase Hosting URLs:

**Current CORS Origins**:
```
https://storage.googleapis.com
```

**New CORS Origins**:
```
https://${PROJECT_ID}.web.app
https://${PROJECT_ID}.firebaseapp.com
```

**Implementation**: Update `backend/app/core/config.py` or Cloud Run environment variables.

## Data Models

No new data models are required for this migration. The frontend application structure remains unchanged.

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Deployment preserves all functionality

*For any* frontend feature that worked with Cloud Storage hosting, that same feature should work identically after deploying to Firebase Hosting.

**Validates: Requirements 1.3**

### Property 2: SPA routing serves index.html for all routes

*For any* valid application route path, requesting that path from Firebase Hosting should return the `index.html` file with a 200 status code.

**Validates: Requirements 2.3**

### Property 3: Deployment script handles all failure types

*For any* type of deployment failure (missing tools, build errors, deploy errors), the deployment script should display a clear error message and exit with a non-zero status code.

**Validates: Requirements 3.5**

### Property 4: Static assets have long-term cache headers

*For any* static asset file (JS, CSS, images, fonts) served by Firebase Hosting, the response should include a `Cache-Control` header with `max-age=31536000`.

**Validates: Requirements 6.1**

### Property 5: HTTPS is enforced for all requests

*For any* request to the Firebase Hosting URL (HTTP or HTTPS), the content should be served over HTTPS.

**Validates: Requirements 6.5**

## Error Handling

### Deployment Errors

| Error Condition | Detection | Handling | User Feedback |
|----------------|-----------|----------|---------------|
| Firebase CLI not installed | Check `command -v firebase` | Exit with error | Display installation instructions |
| Not authenticated | Run `firebase projects:list` | Exit with error | Display `firebase login` command |
| Build fails | Check npm build exit code | Exit with error | Display build error output |
| Deploy fails | Check firebase deploy exit code | Exit with error | Display Firebase error message |
| Health check fails | HTTP request to deployed URL | Display warning | Show URL for manual verification |
| Invalid project ID | Firebase project not found | Exit with error | Display available projects |

### Configuration Errors

| Error Condition | Detection | Handling | User Feedback |
|----------------|-----------|----------|---------------|
| Missing firebase.json | File existence check | Create default config | Inform user of auto-generation |
| Invalid firebase.json | Firebase CLI validation | Exit with error | Display validation errors |
| Missing environment variables | Check `$PROJECT_ID` | Exit with error | List required variables |
| Backend URL not set | Check `$VITE_API_URL` | Exit with error | Explain VITE_API_URL requirement |

### Runtime Errors

| Error Condition | Detection | Handling | User Feedback |
|----------------|-----------|----------|---------------|
| API requests fail (CORS) | Browser console errors | N/A (deployment issue) | Document CORS configuration |
| 404 on routes | Firebase serves index.html | Handled by rewrites | N/A (should not occur) |
| Slow loading | Performance monitoring | N/A (CDN handles) | Document CDN benefits |

## Testing Strategy

### Unit Tests

Unit tests will verify individual components of the deployment process:

1. **Configuration Validation Tests**
   - Test that `firebase.json` has correct structure
   - Test that cache headers are properly configured
   - Test that rewrite rules include SPA routing

2. **Script Function Tests**
   - Test prerequisite checking functions
   - Test error message formatting
   - Test URL construction for health checks

3. **Environment Variable Tests**
   - Test that required variables are validated
   - Test that missing variables produce clear errors

### Property-Based Tests

Property-based tests will verify universal properties using **fast-check** (JavaScript) for frontend tests and **hypothesis** (Python) for backend tests. Each test should run a minimum of 100 iterations.

1. **Property Test: Cache Headers**
   - Generate random asset filenames
   - Verify cache headers match expected patterns
   - **Feature: firebase-hosting-migration, Property 2: Static assets are cached correctly**

2. **Property Test: SPA Routing**
   - Generate random valid route paths
   - Verify all routes serve index.html
   - **Feature: firebase-hosting-migration, Property 4: SPA routing works**

3. **Property Test: Deployment Idempotency**
   - Deploy same artifacts multiple times
   - Verify consistent results
   - **Feature: firebase-hosting-migration, Property 6: Deployment script idempotency**

### Integration Tests

Integration tests will verify the complete deployment workflow:

1. **End-to-End Deployment Test**
   - Run full deployment script in test environment
   - Verify frontend is accessible
   - Verify API communication works
   - Verify all routes return 200 status

2. **CORS Integration Test**
   - Deploy frontend to Firebase
   - Make API requests from deployed frontend
   - Verify no CORS errors occur

3. **Performance Test**
   - Deploy frontend
   - Measure asset load times
   - Verify CDN is serving content
   - Verify cache headers are applied

### Manual Testing Checklist

Before considering the migration complete:

- [ ] Deploy to Firebase Hosting successfully
- [ ] Verify clean URL works (project-id.web.app)
- [ ] Test all application routes
- [ ] Verify API communication with backend
- [ ] Check browser console for errors
- [ ] Verify cache headers in browser DevTools
- [ ] Test on multiple browsers
- [ ] Verify HTTPS is enforced
- [ ] Test custom domain configuration (if applicable)
- [ ] Verify deployment script runs without errors

## Performance Considerations

### Caching Strategy

**Immutable Assets** (JS, CSS, images with content hashes):
- Cache-Control: `public, max-age=31536000, immutable`
- Rationale: Vite generates content-hashed filenames, so these never change

**HTML Files**:
- Cache-Control: `public, max-age=3600, must-revalidate`
- Rationale: HTML may reference new asset versions, so shorter cache

**Benefits**:
- Reduced server requests for returning users
- Faster page loads
- Lower bandwidth costs

### CDN Benefits

Firebase Hosting automatically uses Google's global CDN:
- Content served from edge locations near users
- Reduced latency compared to single-region Cloud Storage
- Automatic compression (gzip/brotli)
- DDoS protection

### Build Optimization

The Vite build process already optimizes:
- Code splitting
- Tree shaking
- Minification
- Asset optimization

No changes needed to build process.

## Security Considerations

### HTTPS

Firebase Hosting automatically provisions SSL certificates:
- Free SSL certificates via Let's Encrypt
- Automatic renewal
- HTTP to HTTPS redirect (configurable)

### Content Security

Firebase Hosting provides:
- DDoS protection
- Rate limiting
- Abuse prevention

### Authentication

For deployment:
- Firebase CLI uses OAuth for authentication
- Service account keys can be used in CI/CD
- Granular IAM permissions available

### CORS Configuration

Backend must explicitly allow Firebase Hosting origins:
```python
cors_origins = [
    f"https://{PROJECT_ID}.web.app",
    f"https://{PROJECT_ID}.firebaseapp.com"
]
```

## Deployment Workflow

### Initial Setup (One-Time)

1. Install Firebase CLI: `npm install -g firebase-tools`
2. Authenticate: `firebase login`
3. Initialize project: `firebase init hosting` (or use provided config)
4. Update backend CORS settings

### Regular Deployment

1. Set environment variables:
   ```bash
   export GCP_PROJECT_ID="your-project"
   export VITE_API_URL="https://backend-url.run.app"
   ```

2. Run deployment script:
   ```bash
   ./scripts/deploy-production.sh
   ```

3. Verify deployment:
   - Check script output for Firebase URL
   - Visit URL in browser
   - Test application functionality

### Rollback Procedure

Firebase Hosting maintains deployment history:

```bash
# List previous deployments
firebase hosting:channel:list

# Rollback to previous version
firebase hosting:rollback
```

## Migration Steps

### Phase 1: Preparation
1. Install Firebase CLI
2. Create Firebase configuration files
3. Test deployment to Firebase in parallel with Cloud Storage

### Phase 2: Update Deployment Script
1. Add Firebase CLI checks
2. Replace Cloud Storage commands with Firebase commands
3. Update health check URLs

### Phase 3: Update Backend
1. Add Firebase Hosting URLs to CORS configuration
2. Deploy backend with updated CORS

### Phase 4: Documentation
1. Update PRODUCTION_DEPLOYMENT.md
2. Add Firebase-specific troubleshooting
3. Document custom domain setup

### Phase 5: Cleanup
1. Remove Cloud Storage deployment code
2. Remove Cloud Storage documentation
3. Optionally delete Cloud Storage bucket

## Rollback Plan

If issues arise after migration:

1. **Immediate Rollback**: Keep Cloud Storage bucket intact for 30 days
2. **Revert Script**: Temporarily revert deployment script to use Cloud Storage
3. **Backend CORS**: Keep both Cloud Storage and Firebase URLs in CORS config during transition
4. **Testing**: Thoroughly test Firebase deployment in non-production environment first

## Documentation Updates

### Files to Update

1. **PRODUCTION_DEPLOYMENT.md**
   - Replace Cloud Storage section with Firebase Hosting
   - Add Firebase CLI installation instructions
   - Update deployment commands
   - Add Firebase-specific troubleshooting

2. **README.md** (if applicable)
   - Update deployment instructions
   - Update architecture diagrams

3. **frontend/README.md**
   - Add Firebase configuration explanation
   - Document local testing with Firebase emulator (optional)

### New Documentation

1. **FIREBASE_HOSTING.md** (optional)
   - Detailed Firebase Hosting guide
   - Custom domain configuration
   - Advanced caching strategies
   - Monitoring and analytics

## Monitoring and Observability

### Firebase Hosting Metrics

Available in Firebase Console:
- Request count
- Bandwidth usage
- Response times
- Error rates
- Geographic distribution

### Health Checks

Deployment script should verify:
- HTTP 200 response from index.html
- Correct Content-Type headers
- Cache-Control headers present
- HTTPS redirect working

### Logging

Firebase Hosting logs available via:
- Firebase Console
- Google Cloud Logging (integrated)
- Can be exported to BigQuery for analysis

## Cost Comparison

### Cloud Storage Costs

- Storage: $0.026/GB/month
- Egress: $0.12/GB (after 1GB free)
- Operations: $0.004 per 10,000 operations

### Firebase Hosting Costs

- Storage: $0.026/GB/month (same)
- Egress: $0.15/GB (after 10GB free)
- **Free tier**: 10GB storage, 360MB/day transfer

### Analysis

For typical usage:
- Firebase Hosting is likely cheaper due to generous free tier
- CDN included at no extra cost
- No separate CDN setup needed

## Future Enhancements

### Custom Domain

Firebase makes custom domains easy:
```bash
firebase hosting:channel:deploy production --domain custom-domain.com
```

### Preview Channels

Firebase supports preview deployments:
```bash
firebase hosting:channel:deploy preview-branch
```

### A/B Testing

Firebase Hosting supports traffic splitting for A/B tests.

### Firebase Analytics

Can integrate Firebase Analytics for user behavior tracking.

## References

- [Firebase Hosting Documentation](https://firebase.google.com/docs/hosting)
- [Firebase CLI Reference](https://firebase.google.com/docs/cli)
- [Vite Build Documentation](https://vitejs.dev/guide/build.html)
- [Cloud Run CORS Configuration](https://cloud.google.com/run/docs/configuring/cors)
