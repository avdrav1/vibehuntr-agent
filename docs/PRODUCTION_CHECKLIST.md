# Production Deployment Checklist

Use this checklist to ensure a smooth production deployment of the Vibehuntr React + FastAPI application.

## Pre-Deployment

### GCP Project Setup
- [ ] GCP project created with billing enabled
- [ ] Project ID documented: `_________________`
- [ ] Region selected: `_________________`
- [ ] Required APIs enabled:
  - [ ] Cloud Run API
  - [ ] Cloud Storage API
  - [ ] Cloud Build API
  - [ ] Secret Manager API
  - [ ] Vertex AI API

### Secrets Configuration
- [ ] Gemini API key obtained
- [ ] Google Places API key obtained
- [ ] Secrets created in Secret Manager:
  - [ ] `GEMINI_API_KEY`
  - [ ] `GOOGLE_PLACES_API_KEY`
- [ ] Service account has Secret Manager access

### Backend Configuration
- [ ] `backend/Dockerfile` created
- [ ] `backend/.dockerignore` configured
- [ ] `backend/.env.production` created with production values
- [ ] CORS origins configured for production domain
- [ ] Health check endpoint verified (`/health`)

### Frontend Configuration
- [ ] `frontend/.env.production` created
- [ ] `VITE_API_URL` set to production backend URL
- [ ] Production build tested locally (`npm run build`)
- [ ] Bundle size optimized (< 500KB gzipped)

### Domain and SSL
- [ ] Domain name registered (if using custom domain)
- [ ] DNS provider access confirmed
- [ ] SSL certificate plan decided:
  - [ ] Google-managed certificate
  - [ ] Custom certificate

## Deployment

### Backend Deployment
- [ ] Backend deployed to Cloud Run
- [ ] Service URL obtained: `_________________`
- [ ] Environment variables configured
- [ ] Secrets mounted correctly
- [ ] Health check passing
- [ ] Logs accessible in Cloud Logging
- [ ] Service account permissions verified

### Frontend Deployment
- [ ] Cloud Storage bucket created
- [ ] Bucket configured for static website hosting
- [ ] Frontend built with production API URL
- [ ] Files uploaded to Cloud Storage
- [ ] Cache headers configured
- [ ] Frontend accessible via bucket URL

### Optional: CDN Setup
- [ ] Backend bucket created
- [ ] Static IP reserved
- [ ] URL map configured
- [ ] HTTPS proxy created
- [ ] SSL certificate attached
- [ ] Forwarding rule created
- [ ] DNS records updated

## Post-Deployment

### Verification
- [ ] Backend health endpoint responding: `curl https://[backend-url]/health`
- [ ] Frontend loading correctly
- [ ] API calls from frontend to backend working
- [ ] CORS working correctly
- [ ] Streaming responses working
- [ ] Session management working
- [ ] Error handling working correctly

### Monitoring Setup
- [ ] Cloud Logging configured
- [ ] Log-based metrics created
- [ ] Monitoring dashboard created with:
  - [ ] Request count
  - [ ] Request latency
  - [ ] Error rate
  - [ ] CPU utilization
  - [ ] Memory utilization
- [ ] Alerts configured:
  - [ ] High error rate alert
  - [ ] High latency alert
  - [ ] Service down alert

### Security
- [ ] HTTPS enabled for both frontend and backend
- [ ] CORS restricted to production domain only
- [ ] Secrets not exposed in logs or responses
- [ ] IAM permissions follow least privilege
- [ ] Service account has minimal required permissions
- [ ] API rate limiting considered
- [ ] Input validation on all endpoints
- [ ] Security headers configured

### Performance
- [ ] Cold start time acceptable (< 5 seconds)
- [ ] Response time acceptable (< 2 seconds)
- [ ] Streaming latency acceptable
- [ ] CDN caching working (if configured)
- [ ] Bundle size optimized
- [ ] Images optimized

### Documentation
- [ ] Production URLs documented
- [ ] Environment variables documented
- [ ] Deployment process documented
- [ ] Rollback procedure documented
- [ ] Monitoring dashboard links shared
- [ ] On-call procedures defined

## Testing in Production

### Functional Testing
- [ ] Send a message and receive response
- [ ] Verify streaming works
- [ ] Start new conversation
- [ ] Verify session persistence
- [ ] Test error scenarios
- [ ] Test with long messages
- [ ] Test with rapid message sending

### Load Testing
- [ ] Test with 10 concurrent users
- [ ] Test with 50 concurrent users
- [ ] Verify auto-scaling works
- [ ] Monitor resource usage under load
- [ ] Verify no memory leaks

### Browser Testing
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)
- [ ] Mobile browsers (iOS Safari, Chrome Mobile)

## Maintenance

### Regular Tasks
- [ ] Monitor error rates daily
- [ ] Review logs weekly
- [ ] Update dependencies monthly
- [ ] Rotate secrets quarterly
- [ ] Review and optimize costs monthly
- [ ] Test rollback procedure quarterly

### Backup Strategy
- [ ] Frontend builds backed up
- [ ] Database backups configured (if applicable)
- [ ] Configuration files version controlled
- [ ] Disaster recovery plan documented

## Rollback Plan

### If Issues Occur
1. [ ] Identify the issue (check logs, metrics)
2. [ ] Decide: fix forward or rollback
3. [ ] If rollback:
   - [ ] Backend: Use `scripts/rollback-production.sh`
   - [ ] Frontend: Restore from backup
4. [ ] Verify rollback successful
5. [ ] Document the issue
6. [ ] Plan fix for next deployment

## Cost Optimization

- [ ] Review Cloud Run instance settings
- [ ] Optimize minimum instances (0 for low traffic)
- [ ] Set appropriate maximum instances
- [ ] Enable CDN caching to reduce egress
- [ ] Review and remove unused resources
- [ ] Set up budget alerts

## Compliance and Legal

- [ ] Privacy policy updated (if applicable)
- [ ] Terms of service updated (if applicable)
- [ ] Data retention policy defined
- [ ] GDPR compliance verified (if applicable)
- [ ] Accessibility standards met (WCAG 2.1)

## Sign-Off

- [ ] Development team sign-off
- [ ] QA team sign-off
- [ ] Product owner sign-off
- [ ] Security team sign-off (if applicable)

---

**Deployment Date**: _________________

**Deployed By**: _________________

**Backend URL**: _________________

**Frontend URL**: _________________

**Notes**:
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________
