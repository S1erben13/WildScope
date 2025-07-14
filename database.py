import logging
import os
from contextlib import contextmanager
from decimal import Decimal
from typing import Any

import psycopg2
from dotenv import load_dotenv
from psycopg2 import OperationalError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_env_vars() -> dict[str, str]:
    """Load environment variables from .env file."""
    load_dotenv()
    return {
        "dbname": os.getenv("POSTGRES_DB"),
        "user": os.getenv("POSTGRES_USER"),
        "password": os.getenv("POSTGRES_PASSWORD"),
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": os.getenv("POSTGRES_PORT", "5432"),
    }


def create_tables(conn: Any) -> None:
    """Create required tables in the database."""
    tables = {
        "Product": """
            CREATE TABLE IF NOT EXISTS Product (
            wb_id BIGINT PRIMARY KEY,
            product_name TEXT NOT NULL,
            price DECIMAL(10, 2) NOT NULL,
            discount_price DECIMAL(10, 2) NOT NULL,
            rating DECIMAL(2, 1) NOT NULL,
            feedbacks INTEGER NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """
    }

    try:
        with conn.cursor() as cursor:
            for table_name, create_query in tables.items():
                cursor.execute(create_query)
                logger.info(f"Table '{table_name}' created or already exists")
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating tables: {e}")
        raise


def add_product(
    conn: Any,
    wb_id: int,
    product_name: str,
    price: float,          # или сразу Decimal, если возможно
    discount_price: float, # поменяйте int на float (или Decimal)
    rating: float,         # или Decimal
    feedbacks: int,
) -> bool:
    """Add new product to database or update if exists."""
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO Product (
                    wb_id,
                    product_name,
                    price,
                    discount_price,
                    rating,
                    feedbacks
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (wb_id) DO UPDATE SET
                    product_name = EXCLUDED.product_name,
                    price = EXCLUDED.price,
                    discount_price = EXCLUDED.discount_price,
                    rating = EXCLUDED.rating,
                    feedbacks = EXCLUDED.feedbacks;
                """,
                (
                    wb_id,
                    product_name,
                    Decimal(str(price)),          # Явное преобразование float → Decimal
                    Decimal(str(discount_price)), # И для discount_price тоже
                    Decimal(str(rating)),         # Чтобы рейтинг не округлялся
                    feedbacks
                ),
            )
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        conn.rollback()
        logger.error(f"Error adding product: {e}")
        raise

def clear_products(conn: Any) -> bool:
    """Clear all records from Product table."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM Product;")
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        conn.rollback()
        logger.error(f"Error clearing products: {e}")
        raise


def get_products(
    conn: Any,
    min_price: int | None = None,
    max_price: int | None = None,
    exact_price: int | None = None,
    min_rating: float | None = None,
    max_rating: float | None = None,
    exact_rating: float | None = None,
    min_feedbacks: int | None = None,
    max_feedbacks: int | None = None,
    exact_feedbacks: int | None = None,
) -> list[dict]:
    """Get filtered products from the database with flexible filtering options."""
    if conn is None:
        raise ValueError("Database connection is not established")
    try:
        with conn.cursor() as cursor:
            query = "SELECT * FROM Product WHERE 1=1"
            params = []

            filters = [
                ("price", exact_price, min_price, max_price),
                ("rating", exact_rating, min_rating, max_rating),
                ("feedbacks", exact_feedbacks, min_feedbacks, max_feedbacks),
            ]

            for field, exact, min_val, max_val in filters:
                if exact is not None:
                    query += " AND {} = %s".format(field)
                    params.append(exact)
                else:
                    if min_val is not None:
                        query += " AND {} >= %s".format(field)
                        params.append(min_val)
                    if max_val is not None:
                        query += " AND {} <= %s".format(field)
                        params.append(max_val)

            cursor.execute(query, params)
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    except Exception as e:
        logger.error(f"Error reading products: {e}")
        raise


@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = None
    try:
        conn = psycopg2.connect(
            dbname=db_config["dbname"],
            user=db_config["user"],
            password=db_config["password"],
            host=db_config["host"],
            port=db_config["port"],
        )
        yield conn
    except OperationalError as e:
        logger.error(f"Database connection error: {e}")
        raise
    finally:
        if conn:
            conn.close()


db_config = load_env_vars()


def main() -> None:
    """Main function to initialize database tables."""
    try:
        with get_db_connection() as conn:
            create_tables(conn)
    except Exception as e:
        logger.error(f"Initialization error: {e}")


if __name__ == "__main__":
    main()