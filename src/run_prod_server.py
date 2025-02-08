import logging
from gunicorn.app.base import BaseApplication

from src.logging_config import setup_logging


class Application(BaseApplication):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()
        logger.info("Application class initialized with options: %s", options)

    def load_config(self):
        config = {
            key: value
            for key, value in self.options.items()
            if key in self.cfg.settings and value is not None
        }
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


if __name__ == "__main__":
    import main

    setup_logging()
    logger = logging.getLogger("backend_logger_server")
    logger.info("Production Server Started!")

    options = {
        "bind": "0.0.0.0:9000",
        "workers": 4,
        "worker_class": "uvicorn.workers.UvicornWorker",
        "timeout": 120,
        "loglevel": "debug",
        "errorlog": "-",
        "accesslog": "-",
        # Add SSL configuration
        "keyfile": "/etc/letsencrypt/live/butakov.su/privkey.pem",
        "certfile": "/etc/letsencrypt/live/butakov.su/fullchain.pem",
        "ssl": True,
    }

    try:
        Application(main.app, options).run()
    except Exception as e:
        logger.critical(f"Server encountered an error: {e}", exc_info=True)
        raise
