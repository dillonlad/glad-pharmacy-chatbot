from typing import Union
from fastapi import APIRouter, Depends, HTTPException
from cognito_user import EditableAttribute
from routers.staff.members.data_structures import MembersOut
from auth import verify_token

router = APIRouter()

@router.get("/", response_model=MembersOut)
async def get_staff_members(
    add_calendar: bool = False,
    user=Depends(verify_token)
):

    return {
        "is_admin": user.is_admin,
        "members": user.get_colleagues(add_calendar)
    }

@router.put("/", response_model=MembersOut)
async def edit_staff_member(
    username: str,
    params: dict[EditableAttribute, Union[int, float, str]],
    user=Depends(verify_token)
):
    
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorised.")
    
    updated_attributes = {
        attr.value: attr_value
        for attr, attr_value in params.items()
        if attr_value not in [None, ""]
    }
    formatted_attrs = [{"Name": f"custom:{k}" if k not in ["name", "sub", "email"] else k, "Value": v} for k, v in updated_attributes.items()]

    user.cognito_client.update_user_attributes(
        username=username,
        new_attrs=formatted_attrs
    )

    return {
        "is_admin": user.is_admin,
        "members": user.get_colleagues(True)
    }