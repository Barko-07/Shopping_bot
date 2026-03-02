import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
import sys

from config import config
from bot.handlers import user, cart, admin
from database.session import init_db, close_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log')
    ]
)
logger = logging.getLogger(__name__)

async def on_startup(bot: Bot) -> None:
    """Initialize bot on startup"""
    logger.info("Starting bot...")
    
    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized successfully")
        
        # Set bot commands
        from aiogram.types import BotCommand
        commands = [
            BotCommand(command="start", description="Start the bot"),
            BotCommand(command="admin", description="Admin panel"),
            BotCommand(command="language", description="Change language"),
            BotCommand(command="help", description="Get help")
        ]
        await bot.set_my_commands(commands)
        logger.info("Bot commands set successfully")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise

async def on_shutdown(bot: Bot) -> None:
    """Cleanup on shutdown"""
    logger.info("Shutting down bot...")
    
    try:
        # Close database connection
        await close_db()
        logger.info("Database connection closed")
        
        # Close bot session
        await bot.session.close()
        logger.info("Bot session closed")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

async def main() -> None:
    """Main bot function"""
    bot = None
    dp = None
    
    try:
        # Initialize bot and dispatcher
        bot = Bot(
            token=config.BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        dp = Dispatcher(storage=MemoryStorage())
        
        # Register routers - ORDER IS IMPORTANT!
        dp.include_router(admin.router)  # Admin routers first (more specific)
        dp.include_router(cart.router)    # Cart routers second
        dp.include_router(user.router)    # User routers last (includes catch-all)
        
        logger.info(f"Routers registered: admin, cart, user")
        
        # Register startup/shutdown handlers
        dp.startup.register(on_startup)
        dp.shutdown.register(on_shutdown)
        
        logger.info(f"Bot started!")
        
        # Start polling
        await dp.start_polling(
            bot,
            allowed_updates=["message", "callback_query", "my_chat_member"],
            handle_signals=True,
            close_bot_session=True
        )
        
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        raise
    finally:
        if bot:
            await bot.session.close()
            logger.info("Bot session closed in finally block")

def start_bot():
    """Start bot function for external calls"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_bot()