#!/bin/bash

# Production Rollback Script for Vibehuntr
# This script helps rollback deployments to previous versions

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

check_prerequisites() {
    print_info "Checking prerequisites..."
    
    if ! command -v gcloud &> /dev/null; then
        print_error "gcloud CLI is not installed"
        exit 1
    fi
    
    if [ -z "$PROJECT_ID" ]; then
        print_error "GCP_PROJECT_ID environment variable is not set"
        exit 1
    fi
    
    print_info "Prerequisites check passed"
}

list_backend_revisions() {
    print_info "Available backend revisions:"
    echo ""
    
    gcloud run revisions list \
        --service "${BACKEND_SERVICE}" \
        --region "${REGION}" \
        --project "${PROJECT_ID}" \
        --format="table(metadata.name,status.conditions[0].status,metadata.creationTimestamp)"
}

rollback_backend() {
    list_backend_revisions
    
    echo ""
    read -p "Enter the revision name to rollback to: " REVISION_NAME
    
    if [ -z "$REVISION_NAME" ]; then
        print_error "No revision name provided"
        exit 1
    fi
    
    print_warning "Rolling back backend to revision: ${REVISION_NAME}"
    read -p "Are you sure? (yes/no): " CONFIRM
    
    if [ "$CONFIRM" != "yes" ]; then
        print_info "Rollback cancelled"
        exit 0
    fi
    
    gcloud run services update-traffic "${BACKEND_SERVICE}" \
        --to-revisions "${REVISION_NAME}=100" \
        --region "${REGION}" \
        --project "${PROJECT_ID}"
    
    print_info "Backend rolled back successfully"
}

rollback_frontend() {
    print_info "Rolling back frontend deployment..."
    
    # List recent Firebase Hosting releases
    print_info "Recent Firebase Hosting releases:"
    firebase hosting:releases:list --project "${PROJECT_ID}" 2>/dev/null || {
        print_error "Failed to list Firebase releases. Ensure Firebase CLI is authenticated."
        return 1
    }
    
    echo ""
    print_warning "Firebase Hosting maintains deployment history automatically"
    print_info "To rollback frontend:"
    echo "1. Run: firebase hosting:rollback --project ${PROJECT_ID}"
    echo "2. Or deploy a specific version from your git history"
    echo ""
    
    read -p "Would you like to rollback to the previous version now? (yes/no): " CONFIRM
    
    if [ "$CONFIRM" = "yes" ]; then
        firebase hosting:rollback --project "${PROJECT_ID}"
        print_info "Frontend rolled back successfully"
    else
        print_info "Rollback cancelled"
    fi
}

show_menu() {
    echo ""
    echo "=========================================="
    echo "Vibehuntr Rollback Menu"
    echo "=========================================="
    echo "1. Rollback Backend (Cloud Run)"
    echo "2. Show Frontend Rollback Instructions"
    echo "3. Exit"
    echo "=========================================="
    echo ""
}

# Main execution
main() {
    check_prerequisites
    
    while true; do
        show_menu
        read -p "Select an option: " OPTION
        
        case $OPTION in
            1)
                rollback_backend
                ;;
            2)
                rollback_frontend
                ;;
            3)
                print_info "Exiting..."
                exit 0
                ;;
            *)
                print_error "Invalid option"
                ;;
        esac
    done
}

# Run main function
main
