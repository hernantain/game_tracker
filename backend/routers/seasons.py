from fastapi import APIRouter, Depends

from ..deps import require_registered, UserContext, get_user_context

# Every route here requires a registered account, not merely a valid token.
router = APIRouter(
    prefix="/api/seasons",
    tags=["seasons"],
    dependencies=[Depends(require_registered)],
)


@router.get("", response_model=list[int])
def list_seasons(ctx: UserContext = Depends(get_user_context)) -> list[int]:
    """Calendar years the caller has attended a game in, newest first."""
    return sorted({m.date.year for m in ctx.matches}, reverse=True)
