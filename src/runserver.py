
from uvicorn import run

from src.logging_config import get_logger, setup_logging

if __name__ == "__main__":
    setup_logging()
    logger = get_logger("server")
    logger.info("Developer Server Started!")

    try:
        run(
            "main:app",
            host="0.0.0.0",
            port=9000,
            reload=True,
            log_level="debug",
            timeout_graceful_shutdown=5,
            timeout_keep_alive=5,
            ws_per_message_deflate=True,
        )
    except Exception as e:
        logger.critical(f"Server encountered an error: {e}", exc_info=True)
        raise
