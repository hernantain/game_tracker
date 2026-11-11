from fastapi import APIRouter, Depends

from ..deps import require_registered, UserContext, get_user_context
from ..schemas import OpponentOut
from ..services import opponents as svc

# Every route here requires a registered account, not merely a valid token.
router = APIRouter(
    prefix="/api/opponents",
    tags=["opponents"],
    dependencies=[Depends(require_registered)],
)


@router.get("", response_model=list[OpponentOut])
def list_opponents(ctx: UserContext = Depends(get_user_context)) -> list[OpponentOut]:
    """Record against each club the caller has seen their team face."""
    return [OpponentOut(**row) for row in svc.summarise(ctx.matches)]
