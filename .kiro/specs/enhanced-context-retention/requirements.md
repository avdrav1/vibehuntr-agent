# Requirements Document: Enhanced Context Retention

## Introduction

This specification addresses the persistent context retention issues in the Vibehuntr agent where the agent fails to remember information from previous messages in the conversation, particularly location information and entity references. The agent currently asks users to repeat information that was already provided, creating a frustrating user experience.

## Glossary

- **Agent**: The AI assistant (Vibehuntr) that processes user messages and generates responses
- **Context**: Information from previous conversation turns including entities, locations, intents, and references
- **Session**: A continuous conversation between a user and the agent, identified by a session_id
- **Entity**: A specific piece of information mentioned in conversation (venue, location, Place ID, event, etc.)
- **ADK Session Service**: Google's Agent Development Kit session management system that maintains conversation history
- **Context Manager**: Custom module that tracks and injects structured context into messages
- **Enhanced Message**: User message with injected context information prepended

## Requirements

### Requirement 1: Location Persistence

**User Story:** As a user, I want the agent to remember the location I specified, so that I don't have to repeat it in every message.

#### Acceptance Criteria

1. WHEN a user mentions a location in any message THEN the System SHALL extract and store that location in the session context
2. WHEN a user sends a follow-up message without specifying location THEN the System SHALL use the previously stored location for any location-dependent operations
3. WHEN the System processes a message with stored location context THEN the System SHALL inject the location into the message before sending to the agent
4. WHEN a user explicitly changes the location THEN the System SHALL update the stored location and use the new value for subsequent messages
5. WHEN a new session starts THEN the System SHALL initialize with no stored location

### Requirement 2: Entity Reference Resolution

**User Story:** As a user, I want to refer to venues or entities mentioned in previous messages using natural language like "that one" or "the first one", so that I can have a natural conversation.

#### Acceptance Criteria

1. WHEN the agent mentions venues with Place IDs in a response THEN the System SHALL extract and store those venue references in session context
2. WHEN a user uses a vague reference like "that one", "the first one", or "more details" THEN the System SHALL resolve the reference to the most recently mentioned entity
3. WHEN the System resolves an entity reference THEN the System SHALL inject the resolved entity information (Place ID, name) into the message context
4. WHEN multiple venues are mentioned THEN the System SHALL maintain an ordered list of recent venues (up to 5) for reference resolution
5. WHEN a user refers to an entity by ordinal position ("first", "second") THEN the System SHALL resolve to the correct entity from the ordered list

### Requirement 3: Search Query Persistence

**User Story:** As a user, I want the agent to remember what I'm searching for, so that follow-up questions maintain the search context.

#### Acceptance Criteria

1. WHEN a user specifies a search query (food type, activity, venue type) THEN the System SHALL extract and store the query in session context
2. WHEN a user sends a follow-up message related to the search THEN the System SHALL inject the stored search query into the message context
3. WHEN a user starts a new search topic THEN the System SHALL update the stored search query to the new topic
4. WHEN the System injects search context THEN the System SHALL include both the query and the location if both are available
5. WHEN a session ends THEN the System SHALL clear the stored search query

### Requirement 4: Agent Response Memory

**User Story:** As a developer, I want the agent to have access to its own previous responses, so that it can reference information it already provided.

#### Acceptance Criteria

1. WHEN the agent generates a response THEN the System SHALL parse the response for extractable entities (venues, Place IDs, events)
2. WHEN entities are found in the agent response THEN the System SHALL store them in the session context
3. WHEN the System injects context THEN the System SHALL include recently mentioned entities from both user and agent messages
4. WHEN the agent needs to reference a previous entity THEN the System SHALL provide the entity information in the injected context
5. WHEN the context becomes too large THEN the System SHALL keep only the most recent 3 entities to avoid token limit issues

### Requirement 5: Explicit Context Injection

**User Story:** As a developer, I want to explicitly inject structured context into every message, so that the agent has reliable access to conversation state.

#### Acceptance Criteria

1. WHEN a user message is processed THEN the System SHALL generate a context string from the session context
2. WHEN a context string is generated THEN the System SHALL format it as "[CONTEXT: key1: value1 | key2: value2]"
3. WHEN a context string exists THEN the System SHALL prepend it to the user message before sending to the agent
4. WHEN no context exists THEN the System SHALL send the user message without modification
5. WHEN context is injected THEN the System SHALL log the injected context for debugging purposes

### Requirement 6: Agent Instruction Enhancement

**User Story:** As a developer, I want the agent instructions to explicitly emphasize context retention, so that the agent is trained to use conversation history effectively.

#### Acceptance Criteria

1. WHEN the agent is initialized THEN the System SHALL include explicit context retention rules in the agent instructions
2. WHEN the agent instructions are defined THEN the System SHALL include examples of correct context usage
3. WHEN the agent instructions are defined THEN the System SHALL include examples of incorrect behavior to avoid
4. WHEN the agent processes a message THEN the System SHALL follow the context retention rules defined in instructions
5. WHEN the agent generates a response THEN the System SHALL avoid asking for information already provided in the conversation

### Requirement 7: Context Debugging and Observability

**User Story:** As a developer, I want to see what context is being injected and tracked, so that I can debug context retention issues.

#### Acceptance Criteria

1. WHEN context is extracted from a message THEN the System SHALL log the extracted information with session_id
2. WHEN context is injected into a message THEN the System SHALL log the complete injected context string
3. WHEN an entity is stored in context THEN the System SHALL log the entity type and key information
4. WHEN context is retrieved for a session THEN the System SHALL log the current context state
5. WHEN context operations fail THEN the System SHALL log detailed error information without breaking the message flow

### Requirement 8: Context Persistence Across Message Turns

**User Story:** As a user, I want the agent to maintain context across multiple message turns, so that I can have a coherent multi-turn conversation.

#### Acceptance Criteria

1. WHEN a user sends multiple messages in sequence THEN the System SHALL accumulate context across all messages
2. WHEN context is updated THEN the System SHALL preserve previous context values unless explicitly overridden
3. WHEN a user sends a message THEN the System SHALL have access to context from all previous messages in the session
4. WHEN the System updates context THEN the System SHALL merge new information with existing context
5. WHEN context conflicts occur (e.g., two different locations) THEN the System SHALL use the most recent value

### Requirement 9: Model Selection for Context Retention

**User Story:** As a developer, I want to use the LLM model with the best context retention capabilities, so that the agent can effectively use conversation history.

#### Acceptance Criteria

1. WHEN the agent is initialized THEN the System SHALL use gemini-2.0-flash-exp model for improved context retention
2. WHEN the model is configured THEN the System SHALL use ADK's session service for automatic history management
3. WHEN the agent processes a message THEN the System SHALL have access to both ADK-managed history and injected context
4. WHEN model performance is insufficient THEN the System SHALL support upgrading to gemini-2.5-flash or other models
5. WHEN the model is changed THEN the System SHALL maintain backward compatibility with existing context injection

### Requirement 10: Context Clearing and Session Management

**User Story:** As a user, I want to start a fresh conversation when I click "New Conversation", so that previous context doesn't interfere with new topics.

#### Acceptance Criteria

1. WHEN a user starts a new session THEN the System SHALL create a new session_id with empty context
2. WHEN a user explicitly clears the session THEN the System SHALL remove all stored context for that session
3. WHEN a session is cleared THEN the System SHALL log the session_id and timestamp of the clear operation
4. WHEN a new session is created THEN the System SHALL not have access to context from previous sessions
5. WHEN the System manages multiple sessions THEN the System SHALL maintain separate context for each session_id

### Requirement 11: Context Visibility UI

**User Story:** As a user, I want to see what information the agent is remembering about our conversation, so that I understand what context is being used and can verify it's correct.

#### Acceptance Criteria

1. WHEN the UI displays the chat interface THEN the System SHALL provide a visual indicator showing active context
2. WHEN context exists for the session THEN the System SHALL display the stored location, search query, and recent entities in a dedicated UI component
3. WHEN a user views the context display THEN the System SHALL show the information in a clear, readable format (e.g., chips, badges, or a sidebar)
4. WHEN context is updated during conversation THEN the System SHALL update the context display in real-time
5. WHEN no context exists THEN the System SHALL either hide the context display or show an empty state message
6. WHEN a user interacts with the context display THEN the System SHALL provide the ability to clear individual context items or all context
7. WHEN context items are displayed THEN the System SHALL use visual design consistent with the Vibehuntr theme (dark mode, purple accents)
