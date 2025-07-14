import argparse
import logging
import subprocess

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
    subparsers = parser.add_subparsers(dest='command', required=True)

    parser_clear = subparsers.add_parser('clear_db', help='Clear the database')

    parser_search = subparsers.add_parser('search', help='Search products')
    parser_search.add_argument('query', nargs='+', help='Search query')

    args = parser.parse_args()

    if args.command == "clear_db":
        clear_db()
    elif args.command == "search":
        quantity = args.query[0]
        search_query = ' '.join(args.query[1:])
        subprocess.run(["python", "main.py", quantity, search_query])