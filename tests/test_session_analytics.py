"""
Tests for session analytics and None handling

Critical test: Ensures analytics don't crash on None values in metrics.
"""
import pytest
from engine.session_manager import InterviewSession


def test_session_initialization():
    """Test InterviewSession initializes with empty history."""
    session = InterviewSession(
        session_id="test-123",
        difficulty="medium",
        topic="Python"
    )
    
    assert session.session_id == "test-123"
    assert session.difficulty == "medium"
    assert session.topic == "Python"
    assert len(session.history["wpm"]) == 0


def test_log_audio_metrics_handles_none():
    """Test logging audio metrics with None WPM doesn't crash."""
    session = InterviewSession("test-123", "medium", "Python")
    
    # Log metrics with None WPM
    session.log_audio_metrics(None, 30.0, 0.85)
    
    # Should store None without crashing
    assert len(session.history["wpm"]) == 1
    assert session.history["wpm"][0] is None


def test_get_stats_filters_none_values():
    """Test get_stats correctly filters None before averaging."""
    session = InterviewSession("test-123", "medium", "Python")
    
    # Log mix of valid and None WPM values
    session.log_audio_metrics(120, 10.0, 0.9)
    session.log_audio_metrics(None, 5.0, 0.5)  # No speech detected
    session.log_audio_metrics(95, 12.0, 0.85)
    session.log_audio_metrics(110, 11.0, 0.88)
    session.log_audio_metrics(None, 3.0, 0.3)  # No speech
    
    stats = session.get_stats()
    
    # Average should exclude None values: (120 + 95 + 110) / 3 = 108.33
    assert stats["avg_wpm"] is not None
    assert 100 < stats["avg_wpm"] < 115
    
    # Should not have NaN or None in result
    assert stats["avg_wpm"] != float('nan')
