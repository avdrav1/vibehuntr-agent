"""Vibehuntr-branded Streamlit playground.

Run with: streamlit run vibehuntr_playground.py
"""

import streamlit as st
import logging
from datetime import datetime
from app.playground_style import VIBEHUNTR_STYLE, VIBEHUNTR_HEADER
from app.event_planning.session_manager import SessionManager, SessionError
from app.event_planning.agent_loader import get_agent
from app.event_planning.agent_invoker import invoke_agent_streaming, AgentInvocationError

# Configure logging with detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="Vibehuntr - Event Planning AI",
    page_icon="🎉",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply custom styling
st.markdown(VIBEHUNTR_STYLE, unsafe_allow_html=True)
st.markdown(VIBEHUNTR_HEADER, unsafe_allow_html=True)

# Initialize session manager
if "session_manager" not in st.session_state:
    st.session_state.session_manager = SessionManager()
    logger.info("Initialized SessionManager")

session_manager = st.session_state.session_manager

# Initialize unique session ID for ADK
if "adk_session_id" not in st.session_state:
    import uuid
    st.session_state.adk_session_id = str(uuid.uuid4())
    logger.info(f"Created ADK session ID: {st.session_state.adk_session_id}")

# Initialize agent (with comprehensive error handling)
if "agent_loaded" not in st.session_state:
    st.session_state.agent_loaded = False
    st.session_state.agent_error = None
    st.session_state.agent_error_type = None

# Initialize processing flag to prevent duplicate processing
if "is_processing" not in st.session_state:
    st.session_state.is_processing = False

if not st.session_state.agent_loaded:
    try:
        agent = get_agent()
        session_manager.set_agent(agent)
        st.session_state.agent_loaded = True
        logger.info("Agent loaded successfully")
    except ImportError as e:
        # Agent module import failed
        error_type = "Configuration Error"
        st.session_state.agent_error = str(e)
        st.session_state.agent_error_type = error_type
        logger.error(
            f"Agent loading failed - {error_type}: {e}",
            extra={
                "timestamp": datetime.now().isoformat(),
                "error_type": error_type,
                "session_id": st.session_state.get("adk_session_id", "unknown")
            },
            exc_info=True
        )
    except RuntimeError as e:
        # Agent initialization failed
        error_type = "Initialization Error"
        st.session_state.agent_error = str(e)
        st.session_state.agent_error_type = error_type
        logger.error(
            f"Agent loading failed - {error_type}: {e}",
            extra={
                "timestamp": datetime.now().isoformat(),
                "error_type": error_type,
                "session_id": st.session_state.get("adk_session_id", "unknown")
            },
            exc_info=True
        )
    except Exception as e:
        # Unexpected error
        error_type = "Unexpected Error"
        st.session_state.agent_error = str(e)
        st.session_state.agent_error_type = error_type
        logger.error(
            f"Agent loading failed - {error_type}: {e}",
            extra={
                "timestamp": datetime.now().isoformat(),
                "error_type": error_type,
                "session_id": st.session_state.get("adk_session_id", "unknown")
            },
            exc_info=True
        )

# Display agent loading error if present (with Vibehuntr styling)
if st.session_state.agent_error:
    error_type = st.session_state.get("agent_error_type", "Error")
    
    # Display user-friendly error message
    st.error(f"🚫 {error_type}: Unable to load the agent")
    
    # Provide helpful context based on error type
    if "Configuration" in error_type or "Import" in str(st.session_state.agent_error):
        st.info("""
        **Troubleshooting Steps:**
        - Check that the `USE_DOCUMENT_RETRIEVAL` environment variable is set correctly
        - Ensure all required dependencies are installed (`uv sync`)
        - Verify your Google Cloud credentials are configured
        - Check that the agent module exists in the expected location
        """)
    elif "Initialization" in error_type:
        st.info("""
        **Troubleshooting Steps:**
        - Verify your API keys are set correctly
        - Check your network connection
        - Ensure GCP services are accessible
        """)
    else:
        st.info("Please check the logs for more details or contact support.")
    
    # Show detailed error in expander for debugging
    with st.expander("🔍 Show Technical Details"):
        st.code(str(st.session_state.agent_error), language="text")
    
    st.stop()

# Display all messages from history
all_messages = session_manager.get_all_messages()

if len(all_messages) == 0:
    st.markdown("""
    <div style="text-align: center; padding: 2rem; margin: 2rem 0;">
        <h2 style="color: #FF6B9D;">👋 Welcome to Vibehuntr!</h2>
        <p style="font-size: 1.1rem; color: #666;">
            I'm your AI event planning assistant. I can help you:
        </p>
        <ul style="text-align: left; display: inline-block; font-size: 1rem; color: #666;">
            <li>🎉 Plan events and gatherings</li>
            <li>📍 Find perfect venues</li>
            <li>👥 Manage groups and attendees</li>
            <li>📅 Coordinate schedules</li>
        </ul>
        <p style="font-size: 1.1rem; color: #666; margin-top: 1rem;">
            What would you like to plan today?
        </p>
    </div>
    """, unsafe_allow_html=True)
else:
    # Show older messages in an expander if there are more than 10 messages
    if session_manager.should_show_history_button(recent_count=10):
        with st.expander("📜 Show Older Messages"):
            older_messages = session_manager.get_older_messages(recent_count=10)
            for message in older_messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

    # Display recent messages (last 10)
    recent_messages = session_manager.get_messages(recent_only=True, recent_count=10)
    for message in recent_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Chat input
prompt = st.chat_input("What would you like to plan today?")

if prompt:
    # Add user message to history
    session_manager.add_message("user", prompt)
    
    # Display user message immediately
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get agent response with streaming display
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            agent = session_manager.get_agent()
            
            if agent:
                # Stream the response
                for item in invoke_agent_streaming(
                    agent,
                    prompt,
                    session_id=st.session_state.adk_session_id,
                    user_id="playground_user",
                    yield_tool_calls=False
                ):
                    if item['type'] == 'text':
                        full_response += item['content']
                        message_placeholder.markdown(full_response + "▌")
                
                # Remove cursor
                message_placeholder.markdown(full_response)
            else:
                full_response = "🚫 Agent Error: Agent not loaded."
                message_placeholder.error(full_response)
        
        except Exception as e:
            full_response = f"🚫 Error: {str(e)}"
            message_placeholder.error(full_response)
            logger.error(f"Error during streaming: {e}", exc_info=True)
    
    # Add assistant response to history
    session_manager.add_message("assistant", full_response)

# Sidebar (with error handling)
with st.sidebar:
    st.markdown("### About")
    st.markdown("AI-powered event planning assistant")
    
    st.markdown("---")
    
    # New Conversation button with confirmation
    if "confirm_clear" not in st.session_state:
        st.session_state.confirm_clear = False
    
    # Check if there are messages to clear (with error handling)
    try:
        has_messages = len(session_manager.get_all_messages()) > 0
    except Exception as e:
        logger.error(f"Failed to check message count: {e}")
        has_messages = False
    
    if not st.session_state.confirm_clear:
        if st.button("🔄 New Conversation", disabled=not has_messages):
            if has_messages:
                st.session_state.confirm_clear = True
                st.rerun()
    else:
        st.warning("⚠️ Clear conversation history?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Yes", use_container_width=True):
                try:
                    # Clear session and get new session ID
                    old_session_id = st.session_state.adk_session_id
                    new_session_id = session_manager.clear_session()
                    
                    # Update the ADK session ID in session state
                    st.session_state.adk_session_id = new_session_id
                    st.session_state.confirm_clear = False
                    
                    logger.info(
                        f"User confirmed conversation clear - new session created",
                        extra={
                            "timestamp": datetime.now().isoformat(),
                            "old_session_id": old_session_id,
                            "new_session_id": new_session_id
                        }
                    )
                    st.rerun()
                except Exception as e:
                    # Handle error gracefully
                    logger.error(
                        f"Failed to clear session: {e}",
                        extra={
                            "timestamp": datetime.now().isoformat(),
                            "session_id": st.session_state.get("adk_session_id", "unknown")
                        }
                    )
                    st.error("Failed to clear conversation. Please refresh the page.")
        with col2:
            if st.button("❌ No", use_container_width=True):
                st.session_state.confirm_clear = False
                st.rerun()
    
    # Show agent status
    st.markdown("---")
    st.markdown("### Agent Status")
    if st.session_state.agent_loaded:
        st.success("✅ Agent Ready")
    else:
        st.error("❌ Agent Not Loaded")
    
    # Show processing status
    if st.session_state.get("is_processing", False):
        st.info("⏳ Processing...")
