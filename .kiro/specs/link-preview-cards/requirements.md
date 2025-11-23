# Requirements Document

## Introduction

This feature adds embedded link preview cards to chat messages. When the agent includes URLs in responses, the system will automatically fetch metadata (title, description, image) and display rich preview cards below the message, similar to how links appear in Slack, Discord, or Twitter.

## Glossary

- **Link Preview Card**: A rich visual component displaying metadata about a URL, including title, description, favicon, and preview image
- **Open Graph Protocol**: A standard for web page metadata used by social media platforms
- **Frontend**: The React-based user interface (TypeScript/React)
- **Backend**: The FastAPI Python service
- **Message Component**: The React component that renders individual chat messages
- **URL Extraction**: The process of identifying and parsing URLs from message text

## Requirements

### Requirement 1

**User Story:** As a user, I want to see rich preview cards for links in chat messages, so that I can quickly understand what a link contains before clicking it.

#### Acceptance Criteria

1. WHEN an assistant message contains one or more URLs THEN the system SHALL extract all valid HTTP/HTTPS URLs from the message content
2. WHEN a URL is detected THEN the system SHALL fetch metadata including title, description, image URL, and favicon
3. WHEN metadata is successfully fetched THEN the system SHALL display a preview card below the message with the fetched information
4. WHEN metadata fetch fails THEN the system SHALL display a minimal preview card with just the URL and domain name
5. WHEN multiple URLs are present in a message THEN the system SHALL display preview cards for all URLs in the order they appear

### Requirement 2

**User Story:** As a user, I want link preview cards to match the Vibehuntr design aesthetic, so that the interface feels cohesive and polished.

#### Acceptance Criteria

1. WHEN a link preview card is displayed THEN the card SHALL use the Vibehuntr color scheme with gradient accents
2. WHEN a user hovers over a preview card THEN the card SHALL show a subtle animation or highlight effect
3. WHEN a preview image is available THEN the image SHALL be displayed with appropriate aspect ratio and rounded corners
4. WHEN no preview image is available THEN the card SHALL display a fallback icon or gradient background
5. WHEN the card is clicked THEN the link SHALL open in a new browser tab with security attributes

### Requirement 3

**User Story:** As a developer, I want link preview metadata to be fetched server-side, so that we avoid CORS issues and can cache results efficiently.

#### Acceptance Criteria

1. WHEN the frontend detects URLs in a message THEN the frontend SHALL send a request to the backend API with the list of URLs
2. WHEN the backend receives a metadata request THEN the backend SHALL fetch HTML content from each URL
3. WHEN HTML content is retrieved THEN the backend SHALL parse Open Graph tags, Twitter Card tags, and standard HTML meta tags
4. WHEN metadata is extracted THEN the backend SHALL return a structured response with title, description, image, favicon, and domain
5. WHEN a URL has been fetched recently THEN the backend SHALL return cached metadata to improve performance

### Requirement 4

**User Story:** As a user, I want link previews to load quickly without blocking the chat interface, so that I can continue my conversation smoothly.

#### Acceptance Criteria

1. WHEN a message with URLs is displayed THEN the message content SHALL render immediately without waiting for metadata
2. WHEN metadata is being fetched THEN the system SHALL show a loading skeleton or placeholder in the preview card area
3. WHEN metadata fetch completes THEN the preview card SHALL fade in smoothly with the fetched content
4. WHEN metadata fetch takes longer than 5 seconds THEN the system SHALL timeout and show a minimal preview
5. WHEN the user scrolls away from a message THEN ongoing metadata fetches SHALL continue in the background

### Requirement 5

**User Story:** As a user, I want link previews to handle errors gracefully, so that broken links don't disrupt my chat experience.

#### Acceptance Criteria

1. WHEN a URL returns a 404 or 5xx error THEN the system SHALL display a minimal preview card indicating the link is unavailable
2. WHEN a URL times out THEN the system SHALL display a minimal preview card with just the domain name
3. WHEN a URL is malformed THEN the system SHALL not display a preview card and leave the URL as plain text
4. WHEN metadata parsing fails THEN the system SHALL fall back to displaying the domain name and URL
5. WHEN an image URL fails to load THEN the system SHALL hide the image section and show only text metadata

### Requirement 6

**User Story:** As a developer, I want to exclude certain URL patterns from preview generation, so that we don't create previews for internal links or special URLs.

#### Acceptance Criteria

1. WHEN a URL matches an excluded pattern THEN the system SHALL not generate a preview card for that URL
2. WHEN a URL is a localhost or internal IP address THEN the system SHALL not attempt to fetch metadata
3. WHEN a URL is a data URI or blob URL THEN the system SHALL not generate a preview
4. WHEN a URL is already handled by the venue links feature THEN the system SHALL not duplicate it with a preview card
5. WHEN configuration specifies excluded domains THEN the system SHALL skip preview generation for those domains

### Requirement 7

**User Story:** As a user, I want link previews to be accessible, so that screen readers and keyboard navigation work properly.

#### Acceptance Criteria

1. WHEN a preview card is rendered THEN the card SHALL include appropriate ARIA labels and roles
2. WHEN a user navigates with keyboard THEN the preview card SHALL be focusable and activatable with Enter key
3. WHEN a screen reader encounters a preview card THEN it SHALL announce the link title and description
4. WHEN an image is displayed THEN it SHALL include alt text from the metadata or a descriptive fallback
5. WHEN a preview card is focused THEN it SHALL show a visible focus indicator

### Requirement 8

**User Story:** As a developer, I want link preview functionality to be testable, so that we can ensure reliability and catch regressions.

#### Acceptance Criteria

1. WHEN unit tests run THEN the URL extraction logic SHALL be tested with various message formats
2. WHEN unit tests run THEN the metadata parsing logic SHALL be tested with sample HTML responses
3. WHEN integration tests run THEN the frontend-backend metadata flow SHALL be tested end-to-end
4. WHEN property-based tests run THEN the URL extraction SHALL handle randomly generated message content correctly
5. WHEN property-based tests run THEN the metadata parser SHALL handle randomly generated HTML content without crashing
