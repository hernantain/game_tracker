from fastapi import APIRouter

from ..services import capabilities as svc

router = APIRouter(prefix="/api/capabilities", tags=["capabilities"])


@router.get("")
def read_capabilities() -> dict:
    """Which datasets the SQL schema can answer.

    Unauthenticated on purpose: the frontend needs it to decide what to render
    before, and independently of, who is signed in.
    """
    return svc.capabilities()
