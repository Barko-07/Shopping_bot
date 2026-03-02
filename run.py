#!/usr/bin/env python3
"""
Telegram Shopping Bot - Main Runner
Run this file to start both the bot and API server
"""
import asyncio
import multiprocessing
import logging
from bot.main import main as bot_main
from api.main import start as api_start

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_bot():
    """Run the Telegram bot"""
    asyncio.run(bot_main())

def run_api():
    """Run the FastAPI server"""
    api_start()

if __name__ == "__main__":
    logger.info("Starting Telegram Shopping Bot...")
    
    # Create processes for bot and API
    bot_process = multiprocessing.Process(target=run_bot)
    api_process = multiprocessing.Process(target=run_api)
    
    try:
        # Start both processes
        bot_process.start()
        api_process.start()
        
        logger.info("Bot and API server are running!")
        logger.info("Press Ctrl+C to stop")
        
        # Wait for processes to complete
        bot_process.join()
        api_process.join()
        
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        bot_process.terminate()
        api_process.terminate()
        bot_process.join()
        api_process.join()
        logger.info("Shutdown complete")