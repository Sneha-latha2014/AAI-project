import os
import aiohttp
from dotenv import load_dotenv
from typing import Optional, Dict, Any
import logging
import json
from ..monitoring import monitor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

logger.info("Initializing Translator module...")

class Translator:
    def __init__(self):
        print("Setting up translator configuration...")
        self.rapid_api_key = os.getenv('RAPID_API_KEY')
        if not self.rapid_api_key:
            print("Warning: RAPID_API_KEY not found in environment variables")
            
        # Language code mapping
        self.language_codes = {
            'en': 'en',
            'hi': 'hi',
            'bn': 'bn',
            'gu': 'gu',
            'kn': 'kn',
            'ml': 'ml',
            'mr': 'mr',
            'ta': 'ta',
            'te': 'te'
        }
        
        if not self.rapid_api_key:
            raise ValueError("RAPID_API_KEY is required for translation service")
            
        # Initialize optional Hugging Face model
        self.model = None
        self.tokenizer = None
            
    def get_language_code(self, lang):
        """Normalize language code"""
        if not lang:
            return 'en'  # Default to English
        return self.language_codes.get(lang.lower(), lang.lower())
        
    async def _translate_rapid(self, text: str, target_lang: str, source_lang: Optional[str] = None) -> str:
        """Translate using RapidAPI service"""
        url = "https://microsoft-translator-text.p.rapidapi.com/translate"
        
        try:
            headers = {
                "content-type": "application/json",
                "X-RapidAPI-Key": self.rapid_api_key,
                "X-RapidAPI-Host": "microsoft-translator-text.p.rapidapi.com"
            }
            
            params = {
                "api-version": "3.0",
                "to": target_lang
            }
            
            if source_lang:
                params["from"] = source_lang
                
            body = [{"text": text}]
                
            print(f"\nDebug Information:")
            print(f"URL: {url}")
            print(f"Headers: {json.dumps(headers, indent=2)}")
            print(f"Params: {json.dumps(params, indent=2)}")
            print(f"Payload: {json.dumps(payload, indent=2)}\n")
            
            if source_lang:
                params["from"] = source_lang
            
            print(f"Sending translation request to {url}")
            print(f"Headers: {headers}")
            print(f"Params: {params}")
            print(f"Payload: {payload}")
            
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.post(
                        url,
                        headers=headers,
                        json=body,
                        params=params,
                        timeout=30
                    ) as response:
                        response_text = await response.text()
                        print(f"\nAPI Response:")
                        print(f"Status Code: {response.status}")
                        print(f"Response Headers: {dict(response.headers)}")
                        print(f"Response Body: {response_text}\n")
                        
                        if response.status != 200:
                            print(f"Error response: {response_text}")
                            return ""
                            
                        try:
                            result = json.loads(response_text)
                            if isinstance(result, list) and len(result) > 0:
                                translations = result[0].get("translations", [])
                                if translations:
                                    return translations[0].get("text", "")
                        except Exception as e:
                            print(f"Error processing response: {str(e)}")
                            
                        return ""
                        else:
                            raise Exception(f"API Error: {response.status} - {response_text}")
                except aiohttp.ClientError as e:
                    print(f"Network error: {str(e)}")
                    raise
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {str(e)}")
                    raise
                except Exception as e:
                    print(f"Unexpected error: {str(e)}")
                    raise
                    
        except Exception as e:
            logger.error(f"RapidAPI translation error: {str(e)}")
            import traceback
            traceback.print_exc()
            raise

    async def _translate_huggingface(self, text: str, target_lang: str) -> str:
        """Translate using local Hugging Face model"""
        if not self.model or not self.tokenizer:
            raise ValueError("Hugging Face model not initialized")
            
        try:
            self.tokenizer.src_lang = target_lang
            encoded = self.tokenizer(text, return_tensors="pt")
            generated_tokens = self.model.generate(
                **encoded,
                forced_bos_token_id=self.tokenizer.get_lang_id(target_lang)
            )
            return self.tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)[0]
        except Exception as e:
            logger.error(f"Hugging Face translation error: {str(e)}")
            raise

    async def translate_text(self, text: str, target_lang: str = 'en', source_lang: Optional[str] = None) -> Dict[str, Any]:
        """
        Translate text using RapidAPI service
        Returns a dictionary containing:
        - translated_text: The translated text
        - success: Boolean indicating if translation was successful
        - error: Error message if translation failed
        - source_lang: Detected or provided source language
        - target_lang: Target language
        """
        if not text:
            return {
                "translated_text": "",
                "success": True,
                "error": None,
                "source_lang": source_lang or "auto",
                "target_lang": target_lang
            }
            
        target_lang = self.get_language_code(target_lang)
        if source_lang:
            source_lang = self.get_language_code(source_lang)
            
        try:
            @monitor.track_time('translation')
            async def _translate():
                return await self._translate_rapid(text, target_lang, source_lang)
                
            translated = await _translate()
            return {
                "translated_text": translated,
                "success": True,
                "error": None,
                "source_lang": source_lang or "auto",
                "target_lang": target_lang
            }
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Translation error: {error_msg}")
            return {
                "translated_text": text,
                "success": False,
                "error": error_msg,
                "source_lang": source_lang or "auto",
                "target_lang": target_lang
            }

# Initialize global translator instance
translator = Translator()