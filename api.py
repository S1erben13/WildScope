import logging
import os
from typing import Optional
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Body
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from database import db_config, get_db_connection, get_products

app = FastAPI()
logger = logging.getLogger(__name__)


@app.get("/api/products/")
async def read_products(
        min_price: Optional[int] = Query(None, description="Minimum price"),
        max_price: Optional[int] = Query(None, description="Maximum price"),
        exact_price: Optional[int] = Query(None, description="Exact price"),
        min_rating: Optional[float] = Query(
            None, description="Minimum rating", ge=0, le=5
        ),
        max_rating: Optional[float] = Query(
            None, description="Maximum rating", ge=0, le=5
        ),
        exact_rating: Optional[float] = Query(
            None, description="Exact rating", ge=0, le=5
        ),
        min_feedbacks: Optional[int] = Query(
            None, description="Minimum number of feedbacks", ge=0
        ),
        max_feedbacks: Optional[int] = Query(
            None, description="Maximum number of feedbacks", ge=0
        ),
        exact_feedbacks: Optional[int] = Query(
            None, description="Exact number of feedbacks", ge=0
        ),
):
    """
    Get list of products with advanced filtering options:
    - Price filters:
        * min_price: Minimum price
        * max_price: Maximum price
        * exact_price: Exact price match
    - Rating filters:
        * min_rating: Minimum rating (0-5)
        * max_rating: Maximum rating (0-5)
        * exact_rating: Exact rating match
    - Feedback filters:
        * min_feedbacks: Minimum number of feedbacks
        * max_feedbacks: Maximum number of feedbacks
        * exact_feedbacks: Exact number of feedbacks
    """

    try:
        with get_db_connection() as conn:
            logger.info(
                f"Fetching products with filters: "
                f"min_price={min_price}, max_price={max_price}, exact_price={exact_price}, "
                f"min_rating={min_rating}, max_rating={max_rating}, exact_rating={exact_rating}, "
                f"min_feedbacks={min_feedbacks}, max_feedbacks={max_feedbacks}, exact_feedbacks={exact_feedbacks}"
            )

            products = get_products(
                conn,
                min_price=min_price,
                max_price=max_price,
                exact_price=exact_price,
                min_rating=min_rating,
                max_rating=max_rating,
                exact_rating=exact_rating,
                min_feedbacks=min_feedbacks,
                max_feedbacks=max_feedbacks,
                exact_feedbacks=exact_feedbacks,
            )
            return {"products": products}
    except Exception as e:
        logger.error(f"Error fetching products: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/products/")
async def fill_db(
        body_query: Optional[str] = Body(None, alias="query",
                                         description="Searching query Wildberries"),
        quantity: Optional[int] = Body(None, alias="quantity",
                                         description="Quantity of products")
):
    search_query = body_query
    logging.info(f'API search_query: "{search_query}"')
    logging.info(f'API quantity: "{quantity}"')
    if not search_query:
        return {"error": "Query parameter is required"}

    command = f"python manage.py search {quantity} {search_query}"
    os.system(command)

    return {"query": "success"}
