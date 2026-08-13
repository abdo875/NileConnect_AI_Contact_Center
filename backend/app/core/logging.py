import logging
import sys
from app.core.config import settings


def setup_logging() -> None:
    """Configure application-wide logging."""
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Reduce SQLAlchemy echo noise in production
    if not settings.DEBUG:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    logging.getLogger("uvicorn.access").setLevel(logging.INFO)


logger = logging.getLogger("nileconnect")
