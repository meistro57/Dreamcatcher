import os
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from api.auth_routes import (
    unlock_user,
    admin_reset_user_password,
    AdminResetPasswordRequest,
)
from api.routes import update_api_keys, ApiKeysUpdateRequest


@pytest.mark.asyncio
@pytest.mark.integration
async def test_unlock_user_clears_lock_state():
    db = MagicMock()
    locked_user = SimpleNamespace(
        failed_login_attempts=9,
        locked_until="later",
        is_active=False,
        updated_at=None,
    )

    user_crud = MagicMock()
    user_crud.get_by_id.return_value = locked_user

    from api import auth_routes
    original_user_crud = auth_routes.UserCRUD
    auth_routes.UserCRUD = lambda _db: user_crud
    try:
        result = await unlock_user(
            user_id="u-1",
            current_user=SimpleNamespace(),
            db=db,
        )
    finally:
        auth_routes.UserCRUD = original_user_crud

    assert result["message"] == "User unlocked successfully"
    assert locked_user.failed_login_attempts == 0
    assert locked_user.locked_until is None
    assert locked_user.is_active is True
    db.commit.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_admin_reset_user_password_calls_service():
    auth_service = MagicMock()
    auth_service.reset_password.return_value = True

    result = await admin_reset_user_password(
        user_id="u-1",
        payload=AdminResetPasswordRequest(new_password="NewSecret123!"),
        current_user=SimpleNamespace(),
        auth_service=auth_service,
    )

    assert result["message"] == "User password reset successfully"
    auth_service.reset_password.assert_called_once_with("u-1", "NewSecret123!")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_persist_api_keys_requires_system_action_permission():
    original_enabled = os.environ.get("ENABLE_SYSTEM_ACTIONS")
    original_users = os.environ.get("SYSTEM_ACTION_USERS")
    original_openai = os.environ.get("OPENAI_API_KEY")
    os.environ["ENABLE_SYSTEM_ACTIONS"] = "true"
    os.environ["SYSTEM_ACTION_USERS"] = "admin"
    os.environ.pop("OPENAI_API_KEY", None)

    with pytest.raises(HTTPException) as exc:
        await update_api_keys(
            payload=ApiKeysUpdateRequest(
                openai_api_key="sk-test",
                persist_to_env=True,
            ),
            current_user=SimpleNamespace(username="user"),
        )

    assert exc.value.status_code == 403
    assert os.environ.get("OPENAI_API_KEY") is None

    if original_enabled is None:
        os.environ.pop("ENABLE_SYSTEM_ACTIONS", None)
    else:
        os.environ["ENABLE_SYSTEM_ACTIONS"] = original_enabled

    if original_users is None:
        os.environ.pop("SYSTEM_ACTION_USERS", None)
    else:
        os.environ["SYSTEM_ACTION_USERS"] = original_users

    if original_openai is None:
        os.environ.pop("OPENAI_API_KEY", None)
    else:
        os.environ["OPENAI_API_KEY"] = original_openai
