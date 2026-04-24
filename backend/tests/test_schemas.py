"""Tests for all Pydantic schemas in app/schemas/."""
import pytest
from datetime import datetime, timezone


class TestUserCreateSchema:
    """Tests for UserCreate schema."""

    def test_valid_user_create(self):
        from app.schemas.user import UserCreate
        user = UserCreate(username="testuser", password="password123")
        assert user.username == "testuser"
        assert user.display_name == ""
        assert user.role == "user"
        assert user.initial_balance == 0

    def test_user_create_rejects_short_username(self):
        from app.schemas.user import UserCreate
        with pytest.raises(Exception):
            UserCreate(username="ab", password="password123")

    def test_user_create_rejects_long_username(self):
        from app.schemas.user import UserCreate
        with pytest.raises(Exception):
            UserCreate(username="a" * 51, password="password123")

    def test_user_create_rejects_short_password(self):
        from app.schemas.user import UserCreate
        with pytest.raises(Exception):
            UserCreate(username="testuser", password="short")

    def test_user_create_allows_all_fields(self):
        from app.schemas.user import UserCreate
        user = UserCreate(
            username="testuser",
            display_name="Test User",
            password="password123",
            role="admin",
            initial_balance=100,
            allowed_ips="10.0.0.1, 192.168.1.1",
        )
        assert user.role == "admin"
        assert user.initial_balance == 100

    def test_user_create_rejects_invalid_role(self):
        from app.schemas.user import UserCreate
        with pytest.raises(Exception):
            UserCreate(username="test", password="password123", role="superadmin")


class TestUserUpdateSchema:
    """Tests for UserUpdate schema."""

    def test_empty_update(self):
        from app.schemas.user import UserUpdate
        update = UserUpdate()
        assert update.model_dump(exclude_unset=True) == {}

    def test_partial_update(self):
        from app.schemas.user import UserUpdate
        update = UserUpdate(display_name="New Name")
        dumped = update.model_dump(exclude_unset=True)
        assert dumped == {"display_name": "New Name"}

    def test_valid_status_values(self):
        from app.schemas.user import UserUpdate
        for status in ["active", "banned", "disabled"]:
            update = UserUpdate(status=status)
            assert update.status == status

    def test_rejects_invalid_status(self):
        from app.schemas.user import UserUpdate
        with pytest.raises(Exception):
            UserUpdate(status="unknown")

    def test_rejects_negative_balance(self):
        from app.schemas.user import UserUpdate
        with pytest.raises(Exception):
            UserUpdate(initial_balance=-1)


class TestUserOutSchema:
    """Tests for UserOut schema."""

    def test_out_schema(self):
        from app.schemas.user import UserOut
        user = UserOut(
            id=1,
            username="testuser",
            display_name="Test",
            role="user",
            status="active",
            balance=100,
            total_usage=50,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        data = user.model_dump()
        assert data["id"] == 1
        assert data["username"] == "testuser"
        assert data["balance"] == 100


class TestUserListSchema:
    """Tests for UserList schema."""

    def test_empty_list(self):
        from app.schemas.user import UserList, UserOut
        from datetime import datetime, timezone
        data = UserList(
            total=0,
            page=1,
            page_size=20,
            items=[],
        )
        assert data.total == 0
        assert len(data.items) == 0

    def test_paginated_list(self):
        from app.schemas.user import UserList, UserOut
        from datetime import datetime, timezone
        items = [
            UserOut(
                id=i,
                username=f"user{i}",
                display_name=f"User {i}",
                role="user",
                status="active",
                balance=0,
                total_usage=0,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            for i in range(5)
        ]
        data = UserList(total=5, page=1, page_size=5, items=items)
        assert data.total == 5
        assert len(data.items) == 5


class TestLoginRequestSchema:
    """Tests for LoginRequest schema."""

    def test_valid_login(self):
        from app.schemas.user import LoginRequest
        login = LoginRequest(username="test", password="pass")
        assert login.username == "test"

    def test_empty_username_accepted(self):
        """LoginRequest has no min_length on username, so empty is accepted."""
        from app.schemas.user import LoginRequest
        login = LoginRequest(username="", password="pass")
        assert login.username == ""


class TestTokenOutSchema:
    """Tests for TokenOut schema."""

    def test_token_out_requires_user(self):
        from app.schemas.user import TokenOut, UserOut
        from datetime import datetime, timezone
        user = UserOut(
            id=1, username="test", display_name="Test", role="user",
            status="active", balance=0, total_usage=0,
            created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
        )
        token = TokenOut(access_token="test-token", user=user)
        assert token.token_type == "bearer"


class TestUserModelSchemas:
    """Tests for model-related schemas."""

    def test_user_model_create_valid(self):
        from app.schemas.model import UserModelCreate
        model = UserModelCreate(model_name="gpt-4", api_url="https://api.example.com", api_key="sk-xxx")
        assert model.model_name == "gpt-4"

    def test_user_model_create_rejects_empty_name(self):
        from app.schemas.model import UserModelCreate
        with pytest.raises(Exception):
            UserModelCreate(model_name="", api_url="https://api.example.com", api_key="sk-xxx")

    def test_api_key_out_valid(self):
        from app.schemas.model import ApiKeyOut
        from datetime import datetime, timezone
        key = ApiKeyOut(
            id=1,
            user_id=1,
            key="sk-xxx",
            name="Main key",
            status="active",
            last_used_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
        )
        assert key.key == "sk-xxx"


class TestGroupSchemas:
    """Tests for group-related schemas."""

    def test_group_create_valid(self):
        from app.schemas.group import GroupCreate
        group = GroupCreate(name="test-group")
        assert group.name == "test-group"

    def test_group_create_rejects_empty_name(self):
        from app.schemas.group import GroupCreate
        with pytest.raises(Exception):
            GroupCreate(name="")

    def test_group_update_empty(self):
        from app.schemas.group import GroupUpdate
        update = GroupUpdate()
        assert update.model_dump(exclude_unset=True) == {}

    def test_group_assign_user_valid(self):
        from app.schemas.group import GroupAssignUser
        assign = GroupAssignUser(user_id=42)
        assert assign.user_id == 42


class TestQASchema:
    """Tests for QA record schemas."""

    def test_qa_record_out_valid(self):
        from app.schemas.qa import QaRecordOut
        from datetime import datetime, timezone
        record = QaRecordOut(
            id=1,
            user_id=1,
            target_model="gpt-4",
            method="POST",
            request_body='{"messages": []}',
            latency_ms=1500,
            status="success",
            created_at=datetime.now(timezone.utc),
        )
        assert record.target_model == "gpt-4"

    def test_qa_record_list_valid(self):
        from app.schemas.qa import QaRecordList, QaRecordOut
        from datetime import datetime, timezone
        records = QaRecordList(
            total=1,
            page=1,
            page_size=1,
            items=[
                QaRecordOut(
                    id=1, user_id=1, target_model="gpt-4", method="POST",
                    request_body="{}", latency_ms=100, status="success",
                    created_at=datetime.now(timezone.utc),
                )
            ],
        )
        assert records.total == 1


class TestGlobalModelSchemas:
    """Tests for global model schemas."""

    def test_global_model_create_valid(self):
        from app.schemas.admin_model import GlobalModelCreate
        model = GlobalModelCreate(model_name="gpt-4", api_url="https://api.example.com")
        assert model.status == "active"
        assert model.api_key is None

    def test_global_model_update_empty(self):
        from app.schemas.admin_model import GlobalModelUpdate
        update = GlobalModelUpdate()
        assert update.model_dump(exclude_unset=True) == {}
