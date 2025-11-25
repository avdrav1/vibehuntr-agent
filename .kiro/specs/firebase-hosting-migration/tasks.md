# Implementation Plan

- [x] 1. Create Firebase configuration files
  - Create `firebase.json` in frontend directory with hosting configuration
  - Configure `dist` as public directory
  - Add SPA rewrite rules to serve index.html for all routes
  - Configure cache headers for static assets (31536000s) and HTML (3600s)
  - Create `.firebaserc` file with project configuration
  - Add Firebase cache files to `.gitignore`
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 1.1 Write unit tests for Firebase configuration
  - Test firebase.json structure is valid
  - Test cache headers are correctly configured
  - Test rewrite rules include SPA routing
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 2. Update deployment script with Firebase CLI integration
  - Add Firebase CLI installation check function
  - Add Firebase authentication verification function
  - Replace Cloud Storage bucket creation with Firebase project check
  - Replace gsutil upload commands with `firebase deploy --only hosting`
  - Update frontend URL construction to use Firebase Hosting URL format
  - Preserve backend deployment logic (no changes needed)
  - _Requirements: 1.1, 1.2, 3.1, 3.2, 3.4_

- [x] 2.1 Write property test for deployment error handling
  - **Property 3: Deployment script handles all failure types**
  - **Validates: Requirements 3.5**

- [x] 3. Update deployment script health checks
  - Modify health check to use Firebase Hosting URL instead of Cloud Storage URL
  - Verify index.html is accessible with 200 status
  - Add check for correct cache headers in response
  - Display Firebase Hosting URL on successful deployment
  - _Requirements: 1.5, 7.1, 7.2, 7.5_

- [x] 3.1 Write unit tests for health check functions
  - Test health check validates index.html accessibility
  - Test health check reports failures with diagnostic info
  - Test successful deployment displays correct URL
  - _Requirements: 7.1, 7.2, 7.4, 7.5_

- [x] 4. Update backend CORS configuration
  - Add Firebase Hosting URLs to CORS origins in backend config
  - Include both `.web.app` and `.firebaseapp.com` domains
  - Update Cloud Run environment variables with new CORS origins
  - Test CORS configuration allows requests from Firebase Hosting
  - _Requirements: 1.3_

- [x] 5. Remove Cloud Storage hosting code
  - Remove gsutil bucket creation commands from deployment script
  - Remove gsutil IAM and web configuration commands
  - Remove gsutil rsync upload commands
  - Remove gsutil setmeta cache header commands
  - Remove Cloud Storage bucket name variables
  - Keep any non-hosting Cloud Storage usage intact
  - _Requirements: 5.1, 5.2, 5.3, 5.5_

- [x] 6. Update production deployment documentation
  - Replace Cloud Storage section with Firebase Hosting in PRODUCTION_DEPLOYMENT.md
  - Add Firebase CLI installation instructions
  - Document Firebase authentication process (`firebase login`)
  - Add step-by-step Firebase project setup instructions
  - Document custom domain configuration for Firebase Hosting
  - Add Firebase-specific troubleshooting section
  - Remove Cloud Storage hosting instructions
  - Update architecture diagrams to show Firebase Hosting
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 5.4_

- [x] 7. Write property test for SPA routing
  - **Property 2: SPA routing serves index.html for all routes**
  - **Validates: Requirements 2.3**

- [x] 8. Write property test for static asset caching
  - **Property 4: Static assets have long-term cache headers**
  - **Validates: Requirements 6.1**

- [x] 9. Write property test for HTTPS enforcement
  - **Property 5: HTTPS is enforced for all requests**
  - **Validates: Requirements 6.5**

- [x] 10. Write integration test for deployment workflow
  - Test complete deployment from build to Firebase
  - Verify frontend is accessible at Firebase URL
  - Verify API communication works from deployed frontend
  - Verify all application routes return 200 status
  - Test CORS integration between Firebase frontend and Cloud Run backend
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 11. Write property test for functionality preservation
  - **Property 1: Deployment preserves all functionality**
  - **Validates: Requirements 1.3**

- [ ] 12. Final checkpoint - Verify complete migration
  - Ensure all tests pass, ask the user if questions arise
  - Deploy to Firebase Hosting and verify clean URL works
  - Test all application routes and features
  - Verify API communication with backend
  - Check browser console for errors
  - Verify cache headers in browser DevTools
  - Confirm HTTPS is enforced
  - Validate deployment script runs without errors
