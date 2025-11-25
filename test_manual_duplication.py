#!/usr/bin/env python3
"""Manual testing script for response duplication fix.

This script tests the exact scenarios from the task:
1. Italian restaurants in South Philly (from screenshot)
2. Multi-turn conversation (cheesesteak -> philly -> more details)
3. Tool usage scenarios

Requirements tested: 1.1, 1.5
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import logging
from typing import List, Dict, Any
from datetime import datetime
import uuid

# Configure logging to see duplication detection
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def collect_response(agent, message: str, session_id: str) -> tuple[str, List[Dict[str, Any]]]:
    """
    Collect complete response and all events from streaming.
    
    Returns:
        Tuple of (complete_response, events_list)
    """
    from app.event_planning.agent_invoker import invoke_agent_streaming
    
    events = []
    text_chunks = []
    
    logger.info(f"\n{'='*80}")
    logger.info(f"Testing message: {message}")
    logger.info(f"Session ID: {session_id}")
    logger.info(f"{'='*80}\n")
    
    for item in invoke_agent_streaming(
        agent=agent,
        message=message,
        session_id=session_id,
        user_id="manual_test_user",
        yield_tool_calls=True
    ):
        events.append(item)
        if item['type'] == 'text':
            text_chunks.append(item['content'])
            # Print as we go for real-time feedback
            print(item['content'], end='', flush=True)
        elif item['type'] == 'tool_call':
            logger.info(f"\n[TOOL CALL: {item['name']}]")
    
    print("\n")  # New line after response
    
    complete_response = "".join(text_chunks)
    return complete_response, events


def check_for_duplicates(response: str, events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Check response for various types of duplication.
    
    Returns:
        Dictionary with duplication analysis results
    """
    results = {
        "has_duplicates": False,
        "duplicate_chunks": [],
        "duplicate_sections": [],
        "duplicate_tool_calls": [],
        "analysis": []
    }
    
    # Check for duplicate chunks in events
    seen_chunks = set()
    for event in events:
        if event['type'] == 'text':
            chunk = event['content']
            chunk_hash = hash(chunk)
            if chunk_hash in seen_chunks:
                results["has_duplicates"] = True
                results["duplicate_chunks"].append(chunk[:100])
                results["analysis"].append(f"Duplicate chunk detected: {chunk[:50]}...")
            seen_chunks.add(chunk_hash)
    
    # Check for duplicate sections in complete response
    # Split into sentences and look for exact duplicates
    sentences = response.split('. ')
    seen_sentences = set()
    for sentence in sentences:
        if sentence and sentence in seen_sentences:
            results["has_duplicates"] = True
            results["duplicate_sections"].append(sentence[:100])
            results["analysis"].append(f"Duplicate section: {sentence[:50]}...")
        if sentence:
            seen_sentences.add(sentence)
    
    # Check for duplicate tool calls
    tool_calls = [e for e in events if e['type'] == 'tool_call']
    tool_call_signatures = []
    for tool_call in tool_calls:
        signature = f"{tool_call['name']}:{tool_call.get('args', '')}"
        if signature in tool_call_signatures:
            results["has_duplicates"] = True
            results["duplicate_tool_calls"].append(tool_call['name'])
            results["analysis"].append(f"Duplicate tool call: {tool_call['name']}")
        tool_call_signatures.append(signature)
    
    return results


def test_scenario_1_italian_restaurants():
    """
    Test Scenario 1: Italian restaurants in South Philly (from screenshot).
    
    This tests the exact scenario that was showing duplication in the screenshot.
    """
    logger.info("\n" + "="*80)
    logger.info("SCENARIO 1: Italian restaurants in South Philly")
    logger.info("="*80 + "\n")
    
    from app.event_planning.agent_loader import get_agent
    
    agent = get_agent()
    session_id = f"test_italian_{uuid.uuid4().hex[:8]}"
    
    message = "Italian restaurants in South Philly"
    response, events = collect_response(agent, message, session_id)
    
    # Analyze for duplicates
    dup_check = check_for_duplicates(response, events)
    
    # Print results
    logger.info("\n" + "-"*80)
    logger.info("SCENARIO 1 RESULTS:")
    logger.info(f"Response length: {len(response)} characters")
    logger.info(f"Number of events: {len(events)}")
    logger.info(f"Text chunks: {len([e for e in events if e['type'] == 'text'])}")
    logger.info(f"Tool calls: {len([e for e in events if e['type'] == 'tool_call'])}")
    logger.info(f"Has duplicates: {dup_check['has_duplicates']}")
    
    if dup_check['has_duplicates']:
        logger.error("❌ FAILED: Duplicates detected!")
        for analysis in dup_check['analysis']:
            logger.error(f"  - {analysis}")
    else:
        logger.info("✅ PASSED: No duplicates detected")
    
    logger.info("-"*80 + "\n")
    
    return not dup_check['has_duplicates'], session_id


def test_scenario_2_multi_turn():
    """
    Test Scenario 2: Multi-turn conversation.
    
    Tests: cheesesteak -> philly -> more details
    """
    logger.info("\n" + "="*80)
    logger.info("SCENARIO 2: Multi-turn conversation")
    logger.info("="*80 + "\n")
    
    from app.event_planning.agent_loader import get_agent
    
    agent = get_agent()
    session_id = f"test_multiturn_{uuid.uuid4().hex[:8]}"
    
    turns = [
        "cheesesteak",
        "philly",
        "more details"
    ]
    
    all_passed = True
    
    for i, message in enumerate(turns, 1):
        logger.info(f"\n--- Turn {i}/{len(turns)} ---")
        response, events = collect_response(agent, message, session_id)
        
        # Analyze for duplicates
        dup_check = check_for_duplicates(response, events)
        
        # Print results for this turn
        logger.info(f"\nTurn {i} Results:")
        logger.info(f"Response length: {len(response)} characters")
        logger.info(f"Has duplicates: {dup_check['has_duplicates']}")
        
        if dup_check['has_duplicates']:
            logger.error(f"❌ Turn {i} FAILED: Duplicates detected!")
            for analysis in dup_check['analysis']:
                logger.error(f"  - {analysis}")
            all_passed = False
        else:
            logger.info(f"✅ Turn {i} PASSED: No duplicates detected")
    
    logger.info("\n" + "-"*80)
    logger.info("SCENARIO 2 OVERALL RESULTS:")
    if all_passed:
        logger.info("✅ PASSED: All turns completed without duplicates")
    else:
        logger.error("❌ FAILED: Some turns had duplicates")
    logger.info("-"*80 + "\n")
    
    return all_passed, session_id


def test_scenario_3_tool_usage():
    """
    Test Scenario 3: Tool usage scenarios.
    
    Tests messages that trigger tool calls to ensure no duplicate tool outputs.
    """
    logger.info("\n" + "="*80)
    logger.info("SCENARIO 3: Tool usage scenarios")
    logger.info("="*80 + "\n")
    
    from app.event_planning.agent_loader import get_agent
    
    agent = get_agent()
    session_id = f"test_tools_{uuid.uuid4().hex[:8]}"
    
    # Messages that should trigger tool calls
    test_messages = [
        "Find me coffee shops in Center City Philadelphia",
        "What are the best rated restaurants near Rittenhouse Square?",
        "Show me bars in Old City"
    ]
    
    all_passed = True
    
    for i, message in enumerate(test_messages, 1):
        logger.info(f"\n--- Tool Test {i}/{len(test_messages)} ---")
        response, events = collect_response(agent, message, session_id)
        
        # Analyze for duplicates
        dup_check = check_for_duplicates(response, events)
        
        # Count tool calls
        tool_calls = [e for e in events if e['type'] == 'tool_call']
        
        # Print results
        logger.info(f"\nTool Test {i} Results:")
        logger.info(f"Response length: {len(response)} characters")
        logger.info(f"Tool calls made: {len(tool_calls)}")
        if tool_calls:
            for tool_call in tool_calls:
                logger.info(f"  - {tool_call['name']}")
        logger.info(f"Has duplicates: {dup_check['has_duplicates']}")
        
        if dup_check['has_duplicates']:
            logger.error(f"❌ Tool Test {i} FAILED: Duplicates detected!")
            for analysis in dup_check['analysis']:
                logger.error(f"  - {analysis}")
            all_passed = False
        else:
            logger.info(f"✅ Tool Test {i} PASSED: No duplicates detected")
    
    logger.info("\n" + "-"*80)
    logger.info("SCENARIO 3 OVERALL RESULTS:")
    if all_passed:
        logger.info("✅ PASSED: All tool usage tests completed without duplicates")
    else:
        logger.error("❌ FAILED: Some tool usage tests had duplicates")
    logger.info("-"*80 + "\n")
    
    return all_passed, session_id


def main():
    """Run all manual test scenarios."""
    logger.info("\n" + "="*80)
    logger.info("MANUAL TESTING: Response Duplication Fix")
    logger.info("Testing Requirements: 1.1, 1.5")
    logger.info("="*80 + "\n")
    
    start_time = datetime.now()
    
    results = {}
    
    # Run all scenarios
    try:
        results['scenario_1'], session_1 = test_scenario_1_italian_restaurants()
    except Exception as e:
        logger.error(f"Scenario 1 crashed: {e}", exc_info=True)
        results['scenario_1'] = False
        session_1 = None
    
    try:
        results['scenario_2'], session_2 = test_scenario_2_multi_turn()
    except Exception as e:
        logger.error(f"Scenario 2 crashed: {e}", exc_info=True)
        results['scenario_2'] = False
        session_2 = None
    
    try:
        results['scenario_3'], session_3 = test_scenario_3_tool_usage()
    except Exception as e:
        logger.error(f"Scenario 3 crashed: {e}", exc_info=True)
        results['scenario_3'] = False
        session_3 = None
    
    # Print final summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    logger.info("\n" + "="*80)
    logger.info("FINAL SUMMARY")
    logger.info("="*80)
    logger.info(f"Test duration: {duration:.2f} seconds")
    logger.info(f"Scenario 1 (Italian restaurants): {'✅ PASSED' if results.get('scenario_1') else '❌ FAILED'}")
    logger.info(f"Scenario 2 (Multi-turn): {'✅ PASSED' if results.get('scenario_2') else '❌ FAILED'}")
    logger.info(f"Scenario 3 (Tool usage): {'✅ PASSED' if results.get('scenario_3') else '❌ FAILED'}")
    
    all_passed = all(results.values())
    logger.info("\n" + "-"*80)
    if all_passed:
        logger.info("✅ ALL TESTS PASSED: No response duplication detected")
        logger.info("Requirements 1.1 and 1.5 are satisfied")
    else:
        logger.error("❌ SOME TESTS FAILED: Response duplication detected")
        logger.error("Please review the logs above for details")
    logger.info("-"*80 + "\n")
    
    # Return exit code
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
