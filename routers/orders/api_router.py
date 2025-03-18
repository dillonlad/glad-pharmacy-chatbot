from fastapi import APIRouter, Depends
from auth import verify_token
from paypal_handler import PayPalHandler
from woocommerce_manager import WoocommerceManager
from wp_db_handler import DBHandler
from data_structures import OrderUpdateOut
from routers.orders.data_structures import MetricsOut

router = APIRouter(prefix="/orders")

@router.get("/metrics", response_model=MetricsOut)
async def get_metrics(user=Depends(verify_token)):
    """
    Get metrics for most popular items.
    """

    db_handler = user.db_handler
    wc_manager = WoocommerceManager(db_handler)
    return wc_manager.get_metrics()


@router.post("/cancel-order", response_model=dict[str, list[OrderUpdateOut]])
async def cancel_order(
    transaction_id: str,
    user=Depends(verify_token)
):
    """
    Cancel a specific paypal order.
    """
    
    db_handler = user.db_handler
    paypal_handler = PayPalHandler()
    paypal_handler.start_session()
    paypal_handler.void_auth(transaction_id)
    paypal_handler.close_session()

    wc_manager = WoocommerceManager(db_handler)
    order_updates = wc_manager.get_orders()

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
    
    db_handler = user.db_handler
    paypal_handler = PayPalHandler()
    paypal_handler.start_session()
    paypal_handler.capture_auth(transaction_id)
    paypal_handler.close_session()

    wc_manager = WoocommerceManager(db_handler)
    order_updates = wc_manager.get_orders()

    return {
        "orders": order_updates
    }