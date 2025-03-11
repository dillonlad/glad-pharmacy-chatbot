from wp_db_handler import DBHandler
from data_structures import ItemOut, OrderUpdateOut

class WoocommerceManager:

    def __init__(self, db_handler: DBHandler):
        self._db_handler = db_handler

    def get_metrics(self):
        """
        Get the most popular items from the last week.
        """

        items = self._db_handler.fetchall("""
                select oi.order_item_name, count(oi.order_item_id) AS `item_total`
                from wp_woocommerce_order_items oi
                inner join wp_wc_orders orders on oi.order_id=orders.id
                where oi.order_item_type='line_item'
                and datediff(current_date, orders.date_created_gmt) < 7
                group by oi.order_item_name;
                """
                )
        total_items = sum([_item["item_total"] for _item in items])
        return {
            "total": total_items,
            "popular": items,
        }

    def get_orders(self):
        """
        Get the individual orders awaiting response.
        """

        on_hold_orders = self._db_handler.fetchall(
            """
            SELECT o.id, o.total_amount, o.transaction_id, addr.name, addr.address, addr2.address as `address`, addr.email, o.date_created_gmt
            FROM wp_wc_orders o 
            LEFT OUTER JOIN (
            SELECT a1.order_id, concat(a1.first_name, ' ', a1.last_name) as `name`, concat(coalesce(a1.address_1, ''), ', ', coalesce(a1.address_2, ''), ', ', coalesce(a1.state, ''), ', ', coalesce(a1.city, ''), ', ', coalesce(a1.postcode, '')) as `address`, a1.email 
            from wp_wc_order_addresses a1 where a1.address_type='shipping'
            ) as addr on o.id=addr.order_id
            LEFT OUTER JOIN (
            SELECT a.order_id, concat(a.first_name, ' ', a.last_name) as `name`, concat(coalesce(a.address_1, ''), ', ', coalesce(a.address_2, ''), ', ', coalesce(a.state, ''), ', ', coalesce(a.city, ''), ', ', coalesce(a.postcode, '')) as `address`, a.email 
            from wp_wc_order_addresses a where a.address_type='billing'
            ) as addr2 on o.id=addr2.order_id
            where o.type='shop_order' and o.`status`='wc-on-hold' 
            order by o.date_created_gmt desc;
            """
        )
        orders_out = []
        for _order in on_hold_orders:
            items = self._db_handler.fetchall("""
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
                items=order_items,
                transaction_id=_order["transaction_id"],
                created=_order["date_created_gmt"]
            )
            orders_out.append(order_update_out)

        return orders_out