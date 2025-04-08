from fastapi import APIRouter, Depends
from routers.staff.members.data_structures import Member
from auth import verify_token

router = APIRouter()

@router.get("/", response_model=dict[str, list[Member]])
async def get_staff_members(
    user=Depends(verify_token)
):

    return {
        "members": user.get_colleagues()
    }