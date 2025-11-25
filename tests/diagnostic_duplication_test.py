#!/usr/bin/env python3
"""
Comprehensive diagnostic test for response duplication.

This test logs all pipeline stages to identify where duplication originates:
1. Agent level (LLM generating duplicate content)
2. Runner level (ADK Runner yielding duplicate events)
3. Streaming level (Token yielding duplicates)
4. Session level (Session history containing duplicates)

Usage:
    python tests/diagnostic_duplication_test.py

Requirements:
    - GOOGLE_API_KEY environment variable set, OR
    - Google Cloud credentials configured via `gcloud auth application-default login`
"""

import os
import sys
import logging
from datetime import datetime
from typing import List, Dict, Any
import hashlib

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.event_planning.agent_loader import get_agent
from app.event_planning.agent_invoker import invoke_agent_streaming, _session_service
from google.adk.runners import Runner
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.genai import types

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('diagnostic_duplication.log', mode='w')
    ]
)

logger = logging.getLogger(__name__)


class DiagnosticCollector:
    """Collects diagnostic information at each pipeline stage."""
    
    def __init__(self):
        self.events: List[Dict[str, Any]] = []
        self.raw_events: List[Any] = []
        self.yielded_tokens: List[str] = []
        self.accumulated_texts: List[str] = []
        self.session_history_snapshots: List[List[Any]] = []
        
    def log_event(self, stage: str, data: Dict[str, Any]):
        """Log an event at a specific pipeline stage."""
        event = {
            'timestamp': datetime.now().isoformat(),
            'stage': stage,
            'data': data
        }
        self.events.append(event)
        logger.info(f"[{stage}] {data}")
    
    def add_raw_event(self, event: Any):
        """Store raw ADK event."""
        self.raw_events.append(event)
    
    def add_yielded_token(self, token: str):
        """Store yielded token."""
        self.yielded_tokens.append(token)
    
    def add_accumulated_text(self, text: str):
        """Store accumulated text snapshot."""
        self.accumulated_texts.append(text)
    
    def add_session_snapshot(self, messages: List[Any]):
        """Store session history snapshot."""
        self.session_history_snapshots.append(messages.copy() if messages else [])
    
    def analyze_duplicates(self) -> Dict[str, Any]:
        """Analyze collected data for duplicates."""
        analysis = {
            'total_events': len(self.raw_events),
            'total_tokens_yielded': len(self.yielded_tokens),
            'duplicate_tokens': [],
            'duplicate_events': [],
            'token_overlap': [],
            'full_response': ''.join(self.yielded_tokens)
        }
        
        # Check for duplicate tokens
        seen_tokens = set()
        for i, token in enumerate(self.yielded_tokens):
            token_hash = hashlib.md5(token.encode()).hexdigest()
            if token_hash in seen_tokens:
                analysis['duplicate_tokens'].append({
                    'index': i,
                    'token': token[:100],
                    'hash': token_hash
                })
            seen_tokens.add(token_hash)
        
        # Check for token overlap (token N+1 starts with token N)
        for i in range(len(self.yielded_tokens) - 1):
            if len(self.yielded_tokens[i]) > 10:  # Only check substantial tokens
                if self.yielded_tokens[i+1].startswith(self.yielded_tokens[i]):
                    analysis['token_overlap'].append({
                        'index': i,
                        'token_i': self.yielded_tokens[i][:100],
                        'token_i_plus_1': self.yielded_tokens[i+1][:100]
                    })
        
        # Check for duplicate events (same content in multiple events)
        event_contents = []
        for event in self.raw_events:
            if hasattr(event, 'content') and event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        event_contents.append(part.text)
        
        seen_contents = set()
        for i, content in enumerate(event_contents):
            content_hash = hashlib.md5(content.encode()).hexdigest()
            if content_hash in seen_contents:
                analysis['duplicate_events'].append({
                    'index': i,
                    'content': content[:100],
                    'hash': content_hash
                })
            seen_contents.add(content_hash)
        
        # Check for sentence-level duplicates in full response
        sentences = [s.strip() for s in analysis['full_response'].split('.') if s.strip()]
        sentence_counts = {}
        for sentence in sentences:
            sentence_counts[sentence] = sentence_counts.get(sentence, 0) + 1
        
        analysis['duplicate_sentences'] = {
            s: count for s, count in sentence_counts.items() if count > 1
        }
        
        return analysis
    
    def print_summary(self):
        """Print diagnostic summary."""
        print("\n" + "=" * 80)
        print("DIAGNOSTIC SUMMARY")
        print("=" * 80)
        
        print(f"\nTotal events collected: {len(self.events)}")
        print(f"Total raw ADK events: {len(self.raw_events)}")
        print(f"Total tokens yielded: {len(self.yielded_tokens)}")
        print(f"Total accumulated text snapshots: {len(self.accumulated_texts)}")
        print(f"Total session history snapshots: {len(self.session_history_snapshots)}")
        
        analysis = self.analyze_duplicates()
        
        print(f"\n--- DUPLICATION ANALYSIS ---")
        print(f"Duplicate tokens: {len(analysis['duplicate_tokens'])}")
        if analysis['duplicate_tokens']:
            print("  Details:")
            for dup in analysis['duplicate_tokens'][:5]:  # Show first 5
                print(f"    - Index {dup['index']}: {dup['token']}")
        
        print(f"\nToken overlaps: {len(analysis['token_overlap'])}")
        if analysis['token_overlap']:
            print("  Details:")
            for overlap in analysis['token_overlap'][:5]:  # Show first 5
                print(f"    - Index {overlap['index']}:")
                print(f"      Token i: {overlap['token_i']}")
                print(f"      Token i+1: {overlap['token_i_plus_1']}")
        
        print(f"\nDuplicate events: {len(analysis['duplicate_events'])}")
        if analysis['duplicate_events']:
            print("  Details:")
            for dup in analysis['duplicate_events'][:5]:  # Show first 5
                print(f"    - Index {dup['index']}: {dup['content']}")
        
        print(f"\nDuplicate sentences: {len(analysis['duplicate_sentences'])}")
        if analysis['duplicate_sentences']:
            print("  Details:")
            for sentence, count in list(analysis['duplicate_sentences'].items())[:5]:
                print(f"    - '{sentence[:100]}...' appears {count} times")
        
        print(f"\n--- FULL RESPONSE ---")
        print(analysis['full_response'][:500])
        if len(analysis['full_response']) > 500:
            print(f"... ({len(analysis['full_response']) - 500} more characters)")
        
        return analysis


def test_with_raw_runner():
    """Test using raw ADK Runner to see events before our processing."""
    print("\n" + "=" * 80)
    print("TEST 1: RAW ADK RUNNER (No agent_invoker processing)")
    print("=" * 80)
    
    collector = DiagnosticCollector()
    
    # Get agent
    agent = get_agent()
    session_id = "diagnostic_raw_runner"
    user_id = "diagnostic_user"
    message = "Find Italian restaurants in South Philadelphia"
    
    collector.log_event("SETUP", {
        "test": "raw_runner",
        "session_id": session_id,
        "message": message
    })
    
    # Create or get session
    try:
        session = _session_service.get_session_sync(
            session_id=session_id,
            app_name="vibehuntr_playground",
            user_id=user_id
        )
        collector.log_event("SESSION", {"action": "retrieved", "session_id": session_id})
    except:
        session = _session_service.create_session_sync(
            session_id=session_id,
            user_id=user_id,
            app_name="vibehuntr_playground"
        )
        collector.log_event("SESSION", {"action": "created", "session_id": session_id})
    
    # Create runner
    runner = Runner(
        agent=agent,
        session_service=_session_service,
        app_name="vibehuntr_playground"
    )
    collector.log_event("RUNNER", {"action": "created"})
    
    # Create message content
    content = types.Content(
        role="user",
        parts=[types.Part.from_text(text=message)]
    )
    collector.log_event("MESSAGE", {"action": "created", "length": len(message)})
    
    # Run agent
    events = runner.run(
        new_message=content,
        user_id=user_id,
        session_id=session_id,
        run_config=RunConfig(streaming_mode=StreamingMode.SSE)
    )
    collector.log_event("AGENT", {"action": "invoked"})
    
    # Process events
    event_count = 0
    for event in events:
        event_count += 1
        collector.add_raw_event(event)
        
        collector.log_event("EVENT_RECEIVED", {
            "event_number": event_count,
            "has_content": hasattr(event, 'content') and event.content is not None,
            "has_parts": hasattr(event, 'content') and event.content and hasattr(event.content, 'parts')
        })
        
        if event.content and event.content.parts:
            for part_idx, part in enumerate(event.content.parts):
                if part.text:
                    collector.log_event("EVENT_PART", {
                        "event_number": event_count,
                        "part_index": part_idx,
                        "text_length": len(part.text),
                        "text_preview": part.text[:100]
                    })
    
    collector.log_event("COMPLETE", {"total_events": event_count})
    
    return collector


def test_with_agent_invoker():
    """Test using agent_invoker to see how our processing affects events."""
    print("\n" + "=" * 80)
    print("TEST 2: AGENT INVOKER (With our processing)")
    print("=" * 80)
    
    collector = DiagnosticCollector()
    
    # Get agent
    agent = get_agent()
    session_id = "diagnostic_agent_invoker"
    user_id = "diagnostic_user"
    message = "Find Italian restaurants in South Philadelphia"
    
    collector.log_event("SETUP", {
        "test": "agent_invoker",
        "session_id": session_id,
        "message": message
    })
    
    # Invoke agent with streaming
    token_count = 0
    for item in invoke_agent_streaming(agent, message, session_id, user_id):
        if item['type'] == 'text':
            token_count += 1
            token = item['content']
            collector.add_yielded_token(token)
            
            collector.log_event("TOKEN_YIELDED", {
                "token_number": token_count,
                "length": len(token),
                "preview": token[:100]
            })
    
    collector.log_event("COMPLETE", {"total_tokens": token_count})
    
    return collector


def test_multi_turn():
    """Test multi-turn conversation to see if duplication occurs across turns."""
    print("\n" + "=" * 80)
    print("TEST 3: MULTI-TURN CONVERSATION")
    print("=" * 80)
    
    collector = DiagnosticCollector()
    
    # Get agent
    agent = get_agent()
    session_id = "diagnostic_multi_turn"
    user_id = "diagnostic_user"
    
    messages = [
        "Find Italian restaurants in South Philadelphia",
        "Tell me more about the first one",
        "What are the hours?"
    ]
    
    for turn_idx, message in enumerate(messages):
        collector.log_event("TURN_START", {
            "turn": turn_idx + 1,
            "message": message
        })
        
        turn_tokens = []
        for item in invoke_agent_streaming(agent, message, session_id, user_id):
            if item['type'] == 'text':
                token = item['content']
                turn_tokens.append(token)
                collector.add_yielded_token(token)
        
        full_response = ''.join(turn_tokens)
        collector.log_event("TURN_COMPLETE", {
            "turn": turn_idx + 1,
            "tokens": len(turn_tokens),
            "response_length": len(full_response),
            "response_preview": full_response[:100]
        })
    
    return collector


def test_session_history():
    """Test session history to see if duplicates are stored."""
    print("\n" + "=" * 80)
    print("TEST 4: SESSION HISTORY INSPECTION")
    print("=" * 80)
    
    collector = DiagnosticCollector()
    
    # Get agent
    agent = get_agent()
    session_id = "diagnostic_session_history"
    user_id = "diagnostic_user"
    message = "Find Italian restaurants in South Philadelphia"
    
    collector.log_event("SETUP", {
        "test": "session_history",
        "session_id": session_id,
        "message": message
    })
    
    # Get initial session state
    try:
        session = _session_service.get_session_sync(
            session_id=session_id,
            app_name="vibehuntr_playground",
            user_id=user_id
        )
        initial_messages = session.messages if hasattr(session, 'messages') else []
        collector.add_session_snapshot(initial_messages)
        collector.log_event("SESSION_INITIAL", {
            "message_count": len(initial_messages)
        })
    except:
        session = _session_service.create_session_sync(
            session_id=session_id,
            user_id=user_id,
            app_name="vibehuntr_playground"
        )
        collector.log_event("SESSION_CREATED", {"session_id": session_id})
        collector.add_session_snapshot([])
    
    # Invoke agent
    tokens = []
    for item in invoke_agent_streaming(agent, message, session_id, user_id):
        if item['type'] == 'text':
            tokens.append(item['content'])
    
    full_response = ''.join(tokens)
    collector.log_event("RESPONSE_COMPLETE", {
        "length": len(full_response),
        "preview": full_response[:100]
    })
    
    # Get final session state
    session = _session_service.get_session_sync(
        session_id=session_id,
        app_name="vibehuntr_playground",
        user_id=user_id
    )
    final_messages = session.messages if hasattr(session, 'messages') else []
    collector.add_session_snapshot(final_messages)
    
    collector.log_event("SESSION_FINAL", {
        "message_count": len(final_messages)
    })
    
    # Analyze session history for duplicates
    if final_messages:
        for idx, msg in enumerate(final_messages):
            msg_content = ""
            if hasattr(msg, 'content') and msg.content:
                if hasattr(msg.content, 'parts'):
                    for part in msg.content.parts:
                        if hasattr(part, 'text'):
                            msg_content += part.text
                elif hasattr(msg.content, 'text'):
                    msg_content = msg.content.text
            
            collector.log_event("SESSION_MESSAGE", {
                "index": idx,
                "role": msg.role if hasattr(msg, 'role') else 'unknown',
                "length": len(msg_content),
                "preview": msg_content[:100]
            })
    
    return collector


def main():
    """Run all diagnostic tests."""
    print("\n" + "=" * 80)
    print("RESPONSE DUPLICATION DIAGNOSTIC TEST SUITE")
    print("=" * 80)
    print("\nThis test suite will:")
    print("1. Test raw ADK Runner to see events before processing")
    print("2. Test agent_invoker to see how our processing affects events")
    print("3. Test multi-turn conversation for cross-turn duplication")
    print("4. Test session history for stored duplicates")
    print("\nAll events are logged to: diagnostic_duplication.log")
    print("=" * 80)
    
    results = {}
    
    try:
        # Test 1: Raw Runner
        print("\n\nRunning Test 1...")
        collector1 = test_with_raw_runner()
        collector1.print_summary()
        results['raw_runner'] = collector1.analyze_duplicates()
        
        # Test 2: Agent Invoker
        print("\n\nRunning Test 2...")
        collector2 = test_with_agent_invoker()
        collector2.print_summary()
        results['agent_invoker'] = collector2.analyze_duplicates()
        
        # Test 3: Multi-turn
        print("\n\nRunning Test 3...")
        collector3 = test_multi_turn()
        collector3.print_summary()
        results['multi_turn'] = collector3.analyze_duplicates()
        
        # Test 4: Session History
        print("\n\nRunning Test 4...")
        collector4 = test_session_history()
        collector4.print_summary()
        results['session_history'] = collector4.analyze_duplicates()
        
        # Final summary
        print("\n\n" + "=" * 80)
        print("FINAL DIAGNOSTIC SUMMARY")
        print("=" * 80)
        
        for test_name, analysis in results.items():
            print(f"\n{test_name.upper()}:")
            print(f"  - Duplicate tokens: {len(analysis['duplicate_tokens'])}")
            print(f"  - Token overlaps: {len(analysis['token_overlap'])}")
            print(f"  - Duplicate events: {len(analysis['duplicate_events'])}")
            print(f"  - Duplicate sentences: {len(analysis['duplicate_sentences'])}")
        
        # Determine root cause
        print("\n" + "=" * 80)
        print("ROOT CAUSE ANALYSIS")
        print("=" * 80)
        
        if len(results['raw_runner']['duplicate_events']) > 0:
            print("\n❌ DUPLICATION AT AGENT/RUNNER LEVEL")
            print("   The ADK Runner is yielding duplicate events.")
            print("   This suggests the issue is in:")
            print("   - Agent configuration (temperature, top_p, etc.)")
            print("   - Agent prompt/instruction")
            print("   - LLM behavior")
            print("   - ADK Runner event processing")
        elif len(results['agent_invoker']['duplicate_tokens']) > 0:
            print("\n❌ DUPLICATION AT STREAMING LEVEL")
            print("   Our agent_invoker is yielding duplicate tokens.")
            print("   This suggests the issue is in:")
            print("   - Token accumulation logic")
            print("   - Duplicate detection logic")
            print("   - Token yielding logic")
        elif len(results['session_history']['duplicate_sentences']) > 0:
            print("\n❌ DUPLICATION AT SESSION LEVEL")
            print("   Session history contains duplicate content.")
            print("   This suggests the issue is in:")
            print("   - Session history storage")
            print("   - Message addition logic")
        else:
            print("\n✓ NO DUPLICATION DETECTED")
            print("   All tests passed without detecting duplicates.")
            print("   The duplication issue may be:")
            print("   - Intermittent")
            print("   - Specific to certain queries")
            print("   - Already fixed")
        
        print("\n" + "=" * 80)
        print("See diagnostic_duplication.log for detailed logs")
        print("=" * 80)
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
