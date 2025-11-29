from textblob import TextBlob
import asyncio
import logging
from typing import Dict, Any
from ..monitoring import monitor

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    def __init__(self):
        logger.info("Initializing SentimentAnalyzer")
        
    def analyze(self, text: str) -> Dict[str, Any]:
        """Synchronous sentiment analysis"""
        return self._analyze_text(text)
        
    @monitor.track_time('sentiment')
    async def analyze_async(self, text: str) -> Dict[str, Any]:
        """Asynchronous sentiment analysis"""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._analyze_text, text)
        except Exception as e:
            logger.error(f"Error in async sentiment analysis: {str(e)}")
            return {
                "sentiment": "NEUTRAL",
                "score": 0.5,
                "confidence": 0,
                "details": None,
                "success": False,
                "error": str(e)
            }
        
    def _analyze_text(self, text: str) -> Dict[str, Any]:
        """Core sentiment analysis logic"""
        try:
            if not text:
                return {
                    "sentiment": "NEUTRAL",
                    "score": 0.5,
                    "confidence": 0,
                    "details": None,
                    "success": False,
                    "error": "Empty text provided"
                }

            analysis = TextBlob(text)
            # Convert polarity (-1 to 1) to a score (0 to 1)
            score = (analysis.sentiment.polarity + 1) / 2
            
            # Determine sentiment label
            if analysis.sentiment.polarity > 0.1:
                label = "POSITIVE"
            elif analysis.sentiment.polarity < -0.1:
                label = "NEGATIVE"
            else:
                label = "NEUTRAL"
                
            return {
                'sentiment': label,
                'score': float(score),
                'confidence': 1 - analysis.sentiment.subjectivity,
                'details': {
                    'polarity': analysis.sentiment.polarity,
                    'subjectivity': analysis.sentiment.subjectivity
                },
                'success': True,
                'error': None
            }
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {str(e)}")
            return {
                "sentiment": "NEUTRAL",
                "score": 0.5,
                "confidence": 0,
                "details": None,
                "success": False,
                "error": str(e)
            }

sentiment_analyzer = SentimentAnalyzer()