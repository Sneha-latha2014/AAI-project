import os
from dotenv import load_dotenv
import logging
from typing import Optional, Dict, Any
from ..monitoring import monitor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

print("Initializing ChatProcessor module...")

class ChatProcessor:
    def __init__(self):
        print("Setting up chat processor configuration...")
        self.api_key = os.getenv('GOOGLE_GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GOOGLE_GEMINI_API_KEY is required")
        
        self.model = None
        self.generation_config = {
            "temperature": float(os.getenv('MODEL_TEMPERATURE', '0.7')),
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 1024,
        }
        
        self.safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]
        print("Chat processor configuration complete.")
        
    def process(self, text: str) -> Dict[str, Any]:
        """Synchronous chat processing"""
        if not text:
            return {
                "response": "I'd be happy to help! Please provide your question or message.",
                "success": True,
                "error": None
            }
        return self._process_text(text)
        
    async def process_async(self, text: str) -> Dict[str, Any]:
        """Asynchronous chat processing"""
        if not text:
            return {
                "response": "I'd be happy to help! Please provide your question or message.",
                "success": True,
                "error": None
            }
            
        import asyncio
        loop = asyncio.get_event_loop()
        try:
            @monitor.track_time('chat')
            async def _process():
                return await loop.run_in_executor(None, self._process_text, text)
            
            result = await _process()
            return {
                "response": result,
                "success": True,
                "error": None
            }
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Async chat processing error: {error_msg}")
            return {
                "response": "I apologize, but I'm having trouble processing your request at the moment. Please try again.",
                "success": False,
                "error": error_msg
            }
        
    def _init_model(self):
        """Initialize the Gemini model if not already initialized"""
        if self.model is None:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel(
                    model_name='gemini-pro',
                    generation_config=self.generation_config,
                    safety_settings=self.safety_settings
                )
                print("Gemini model initialized successfully")
            except Exception as e:
                print(f"Error initializing Gemini model: {str(e)}")
                raise

    def _process_text(self, text: str) -> str:
        """Core chat processing logic"""
        try:
            if not self.model:
                self._init_model()
                
            # Add context to the prompt
            prompt = f"""You are a helpful AI assistant with deep knowledge of diverse topics. Please provide a clear and informative response to help the user.

Question/Message: {text}

Response:"""
            
            try:
                response = self.model.generate_content(prompt)
                
                if hasattr(response, 'text') and response.text:
                    return response.text.strip()
                elif isinstance(response, dict) and 'candidates' in response:
                    return response['candidates'][0]['content'].strip()
                else:
                    # Handle other response formats
                    str_response = str(response)
                    if len(str_response) > 0:
                        return str_response
                    return "I understand your message. How can I assist you further?"
                    
            except AttributeError:
                # If response structure is different than expected
                print("Unexpected response structure, trying alternative method...")
                response = self.model.generate_content(text, stream=False)
                if hasattr(response, 'text'):
                    return response.text.strip()
                return str(response)
                
        except Exception as e:
            print(f"Chat processing error: {str(e)}")
            import traceback
            traceback.print_exc()
            return "I'm currently experiencing some difficulty processing your request. Could you please rephrase or try again in a moment?"

print("Creating chat processor instance...")
chat_processor = ChatProcessor()
print("Chat processor instance created successfully")