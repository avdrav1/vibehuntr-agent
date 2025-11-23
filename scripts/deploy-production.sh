#!/bin/bash

# Production Deployment Script for Vibehuntr
# This script automates the deployment of both backend and frontend to GCP

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-}"
REGION="${GCP_REGION:-us-central1}"
BACKEND_SERVICE="vibehuntr-backend"
FRONTEND_BUCKET="${PROJECT_ID}-vibehuntr-frontend"

# Functions
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    print_info "Checking prerequisites..."
    
    # Check if gcloud is installed
    if ! command -v gcloud &> /dev/null; then
        print_error "gcloud CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check if authenticated
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
        print_error "Not authenticated with gcloud. Run: gcloud auth login"
        exit 1
    fi
    
    # Check if project is set
    if [ -z "$PROJECT_ID" ]; then
        print_error "GCP_PROJECT_ID environment variable is not set"
        exit 1
    fi
    
    print_info "Prerequisites check passed"
}

enable_apis() {
    print_info "Enabling required GCP APIs..."
    
    gcloud services enable \
        run.googleapis.com \
        storage.googleapis.com \
        cloudbuild.googleapis.com \
        secretmanager.googleapis.com \
        aiplatform.googleapis.com \
        --project="${PROJECT_ID}"
    
    print_info "APIs enabled successfully"
}

deploy_backend() {
    print_info "Deploying backend to Cloud Run..."
    
    cd backend
    
    # Deploy to Cloud Run
    gcloud run deploy "${BACKEND_SERVICE}" \
        --source . \
        --platform managed \
        --region "${REGION}" \
        --allow-unauthenticated \
        --set-env-vars PROJECT_ID="${PROJECT_ID}",LOCATION="${REGION}",ENVIRONMENT=production \
        --set-secrets GEMINI_API_KEY=GEMINI_API_KEY:latest,GOOGLE_PLACES_API_KEY=GOOGLE_PLACES_API_KEY:latest \
        --memory 2Gi \
        --cpu 2 \
        --timeout 300 \
        --max-instances 10 \
        --min-instances 0 \
        --port 8080 \
        --project="${PROJECT_ID}"
    
    # Get the service URL
    BACKEND_URL=$(gcloud run services describe "${BACKEND_SERVICE}" \
        --region "${REGION}" \
        --format 'value(status.url)' \
        --project="${PROJECT_ID}")
    
    print_info "Backend deployed successfully at: ${BACKEND_URL}"
    
    cd ..
    
    # Export for frontend build
    export VITE_API_URL="${BACKEND_URL}"
}

deploy_frontend() {
    print_info "Deploying frontend to Cloud Storage..."
    
    # Check if bucket exists, create if not
    if ! gsutil ls -b "gs://${FRONTEND_BUCKET}" &> /dev/null; then
        print_info "Creating Cloud Storage bucket..."
        gsutil mb -p "${PROJECT_ID}" -c STANDARD -l "${REGION}" "gs://${FRONTEND_BUCKET}"
        gsutil iam ch allUsers:objectViewer "gs://${FRONTEND_BUCKET}"
        gsutil web set -m index.html -e index.html "gs://${FRONTEND_BUCKET}"
    fi
    
    cd frontend
    
    # Install dependencies
    print_info "Installing frontend dependencies..."
    npm ci
    
    # Build
    print_info "Building frontend..."
    npm run build
    
    # Deploy to Cloud Storage
    print_info "Uploading to Cloud Storage..."
    gsutil -m rsync -r -d dist/ "gs://${FRONTEND_BUCKET}"
    
    # Set cache control headers
    gsutil -m setmeta -h "Cache-Control:public, max-age=31536000" "gs://${FRONTEND_BUCKET}/**/*.js" || true
    gsutil -m setmeta -h "Cache-Control:public, max-age=31536000" "gs://${FRONTEND_BUCKET}/**/*.css" || true
    gsutil -m setmeta -h "Cache-Control:public, max-age=3600" "gs://${FRONTEND_BUCKET}/index.html" || true
    
    print_info "Frontend deployed successfully"
    print_info "Frontend URL: https://storage.googleapis.com/${FRONTEND_BUCKET}/index.html"
    
    cd ..
}

verify_deployment() {
    print_info "Verifying deployment..."
    
    # Check backend health
    if curl -f "${VITE_API_URL}/health" &> /dev/null; then
        print_info "Backend health check passed"
    else
        print_warning "Backend health check failed"
    fi
    
    # Check frontend
    if curl -f "https://storage.googleapis.com/${FRONTEND_BUCKET}/index.html" &> /dev/null; then
        print_info "Frontend is accessible"
    else
        print_warning "Frontend is not accessible"
    fi
}

print_summary() {
    echo ""
    echo "=========================================="
    echo "Deployment Summary"
    echo "=========================================="
    echo "Project ID: ${PROJECT_ID}"
    echo "Region: ${REGION}"
    echo "Backend URL: ${VITE_API_URL}"
    echo "Frontend URL: https://storage.googleapis.com/${FRONTEND_BUCKET}/index.html"
    echo ""
    echo "Next steps:"
    echo "1. Configure a custom domain (optional)"
    echo "2. Set up Cloud CDN for better performance"
    echo "3. Configure monitoring and alerts"
    echo "4. Update CORS_ORIGINS on backend if using custom domain"
    echo "=========================================="
}

# Main execution
main() {
    print_info "Starting production deployment..."
    
    check_prerequisites
    enable_apis
    deploy_backend
    deploy_frontend
    verify_deployment
    print_summary
    
    print_info "Deployment completed successfully!"
}

# Run main function
main
