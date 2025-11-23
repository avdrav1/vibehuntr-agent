"""Integration tests for the CLI interface.

Tests end-to-end workflows through the CLI to ensure all commands work correctly.
"""

import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from click.testing import CliRunner

from cli.event_planner import cli
from app.event_planning.models.event import Location
from app.event_planning.models.suggestion import EventSuggestion


class TestCLIUserManagement:
    """Test user management commands."""
    
    def test_create_and_list_users(self):
        """Test creating users and listing them."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a user
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'user', 'create',
                '--name', 'Alice',
                '--email', 'alice@example.com'
            ])
            
            assert result.exit_code == 0
            assert 'User created successfully' in result.output
            assert 'Alice' in result.output
            
            # List users
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'user', 'list'
            ])
            
            assert result.exit_code == 0
            assert 'Found 1 user(s)' in result.output
            assert 'Alice' in result.output
            assert 'alice@example.com' in result.output
    
    def test_create_duplicate_email_fails(self):
        """Test that creating a user with duplicate email fails."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create first user
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'user', 'create',
                '--name', 'Alice',
                '--email', 'alice@example.com'
            ])
            assert result.exit_code == 0
            
            # Try to create second user with same email
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'user', 'create',
                '--name', 'Bob',
                '--email', 'alice@example.com'
            ])
            
            assert result.exit_code == 1
            assert 'Error' in result.output
    
    def test_update_user_preferences(self):
        """Test updating user preferences."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a user
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'user', 'create',
                '--name', 'Alice',
                '--email', 'alice@example.com'
            ])
            assert result.exit_code == 0
            
            # Extract user ID from output
            lines = result.output.split('\n')
            user_id = None
            for line in lines:
                if 'ID:' in line:
                    user_id = line.split('ID:')[1].strip()
                    break
            
            assert user_id is not None
            
            # Update preferences
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'user', 'update-preferences', user_id,
                '--activity', 'hiking:0.8',
                '--activity', 'dining:0.6',
                '--budget', '50.0',
                '--location', 'Downtown'
            ])
            
            assert result.exit_code == 0
            assert 'Preferences updated' in result.output
            
            # Show user to verify preferences
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'user', 'show', user_id
            ])
            
            assert result.exit_code == 0
            assert 'hiking' in result.output
            assert 'Max Budget: $50.0' in result.output
    
    def test_add_availability(self):
        """Test adding availability windows."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a user
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'user', 'create',
                '--name', 'Alice',
                '--email', 'alice@example.com'
            ])
            assert result.exit_code == 0
            
            # Extract user ID
            lines = result.output.split('\n')
            user_id = None
            for line in lines:
                if 'ID:' in line:
                    user_id = line.split('ID:')[1].strip()
                    break
            
            # Add availability
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'user', 'add-availability', user_id,
                '--start', '2025-01-25T18:00:00',
                '--end', '2025-01-25T22:00:00',
                '--timezone', 'UTC'
            ])
            
            assert result.exit_code == 0
            assert 'Availability added' in result.output


class TestCLIGroupManagement:
    """Test group management commands."""
    
    def test_create_and_list_groups(self):
        """Test creating groups and listing them."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a user first
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'user', 'create',
                '--name', 'Alice',
                '--email', 'alice@example.com'
            ])
            assert result.exit_code == 0
            
            # Extract user ID
            lines = result.output.split('\n')
            user_id = None
            for line in lines:
                if 'ID:' in line:
                    user_id = line.split('ID:')[1].strip()
                    break
            
            # Create a group
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'group', 'create',
                '--name', 'Weekend Warriors',
                '--creator', user_id
            ])
            
            assert result.exit_code == 0
            assert 'Group created successfully' in result.output
            assert 'Weekend Warriors' in result.output
            
            # List groups
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'group', 'list'
            ])
            
            assert result.exit_code == 0
            assert 'Weekend Warriors' in result.output
    
    def test_add_and_remove_members(self):
        """Test adding and removing group members."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create two users
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'user', 'create',
                '--name', 'Alice',
                '--email', 'alice@example.com'
            ])
            alice_id = result.output.split('ID:')[1].split('\n')[0].strip()
            
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'user', 'create',
                '--name', 'Bob',
                '--email', 'bob@example.com'
            ])
            bob_id = result.output.split('ID:')[1].split('\n')[0].strip()
            
            # Create a group
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'group', 'create',
                '--name', 'Test Group',
                '--creator', alice_id
            ])
            group_id = result.output.split('ID:')[1].split('\n')[0].strip()
            
            # Add Bob to the group
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'group', 'add-member', group_id, bob_id
            ])
            
            assert result.exit_code == 0
            assert 'Added' in result.output
            
            # Show group to verify
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'group', 'show', group_id
            ])
            
            assert result.exit_code == 0
            assert 'Bob' in result.output
            assert '2 members' in result.output or 'Members (2)' in result.output


class TestCLIEventManagement:
    """Test event management commands."""
    
    def test_create_and_finalize_event(self):
        """Test creating and finalizing an event."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create users
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'user', 'create',
                '--name', 'Alice',
                '--email', 'alice@example.com'
            ])
            alice_id = result.output.split('ID:')[1].split('\n')[0].strip()
            
            # Add availability for Alice
            runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'user', 'add-availability', alice_id,
                '--start', '2025-01-25T18:00:00',
                '--end', '2025-01-25T22:00:00'
            ])
            
            # Create suggestions file
            suggestions = [
                {
                    "id": "suggestion-1",
                    "activity_type": "dining",
                    "location": {
                        "name": "Italian Restaurant",
                        "address": "123 Main St",
                        "latitude": 40.7128,
                        "longitude": -74.0060
                    },
                    "estimated_duration": 7200,
                    "estimated_cost_per_person": 30.0,
                    "description": "Great Italian food",
                    "consensus_score": 0.0,
                    "member_compatibility": {}
                }
            ]
            
            suggestions_file = Path(tmpdir) / 'suggestions.json'
            with open(suggestions_file, 'w') as f:
                json.dump(suggestions, f)
            
            # Create an event
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'event', 'create',
                '--suggestion-id', 'suggestion-1',
                '--suggestions-file', str(suggestions_file),
                '--name', 'Dinner Night',
                '--start', '2025-01-25T19:00:00',
                '--participant', alice_id
            ])
            
            assert result.exit_code == 0
            assert 'Event created successfully' in result.output
            
            # Extract event ID
            event_id = result.output.split('ID:')[1].split('\n')[0].strip()
            
            # Finalize the event
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'event', 'finalize', event_id
            ])
            
            assert result.exit_code == 0
            assert 'Event finalized' in result.output
    
    def test_list_events(self):
        """Test listing events."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a user
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'user', 'create',
                '--name', 'Alice',
                '--email', 'alice@example.com'
            ])
            alice_id = result.output.split('ID:')[1].split('\n')[0].strip()
            
            # Add availability (morning time for hiking)
            runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'user', 'add-availability', alice_id,
                '--start', '2025-01-25T08:00:00',
                '--end', '2025-01-25T14:00:00'
            ])
            
            # Create suggestions file
            suggestions = [
                {
                    "id": "suggestion-1",
                    "activity_type": "hiking",
                    "location": {
                        "name": "Mountain Trail",
                        "address": "456 Trail Rd"
                    },
                    "estimated_duration": 7200,
                    "estimated_cost_per_person": 0.0,
                    "description": "Beautiful trail",
                    "consensus_score": 0.0,
                    "member_compatibility": {}
                }
            ]
            
            suggestions_file = Path(tmpdir) / 'suggestions.json'
            with open(suggestions_file, 'w') as f:
                json.dump(suggestions, f)
            
            # Create an event
            create_result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'event', 'create',
                '--suggestion-id', 'suggestion-1',
                '--suggestions-file', str(suggestions_file),
                '--name', 'Hiking Trip',
                '--start', '2025-01-25T10:00:00',
                '--participant', alice_id
            ])
            
            # Verify event was created
            assert create_result.exit_code == 0, f"Event creation failed: {create_result.output}"
            
            # List events
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'event', 'list'
            ])
            
            assert result.exit_code == 0
            assert 'Hiking Trip' in result.output


class TestCLIFeedback:
    """Test feedback commands."""
    
    def test_submit_and_list_feedback(self):
        """Test submitting and listing feedback."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a user
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'user', 'create',
                '--name', 'Alice',
                '--email', 'alice@example.com'
            ])
            alice_id = result.output.split('ID:')[1].split('\n')[0].strip()
            
            # Add availability
            runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'user', 'add-availability', alice_id,
                '--start', '2025-01-25T18:00:00',
                '--end', '2025-01-25T22:00:00'
            ])
            
            # Create suggestions file
            suggestions = [
                {
                    "id": "suggestion-1",
                    "activity_type": "dining",
                    "location": {
                        "name": "Restaurant",
                        "address": "123 St"
                    },
                    "estimated_duration": 7200,
                    "estimated_cost_per_person": 25.0,
                    "description": "Good food",
                    "consensus_score": 0.0,
                    "member_compatibility": {}
                }
            ]
            
            suggestions_file = Path(tmpdir) / 'suggestions.json'
            with open(suggestions_file, 'w') as f:
                json.dump(suggestions, f)
            
            # Create and finalize an event
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'event', 'create',
                '--suggestion-id', 'suggestion-1',
                '--suggestions-file', str(suggestions_file),
                '--name', 'Dinner',
                '--start', '2025-01-25T19:00:00',
                '--participant', alice_id
            ])
            event_id = result.output.split('ID:')[1].split('\n')[0].strip()
            
            runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'event', 'finalize', event_id
            ])
            
            # Submit feedback
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'feedback', 'submit', event_id, alice_id,
                '--rating', '5',
                '--comments', 'Great event!'
            ])
            
            assert result.exit_code == 0
            assert 'Feedback submitted' in result.output
            assert 'Rating: 5/5' in result.output
            
            # List feedback
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'feedback', 'list'
            ])
            
            assert result.exit_code == 0
            assert 'Alice' in result.output
            assert '5/5' in result.output


class TestCLISearchAndScheduling:
    """Test search and scheduling commands."""
    
    def test_search_suggestions(self):
        """Test searching and filtering event suggestions."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a user and group
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'user', 'create',
                '--name', 'Alice',
                '--email', 'alice@example.com'
            ])
            alice_id = result.output.split('ID:')[1].split('\n')[0].strip()
            
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'group', 'create',
                '--name', 'Test Group',
                '--creator', alice_id
            ])
            group_id = result.output.split('ID:')[1].split('\n')[0].strip()
            
            # Create suggestions file with multiple suggestions
            suggestions = [
                {
                    "id": "suggestion-1",
                    "activity_type": "hiking",
                    "location": {
                        "name": "Mountain Trail",
                        "address": "Downtown"
                    },
                    "estimated_duration": 7200,
                    "estimated_cost_per_person": 0.0,
                    "description": "Beautiful trail",
                    "consensus_score": 0.8,
                    "member_compatibility": {}
                },
                {
                    "id": "suggestion-2",
                    "activity_type": "dining",
                    "location": {
                        "name": "Italian Restaurant",
                        "address": "Uptown"
                    },
                    "estimated_duration": 7200,
                    "estimated_cost_per_person": 50.0,
                    "description": "Great food",
                    "consensus_score": 0.7,
                    "member_compatibility": {}
                }
            ]
            
            suggestions_file = Path(tmpdir) / 'suggestions.json'
            with open(suggestions_file, 'w') as f:
                json.dump(suggestions, f)
            
            # Search with activity filter
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'search', 'suggestions', group_id,
                '--suggestions-file', str(suggestions_file),
                '--activity', 'hiking'
            ])
            
            assert result.exit_code == 0
            assert 'hiking' in result.output
            assert 'Mountain Trail' in result.output
    
    def test_find_optimal_time(self):
        """Test finding optimal time slots for a group."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create users
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'user', 'create',
                '--name', 'Alice',
                '--email', 'alice@example.com'
            ])
            alice_id = result.output.split('ID:')[1].split('\n')[0].strip()
            
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'user', 'create',
                '--name', 'Bob',
                '--email', 'bob@example.com'
            ])
            bob_id = result.output.split('ID:')[1].split('\n')[0].strip()
            
            # Add availability for both users
            runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'user', 'add-availability', alice_id,
                '--start', '2025-01-25T18:00:00',
                '--end', '2025-01-25T22:00:00'
            ])
            
            runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'user', 'add-availability', bob_id,
                '--start', '2025-01-25T19:00:00',
                '--end', '2025-01-25T23:00:00'
            ])
            
            # Create a group
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'group', 'create',
                '--name', 'Test Group',
                '--creator', alice_id,
                '--member', bob_id
            ])
            group_id = result.output.split('ID:')[1].split('\n')[0].strip()
            
            # Find optimal time
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'schedule', 'find-time', group_id,
                '--duration', '2'
            ])
            
            assert result.exit_code == 0
            assert 'time slot' in result.output.lower()


class TestCLICompleteWorkflow:
    """Test complete end-to-end workflows."""
    
    def test_complete_event_planning_workflow(self):
        """Test a complete workflow from user creation to event feedback."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Step 1: Create users
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'user', 'create',
                '--name', 'Alice',
                '--email', 'alice@example.com'
            ])
            assert result.exit_code == 0
            alice_id = result.output.split('ID:')[1].split('\n')[0].strip()
            
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'user', 'create',
                '--name', 'Bob',
                '--email', 'bob@example.com'
            ])
            assert result.exit_code == 0
            bob_id = result.output.split('ID:')[1].split('\n')[0].strip()
            
            # Step 2: Update preferences
            runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'user', 'update-preferences', alice_id,
                '--activity', 'dining:0.8',
                '--budget', '50.0'
            ])
            
            runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'user', 'update-preferences', bob_id,
                '--activity', 'dining:0.7',
                '--budget', '40.0'
            ])
            
            # Step 3: Add availability
            runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'user', 'add-availability', alice_id,
                '--start', '2025-01-25T18:00:00',
                '--end', '2025-01-25T22:00:00'
            ])
            
            runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'user', 'add-availability', bob_id,
                '--start', '2025-01-25T18:00:00',
                '--end', '2025-01-25T22:00:00'
            ])
            
            # Step 4: Create a group
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'group', 'create',
                '--name', 'Dinner Club',
                '--creator', alice_id,
                '--member', bob_id
            ])
            assert result.exit_code == 0
            group_id = result.output.split('ID:')[1].split('\n')[0].strip()
            
            # Step 5: Create suggestions file
            suggestions = [
                {
                    "id": "suggestion-1",
                    "activity_type": "dining",
                    "location": {
                        "name": "Italian Restaurant",
                        "address": "123 Main St"
                    },
                    "estimated_duration": 7200,
                    "estimated_cost_per_person": 35.0,
                    "description": "Great Italian food",
                    "consensus_score": 0.0,
                    "member_compatibility": {}
                }
            ]
            
            suggestions_file = Path(tmpdir) / 'suggestions.json'
            with open(suggestions_file, 'w') as f:
                json.dump(suggestions, f)
            
            # Step 6: Create an event
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'event', 'create',
                '--suggestion-id', 'suggestion-1',
                '--suggestions-file', str(suggestions_file),
                '--name', 'Dinner Night',
                '--start', '2025-01-25T19:00:00',
                '--participant', alice_id,
                '--participant', bob_id
            ])
            assert result.exit_code == 0
            event_id = result.output.split('ID:')[1].split('\n')[0].strip()
            
            # Step 7: Check for conflicts
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'event', 'check-conflicts', event_id
            ])
            assert result.exit_code == 0
            assert 'Conflict check' in result.output
            
            # Step 8: Finalize the event
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'event', 'finalize', event_id
            ])
            assert result.exit_code == 0
            assert 'finalized' in result.output
            
            # Step 9: Submit feedback
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'feedback', 'submit', event_id, alice_id,
                '--rating', '5',
                '--comments', 'Great dinner!'
            ])
            assert result.exit_code == 0
            assert 'Feedback submitted' in result.output
            
            # Step 10: List feedback
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'feedback', 'list',
                '--event', event_id
            ])
            assert result.exit_code == 0
            assert 'Alice' in result.output
            assert '5/5' in result.output
    
    def test_group_with_priority_members(self):
        """Test creating a group with priority members."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create users
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'user', 'create',
                '--name', 'Alice',
                '--email', 'alice@example.com'
            ])
            alice_id = result.output.split('ID:')[1].split('\n')[0].strip()
            
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'user', 'create',
                '--name', 'Bob',
                '--email', 'bob@example.com'
            ])
            bob_id = result.output.split('ID:')[1].split('\n')[0].strip()
            
            # Create group with priority member
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'group', 'create',
                '--name', 'Test Group',
                '--creator', alice_id,
                '--member', bob_id,
                '--priority', alice_id
            ])
            
            assert result.exit_code == 0
            group_id = result.output.split('ID:')[1].split('\n')[0].strip()
            
            # Show group to verify priority member
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'group', 'show', group_id
            ])
            
            assert result.exit_code == 0
            assert '[PRIORITY]' in result.output


class TestCLIErrorHandling:
    """Test error handling in CLI commands."""
    
    def test_invalid_user_id(self):
        """Test that invalid user IDs are handled gracefully."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'user', 'show', 'invalid-id'
            ])
            
            assert result.exit_code == 1
            assert 'not found' in result.output
    
    def test_invalid_activity_format(self):
        """Test that invalid activity preference format is rejected."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a user
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'user', 'create',
                '--name', 'Alice',
                '--email', 'alice@example.com'
            ])
            alice_id = result.output.split('ID:')[1].split('\n')[0].strip()
            
            # Try to update with invalid format
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'user', 'update-preferences', alice_id,
                '--activity', 'invalid_format'
            ])
            
            assert result.exit_code == 1
            assert 'Invalid activity format' in result.output
    
    def test_create_group_with_invalid_creator(self):
        """Test that creating a group with invalid creator fails."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'group', 'create',
                '--name', 'Test Group',
                '--creator', 'invalid-id'
            ])
            
            assert result.exit_code == 1
            assert 'Error' in result.output
    
    def test_invalid_event_time(self):
        """Test that creating an event outside availability fails."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a user
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'user', 'create',
                '--name', 'Alice',
                '--email', 'alice@example.com'
            ])
            alice_id = result.output.split('ID:')[1].split('\n')[0].strip()
            
            # Add availability
            runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'user', 'add-availability', alice_id,
                '--start', '2025-01-25T18:00:00',
                '--end', '2025-01-25T22:00:00'
            ])
            
            # Create suggestions file
            suggestions = [
                {
                    "id": "suggestion-1",
                    "activity_type": "dining",
                    "location": {
                        "name": "Restaurant",
                        "address": "123 St"
                    },
                    "estimated_duration": 7200,
                    "estimated_cost_per_person": 25.0,
                    "description": "Good food",
                    "consensus_score": 0.0,
                    "member_compatibility": {}
                }
            ]
            
            suggestions_file = Path(tmpdir) / 'suggestions.json'
            with open(suggestions_file, 'w') as f:
                json.dump(suggestions, f)
            
            # Try to create event outside availability window
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'event', 'create',
                '--suggestion-id', 'suggestion-1',
                '--suggestions-file', str(suggestions_file),
                '--name', 'Dinner',
                '--start', '2025-01-25T10:00:00',  # Outside availability
                '--participant', alice_id
            ])
            
            assert result.exit_code == 1
            assert 'availability' in result.output.lower()
    
    def test_cancel_nonexistent_event(self):
        """Test that canceling a non-existent event fails gracefully."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'event', 'cancel', 'invalid-event-id'
            ])
            
            assert result.exit_code == 1
            assert 'Error' in result.output
    
    def test_invalid_rating_value(self):
        """Test that invalid feedback rating is rejected."""
        runner = CliRunner()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a user
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'user', 'create',
                '--name', 'Alice',
                '--email', 'alice@example.com'
            ])
            alice_id = result.output.split('ID:')[1].split('\n')[0].strip()
            
            # Add availability
            runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'user', 'add-availability', alice_id,
                '--start', '2025-01-25T18:00:00',
                '--end', '2025-01-25T22:00:00'
            ])
            
            # Create and finalize an event
            suggestions = [
                {
                    "id": "suggestion-1",
                    "activity_type": "dining",
                    "location": {
                        "name": "Restaurant",
                        "address": "123 St"
                    },
                    "estimated_duration": 7200,
                    "estimated_cost_per_person": 25.0,
                    "description": "Good food",
                    "consensus_score": 0.0,
                    "member_compatibility": {}
                }
            ]
            
            suggestions_file = Path(tmpdir) / 'suggestions.json'
            with open(suggestions_file, 'w') as f:
                json.dump(suggestions, f)
            
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'event', 'create',
                '--suggestion-id', 'suggestion-1',
                '--suggestions-file', str(suggestions_file),
                '--name', 'Dinner',
                '--start', '2025-01-25T19:00:00',
                '--participant', alice_id
            ])
            event_id = result.output.split('ID:')[1].split('\n')[0].strip()
            
            runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'event', 'finalize', event_id
            ])
            
            # Try to submit feedback with invalid rating
            result = runner.invoke(cli, [
                '--storage-dir', tmpdir,
                'feedback', 'submit', event_id, alice_id,
                '--rating', '10'  # Invalid rating (should be 1-5)
            ])
            
            assert result.exit_code == 1
            assert 'Error' in result.output
