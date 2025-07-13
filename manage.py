import argparse
import logging
from database import clear_products, get_db_connection

logger = logging.getLogger(__name__)


def clear_db():
    """
    Clear all products from the database.
    Logs success or failure of the operation.
    """
    try:
        with get_db_connection() as conn:
            if conn:
                clear_products(conn)
                logger.info("Product table cleared successfully!")
            else:
                logger.error("Failed to connect to the database")
    except Exception as e:
        logger.error(f"Error while clearing database: {str(e)}")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Database management utility"
    )
    parser.add_argument(
        "command",
        help="Command to execute (available: clear_db)"
    )

    args = parser.parse_args()

    if args.command == "clear_db":
        clear_db()
    else:
        logger.error(f"Unknown command: {args.command}")