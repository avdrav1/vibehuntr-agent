"""Property-based tests for group coordination models.

This module tests the round-trip serialization properties for group coordination data models
and the planning session service properties.
"""

import sys
import os
from datetime import datetime, timedelta
from hypothesis import given, strategies as st, settings, assume
from hypothesis.strategies import composite
import pytest

# Add the project root to the path to import models directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.event_planning.models.planning_session import (
    PlanningSession,
    Participant,
    SessionStatus,
)
from app.event_planning.models.venue import VenueOption, Vote, VoteType
from app.event_planning.models.itinerary import ItineraryItem, Comment, COMMENT_MAX_LENGTH
from app.event_planning.models.session_summary import SessionSummary
from app.event_planning.services.planning_session_service import PlanningSessionService


# Custom strategies for generating test data

@composite
def participant_strategy(draw: st.DrawFn) -> Participant:
    """Generate a valid Participant."""
    participant_id = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        whitelist_characters="-_"
    )))
    session_id = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        whitelist_characters="-_"
    )))
    display_name = draw(st.text(min_size=1, max_size=100))
    joined_at = draw(st.datetimes(
        min_value=datetime(2020, 1, 1),
        max_value=datetime(2030, 12, 31)
    ))
    is_organizer = draw(st.booleans())
    
    return Participant(
        id=participant_id,
        session_id=session_id,
        display_name=display_name,
        joined_at=joined_at,
        is_organizer=is_organizer,
    )


@composite
def planning_session_strategy(draw: st.DrawFn) -> PlanningSession:
    """Generate a valid PlanningSession."""
    session_id = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        whitelist_characters="-_"
    )))
    name = draw(st.text(min_size=1, max_size=100))
    organizer_id = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        whitelist_characters="-_"
    )))
    invite_token = draw(st.text(min_size=32, max_size=64, alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        whitelist_characters="-_"
    )))
    
    created_at = draw(st.datetimes(
        min_value=datetime(2020, 1, 1),
        max_value=datetime(2030, 12, 31)
    ))
    # Ensure invite_expires_at is after created_at
    expiry_duration = draw(st.timedeltas(min_value=timedelta(hours=1), max_value=timedelta(days=30)))
    invite_expires_at = created_at + expiry_duration
    
    updated_at = draw(st.datetimes(
        min_value=created_at,
        max_value=datetime(2030, 12, 31)
    ))
    
    invite_revoked = draw(st.booleans())
    status = draw(st.sampled_from(list(SessionStatus)))
    
    # Generate unique participant IDs
    num_participants = draw(st.integers(min_value=0, max_value=10))
    participant_ids = draw(st.lists(
        st.text(min_size=1, max_size=50, alphabet=st.characters(
            whitelist_categories=("Lu", "Ll", "Nd"),
            whitelist_characters="-_"
        )),
        min_size=num_participants,
        max_size=num_participants,
        unique=True
    ))
    
    return PlanningSession(
        id=session_id,
        name=name,
        organizer_id=organizer_id,
        invite_token=invite_token,
        invite_expires_at=invite_expires_at,
        invite_revoked=invite_revoked,
        status=status,
        created_at=created_at,
        updated_at=updated_at,
        participant_ids=participant_ids,
    )


@composite
def itinerary_item_strategy(draw: st.DrawFn) -> ItineraryItem:
    """Generate a valid ItineraryItem."""
    item_id = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        whitelist_characters="-_"
    )))
    session_id = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        whitelist_characters="-_"
    )))
    venue_id = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        whitelist_characters="-_"
    )))
    scheduled_time = draw(st.datetimes(
        min_value=datetime(2020, 1, 1),
        max_value=datetime(2030, 12, 31)
    ))
    added_at = draw(st.datetimes(
        min_value=datetime(2020, 1, 1),
        max_value=datetime(2030, 12, 31)
    ))
    added_by = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        whitelist_characters="-_"
    )))
    order = draw(st.integers(min_value=0, max_value=100))
    
    return ItineraryItem(
        id=item_id,
        session_id=session_id,
        venue_id=venue_id,
        scheduled_time=scheduled_time,
        added_at=added_at,
        added_by=added_by,
        order=order,
    )


# Property Tests

@given(planning_session_strategy())
@settings(max_examples=100)
def test_property_12_session_serialization_round_trip(session: PlanningSession) -> None:
    """
    **Feature: group-coordination, Property 12: Session serialization round-trip**
    
    *For any* valid planning session, serializing to JSON then deserializing
    SHALL produce an equivalent session object.
    
    **Validates: Requirements 5.4, 5.5**
    """
    # Serialize to JSON
    json_str = session.to_json()
    
    # Deserialize from JSON
    restored_session = PlanningSession.from_json(json_str)
    
    # Verify all fields match
    assert restored_session.id == session.id
    assert restored_session.name == session.name
    assert restored_session.organizer_id == session.organizer_id
    assert restored_session.invite_token == session.invite_token
    assert restored_session.invite_revoked == session.invite_revoked
    assert restored_session.status == session.status
    assert restored_session.participant_ids == session.participant_ids
    
    # Compare timestamps (allow for microsecond precision differences)
    assert abs((restored_session.invite_expires_at - session.invite_expires_at).total_seconds()) < 0.001
    assert abs((restored_session.created_at - session.created_at).total_seconds()) < 0.001
    assert abs((restored_session.updated_at - session.updated_at).total_seconds()) < 0.001


@given(participant_strategy())
@settings(max_examples=100)
def test_participant_serialization_round_trip(participant: Participant) -> None:
    """
    Test that Participant serialization round-trip preserves all data.
    """
    # Serialize to JSON
    json_str = participant.to_json()
    
    # Deserialize from JSON
    restored = Participant.from_json(json_str)
    
    # Verify all fields match
    assert restored.id == participant.id
    assert restored.session_id == participant.session_id
    assert restored.display_name == participant.display_name
    assert restored.is_organizer == participant.is_organizer
    assert abs((restored.joined_at - participant.joined_at).total_seconds()) < 0.001



# Strategies for service testing

@composite
def organizer_id_strategy(draw: st.DrawFn) -> str:
    """Generate a valid organizer ID."""
    return draw(st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        whitelist_characters="-_"
    )))


@composite
def session_name_strategy(draw: st.DrawFn) -> str:
    """Generate a valid session name."""
    return draw(st.text(min_size=1, max_size=100))


@composite
def display_name_strategy(draw: st.DrawFn) -> str:
    """Generate a valid display name."""
    return draw(st.text(min_size=1, max_size=100))


# Property Tests for Planning Session Service

@given(
    organizer_ids=st.lists(
        organizer_id_strategy(),
        min_size=2,
        max_size=50,
        unique=True
    ),
    session_names=st.lists(
        session_name_strategy(),
        min_size=2,
        max_size=50
    )
)
@settings(max_examples=100)
def test_property_1_invite_token_uniqueness(
    organizer_ids: list,
    session_names: list
) -> None:
    """
    **Feature: group-coordination, Property 1: Invite token uniqueness**
    
    *For any* set of created planning sessions, all generated invite tokens
    SHALL be unique and have sufficient entropy (at least 128 bits).
    
    **Validates: Requirements 1.1**
    """
    # Ensure we have matching lists
    num_sessions = min(len(organizer_ids), len(session_names))
    assume(num_sessions >= 2)
    
    service = PlanningSessionService()
    tokens = set()
    
    for i in range(num_sessions):
        session = service.create_session(
            organizer_id=organizer_ids[i],
            name=session_names[i]
        )
        
        # Verify token is unique
        assert session.invite_token not in tokens, \
            f"Duplicate token found: {session.invite_token}"
        tokens.add(session.invite_token)
        
        # Verify token has sufficient entropy (at least 128 bits)
        # secrets.token_urlsafe(32) produces 256 bits of entropy
        # URL-safe base64 encoding uses 6 bits per character
        # 32 bytes = 256 bits, encoded as ~43 characters
        assert len(session.invite_token) >= 32, \
            f"Token too short: {len(session.invite_token)} chars"
    
    # All tokens should be unique
    assert len(tokens) == num_sessions, \
        f"Expected {num_sessions} unique tokens, got {len(tokens)}"



@given(
    organizer_id=organizer_id_strategy(),
    session_name=session_name_strategy(),
    participant_names=st.lists(
        display_name_strategy(),
        min_size=0,
        max_size=20,
        unique=True
    )
)
@settings(max_examples=100)
def test_property_2_participant_list_completeness(
    organizer_id: str,
    session_name: str,
    participant_names: list
) -> None:
    """
    **Feature: group-coordination, Property 2: Participant list completeness**
    
    *For any* planning session with N joined participants, the participant list
    SHALL contain exactly N entries with correct display names.
    
    **Validates: Requirements 1.4**
    """
    service = PlanningSessionService()
    session = service.create_session(
        organizer_id=organizer_id,
        name=session_name
    )
    
    # Join participants
    joined_names = []
    for name in participant_names:
        try:
            participant = service.join_session(session.invite_token, name)
            joined_names.append(name)
        except Exception:
            # Skip if join fails (e.g., duplicate)
            pass
    
    # Get participants
    participants = service.get_participants(session.id)
    
    # Should have organizer + joined participants
    expected_count = 1 + len(joined_names)  # 1 for organizer
    assert len(participants) == expected_count, \
        f"Expected {expected_count} participants, got {len(participants)}"
    
    # Verify all joined names are present
    participant_display_names = [p.display_name for p in participants]
    for name in joined_names:
        assert name in participant_display_names, \
            f"Participant '{name}' not found in list"
    
    # Verify organizer is present
    organizer_participants = [p for p in participants if p.is_organizer]
    assert len(organizer_participants) == 1, \
        "Expected exactly one organizer"



@given(
    organizer_id=organizer_id_strategy(),
    session_name=session_name_strategy(),
    participant_names=st.lists(
        display_name_strategy(),
        min_size=1,
        max_size=15,
        unique=True
    )
)
@settings(max_examples=100)
def test_property_3_invite_revocation_preserves_participants(
    organizer_id: str,
    session_name: str,
    participant_names: list
) -> None:
    """
    **Feature: group-coordination, Property 3: Invite revocation preserves participants**
    
    *For any* planning session with existing participants, revoking the invite link
    SHALL preserve all existing participants while preventing new joins.
    
    **Validates: Requirements 1.5**
    """
    from app.event_planning.services.planning_session_service import InviteRevokedError
    
    service = PlanningSessionService()
    session = service.create_session(
        organizer_id=organizer_id,
        name=session_name
    )
    
    # Join some participants before revoking
    joined_ids = []
    for name in participant_names:
        try:
            participant = service.join_session(session.invite_token, name)
            joined_ids.append(participant.id)
        except Exception:
            pass
    
    # Get participants before revocation
    participants_before = service.get_participants(session.id)
    participant_ids_before = {p.id for p in participants_before}
    
    # Revoke the invite
    service.revoke_invite(session.id, organizer_id)
    
    # Get participants after revocation
    participants_after = service.get_participants(session.id)
    participant_ids_after = {p.id for p in participants_after}
    
    # Verify all participants are preserved
    assert participant_ids_before == participant_ids_after, \
        "Participants should be preserved after revocation"
    
    assert len(participants_before) == len(participants_after), \
        f"Expected {len(participants_before)} participants, got {len(participants_after)}"
    
    # Verify new joins are blocked
    try:
        service.join_session(session.invite_token, "NewParticipant")
        assert False, "Should have raised InviteRevokedError"
    except InviteRevokedError:
        pass  # Expected behavior



# Import VoteManager and related types
from app.event_planning.services.vote_manager import VoteManager, VoteTally, RankedVenue


# Strategies for vote testing

@composite
def venue_data_strategy(draw: st.DrawFn) -> dict:
    """Generate valid venue data for testing."""
    return {
        "place_id": draw(st.text(min_size=1, max_size=50, alphabet=st.characters(
            whitelist_categories=("Lu", "Ll", "Nd"),
            whitelist_characters="-_"
        ))),
        "name": draw(st.text(min_size=1, max_size=100)),
        "address": draw(st.text(min_size=1, max_size=200)),
        "suggested_by": draw(st.sampled_from(["agent"]) | st.text(min_size=1, max_size=50, alphabet=st.characters(
            whitelist_categories=("Lu", "Ll", "Nd"),
            whitelist_characters="-_"
        ))),
        "rating": draw(st.none() | st.floats(min_value=0, max_value=5, allow_nan=False)),
        "price_level": draw(st.none() | st.integers(min_value=0, max_value=4)),
    }


@composite
def vote_sequence_strategy(draw: st.DrawFn) -> list:
    """Generate a sequence of votes from different participants."""
    num_votes = draw(st.integers(min_value=1, max_value=20))
    votes = []
    
    for i in range(num_votes):
        participant_id = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(
            whitelist_categories=("Lu", "Ll", "Nd"),
            whitelist_characters="-_"
        )))
        vote_type = draw(st.sampled_from(list(VoteType)))
        votes.append((participant_id, vote_type))
    
    return votes


# Property Tests for Vote Manager

@given(
    session_id=st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        whitelist_characters="-_"
    )),
    venue_data=venue_data_strategy(),
    votes=vote_sequence_strategy()
)
@settings(max_examples=100)
def test_property_4_vote_tally_accuracy(
    session_id: str,
    venue_data: dict,
    votes: list
) -> None:
    """
    **Feature: group-coordination, Property 4: Vote tally accuracy**
    
    *For any* venue with votes cast, the vote tally SHALL equal the count
    of distinct participant votes for that venue.
    
    **Validates: Requirements 2.2, 2.4**
    """
    manager = VoteManager()
    
    # Add venue
    venue = manager.add_venue_option(
        session_id=session_id,
        place_id=venue_data["place_id"],
        name=venue_data["name"],
        address=venue_data["address"],
        suggested_by=venue_data["suggested_by"],
        rating=venue_data["rating"],
        price_level=venue_data["price_level"],
    )
    
    # Cast all votes
    for participant_id, vote_type in votes:
        manager.cast_vote(session_id, venue.id, participant_id, vote_type)
    
    # Get tally
    tally = manager.get_votes(session_id, venue.id)
    
    # Calculate expected counts based on final vote per participant
    # (since votes can be changed, only the last vote per participant counts)
    final_votes: Dict[str, VoteType] = {}
    for participant_id, vote_type in votes:
        final_votes[participant_id] = vote_type
    
    expected_upvotes = sum(1 for v in final_votes.values() if v == VoteType.UPVOTE)
    expected_downvotes = sum(1 for v in final_votes.values() if v == VoteType.DOWNVOTE)
    expected_neutral = sum(1 for v in final_votes.values() if v == VoteType.NEUTRAL)
    expected_total = len(final_votes)
    
    # Verify tally accuracy
    assert tally.upvotes == expected_upvotes, \
        f"Expected {expected_upvotes} upvotes, got {tally.upvotes}"
    assert tally.downvotes == expected_downvotes, \
        f"Expected {expected_downvotes} downvotes, got {tally.downvotes}"
    assert tally.neutral == expected_neutral, \
        f"Expected {expected_neutral} neutral, got {tally.neutral}"
    assert tally.total_votes == expected_total, \
        f"Expected {expected_total} total votes, got {tally.total_votes}"
    
    # Verify voters list contains all unique participants
    assert set(tally.voters) == set(final_votes.keys()), \
        "Voters list should contain all unique participants"



@given(
    session_id=st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        whitelist_characters="-_"
    )),
    venue_data=venue_data_strategy(),
    participant_id=st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        whitelist_characters="-_"
    )),
    initial_vote=st.sampled_from(list(VoteType)),
    changed_vote=st.sampled_from(list(VoteType)),
    other_votes=st.lists(
        st.tuples(
            st.text(min_size=1, max_size=50, alphabet=st.characters(
                whitelist_categories=("Lu", "Ll", "Nd"),
                whitelist_characters="-_"
            )),
            st.sampled_from(list(VoteType))
        ),
        min_size=0,
        max_size=10
    )
)
@settings(max_examples=100)
def test_property_5_vote_change_consistency(
    session_id: str,
    venue_data: dict,
    participant_id: str,
    initial_vote: VoteType,
    changed_vote: VoteType,
    other_votes: list
) -> None:
    """
    **Feature: group-coordination, Property 5: Vote change consistency**
    
    *For any* participant changing their vote on a venue, the total vote count
    SHALL remain unchanged (one vote per participant per venue).
    
    **Validates: Requirements 2.3, 2.5**
    """
    # Ensure participant_id is not in other_votes
    other_votes = [(pid, vt) for pid, vt in other_votes if pid != participant_id]
    
    manager = VoteManager()
    
    # Add venue
    venue = manager.add_venue_option(
        session_id=session_id,
        place_id=venue_data["place_id"],
        name=venue_data["name"],
        address=venue_data["address"],
        suggested_by=venue_data["suggested_by"],
        rating=venue_data["rating"],
        price_level=venue_data["price_level"],
    )
    
    # Cast other votes first
    for other_pid, vote_type in other_votes:
        manager.cast_vote(session_id, venue.id, other_pid, vote_type)
    
    # Cast initial vote
    manager.cast_vote(session_id, venue.id, participant_id, initial_vote)
    
    # Get tally before change
    tally_before = manager.get_votes(session_id, venue.id)
    total_before = tally_before.total_votes
    
    # Change vote
    manager.cast_vote(session_id, venue.id, participant_id, changed_vote)
    
    # Get tally after change
    tally_after = manager.get_votes(session_id, venue.id)
    total_after = tally_after.total_votes
    
    # Total vote count should remain unchanged
    assert total_before == total_after, \
        f"Total votes changed from {total_before} to {total_after} after vote change"
    
    # Participant should still have exactly one vote
    participant_votes = manager.get_participant_votes(session_id, participant_id)
    venue_votes = [v for v in participant_votes if v.venue_id == venue.id]
    assert len(venue_votes) == 1, \
        f"Participant should have exactly 1 vote on venue, got {len(venue_votes)}"
    
    # The vote should reflect the changed value
    assert venue_votes[0].vote_type == changed_vote, \
        f"Vote type should be {changed_vote}, got {venue_votes[0].vote_type}"



@given(
    session_id=st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        whitelist_characters="-_"
    )),
    num_venues=st.integers(min_value=1, max_value=10),
    num_participants=st.integers(min_value=1, max_value=15)
)
@settings(max_examples=100)
def test_property_10_venue_ranking_by_votes(
    session_id: str,
    num_venues: int,
    num_participants: int
) -> None:
    """
    **Feature: group-coordination, Property 10: Venue ranking by votes**
    
    *For any* set of venues with votes, the ranked list SHALL be sorted
    in descending order by vote count.
    
    **Validates: Requirements 4.1**
    """
    import random
    
    manager = VoteManager()
    
    # Add venues
    venues = []
    for i in range(num_venues):
        venue = manager.add_venue_option(
            session_id=session_id,
            place_id=f"place_{i}",
            name=f"Venue {i}",
            address=f"Address {i}",
            suggested_by="agent",
        )
        venues.append(venue)
    
    # Generate random votes
    participant_ids = [f"participant_{i}" for i in range(num_participants)]
    
    for venue in venues:
        # Each participant may or may not vote on each venue
        for pid in participant_ids:
            if random.random() > 0.3:  # 70% chance to vote
                vote_type = random.choice(list(VoteType))
                manager.cast_vote(session_id, venue.id, pid, vote_type)
    
    # Get ranked venues
    ranked = manager.get_ranked_venues(session_id)
    
    # Verify all venues are present
    assert len(ranked) == num_venues, \
        f"Expected {num_venues} ranked venues, got {len(ranked)}"
    
    # Verify descending order by net score
    for i in range(len(ranked) - 1):
        current_score = ranked[i].tally.net_score
        next_score = ranked[i + 1].tally.net_score
        assert current_score >= next_score, \
            f"Venues not sorted: score {current_score} followed by {next_score}"
    
    # Verify ranks are assigned correctly
    for i in range(len(ranked) - 1):
        current = ranked[i]
        next_rv = ranked[i + 1]
        
        if current.tally.net_score > next_rv.tally.net_score:
            # Different scores should have different ranks
            assert next_rv.rank > current.rank, \
                f"Lower score should have higher rank number"
        else:
            # Same scores should have same rank (tie)
            assert current.rank == next_rv.rank, \
                f"Same scores should have same rank"
    
    # Verify ties are marked correctly
    rank_counts: Dict[int, int] = {}
    for rv in ranked:
        rank_counts[rv.rank] = rank_counts.get(rv.rank, 0) + 1
    
    for rv in ranked:
        if rank_counts[rv.rank] > 1:
            assert rv.is_tied, \
                f"Venue with rank {rv.rank} should be marked as tied"
        else:
            assert not rv.is_tied, \
                f"Venue with unique rank {rv.rank} should not be marked as tied"



# Import ItineraryManager
from app.event_planning.services.itinerary_manager import (
    ItineraryManager,
    ItineraryItemNotFoundError,
)


# Strategies for itinerary testing

@composite
def scheduled_time_strategy(draw: st.DrawFn) -> datetime:
    """Generate a valid scheduled time."""
    return draw(st.datetimes(
        min_value=datetime(2020, 1, 1),
        max_value=datetime(2030, 12, 31)
    ))


@composite
def itinerary_items_data_strategy(draw: st.DrawFn, min_items: int = 1, max_items: int = 20) -> list:
    """Generate a list of itinerary item data for testing."""
    num_items = draw(st.integers(min_value=min_items, max_value=max_items))
    items = []
    
    for i in range(num_items):
        venue_id = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(
            whitelist_categories=("Lu", "Ll", "Nd"),
            whitelist_characters="-_"
        )))
        scheduled_time = draw(st.datetimes(
            min_value=datetime(2020, 1, 1),
            max_value=datetime(2030, 12, 31)
        ))
        added_by = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(
            whitelist_categories=("Lu", "Ll", "Nd"),
            whitelist_characters="-_"
        )))
        items.append({
            "venue_id": venue_id,
            "scheduled_time": scheduled_time,
            "added_by": added_by,
        })
    
    return items


# Property Tests for Itinerary Manager

@given(
    session_id=st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        whitelist_characters="-_"
    )),
    items_data=itinerary_items_data_strategy(min_items=2, max_items=20),
    remove_index=st.integers(min_value=0, max_value=100)
)
@settings(max_examples=100)
def test_property_7_itinerary_removal_consistency(
    session_id: str,
    items_data: list,
    remove_index: int
) -> None:
    """
    **Feature: group-coordination, Property 7: Itinerary removal consistency**
    
    *For any* itinerary with N items, removing one item SHALL result in
    exactly N-1 items with the removed item absent.
    
    **Validates: Requirements 3.3**
    """
    # Ensure we have at least 2 items
    assume(len(items_data) >= 2)
    
    manager = ItineraryManager()
    
    # Add all items to the itinerary
    added_items = []
    for item_data in items_data:
        item = manager.add_to_itinerary(
            session_id=session_id,
            venue_id=item_data["venue_id"],
            scheduled_time=item_data["scheduled_time"],
            added_by=item_data["added_by"],
        )
        added_items.append(item)
    
    # Get initial count
    initial_itinerary = manager.get_itinerary(session_id)
    initial_count = len(initial_itinerary)
    
    # Select an item to remove (use modulo to ensure valid index)
    remove_idx = remove_index % len(added_items)
    item_to_remove = added_items[remove_idx]
    
    # Remove the item
    result = manager.remove_from_itinerary(session_id, item_to_remove.id)
    assert result is True, "Removal should return True"
    
    # Get itinerary after removal
    final_itinerary = manager.get_itinerary(session_id)
    final_count = len(final_itinerary)
    
    # Verify count is N-1
    assert final_count == initial_count - 1, \
        f"Expected {initial_count - 1} items after removal, got {final_count}"
    
    # Verify removed item is absent
    final_item_ids = {item.id for item in final_itinerary}
    assert item_to_remove.id not in final_item_ids, \
        f"Removed item {item_to_remove.id} should not be in itinerary"
    
    # Verify all other items are still present
    for item in added_items:
        if item.id != item_to_remove.id:
            assert item.id in final_item_ids, \
                f"Item {item.id} should still be in itinerary"



@given(
    session_id=st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        whitelist_characters="-_"
    )),
    items_data=itinerary_items_data_strategy(min_items=1, max_items=20)
)
@settings(max_examples=100)
def test_property_6_itinerary_chronological_ordering(
    session_id: str,
    items_data: list
) -> None:
    """
    **Feature: group-coordination, Property 6: Itinerary chronological ordering**
    
    *For any* itinerary with multiple items, the items SHALL be sorted
    in ascending order by scheduled_time.
    
    **Validates: Requirements 3.2**
    """
    manager = ItineraryManager()
    
    # Add all items to the itinerary (in random order based on generation)
    for item_data in items_data:
        manager.add_to_itinerary(
            session_id=session_id,
            venue_id=item_data["venue_id"],
            scheduled_time=item_data["scheduled_time"],
            added_by=item_data["added_by"],
        )
    
    # Get the itinerary
    itinerary = manager.get_itinerary(session_id)
    
    # Verify all items are present
    assert len(itinerary) == len(items_data), \
        f"Expected {len(items_data)} items, got {len(itinerary)}"
    
    # Verify chronological ordering (ascending by scheduled_time)
    for i in range(len(itinerary) - 1):
        current_time = itinerary[i].scheduled_time
        next_time = itinerary[i + 1].scheduled_time
        assert current_time <= next_time, \
            f"Items not in chronological order: {current_time} > {next_time}"
    
    # Verify order values are consistent with position
    for i, item in enumerate(itinerary):
        assert item.order == i, \
            f"Item at position {i} has order {item.order}"


# Import CommentService for comment testing
from app.event_planning.services.comment_service import CommentService


# Strategies for comment testing

@composite
def comment_data_strategy(draw: st.DrawFn) -> dict:
    """Generate valid comment data for testing."""
    # Generate text within the 500 character limit (use smaller max for performance)
    text = draw(st.text(min_size=1, max_size=100, alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd", "Zs"),
        whitelist_characters=".,!?-_"
    )))
    participant_id = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        whitelist_characters="-_"
    )))
    created_at = draw(st.datetimes(
        min_value=datetime(2020, 1, 1),
        max_value=datetime(2030, 12, 31)
    ))
    return {
        "participant_id": participant_id,
        "text": text,
        "created_at": created_at,
    }


@composite
def comments_list_strategy(draw: st.DrawFn, min_comments: int = 1, max_comments: int = 20) -> list:
    """Generate a list of comment data for testing."""
    num_comments = draw(st.integers(min_value=min_comments, max_value=max_comments))
    comments = []
    
    for _ in range(num_comments):
        comment_data = draw(comment_data_strategy())
        comments.append(comment_data)
    
    return comments


# Property Test for Comment Service

@given(
    session_id=st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        whitelist_characters="-_"
    )),
    venue_id=st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        whitelist_characters="-_"
    )),
    comments_data=comments_list_strategy(min_comments=1, max_comments=15)
)
@settings(max_examples=100, deadline=None)
def test_property_13_comment_chronological_ordering(
    session_id: str,
    venue_id: str,
    comments_data: list
) -> None:
    """
    **Feature: group-coordination, Property 13: Comment chronological ordering**
    
    *For any* venue with multiple comments, the comments SHALL be sorted
    in ascending order by created_at timestamp.
    
    **Validates: Requirements 6.2**
    """
    service = CommentService()
    
    # Register the venue
    service.register_venue(session_id, venue_id)
    
    # Add all comments (in the order generated, which may not be chronological)
    for comment_data in comments_data:
        service.add_comment(
            session_id=session_id,
            venue_id=venue_id,
            participant_id=comment_data["participant_id"],
            text=comment_data["text"],
            created_at=comment_data["created_at"],
        )
    
    # Get comments
    comments = service.get_comments(session_id, venue_id)
    
    # Verify all comments are present
    assert len(comments) == len(comments_data), \
        f"Expected {len(comments_data)} comments, got {len(comments)}"
    
    # Verify chronological ordering (ascending by created_at)
    for i in range(len(comments) - 1):
        current_time = comments[i].created_at
        next_time = comments[i + 1].created_at
        assert current_time <= next_time, \
            f"Comments not in chronological order: {current_time} > {next_time}"



# Property Test for Finalization Immutability

@given(
    organizer_id=organizer_id_strategy(),
    session_name=session_name_strategy(),
    participant_names=st.lists(
        display_name_strategy(),
        min_size=0,
        max_size=5,
        unique=True
    ),
    venue_data=venue_data_strategy(),
)
@settings(max_examples=100, deadline=None)
def test_property_9_finalization_immutability(
    organizer_id: str,
    session_name: str,
    participant_names: list,
    venue_data: dict,
) -> None:
    """
    **Feature: group-coordination, Property 9: Finalization immutability**
    
    *For any* finalized session, all modification operations (add venue,
    cast vote, add to itinerary) SHALL be rejected.
    
    **Validates: Requirements 3.5**
    """
    from app.event_planning.services.planning_session_service import (
        PlanningSessionService,
        SessionFinalizedError as SessionServiceFinalizedError,
    )
    from app.event_planning.services.vote_manager import (
        VoteManager,
        SessionFinalizedError as VoteManagerFinalizedError,
    )
    from app.event_planning.services.itinerary_manager import (
        ItineraryManager,
        SessionFinalizedError as ItineraryFinalizedError,
    )
    from app.event_planning.services.comment_service import (
        CommentService,
        SessionFinalizedError as CommentFinalizedError,
    )
    
    # Create services
    session_service = PlanningSessionService()
    vote_manager = VoteManager()
    itinerary_manager = ItineraryManager()
    comment_service = CommentService()
    
    # Create a session
    session = session_service.create_session(
        organizer_id=organizer_id,
        name=session_name
    )
    
    # Join some participants
    for name in participant_names:
        try:
            session_service.join_session(session.invite_token, name)
        except Exception:
            pass
    
    # Add a venue before finalization (should succeed)
    venue = vote_manager.add_venue_option(
        session_id=session.id,
        place_id=venue_data["place_id"],
        name=venue_data["name"],
        address=venue_data["address"],
        suggested_by=venue_data["suggested_by"],
        rating=venue_data["rating"],
        price_level=venue_data["price_level"],
    )
    
    # Register venue for comments
    comment_service.register_venue(session.id, venue.id)
    
    # Finalize the session
    summary = session_service.finalize_session(
        session_id=session.id,
        organizer_id=organizer_id
    )
    
    # Verify session is finalized
    assert session_service.is_session_finalized(session.id), \
        "Session should be finalized"
    
    # Update status in other services
    vote_manager.set_session_status(session.id, SessionStatus.FINALIZED)
    itinerary_manager.set_session_status(session.id, SessionStatus.FINALIZED)
    comment_service.set_session_status(session.id, SessionStatus.FINALIZED)
    
    # Test 1: Adding a new venue should be rejected
    try:
        vote_manager.add_venue_option(
            session_id=session.id,
            place_id="new_place",
            name="New Venue",
            address="New Address",
            suggested_by="agent",
        )
        assert False, "Adding venue to finalized session should raise SessionFinalizedError"
    except VoteManagerFinalizedError:
        pass  # Expected behavior
    
    # Test 2: Casting a vote should be rejected
    try:
        vote_manager.cast_vote(
            session_id=session.id,
            venue_id=venue.id,
            participant_id=organizer_id,
            vote_type=VoteType.UPVOTE,
        )
        assert False, "Casting vote in finalized session should raise SessionFinalizedError"
    except VoteManagerFinalizedError:
        pass  # Expected behavior
    
    # Test 3: Adding to itinerary should be rejected
    try:
        itinerary_manager.add_to_itinerary(
            session_id=session.id,
            venue_id=venue.id,
            scheduled_time=datetime.now(),
            added_by=organizer_id,
        )
        assert False, "Adding to itinerary in finalized session should raise SessionFinalizedError"
    except ItineraryFinalizedError:
        pass  # Expected behavior
    
    # Test 4: Adding a comment should be rejected
    try:
        comment_service.add_comment(
            session_id=session.id,
            venue_id=venue.id,
            participant_id=organizer_id,
            text="Test comment",
        )
        assert False, "Adding comment to finalized session should raise SessionFinalizedError"
    except CommentFinalizedError:
        pass  # Expected behavior
    
    # Test 5: Joining the session should be rejected
    try:
        session_service.join_session(session.invite_token, "NewParticipant")
        assert False, "Joining finalized session should raise SessionFinalizedError"
    except SessionServiceFinalizedError:
        pass  # Expected behavior
    
    # Test 6: Finalizing again should be rejected
    try:
        session_service.finalize_session(
            session_id=session.id,
            organizer_id=organizer_id
        )
        assert False, "Finalizing already finalized session should raise SessionFinalizedError"
    except SessionServiceFinalizedError:
        pass  # Expected behavior



# Property Test for Summary Completeness

@given(
    organizer_id=organizer_id_strategy(),
    session_name=session_name_strategy(),
    participant_names=st.lists(
        display_name_strategy(),
        min_size=1,
        max_size=10,
        unique=True
    ),
    items_data=itinerary_items_data_strategy(min_items=1, max_items=10),
)
@settings(max_examples=100, deadline=None)
def test_property_11_summary_completeness(
    organizer_id: str,
    session_name: str,
    participant_names: list,
    items_data: list,
) -> None:
    """
    **Feature: group-coordination, Property 11: Summary completeness**
    
    *For any* finalized session, the generated summary SHALL contain all
    itinerary items, their times, addresses, and all participant names.
    
    **Validates: Requirements 4.5**
    """
    from app.event_planning.services.planning_session_service import PlanningSessionService
    
    # Create services
    session_service = PlanningSessionService()
    itinerary_manager = ItineraryManager()
    
    # Create a session
    session = session_service.create_session(
        organizer_id=organizer_id,
        name=session_name
    )
    
    # Join participants
    joined_names = []
    for name in participant_names:
        try:
            participant = session_service.join_session(session.invite_token, name)
            joined_names.append(name)
        except Exception:
            pass
    
    # Add itinerary items
    added_items = []
    for item_data in items_data:
        item = itinerary_manager.add_to_itinerary(
            session_id=session.id,
            venue_id=item_data["venue_id"],
            scheduled_time=item_data["scheduled_time"],
            added_by=item_data["added_by"],
        )
        added_items.append(item)
    
    # Get the itinerary (sorted chronologically)
    itinerary = itinerary_manager.get_itinerary(session.id)
    
    # Finalize the session with the itinerary
    summary = session_service.finalize_session(
        session_id=session.id,
        organizer_id=organizer_id,
        itinerary_items=itinerary,
    )
    
    # Verify summary completeness
    
    # 1. Check session info
    assert summary.session_id == session.id, \
        "Summary should contain correct session_id"
    assert summary.session_name == session_name, \
        "Summary should contain correct session_name"
    
    # 2. Check all participants are included
    summary_participant_names = summary.get_participant_names()
    
    # Organizer should be included
    organizer_found = any(
        p.is_organizer for p in summary.participants
    )
    assert organizer_found, "Summary should include the organizer"
    
    # All joined participants should be included
    for name in joined_names:
        assert name in summary_participant_names, \
            f"Participant '{name}' should be in summary"
    
    # Total participant count should match (organizer + joined)
    expected_participant_count = 1 + len(joined_names)  # 1 for organizer
    assert len(summary.participants) == expected_participant_count, \
        f"Expected {expected_participant_count} participants, got {len(summary.participants)}"
    
    # 3. Check all itinerary items are included
    assert len(summary.itinerary) == len(itinerary), \
        f"Expected {len(itinerary)} itinerary items, got {len(summary.itinerary)}"
    
    # Verify all venue IDs are present
    summary_venue_ids = summary.get_venue_ids()
    for item in itinerary:
        assert item.venue_id in summary_venue_ids, \
            f"Venue '{item.venue_id}' should be in summary itinerary"
    
    # 4. Check all scheduled times are included
    summary_times = summary.get_scheduled_times()
    for item in itinerary:
        # Check if the scheduled time is present (allowing for microsecond differences)
        time_found = any(
            abs((t - item.scheduled_time).total_seconds()) < 0.001
            for t in summary_times
        )
        assert time_found, \
            f"Scheduled time '{item.scheduled_time}' should be in summary"
    
    # 5. Check shareable URL is generated
    assert summary.share_url, "Summary should have a shareable URL"
    assert session.id in summary.share_url, \
        "Shareable URL should contain session ID"
    
    # 6. Check finalized_at timestamp is set
    assert summary.finalized_at is not None, \
        "Summary should have finalized_at timestamp"


# Property 8: Session state synchronization
# **Feature: group-coordination, Property 8: Session state synchronization**
# **Validates: Requirements 3.4**

@given(
    organizer_id=st.text(min_size=1, max_size=50, alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        whitelist_characters="-_"
    )),
    session_name=st.text(min_size=1, max_size=100),
    num_participants=st.integers(min_value=1, max_value=5),
    num_venues=st.integers(min_value=1, max_value=5),
    num_itinerary_items=st.integers(min_value=0, max_value=5),
)
@settings(max_examples=100, deadline=None)
def test_property_8_session_state_synchronization(
    organizer_id: str,
    session_name: str,
    num_participants: int,
    num_venues: int,
    num_itinerary_items: int,
) -> None:
    """
    **Feature: group-coordination, Property 8: Session state synchronization**
    **Validates: Requirements 3.4**
    
    Property: For any participant reconnecting to a session, the synchronized
    state SHALL match the current session state exactly.
    
    This test verifies that when a participant reconnects, they receive the
    complete and accurate current state of the session including:
    - All participants
    - All venues
    - All votes
    - All itinerary items
    - All comments
    - Session status
    """
    from app.event_planning.services.session_coordinator import SessionCoordinator
    from app.event_planning.models.venue import VoteType
    
    # Create coordinator with all services
    coordinator = SessionCoordinator()
    
    # Create a session
    session = coordinator.session_service.create_session(
        organizer_id=organizer_id,
        name=session_name,
        expiry_hours=72
    )
    session_id = session.id
    
    # Add participants
    participant_ids = []
    for i in range(num_participants):
        participant = coordinator.session_service.join_session(
            invite_token=session.invite_token,
            display_name=f"Participant-{i}",
            participant_id=f"participant-{i}"
        )
        participant_ids.append(participant.id)
    
    # Add venues and register them with comment service
    venue_ids = []
    for i in range(num_venues):
        venue = coordinator.vote_manager.add_venue_option(
            session_id=session_id,
            place_id=f"place-{i}",
            name=f"Venue {i}",
            address=f"Address {i}",
            suggested_by="agent",
            venue_id=f"venue-{i}"
        )
        venue_ids.append(venue.id)
        # Register venue with comment service
        coordinator.comment_service.register_venue(session_id, venue.id)
    
    # Cast some votes
    if venue_ids and participant_ids:
        for i, participant_id in enumerate(participant_ids):
            venue_id = venue_ids[i % len(venue_ids)]
            vote_type = [VoteType.UPVOTE, VoteType.DOWNVOTE, VoteType.NEUTRAL][i % 3]
            coordinator.vote_manager.cast_vote(
                session_id=session_id,
                venue_id=venue_id,
                participant_id=participant_id,
                vote_type=vote_type
            )
    
    # Add itinerary items
    itinerary_item_ids = []
    if venue_ids:
        for i in range(min(num_itinerary_items, len(venue_ids))):
            scheduled_time = datetime.now() + timedelta(hours=i+1)
            item = coordinator.itinerary_manager.add_to_itinerary(
                session_id=session_id,
                venue_id=venue_ids[i],
                scheduled_time=scheduled_time,
                added_by=organizer_id,
                item_id=f"item-{i}"
            )
            itinerary_item_ids.append(item.id)
    
    # Add some comments
    if venue_ids and participant_ids:
        for i, venue_id in enumerate(venue_ids):
            participant_id = participant_ids[i % len(participant_ids)]
            coordinator.comment_service.add_comment(
                session_id=session_id,
                venue_id=venue_id,
                participant_id=participant_id,
                text=f"Comment {i} on venue {venue_id}"
            )
    
    # Get the current session state
    state = coordinator.get_session_state(session_id)
    
    # Verify state completeness
    
    # 1. Check session ID
    assert state.session_id == session_id, \
        "State should contain correct session_id"
    
    # 2. Check all participants are included (organizer + joined)
    expected_participant_count = 1 + num_participants  # 1 for organizer
    assert len(state.participants) == expected_participant_count, \
        f"Expected {expected_participant_count} participants, got {len(state.participants)}"
    
    # Verify organizer is included
    organizer_found = any(
        p.get("is_organizer", False) for p in state.participants
    )
    assert organizer_found, "State should include the organizer"
    
    # Verify all joined participants are included
    state_participant_ids = [p["id"] for p in state.participants]
    for participant_id in participant_ids:
        assert participant_id in state_participant_ids, \
            f"Participant '{participant_id}' should be in state"
    
    # 3. Check all venues are included
    assert len(state.venues) == num_venues, \
        f"Expected {num_venues} venues, got {len(state.venues)}"
    
    state_venue_ids = [v["id"] for v in state.venues]
    for venue_id in venue_ids:
        assert venue_id in state_venue_ids, \
            f"Venue '{venue_id}' should be in state"
    
    # 4. Check all itinerary items are included
    assert len(state.itinerary) == len(itinerary_item_ids), \
        f"Expected {len(itinerary_item_ids)} itinerary items, got {len(state.itinerary)}"
    
    state_item_ids = [item["id"] for item in state.itinerary]
    for item_id in itinerary_item_ids:
        assert item_id in state_item_ids, \
            f"Itinerary item '{item_id}' should be in state"
    
    # 5. Check votes are included for all venues
    assert len(state.votes) == num_venues, \
        f"Expected votes for {num_venues} venues, got {len(state.votes)}"
    
    for venue_id in venue_ids:
        assert venue_id in state.votes, \
            f"Votes for venue '{venue_id}' should be in state"
    
    # 6. Check comments are included for all venues
    assert len(state.comments) == num_venues, \
        f"Expected comments for {num_venues} venues, got {len(state.comments)}"
    
    for venue_id in venue_ids:
        assert venue_id in state.comments, \
            f"Comments for venue '{venue_id}' should be in state"
    
    # 7. Check session status
    assert state.status == session.status.value, \
        "State should contain correct session status"
    
    # 8. Verify state consistency by getting it again
    # (simulating a reconnection scenario)
    state2 = coordinator.get_session_state(session_id)
    
    # The two states should be identical
    assert state2.session_id == state.session_id, \
        "Reconnected state should have same session_id"
    assert len(state2.participants) == len(state.participants), \
        "Reconnected state should have same number of participants"
    assert len(state2.venues) == len(state.venues), \
        "Reconnected state should have same number of venues"
    assert len(state2.itinerary) == len(state.itinerary), \
        "Reconnected state should have same number of itinerary items"
    assert len(state2.votes) == len(state.votes), \
        "Reconnected state should have same number of vote tallies"
    assert len(state2.comments) == len(state.comments), \
        "Reconnected state should have same number of comment lists"
    assert state2.status == state.status, \
        "Reconnected state should have same status"
