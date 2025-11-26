# Requirements Document

## Introduction

The vibehuntr-agent currently fails to capture and retain user price preferences during venue search conversations. When users specify budget constraints (e.g., "cheap restaurants", "under $20", "$$"), this information is not stored in the conversation context, forcing users to repeat their price preferences in subsequent queries. This feature will add price preference tracking to the context manager to improve conversation continuity.

## Glossary

- **Context Manager**: The system component that tracks conversation state and entities across turns
- **Price Preference**: User-specified budget constraints expressed as price levels (1-4) or natural language terms
- **Price Level**: Google Places API price scale where 1=inexpensive, 2=moderate, 3=expensive, 4=very expensive
- **Conversation Context**: The data structure that stores extracted information from user and agent messages

## Requirements

### Requirement 1

**User Story:** As a user, I want my price preferences to be remembered during a conversation, so that I don't have to repeat my budget constraints for every venue search.

#### Acceptance Criteria

1. WHEN a user mentions a price preference in natural language (e.g., "cheap", "budget", "expensive"), THEN the system SHALL extract and store the corresponding price level (1-4)
2. WHEN a user mentions a specific price symbol (e.g., "$", "$$", "$$$", "$$$$"), THEN the system SHALL map it to the corresponding price level (1-4)
3. WHEN a user mentions a dollar amount budget (e.g., "under $20", "around $50"), THEN the system SHALL map it to an appropriate price level
4. WHEN price preference is stored in context, THEN the system SHALL include it in the context string injected into agent messages
5. WHEN a user performs a venue search with price preference in context, THEN the system SHALL automatically apply the max_price filter without requiring the user to repeat it

### Requirement 2

**User Story:** As a user, I want the agent to use my stated price preferences when searching for venues, so that search results match my budget constraints.

#### Acceptance Criteria

1. WHEN the context contains a price preference and the user requests a venue search, THEN the agent SHALL use the stored price level as the max_price parameter
2. WHEN search results are returned, THEN venues exceeding the user's price preference SHALL be clearly marked
3. WHEN a user updates their price preference, THEN the system SHALL replace the old preference with the new one
4. WHEN a user clears their session, THEN the system SHALL remove the stored price preference

### Requirement 3

**User Story:** As a developer, I want price preference extraction to handle various natural language expressions, so that users can express budget constraints naturally.

#### Acceptance Criteria

1. WHEN a user uses terms like "cheap", "inexpensive", "budget", "affordable", THEN the system SHALL map to price level 1
2. WHEN a user uses terms like "moderate", "mid-range", "reasonable", THEN the system SHALL map to price level 2
3. WHEN a user uses terms like "expensive", "upscale", "fancy", "nice", THEN the system SHALL map to price level 3
4. WHEN a user uses terms like "very expensive", "luxury", "high-end", "splurge", THEN the system SHALL map to price level 4
5. WHEN a user mentions dollar amounts, THEN the system SHALL map them to price levels using reasonable thresholds (e.g., <$15=1, $15-30=2, $30-60=3, >$60=4)
