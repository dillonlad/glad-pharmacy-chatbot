from fastapi import APIRouter, Depends
from auth import verify_token
from paypal_handler import PayPalHandler
from woocommerce_manager import WoocommerceManager
from wp_db_handler import DBHandler
from data_structures import OrderUpdateOut

router = APIRouter(prefix="/orders")

@router.post("/cancel-order", response_model=dict[str, list[OrderUpdateOut]])
async def cancel_order(
    transaction_id: str,
    user=Depends(verify_token)
):
    """
    Cancel a specific paypal order.
    """
    
    paypal_handler = PayPalHandler()
    paypal_handler.start_session()
    paypal_handler.void_auth(transaction_id)
    paypal_handler.close_session()

    db_handler = DBHandler()
    db_handler.start_session()
    wc_manager = WoocommerceManager(db_handler)
    order_updates = wc_manager.get_orders()
    db_handler.end_session()

    return {
        "orders": order_updates
    }

@router.post("/complete-order", response_model=dict[str, list[OrderUpdateOut]])
async def cancel_order(
    transaction_id: str,
    user=Depends(verify_token)
):
    """
    Completes a specific paypal order.
    """
    
    paypal_handler = PayPalHandler()
    paypal_handler.start_session()
    paypal_handler.capture_auth(transaction_id)
    paypal_handler.close_session()

    db_handler = DBHandler()
    db_handler.start_session()
    wc_manager = WoocommerceManager(db_handler)
    order_updates = wc_manager.get_orders()
    db_handler.end_session()

    return {
        "orders": order_updates
    }