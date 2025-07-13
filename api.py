import logging
from typing import Optional
from fastapi import Depends, FastAPI, HTTPException, Query

from database import db_config, get_db_connection, get_products

app = FastAPI()
logger = logging.getLogger(__name__)


@app.get("/api/products/")
async def read_products(
    min_price: Optional[int] = Query(None, description="Minimum price"),
    max_price: Optional[int] = Query(None, description="Maximum price"),
    min_rating: Optional[float] = Query(
        None, description="Minimum rating", ge=0, le=5
    ),
    min_feedbacks: Optional[int] = Query(
        None, description="Minimum number of feedbacks"
    ),
    conn=Depends(get_db_connection),
):
    """
    Get list of products with filtering options:
    - by price range (min_price/max_price)
    - by minimum rating (min_rating)
    - by minimum number of feedbacks (min_feedbacks)
    """
    try:
        logger.info(
            f"Fetching products with filters: min_price={min_price}, "
            f"max_price={max_price}, min_rating={min_rating}, "
            f"min_feedbacks={min_feedbacks}"
        )
        products = get_products(
            conn,
            min_price=min_price,
            max_price=max_price,
            min_rating=min_rating,
            min_feedbacks=min_feedbacks,
        )
        return {"products": products}
    except Exception as e:
        logger.error(f"Error fetching products: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")