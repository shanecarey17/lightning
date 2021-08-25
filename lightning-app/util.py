import logging
import os
import sys
import time

def setup():
    """
    Setup standard logging, doten, and uncaught exception behavior
    """
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    logging_level = logging.DEBUG if os.environ.get('DEBUG') else logging.INFO

    logging.basicConfig(
        stream=sys.stdout,
        level=logging_level,
        format='%(asctime)s %(levelname)s %(message)s',
    )

    def excepthook(exctype, exc, traceback):
        logging.exception(exc, exc_info=(exctype, exc, traceback))

    sys.excepthook = excepthook

