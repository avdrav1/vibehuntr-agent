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

check_firebase_cli() {
    if ! command -v firebase &> /dev/null; then
        print_error "Firebase CLI is not installed"
        print_info "Install with: npm install -g firebase-tools"
        exit 1
    fi
}

check_firebase_auth() {
    if ! firebase projects:list &> /dev/null; then
        print_error "Not authenticated with Firebase"
        print_info "Run: firebase login"
        exit 1
    fi
}

check_firebase_project() {
    print_info "Checking Firebase project..."
    
    if ! firebase projects:list 2>/dev/null | grep -q "${PROJECT_ID}"; then
        print_error "Firebase project '${PROJECT_ID}' not found or not accessible"
        print_info "Available projects:"
        firebase projects:list 2>/dev/null || true
        exit 1
    fi
    
    print_info "Firebase project '${PROJECT_ID}' verified"
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
    
    # Check if npm is installed
    if ! command -v npm &> /dev/null; then
        print_error "npm is not installed. Please install Node.js and npm first."
        exit 1
    fi
    
    # Check Firebase CLI
    check_firebase_cli
    check_firebase_auth
    check_firebase_project
    
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
    
    # Construct Firebase Hosting URLs for CORS
    # Requirements: 1.3 (Firebase Hosting Migration)
    FIREBASE_CORS_ORIGINS="https://${PROJECT_ID}.web.app,https://${PROJECT_ID}.firebaseapp.com"
    
    # Deploy to Cloud Run
    gcloud run deploy "${BACKEND_SERVICE}" \
        --source . \
        --platform managed \
        --region "${REGION}" \
        --allow-unauthenticated \
        --set-env-vars PROJECT_ID="${PROJECT_ID}",LOCATION="${REGION}",ENVIRONMENT=production,FIREBASE_PROJECT_ID="${PROJECT_ID}",CORS_ORIGINS="${FIREBASE_CORS_ORIGINS}" \
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
    print_info "CORS configured for Firebase Hosting URLs:"
    print_info "  - https://${PROJECT_ID}.web.app"
    print_info "  - https://${PROJECT_ID}.firebaseapp.com"
    
    cd ..
    
    # Export for frontend build
    export VITE_API_URL="${BACKEND_URL}"
}

deploy_frontend() {
    print_info "Deploying frontend to Firebase Hosting..."
    
    cd frontend
    
    # Install dependencies
    print_info "Installing frontend dependencies..."
    npm ci
    
    # Build
    print_info "Building frontend..."
    npm run build
    
    # Deploy to Firebase Hosting
    print_info "Deploying to Firebase Hosting..."
    firebase deploy \
        --only hosting \
        --project "${PROJECT_ID}" \
        --non-interactive
    
    # Construct Firebase Hosting URL
    FRONTEND_URL="https://${PROJECT_ID}.web.app"
    
    print_info "Frontend deployed successfully"
    print_info "Frontend URL: ${FRONTEND_URL}"
    
    cd ..
    
    # Export for verification
    export FRONTEND_URL
}

check_frontend_health() {
    local frontend_url="$1"
    local temp_file=$(mktemp)
    
    print_info "Checking frontend health at ${frontend_url}..."
    
    # Make request and capture headers
    if curl -s -o /dev/null -w "%{http_code}" -D "${temp_file}" "${frontend_url}" > /tmp/status_code.txt 2>&1; then
        local status_code=$(cat /tmp/status_code.txt)
        
        # Check if index.html is accessible with 200 status
        if [ "${status_code}" = "200" ]; then
            print_info "✓ Frontend is accessible (HTTP ${status_code})"
            
            # Extract and validate cache headers
            if grep -qi "cache-control" "${temp_file}"; then
                local cache_header=$(grep -i "cache-control" "${temp_file}" | cut -d: -f2- | tr -d '\r')
                print_info "  Cache-Control:${cache_header}"
                
                # Validate cache headers contain expected values
                if echo "${cache_header}" | grep -qi "public"; then
                    print_info "  ✓ Cache headers are configured"
                else
                    print_warning "  Cache headers may not be optimal"
                fi
            else
                print_warning "  Cache-Control header not found"
            fi
            
            rm -f "${temp_file}" /tmp/status_code.txt
            return 0
        else
            print_error "✗ Frontend returned HTTP ${status_code}"
            print_info "Diagnostic Information:"
            print_info "  - URL: ${frontend_url}"
            print_info "  - Status: ${status_code}"
            print_info "  - Verify Firebase deployment completed successfully"
            print_info "  - Check Firebase Hosting configuration"
            rm -f "${temp_file}" /tmp/status_code.txt
            return 1
        fi
    else
        print_error "✗ Frontend health check failed"
        print_info "Diagnostic Information:"
        print_info "  - URL: ${frontend_url}"
        print_info "  - Error: Connection failed or timeout"
        print_info "  - Verify Firebase deployment completed successfully"
        print_info "  - Check Firebase Hosting configuration"
        print_info "  - Ensure DNS records are properly configured"
        rm -f "${temp_file}" /tmp/status_code.txt
        return 1
    fi
}

verify_deployment() {
    print_info "Verifying deployment..."
    
    # Check backend health
    if curl -f "${VITE_API_URL}/health" &> /dev/null; then
        print_info "✓ Backend health check passed"
    else
        print_warning "✗ Backend health check failed"
    fi
    
    # Check frontend with detailed health check
    if check_frontend_health "${FRONTEND_URL}"; then
        print_info "✓ Frontend health check passed"
    else
        print_warning "✗ Frontend health check failed (see diagnostic info above)"
    fi
}

print_summary() {
    echo ""
    echo "=========================================="
    echo "Deployment Summary"
    echo "=========================================="
    echo "Project ID: ${PROJECT_ID}"
    echo "Region: ${REGION}"
    echo ""
    echo "Backend URL: ${VITE_API_URL}"
    echo "CORS Origins: Configured for Firebase Hosting"
    echo "  ✓ https://${PROJECT_ID}.web.app"
    echo "  ✓ https://${PROJECT_ID}.firebaseapp.com"
    echo ""
    echo -e "${GREEN}Frontend URL: ${FRONTEND_URL}${NC}"
    echo "Alternative URL: https://${PROJECT_ID}.firebaseapp.com"
    echo ""
    echo "Next steps:"
    echo "1. Visit ${FRONTEND_URL} to verify the application"
    echo "2. Test API communication from frontend to backend"
    echo "3. Configure a custom domain (optional)"
    echo "4. Configure monitoring and alerts"
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
