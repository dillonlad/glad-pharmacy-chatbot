from fastapi import APIRouter, Depends
from datetime import datetime
from pytz import utc
import json

from wp_db_handler import DBHandler
from auth import verify_token
from s3_client import S3Client
from routers.forms.data_structures import FormEntryOut, FormType

router = APIRouter(prefix="/forms")

def get_forms(db_handler: DBHandler, form_type: str):

    # Get latest form entried from website
    current_timestamp = int(datetime.now(tz=utc).timestamp())
    sql = """
            SELECT `entries`.id, `entries`.form_name, `entries`.file_path, `entries`.metadata, `urls`.presigned_url, `urls`.expiry
            FROM wp_form_entries `entries`
            LEFT OUTER JOIN form_entry_presigned_urls `urls` ON `entries`.id=`urls`.form_entry_id
            WHERE `entries`.viewed=0 AND `entries`.form_name='{}';
          """.format(form_type.value)
    form_entries = db_handler.fetchall(sql)
    s3_client = S3Client()
    form_entry_updates = []
    commit = False
    for _form_entry in form_entries:
        form_entry_update = _form_entry
        if _form_entry["presigned_url"]  is not None:
            if current_timestamp < _form_entry["expiry"]:
                form_entry_update["presigned_url"] = _form_entry["presigned_url"]
            else:
                presigned_url = s3_client.get_form_presigned_url(_form_entry["file_path"])
                form_entry_update["presigned_url"] = presigned_url
                update_sql = "UPDATE form_entry_presigned_urls set presigned_url='%s' where form_entry_id=%s" % (presigned_url, _form_entry["id"],)
                db_handler.execute(update_sql)
                commit = True
        else:
            presigned_url = s3_client.get_form_presigned_url(_form_entry["file_path"])
            form_entry_update["presigned_url"] = presigned_url
            url_expiry = current_timestamp + s3_client.presigned_url_expiry
            insert_sql = "INSERT INTO  form_entry_presigned_urls (form_entry_id, presigned_url, expiry) values (%s, '%s', %s)" % (_form_entry["id"], presigned_url, url_expiry,)
            db_handler.execute(insert_sql)
            commit = True

        form_entry_update["metadata"] = json.loads(form_entry_update["metadata"]) if form_entry_update["metadata"] is not None else None
        form_entry_updates.append(form_entry_update)

    if commit is True:
        db_handler.commit()

    return form_entry_updates


@router.get("/{form_type}/updates", response_model=dict[str, list[FormEntryOut]])
async def get_form_updates(
    form_type: FormType, 
    db_handler=Depends(verify_token),
):
    """
    Get the latest unread forms.
    """

    form_entry_updates = get_forms(db_handler, form_type)

    return {
        "forms": form_entry_updates
    }

@router.post("/{form_type}/mark-read")
async def mark_form_read(
    form_type: FormType,
    form_id: int,
    db_handler=Depends(verify_token),
):
    """
    Mark a form as 'read' so it's no longer an update.
    """
    
    form_entry_updates = get_forms(db_handler, form_type)

    db_handler.execute("UPDATE wp_form_entries set viewed=1 where id = %s" % (form_id,))
    db_handler.commit()

    form_entry_updates = [_entry for _entry in form_entry_updates if _entry["id"] != form_id]

    return {
        "forms": form_entry_updates
    }