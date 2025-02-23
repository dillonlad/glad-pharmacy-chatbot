from fastapi import APIRouter, Depends
from auth import verify_token
from wp_db_handler import DBHandler
from woocommerce_manager import WoocommerceManager
from routers.updates.data_structures import UpdatesOut


router = APIRouter()


@router.get("/updates", response_model=UpdatesOut)
async def get_updates(user=Depends(verify_token)):
    """
    Get all updates.
    """

    db_handler: DBHandler = DBHandler()
    db_handler.start_session()
    wc_manager = WoocommerceManager(db_handler)
    orders_out = wc_manager.get_orders()
    db_handler.end_session()
        
    return UpdatesOut(orders=orders_out)


# Example root endpoint
@router.get("/")
async def root():
    return {"message": "Hugging Face Model API is running!"}