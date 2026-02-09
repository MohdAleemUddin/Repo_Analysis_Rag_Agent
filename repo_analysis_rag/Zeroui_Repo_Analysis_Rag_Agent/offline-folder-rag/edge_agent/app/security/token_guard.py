from fastapi import Header, HTTPException
from .token_store import get_or_create_token

async def verify_token(x_local_token: str = Header(None, alias="X-LOCAL-TOKEN")):
    valid_token = get_or_create_token()
    if not x_local_token or x_local_token != valid_token:
        raise HTTPException(
            status_code=401,
            detail="INVALID_TOKEN"
        )
    return x_local_token
