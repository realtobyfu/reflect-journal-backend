import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models import User, JournalEntry, EmotionHistory
from app.database import get_db

client = TestClient(app)

# Mock user for testing
test_user = {
    "id": 1,
    "email": "test@example.com",
    "username": "testuser",
    "firebase_uid": "test_firebase_uid"
}

# Mock database session
@pytest.fixture
def mock_db():
    db = MagicMock(spec=Session)
    return db

@pytest.fixture
def mock_current_user():
    user = MagicMock(spec=User)
    user.id = 1
    user.email = "test@example.com"
    user.username = "testuser"
    return user

def test_stores_multi_dimensional_emotion_data(mock_db, mock_current_user):
    """Test that emotion API stores multi-dimensional emotion data correctly."""
    # Mock entry
    mock_entry = MagicMock(spec=JournalEntry)
    mock_entry.id = 1
    mock_entry.user_id = 1
    mock_db.query().filter().first.return_value = mock_entry
    
    emotion_data = {
        "primary": {"emotion": "joy", "intensity": 75},
        "secondary": ["excited", "grateful"],
        "energy": 25,
        "context": {"activity": "work", "social": True}
    }
    
    with patch('app.api.emotions.get_db', return_value=mock_db), \
         patch('app.api.emotions.get_current_user', return_value=mock_current_user):
        
        response = client.post(
            "/api/emotions/entries/1/emotions",
            json=emotion_data
        )
    
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["message"] == "Emotions updated successfully"
    assert response_data["entry_id"] == 1
    
    # Verify the entry was updated
    assert mock_entry.emotions == emotion_data
    assert mock_entry.energy_level == 25
    mock_db.commit.assert_called_once()

def test_retrieves_emotion_history_with_pagination(mock_db, mock_current_user):
    """Test that emotion history is retrieved with proper pagination."""
    # Mock emotion history data
    mock_emotions = []
    for i in range(10):
        mock_emotion = MagicMock(spec=EmotionHistory)
        mock_emotion.emotion_data = {
            "primary": {"emotion": f"emotion_{i}", "intensity": 50 + i}
        }
        mock_emotion.created_at = datetime.utcnow() - timedelta(days=i)
        mock_emotions.append(mock_emotion)
    
    mock_db.query().filter().order_by().all.return_value = mock_emotions
    
    with patch('app.api.emotions.get_db', return_value=mock_db), \
         patch('app.api.emotions.get_current_user', return_value=mock_current_user):
        
        response = client.get("/api/emotions/history?days=30")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "patterns" in data
    assert "recent_emotions" in data
    assert "insights" in data
    assert len(data["recent_emotions"]) <= 7  # Recent emotions limited

def test_generates_contextual_suggestions(mock_db, mock_current_user):
    """Test that contextual emotion suggestions are generated."""
    # Mock recent emotions for pattern analysis
    mock_emotions = [
        MagicMock(emotion_data={"primary": {"emotion": "happy", "intensity": 70}}),
        MagicMock(emotion_data={"primary": {"emotion": "content", "intensity": 60}}),
    ]
    mock_db.query().filter().order_by().limit().all.return_value = mock_emotions
    
    with patch('app.api.emotions.get_db', return_value=mock_db), \
         patch('app.api.emotions.get_current_user', return_value=mock_current_user), \
         patch('app.api.emotions.datetime') as mock_datetime:
        
        # Mock morning time
        mock_datetime.now.return_value.hour = 8
        mock_datetime.utcnow.return_value = datetime.utcnow()
        
        response = client.get("/api/emotions/suggestions")
    
    assert response.status_code == 200
    suggestions = response.json()
    
    assert len(suggestions) <= 3
    for suggestion in suggestions:
        assert "emotion" in suggestion
        assert "intensity" in suggestion
        assert "reason" in suggestion
        assert 0 <= suggestion["intensity"] <= 100

def test_handles_emotion_data_migration_from_old_schema(mock_db, mock_current_user):
    """Test that the API handles migration from old mood schema."""
    # Test entry with old mood field but no emotions
    mock_entry = MagicMock(spec=JournalEntry)
    mock_entry.id = 1
    mock_entry.user_id = 1
    mock_entry.mood = "happy"  # Old schema
    mock_entry.emotions = None  # New schema not yet populated
    mock_db.query().filter().first.return_value = mock_entry
    
    emotion_data = {
        "primary": {"emotion": "joy", "intensity": 80},
        "secondary": [],
        "energy": 15
    }
    
    with patch('app.api.emotions.get_db', return_value=mock_db), \
         patch('app.api.emotions.get_current_user', return_value=mock_current_user):
        
        response = client.post(
            "/api/emotions/entries/1/emotions",
            json=emotion_data
        )
    
    assert response.status_code == 200
    # Should successfully update even with old mood data present
    assert mock_entry.emotions == emotion_data

def test_emotion_not_found_error(mock_db, mock_current_user):
    """Test error handling when entry is not found."""
    mock_db.query().filter().first.return_value = None
    
    with patch('app.api.emotions.get_db', return_value=mock_db), \
         patch('app.api.emotions.get_current_user', return_value=mock_current_user):
        
        response = client.post(
            "/api/emotions/entries/999/emotions",
            json={"primary": {"emotion": "joy", "intensity": 50}, "energy": 0}
        )
    
    assert response.status_code == 404
    assert "Entry not found" in response.json()["detail"]

def test_emotion_validation():
    """Test emotion data validation."""
    invalid_data = {
        "primary": {"emotion": "joy", "intensity": 150},  # Invalid intensity > 100
        "energy": 60  # Invalid energy > 50
    }
    
    response = client.post(
        "/api/emotions/entries/1/emotions",
        json=invalid_data
    )
    
    # Should return validation error
    assert response.status_code == 422  # Validation error

def test_empty_emotion_history_response(mock_db, mock_current_user):
    """Test response when user has no emotion history."""
    mock_db.query().filter().order_by().all.return_value = []
    
    with patch('app.api.emotions.get_db', return_value=mock_db), \
         patch('app.api.emotions.get_current_user', return_value=mock_current_user):
        
        response = client.get("/api/emotions/history")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["patterns"] == []
    assert data["recent_emotions"] == []
    assert len(data["insights"]) > 0
    assert "Start tracking" in data["insights"][0]