import logging
from uvicorn import run

from src.logging_config import setup_logging

if __name__ == "__main__":
    import main

    setup_logging()
    logger = logging.getLogger("backend_logger_server")
    logger.info("Developer Server Started!")

    app = main.app

    run("main:app", host="0.0.0.0", port=9000, reload=True)
