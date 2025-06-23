# app/services/ai_service.py

import os
import json
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import random
from app.models import JournalEntry, User
from sqlalchemy.orm import Session
from sqlalchemy import func

class AIService:
    """Service for AI-powered features including prompts, sentiment analysis, and theme extraction"""
    
    def __init__(self):
        # In production, integrate with OpenAI API
        # For MVP, we'll use rule-based approaches
        pass
    
    def generate_daily_prompts(self, user: User, db: Session) -> List[Dict[str, str]]:
        """Generate personalized prompts based on user history"""
        
        # Get user's recent entries for context
        recent_entries = db.query(JournalEntry).filter(
            JournalEntry.user_id == user.id
        ).order_by(JournalEntry.created_at.desc()).limit(7).all()
        
        # Get user's common moods
        mood_counts = db.query(
            JournalEntry.mood,
            func.count(JournalEntry.id)
        ).filter(
            JournalEntry.user_id == user.id,
            JournalEntry.mood.isnot(None)
        ).group_by(JournalEntry.mood).all()
        
        # Base prompts categorized by type
        prompt_templates = {
            "memory": [
                "What moment from today would you want to remember in 5 years?",
                "Describe a conversation today that made you think differently.",
                "What small victory did you achieve today?",
                "What made you smile unexpectedly today?"
            ],
            "growth": [
                "What challenged you today, and how did you grow from it?",
                "What did you learn about yourself today?",
                "How did you step outside your comfort zone today?",
                "What would you do differently if you could replay today?"
            ],
            "mindfulness": [
                "Describe a small detail you noticed today that others might have missed.",
                "What sounds, smells, or textures stood out to you today?",
                "When did you feel most present today?",
                "What beauty did you encounter in the ordinary today?"
            ],
            "creative": [
                "If today had a color, what would it be and why?",
                "Write today's story in exactly six words.",
                "If today was a song, what would its title be?",
                "Describe today using only metaphors from nature."
            ],
            "gratitude": [
                "List three things you're grateful for today, no matter how small.",
                "Who made a positive impact on your day?",
                "What comfort or convenience did you appreciate today?",
                "What aspect of your health are you thankful for today?"
            ],
            "relationships": [
                "How did you connect with someone today?",
                "What did you appreciate about someone in your life today?",
                "How did you show kindness today?",
                "What relationship do you want to nurture more?"
            ]
        }
        
        # Personalization logic based on user patterns
        selected_prompts = []
        
        # If user has been sad/frustrated lately, add growth and gratitude prompts
        if mood_counts:
            negative_moods = sum(count for mood, count in mood_counts if mood in ['sad', 'frustrated', 'anxious'])
            total_moods = sum(count for _, count in mood_counts)
            
            if negative_moods > total_moods * 0.5:
                selected_prompts.extend(random.sample(prompt_templates["gratitude"], 1))
                selected_prompts.extend(random.sample(prompt_templates["growth"], 1))
        
        # Add variety with other categories
        for category in ["memory", "mindfulness", "creative", "relationships"]:
            selected_prompts.extend(random.sample(prompt_templates[category], 1))
        
        # Ensure we have 4 prompts
        while len(selected_prompts) < 4:
            category = random.choice(list(prompt_templates.keys()))
            prompt = random.choice(prompt_templates[category])
            if prompt not in [p["text"] for p in selected_prompts]:
                selected_prompts.append({"text": prompt, "category": category})
        
        # Format prompts
        return [
            {
                "id": i + 1,
                "text": prompt["text"] if isinstance(prompt, dict) else prompt,
                "category": prompt.get("category", "general") if isinstance(prompt, dict) else category
            }
            for i, prompt in enumerate(selected_prompts[:4])
        ]
    
    def analyze_sentiment(self, text: str) -> Dict[str, any]:
        """Analyze sentiment of journal entry text"""
        
        # Simple keyword-based sentiment analysis for MVP
        # In production, use OpenAI or specialized NLP models
        
        positive_words = [
            'happy', 'joy', 'excited', 'grateful', 'love', 'wonderful', 'amazing',
            'great', 'good', 'fantastic', 'excellent', 'blessed', 'thankful',
            'peaceful', 'calm', 'content', 'satisfied', 'proud', 'accomplished'
        ]
        
        negative_words = [
            'sad', 'angry', 'frustrated', 'worried', 'anxious', 'stressed', 'tired',
            'exhausted', 'disappointed', 'hurt', 'lonely', 'scared', 'overwhelmed',
            'depressed', 'upset', 'terrible', 'awful', 'horrible', 'bad'
        ]
        
        text_lower = text.lower()
        words = text_lower.split()
        
        positive_count = sum(1 for word in words if any(pos in word for pos in positive_words))
        negative_count = sum(1 for word in words if any(neg in word for neg in negative_words))
        total_words = len(words)
        
        # Calculate sentiment score (-1 to 1)
        if total_words == 0:
            sentiment_score = 0
        else:
            sentiment_score = (positive_count - negative_count) / (positive_count + negative_count + 1)
        
        # Determine primary emotion
        if sentiment_score > 0.3:
            primary_emotion = "positive"
            secondary_emotion = "content"
        elif sentiment_score < -0.3:
            primary_emotion = "negative"
            secondary_emotion = "concerned"
        else:
            primary_emotion = "neutral"
            secondary_emotion = "reflective"
        
        return {
            "sentiment_score": round(sentiment_score, 2),
            "primary_emotion": primary_emotion,
            "secondary_emotion": secondary_emotion,
            "positive_word_count": positive_count,
            "negative_word_count": negative_count
        }
    
    def extract_themes(self, entries: List[JournalEntry]) -> List[Dict[str, any]]:
        """Extract common themes from multiple entries"""
        
        # Combine all entry content
        all_text = " ".join([entry.content for entry in entries])
        words = all_text.lower().split()
        
        # Theme keywords mapping
        theme_keywords = {
            "work": ["work", "job", "career", "office", "meeting", "project", "deadline", "colleague", "boss"],
            "relationships": ["friend", "family", "love", "partner", "relationship", "mom", "dad", "wife", "husband"],
            "health": ["health", "exercise", "workout", "sick", "doctor", "sleep", "tired", "energy", "meditation"],
            "personal_growth": ["learn", "grow", "challenge", "improve", "goal", "achievement", "progress", "development"],
            "creativity": ["create", "art", "write", "music", "design", "idea", "inspiration", "imagine"],
            "nature": ["nature", "outside", "walk", "sun", "rain", "tree", "park", "weather"],
            "gratitude": ["grateful", "thankful", "appreciate", "blessed", "fortunate", "gratitude"],
            "stress": ["stress", "anxious", "worry", "pressure", "overwhelm", "busy", "rush"],
            "leisure": ["relax", "fun", "enjoy", "hobby", "read", "watch", "play", "vacation"]
        }
        
        # Count theme occurrences
        theme_counts = {}
        for theme, keywords in theme_keywords.items():
            count = sum(1 for word in words if any(keyword in word for keyword in keywords))
            if count > 0:
                theme_counts[theme] = count
        
        # Sort themes by frequency
        sorted_themes = sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Return top 5 themes with percentages
        total_theme_words = sum(theme_counts.values())
        return [
            {
                "theme": theme.replace("_", " ").title(),
                "count": count,
                "percentage": round((count / total_theme_words) * 100, 1) if total_theme_words > 0 else 0
            }
            for theme, count in sorted_themes[:5]
        ]
    
    def generate_reflection_response(self, entry: JournalEntry) -> str:
        """Generate an AI reflection response to an entry"""
        
        sentiment = self.analyze_sentiment(entry.content)
        
        # Template responses based on sentiment
        if sentiment["primary_emotion"] == "positive":
            responses = [
                "It's wonderful to see you experiencing such positive moments. These are the memories that light up our lives.",
                "Your gratitude and joy shine through your words. Keep nurturing these positive experiences.",
                "What a beautiful reflection! It's clear that you're finding meaning in life's precious moments."
            ]
        elif sentiment["primary_emotion"] == "negative":
            responses = [
                "It sounds like you're going through a challenging time. Remember that difficult moments help us grow stronger.",
                "Your honesty in expressing these feelings is a sign of strength. Be gentle with yourself during this time.",
                "Thank you for sharing these difficult emotions. Remember that this too shall pass, and you're not alone."
            ]
        else:
            responses = [
                "Your reflection shows deep self-awareness. Continue observing and learning from your experiences.",
                "It's valuable to take time to process your thoughts like this. What insights are emerging for you?",
                "Your thoughtful observations reveal a mindful approach to life. Keep exploring these reflections."
            ]
        
        return random.choice(responses)
    
    def get_writing_insights(self, user_id: int, db: Session) -> Dict[str, any]:
        """Generate insights about user's writing patterns"""
        
        # Get all user entries
        entries = db.query(JournalEntry).filter(
            JournalEntry.user_id == user_id
        ).order_by(JournalEntry.created_at.desc()).all()
        
        if not entries:
            return {
                "total_entries": 0,
                "themes": [],
                "average_sentiment": 0,
                "writing_pattern": "No data yet"
            }
        
        # Extract themes
        themes = self.extract_themes(entries)
        
        # Calculate average sentiment
        sentiments = [self.analyze_sentiment(entry.content)["sentiment_score"] for entry in entries]
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
        
        # Analyze writing patterns
        entry_hours = [entry.created_at.hour for entry in entries]
        most_common_hour = max(set(entry_hours), key=entry_hours.count) if entry_hours else 0
        
        if 5 <= most_common_hour < 12:
            pattern = "morning writer"
        elif 12 <= most_common_hour < 17:
            pattern = "afternoon reflector"
        elif 17 <= most_common_hour < 22:
            pattern = "evening journalist"
        else:
            pattern = "night owl"
        
        return {
            "total_entries": len(entries),
            "themes": themes,
            "average_sentiment": round(avg_sentiment, 2),
            "writing_pattern": pattern,
            "most_active_hour": most_common_hour
        }

# Create singleton instance
ai_service = AIService()