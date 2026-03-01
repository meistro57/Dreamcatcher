import os
from types import SimpleNamespace
from unittest.mock import MagicMock
import tempfile

import pytest
from fastapi import HTTPException

from api.auth_routes import (
    unlock_user,
    admin_reset_user_password,
    AdminResetPasswordRequest,
)
from api.routes import (
    update_api_keys,
    ApiKeysUpdateRequest,
    AiModelUpdateRequest,
    set_default_ai_model,
    run_system_action,
    get_system_actions_history,
)


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


@pytest.mark.asyncio
@pytest.mark.integration
async def test_system_action_history_records_success(monkeypatch):
    original_enabled = os.environ.get("ENABLE_SYSTEM_ACTIONS")
    original_users = os.environ.get("SYSTEM_ACTION_USERS")
    original_audit = os.environ.get("SYSTEM_ACTION_AUDIT_FILE")

    with tempfile.TemporaryDirectory() as temp_dir:
        audit_file = os.path.join(temp_dir, "audit.jsonl")
        os.environ["ENABLE_SYSTEM_ACTIONS"] = "true"
        os.environ["SYSTEM_ACTION_USERS"] = "admin"
        os.environ["SYSTEM_ACTION_AUDIT_FILE"] = audit_file

        async def fake_run(_action: str):
            return {
                "success": True,
                "action": "restart_backend",
                "steps": [{"command": "echo ok", "return_code": 0}],
            }

        from api import routes
        monkeypatch.setattr(routes, "_run_system_action", fake_run)

        result = await run_system_action("restart_backend", current_user=SimpleNamespace(username="admin"))
        history = await get_system_actions_history(
            limit=10,
            status=None,
            current_user=SimpleNamespace(username="admin"),
        )

        assert result["success"] is True
        assert history["count"] >= 1
        assert history["entries"][0]["action"] == "restart_backend"
        assert history["entries"][0]["status"] == "success"

    if original_enabled is None:
        os.environ.pop("ENABLE_SYSTEM_ACTIONS", None)
    else:
        os.environ["ENABLE_SYSTEM_ACTIONS"] = original_enabled

    if original_users is None:
        os.environ.pop("SYSTEM_ACTION_USERS", None)
    else:
        os.environ["SYSTEM_ACTION_USERS"] = original_users

    if original_audit is None:
        os.environ.pop("SYSTEM_ACTION_AUDIT_FILE", None)
    else:
        os.environ["SYSTEM_ACTION_AUDIT_FILE"] = original_audit


@pytest.mark.asyncio
@pytest.mark.integration
async def test_set_default_ai_model_requires_permission_when_persisting():
    original_enabled = os.environ.get("ENABLE_SYSTEM_ACTIONS")
    original_users = os.environ.get("SYSTEM_ACTION_USERS")
    os.environ["ENABLE_SYSTEM_ACTIONS"] = "true"
    os.environ["SYSTEM_ACTION_USERS"] = "admin"

    with pytest.raises(HTTPException) as exc:
        await set_default_ai_model(
            payload=AiModelUpdateRequest(
                model="gpt-4",
                persist_to_env=True,
            ),
            current_user=SimpleNamespace(username="user"),
        )

    assert exc.value.status_code == 403

    if original_enabled is None:
        os.environ.pop("ENABLE_SYSTEM_ACTIONS", None)
    else:
        os.environ["ENABLE_SYSTEM_ACTIONS"] = original_enabled

    if original_users is None:
        os.environ.pop("SYSTEM_ACTION_USERS", None)
    else:
        os.environ["SYSTEM_ACTION_USERS"] = original_users


@pytest.mark.asyncio
@pytest.mark.integration
async def test_set_default_ai_model_updates_runtime(monkeypatch):
    from api import routes

    class StubAiService:
        default_model = "claude-3-haiku"

        def set_default_model(self, model: str):
            self.default_model = model
            return model

    monkeypatch.setattr(routes, "ai_service", StubAiService())
    result = await set_default_ai_model(
        payload=AiModelUpdateRequest(model="openrouter/openai/gpt-4o-mini", persist_to_env=False),
        current_user=SimpleNamespace(username="admin"),
    )

    assert result["default_model"] == "openrouter/openai/gpt-4o-mini"
    assert result["persisted_to_env"] is False
