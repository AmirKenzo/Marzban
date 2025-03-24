from datetime import datetime as dt

from fastapi import APIRouter, Depends, Query

from app.db import AsyncSession, get_db
from .authentication import check_sudo_admin, get_current
from app.models.admin import Admin
from app.models.user import (
    UserCreate,
    UserModify,
    UserResponse,
    UsersResponse,
    UserStatus,
    UsersUsagesResponse,
    UserUsagesResponse,
    RemoveUsersResponse,
)
from app.utils import responses
from app.operation import OperatorType
from app.operation.user import UserOperator
from app.operation.node import NodeOperator


user_operator = UserOperator(operator_type=OperatorType.API)
node_operator = NodeOperator(operator_type=OperatorType.API)
router = APIRouter(tags=["User"], prefix="/api/user", responses={401: responses._401})


@router.post("", response_model=UserResponse, responses={400: responses._400, 409: responses._409})
async def add_user(new_user: UserCreate, db: AsyncSession = Depends(get_db), admin: Admin = Depends(get_current)):
    """
    Add a new user

    - **username**: 3 to 32 characters, can include a-z, 0-9, and underscores.
    - **status**: User's status, defaults to `active`. Special rules if `on_hold`.
    - **expire**: UTC datetime for account expiration. Use `0` for unlimited.
    - **data_limit**: Max data usage in bytes (e.g., `1073741824` for 1GB). `0` means unlimited.
    - **data_limit_reset_strategy**: Defines how/if data limit resets. `no_reset` means it never resets.
    - **proxy_settings**: Dictionary of protocol settings (e.g., `vmess`, `vless`) will generate data for all protocol by default.
    - **group_ids**: List of group IDs to assign to the user.
    - **note**: Optional text field for additional user information or notes.
    - **on_hold_timeout**: UTC timestamp when `on_hold` status should start or end.
    - **on_hold_expire_duration**: Duration (in seconds) for how long the user should stay in `on_hold` status.
    - **next_plan**: Next user plan (resets after use).
    """

    return await user_operator.add_user(db, new_user=new_user, admin=admin)


@router.put(
    "/{username}",
    response_model=UserResponse,
    responses={400: responses._400, 403: responses._403, 404: responses._404},
)
async def modify_user(
    username: str, modified_user: UserModify, db: AsyncSession = Depends(get_db), admin: Admin = Depends(get_current)
):
    """
    Modify an existing user

    - **username**: Cannot be changed. Used to identify the user.
    - **status**: User's new status. Can be 'active', 'disabled', 'on_hold', 'limited', or 'expired'.
    - **expire**: UTC datetime for new account expiration. Set to `0` for unlimited, `null` for no change.
    - **data_limit**: New max data usage in bytes (e.g., `1073741824` for 1GB). Set to `0` for unlimited, `null` for no change.
    - **data_limit_reset_strategy**: New strategy for data limit reset. Options include 'daily', 'weekly', 'monthly', or 'no_reset'.
    - **proxies**: Dictionary of new protocol settings (e.g., `vmess`, `vless`). Empty dictionary means no change.
    - **group_ids**: List of new group IDs to assign to the user. Empty list means no change.
    - **note**: New optional text for additional user information or notes. `null` means no change.
    - **on_hold_timeout**: New UTC timestamp for when `on_hold` status should start or end. Only applicable if status is changed to 'on_hold'.
    - **on_hold_expire_duration**: New duration (in seconds) for how long the user should stay in `on_hold` status. Only applicable if status is changed to 'on_hold'.
    - **next_plan**: Next user plan (resets after use).

    Note: Fields set to `null` or omitted will not be modified.
    """
    return await user_operator.modify_user(db, username=username, modified_user=modified_user, admin=admin)


@router.delete("/{username}", responses={403: responses._403, 404: responses._404})
async def remove_user(username: str, db: AsyncSession = Depends(get_db), admin: Admin = Depends(get_current)):
    """Remove a user"""
    return await user_operator.remove_user(db, username=username, admin=admin)


@router.post("/{username}/reset", response_model=UserResponse, responses={403: responses._403, 404: responses._404})
async def reset_user_data_usage(username: str, db: AsyncSession = Depends(get_db), admin: Admin = Depends(get_current)):
    """Reset user data usage"""
    return await user_operator.reset_user_data_usage(db, username=username, admin=admin)


@router.post(
    "/{username}/revoke_sub", response_model=UserResponse, responses={403: responses._403, 404: responses._404}
)
async def revoke_user_subscription(username: str, db: AsyncSession = Depends(get_db), admin: Admin = Depends(get_current)):
    """Revoke users subscription (Subscription link and proxies)"""
    return await user_operator.revoke_user_sub(db, username=username, admin=admin)


@router.post("s/reset", responses={403: responses._403, 404: responses._404})
async def reset_users_data_usage(db: AsyncSession = Depends(get_db), admin: Admin = Depends(check_sudo_admin)):
    """Reset all users data usage"""
    await user_operator.reset_users_data_usage(db, admin)
    await node_operator.restart_all_node(db, admin=admin)
    return {}


@router.put("/{username}/set-owner", response_model=UserResponse)
async def set_owner(
    username: str,
    admin_username: str,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(check_sudo_admin),
):
    """Set a new owner (admin) for a user."""
    return await user_operator.set_owner(db, username=username, admin_username=admin_username, admin=admin)


@router.post(
    "/{username}/active-next", response_model=UserResponse, responses={403: responses._403, 404: responses._404}
)
async def active_next_plan(username: str, db: AsyncSession = Depends(get_db), admin: Admin = Depends(get_current)):
    """Reset user by next plan"""

    return user_operator.active_next_plan(db, username=username, admin=admin)


@router.get("/{username}", response_model=UserResponse, responses={403: responses._403, 404: responses._404})
async def get_user(username: str, db: AsyncSession = Depends(get_db), admin: Admin = Depends(get_current)):
    """Get user information"""
    return await user_operator.get_validated_user(db=db, username=username, admin=admin)


@router.get(
    "s", response_model=UsersResponse, responses={400: responses._400, 403: responses._403, 404: responses._404}
)
async def get_users(
    offset: int = None,
    limit: int = None,
    username: list[str] = Query(None),
    search: str | None = None,
    owner: list[str] | None = Query(None, alias="admin"),
    status: UserStatus | None = None,
    sort: str | None = None,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current),
):
    """Get all users"""
    return await user_operator.get_users(
        db=db,
        admin=admin,
        offset=offset,
        limit=limit,
        username=username,
        search=search,
        owner=owner,
        status=status,
        sort=sort,
    )


@router.get(
    "/{username}/usage", response_model=UserUsagesResponse, responses={403: responses._403, 404: responses._404}
)
async def get_user_usage(
    username: str,
    start: dt | None = Query(None, example="2024-01-01T00:00:00"),
    end: dt | None = Query(None, example="2024-01-31T23:59:59"),
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current),
):
    """Get users usage"""
    return await user_operator.get_user_usage(db, username=username, admin=admin, start=start, end=end)


@router.get("s/usage", response_model=UsersUsagesResponse)
async def get_users_usage(
    start: dt | None = Query(None, example="2024-01-01T00:00:00"),
    end: dt | None = Query(None, example="2024-01-31T23:59:59"),
    db: AsyncSession = Depends(get_db),
    owner: list[str] | None = Query(None, alias="admin"),
    admin: Admin = Depends(get_current),
):
    """Get all users usage"""
    return await user_operator.get_users_usage(db, admin=admin, start=start, end=end, owner=owner)


@router.get("s/expired", response_model=list[str])
async def get_expired_users(
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current),
    expired_after: dt | None = Query(None, example="2024-01-01T00:00:00"),
    expired_before: dt | None = Query(None, example="2024-01-31T23:59:59"),
):
    """
    Get users who have expired within the specified date range.

    - **expired_after** UTC datetime (optional)
    - **expired_before** UTC datetime (optional)
    - At least one of expired_after or expired_before must be provided for filtering
    - If both are omitted, returns all expired users
    """

    return await user_operator.get_expired_users(db, admin, expired_after, expired_before)


@router.delete("s/expired", response_model=RemoveUsersResponse)
async def delete_expired_users(
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_current),
    expired_after: dt | None = Query(None, example="2024-01-01T00:00:00"),
    expired_before: dt | None = Query(None, example="2024-01-31T23:59:59"),
):
    """
    Delete users who have expired within the specified date range.

    - **expired_after** UTC datetime (optional)
    - **expired_before** UTC datetime (optional)
    - At least one of expired_after or expired_before must be provided
    """
    return await user_operator.delete_expired_users(db, admin, expired_after, expired_before)
