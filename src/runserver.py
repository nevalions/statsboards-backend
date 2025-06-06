import logging
from uvicorn import run
from src.logging_config import setup_logging

if __name__ == "__main__":
    setup_logging()
    logger = logging.getLogger("backend_logger_server")
    logger.info("Developer Server Started!")

    try:
        run("main:app", host="0.0.0.0", port=9000, reload=True, log_level="debug")
    except Exception as e:
        logger.critical(f"Server encountered an error: {e}", exc_info=True)
        raise
