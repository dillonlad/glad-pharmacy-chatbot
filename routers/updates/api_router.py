from fastapi import APIRouter, Depends
from auth import verify_token
from wp_db_handler import DBHandler
from routers.updates.data_structures import ItemOut, OrderUpdateOut, UpdatesOut


router = APIRouter()


@router.get("/updates", response_model=UpdatesOut)
async def get_updates(user=Depends(verify_token)):
    db_handler = DBHandler()
    db_handler.start_session()
    on_hold_orders = db_handler.fetchall(
        """
        SELECT o.id, o.total_amount, o.transaction_id, addr.name, addr.address, addr.email
        FROM wp_wc_orders o 
        LEFT OUTER JOIN (
        SELECT a.order_id, concat(a.first_name, ' ', a.last_name) as `name`, concat(a.address_1, ' ', a.address_2, ' ', a.state, ' ', a.city, ' ', a.postcode) as `address`, a.email 
        from wp_wc_order_addresses a where a.address_type='shipping'
        ) as addr on o.id=addr.order_id
        where o.type='shop_order' and o.`status`='wc-on-hold' 
        order by o.date_created_gmt desc;
        """
    )
    orders_out = []
    for _order in on_hold_orders:
        items = db_handler.fetchall("""
                SELECT oi.order_item_name AS product_name,
                oim_qty.meta_value AS quantity, oim_sku.sku as product_sku
                FROM wp_woocommerce_order_items oi
                LEFT JOIN (
                    select b_meta.meta_value, b_meta.order_item_id, b_meta.meta_key, lookup.sku 
                    from wp_woocommerce_order_itemmeta b_meta
                    inner join wp_wc_product_meta_lookup lookup on b_meta.meta_value=lookup.product_id
                ) oim_sku 
                ON oi.order_item_id = oim_sku.order_item_id AND oim_sku.meta_key = '_product_id'
                LEFT JOIN wp_woocommerce_order_itemmeta oim_qty 
                ON oi.order_item_id = oim_qty.order_item_id AND oim_qty.meta_key = '_qty'
                WHERE oim_qty.meta_key = '_qty'AND oi.order_id = {};
            """.format(_order['id']))
        
        order_items = []
        for _item in items:
            _item_out = ItemOut(item_name=_item["product_name"], quantity=_item["quantity"], item_sku=_item["product_sku"])
            order_items.append(_item_out)
        order_update_out = OrderUpdateOut(
            id=_order["id"],
            amount_paid=_order["total_amount"],
            address=_order["address"],
            name=_order["name"],
            email=_order["email"],
            items=order_items
        )
        orders_out.append(order_update_out)
        
    return UpdatesOut(orders=orders_out)


# Example root endpoint
@router.get("/")
async def root():
    return {"message": "Hugging Face Model API is running!"}