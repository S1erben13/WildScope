import logging
import sys
from urllib.parse import quote

import requests
from database import add_product, get_db_connection, get_products

logger = logging.getLogger(__name__)


def fetch_wildberries_products(search_query: str, limit=10) -> list:
    """
    Fetch products from Wildberries API for given search query.

    Args:
        search_query: Search term to query Wildberries
        :param limit:

    Returns:
        List of product dictionaries

    Raises:
        requests.exceptions.RequestException: If API request fails
        ValueError: If response parsing fails
    """
    url = "https://search.wb.ru/exactmatch/ru/common/v4/search"
    params = {
        "query": search_query,
        "resultset": "catalog",
        # "sort": "newest", #pricedown #priceup
        "dest": -1257786,
        "regions": "80,64,38,4,115,83,33,68,70,69,30,86,75,40,1,66,48,110,31,22,71,114",
        "limit": limit,
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    return data.get("data", {}).get("products", [])


def process_products(products: list) -> int:
    """
    Process and store products in database.

    Args:
        products: List of product dictionaries from API

    Returns:
        Number of successfully added products

    Raises:
        Exception: If database operation fails
    """
    added_count = 0
    with get_db_connection() as conn:
        if not conn:
            logger.error("Database connection failed")
            return 0

        for product in products:
            product_name = product.get("name", "")
            if isinstance(product_name, str):
                product_name = product_name.encode("utf-8", errors="replace").decode("utf-8")

            success = add_product(
                conn=conn,
                wb_id=product.get("id"),
                product_name=product_name,
                price=product.get("priceU", 0) // 100,
                discount_price=product.get("salePriceU", 0) // 100,
                rating=product.get("reviewRating", 0),
                feedbacks=product.get("feedbacks", 0),
            )
            if success:
                added_count += 1

        return added_count


def display_sample_products(conn):
    """Display sample products from database for verification."""
    logger.info("\nAll products in DB (sample):")
    all_products = get_products(conn)
    for p in all_products[:5]:
        logger.info(f"{p['wb_id']}: {p['product_name']} - {p['price']} rub")

    logger.info("\nProducts over 5000 rub:")
    expensive = get_products(conn, min_price=5000)
    for p in expensive[:5]:
        logger.info(f"{p['product_name']} - {p['price']} rub")

    logger.info("\nProducts with rating 4+:")
    top_rated = get_products(conn, min_rating=4)
    for p in top_rated[:5]:
        logger.info(f"{p['product_name']} - rating {p['rating']}")


def main():
    """Main function to execute the product fetching and processing."""
    try:
        all_args = sys.argv[2:]
        quantity = int(sys.argv[1])
        search_query = ' '.join(all_args)
        logging.info(f'main.py search_query: "{search_query}"')
        logging.info(f'main.py quantity: "{quantity}"')
        logger.info(f"\nSearching products for query: {search_query}")

        products = fetch_wildberries_products(search_query, quantity)

        logger.info(f"\nFound products: {len(products)}")

        with get_db_connection() as conn:
            if conn:
                added_count = process_products(products)
                logger.info(f"Added to DB: {added_count} products")
                # display_sample_products(conn)
            else:
                logger.error("Database connection error")

    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {e}")
    except ValueError as e:
        logger.error(f"JSON parsing error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()