import sys
import os
import logging
import traceback
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import asyncio
from functools import wraps
import json
import time

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configure environment
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUNBUFFERED'] = '1'

# Initialize Flask app
app = Flask(__name__, 
    template_folder='web_interface/templates',
    static_folder='web_interface/static')

# Configure CORS
CORS(app)

# Import core modules
logger.info("Starting import process...")

from core.monitoring import monitor

try:
    from core.translation import translator
    logger.info("Translation module loaded")
except Exception as e:
    logger.error(f"Error loading translation module: {str(e)}")
    translator = None
    
try:
    from core.chat_engine import chat_processor
    logger.info("Chat engine module loaded")
except Exception as e:
    logger.error(f"Error loading chat engine module: {str(e)}")
    chat_processor = None
    
try:
    from core.analysis import sentiment_analyzer
    logger.info("Sentiment analyzer module loaded")
except Exception as e:
    logger.error(f"Error loading sentiment analyzer module: {str(e)}")
    sentiment_analyzer = None

logger.info("All imports completed")

@app.route('/metrics', methods=['GET'])
def get_metrics():
    """Get performance metrics for all services"""
    try:
        metrics = monitor.get_metrics()
        return jsonify(metrics)
    except Exception as e:
        logger.error(f"Error getting metrics: {str(e)}")
        return jsonify({'error': 'Failed to retrieve metrics'}), 500

@app.route('/')
def home():
    """Serve the main application page"""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
async def analyze():
    """Handle analysis requests"""
    start_time = time.time()
    logger.info("Received /analyze request")
    
    try:
        data = request.get_json()
        logger.debug(f"Request data: {data}")
        
        if not data:
            logger.warning("No JSON data in request")
            return jsonify({'error': 'No data provided'}), 400
            
        text = data.get('text', '')
        if not text:
            return jsonify({'error': 'No text provided'}), 400
            
        source_lang = data.get('source_lang', 'en')
        target_lang = data.get('target_lang', 'hi')
        
        logger.info(f"Processing request: text='{text}', source_lang='{source_lang}', target_lang='{target_lang}'")
        
        # Process all services concurrently
        try:
            # Create tasks for all services
            @monitor.track_time('translation')
            async def run_translation():
                if not translator:
                    return {'text': text, 'success': False, 'error': 'Translation service not available'}
                try:
                    return await translator.translate_text(
                        text=text,
                        target_lang=target_lang,
                        source_lang=source_lang
                    )
                except Exception as e:
                    logger.error(f"Translation error: {str(e)}")
                    return {'text': text, 'success': False, 'error': str(e)}
                    
            translation_task = run_translation()
            
            @monitor.track_time('sentiment')
            async def run_sentiment():
                if not sentiment_analyzer:
                    return {'sentiment': 'NEUTRAL', 'score': 0.5, 'error': 'Sentiment analysis not available'}
                try:
                    return await sentiment_analyzer.analyze_async(text)
                except Exception as e:
                    logger.error(f"Sentiment analysis error: {str(e)}")
                    return {'sentiment': 'NEUTRAL', 'score': 0.5, 'error': str(e)}
            
            sentiment_task = run_sentiment()
            
            @monitor.track_time('chat')
            async def run_chat():
                if not chat_processor:
                    return {'response': 'Chat service not available', 'success': False, 'error': 'Chat service not loaded'}
                try:
                    return await chat_processor.process_async(text)
                except Exception as e:
                    logger.error(f"Chat processing error: {str(e)}")
                    return {'response': "I apologize, but I'm having trouble processing your request.", 'success': False, 'error': str(e)}
            
            chat_task = run_chat()
            
            # Wait for all tasks to complete
            translation_result, sentiment_result, chat_result = await asyncio.gather(
                translation_task,
                sentiment_task,
                chat_task
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            response_data = {
                'translation': translation_result,
                'sentiment': sentiment_result,
                'chat': chat_result,
                'performance': {
                    'total_time': f"{processing_time:.2f}s",
                    'metrics': monitor.get_metrics()
                }
            }
            
            logger.info(f"Request processed successfully in {processing_time:.2f}s")
            logger.debug(f"Response data: {response_data}")
            
            return jsonify(response_data)
            
        except Exception as e:
            logger.error(f"Error in concurrent processing: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({
                'error': 'Error processing request',
                'details': str(e),
                'service_status': {
                    'translation': bool(translator),
                    'sentiment': bool(sentiment_analyzer),
                    'chat': bool(chat_processor)
                }
            }), 500
            
    except Exception as e:
        logger.error(f"Error handling request: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': 'An error occurred while processing your request',
            'details': str(e)
        }), 500

if __name__ == '__main__':
    try:
        port = int(os.getenv('PORT', 8080))
        host = os.getenv('HOST', '127.0.0.1')
        debug = os.getenv('FLASK_DEBUG', '1') == '1'
        
        logger.info(f"Starting server on {host}:{port} (debug={debug})")
        logger.info(f"Access the application at: http://{host}:{port}")
        
        app.run(
            host=host,
            port=port,
            debug=debug,
            use_reloader=False
        )
    except Exception as e:
        logger.error(f"Error starting server: {str(e)}")
        logger.error(traceback.format_exc())