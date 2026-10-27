import json
import boto3
import os
import pymysql
from db_client import get_db_connection
import traceback

dynamodb = boto3.resource('dynamodb', region_name='eu-west-2')
TABLE_NAME = os.environ.get('UPDATES_TABLE_NAME')
table = dynamodb.Table(TABLE_NAME)

def get_forms(cursor):
    cursor.execute("""
        SELECT `form_name`, COUNT(`id`) AS `unread_entries`
        FROM wp_form_entries
        WHERE `viewed`=0
        GROUP BY `form_name`;
        """)
    unread_forms = cursor.fetchall() # Fixed typo fetcall -> fetchall
    repeats = next((_form_count["unread_entries"] for _form_count in unread_forms if _form_count["form_name"] == "repeat-prescription-sign-up"), 0)
    contact_forms = next((_form_count["unread_entries"] for _form_count in unread_forms if _form_count["form_name"] == "contact-form"), 0)
    return repeats, contact_forms
        

def get_total_unread_voicemails(cursor):
    cursor.execute("""SELECT COUNT(id) as `count` from `voicemails` where `read`=0""")
    result = cursor.fetchone()
    return result["count"] if result else 0

def get_unread_conversations(cursor):
    """
    Get the number of unread messages. (For the number shows above WhatsApp icon)
    """
    cursor.execute("SELECT COUNT(id) AS unread_messages FROM conversations where `read`=0")
    result = cursor.fetchone()
    return result["unread_messages"] if result else 0

def get_orders(cursor):
    """
    Get the individual orders awaiting response.
    """
    cursor.execute(
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
    on_hold_orders = cursor.fetchall()
    orders_out = []
    for _order in on_hold_orders:
        cursor.execute("""
                SELECT oi.order_item_name AS product_name,
                oim_qty.meta_value AS quantity, oim_sku.sku as product_sku, oim_sku.meta_value AS product_id
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
        items = cursor.fetchall()
        order_items = []
        for _item in items:
            _item_out = dict(
                item_name=_item["product_name"], 
                quantity=_item["quantity"], 
                item_sku=_item["product_sku"],
                item_product_id=_item["product_id"],
                )
            order_items.append(_item_out)

        order_update_out = dict(
            id=str(_order["id"]),
            amount_paid=str(_order["total_amount"]),
            address=_order["address"],
            name=_order["name"],
            email=_order["email"],
            items=order_items,
            transaction_id=_order["transaction_id"],
            created=str(_order["date_created_gmt"])
        )
        orders_out.append(order_update_out)

    return orders_out


def lambda_handler(event, context):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # Get latest updates from MySQL
            orders = get_orders(cursor)
            unread_conversations = get_unread_conversations(cursor)
            voicemails = get_total_unread_voicemails(cursor)
            repeats, contact_forms = get_forms(cursor)
            
            metadata = {
                "updates": "current_updates",  # Partition key for the item
                "orders": orders, 
                "unread_whatsapps": unread_conversations, 
                "repeats": repeats,
                "contact_forms": contact_forms,
                "unread_voicemails": voicemails,
            }
            
            # Save/Overwrite the metadata item in DynamoDB
            table.put_item(Item=metadata)
                
        return {"statusCode": 200, "body": json.dumps({"message": "Updates stored successfully"})}

    except Exception as e:
        print(traceback.format_exc())
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}