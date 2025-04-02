import re
import asyncio
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .validators import NumericValidatorMixin, ListValidator
from app.db.models import UserStatus, UserDataLimitResetStrategy
from app.models.admin import AdminBaseInfo
from app.models.proxy import ProxyTable


class UserStatusModify(str, Enum):
    active = "active"
    disabled = "disabled"
    on_hold = "on_hold"


class UserStatusCreate(str, Enum):
    active = "active"
    on_hold = "on_hold"


class NextPlanModel(BaseModel):
    user_template_id: int | None = None
    data_limit: int | None = None
    expire: int | None = None
    add_remaining_traffic: bool = False
    fire_on_either: bool = True
    model_config = ConfigDict(from_attributes=True)


class User(BaseModel):
    proxy_settings: ProxyTable = Field(default_factory=ProxyTable)
    expire: datetime | int | None = Field(None, nullable=True)
    data_limit: int | None = Field(ge=0, default=None, description="data_limit can be 0 or greater")
    data_limit_reset_strategy: UserDataLimitResetStrategy | None = None
    note: str | None = Field(max_length=500, default=None)
    sub_updated_at: datetime | None = Field(None, nullable=True)
    sub_last_user_agent: str | None = Field(None, nullable=True)
    online_at: datetime | None = Field(None, nullable=True)
    on_hold_expire_duration: int | None = Field(None, nullable=True)
    on_hold_timeout: datetime | int | None = Field(None, nullable=True)
    group_ids: list[int] | None = Field(default_factory=list)
    auto_delete_in_days: int | None = Field(None, nullable=True)

    next_plan: NextPlanModel | None = Field(None, nullable=True)


class UserWithValidator(User):
    @field_validator("on_hold_expire_duration")
    @classmethod
    def validate_timeout(cls, v):
        # Check if expire is 0 or None and timeout is not 0 or None
        if v in (0, None):
            return None
        return v

    @field_validator("on_hold_timeout", check_fields=False)
    @classmethod
    def validator_on_hold_timeout(cls, value):
        if value == 0 or isinstance(value, datetime) or value is None:
            return value
        else:
            raise ValueError("on_hold_timeout can be datetime or 0")

    @field_validator("expire", check_fields=False)
    @classmethod
    def validator_expire(cls, value):
        if value == 0 or isinstance(value, datetime) or value is None:
            return value
        elif isinstance(value, int):
            return datetime.fromtimestamp(value, tz=timezone.utc)
        else:
            raise ValueError("expire can be datetime, timestamp or 0")

    @field_validator("status", mode="before", check_fields=False)
    def validate_status(cls, status, values):
        on_hold_expire = values.data.get("on_hold_expire_duration")
        expire = values.data.get("expire")
        if status == UserStatusCreate.on_hold:
            if on_hold_expire == 0 or on_hold_expire is None:
                raise ValueError("User cannot be on hold without a valid on_hold_expire_duration.")
            if expire:
                raise ValueError("User cannot be on hold with specified expire.")
        return status


class UserCreate(UserWithValidator):
    username: str = Field(min_length=3, max_length=32)
    status: UserStatusCreate | None = None
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "user1234",
                "proxy_settings": {
                    "vmess": {"id": "35e4e39c-7d5c-4f4b-8b71-558e4f37ff53"},
                    "vless": {},
                },
                "group_ids": [1, 3, 5],
                "next_plan": {"data_limit": 0, "expire": 0, "add_remaining_traffic": False, "fire_on_either": True},
                "expire": 0,
                "data_limit": 0,
                "data_limit_reset_strategy": "no_reset",
                "status": "active",
                "note": "",
                "on_hold_timeout": "2023-11-03T20:30:00",
                "on_hold_expire_duration": 0,
            }
        }
    )

    @field_validator("username", check_fields=False)
    @classmethod
    def validate_username(cls, v):
        if not re.match(r"^[a-zA-Z0-9-_@.]+$", v):
            raise ValueError("Username can only contain alphanumeric characters, -, _, @, and .")

        # Additional check to prevent consecutive special characters
        if re.search(r"[-_@.]{2,}", v):
            raise ValueError("Username cannot have consecutive special characters")

        return v

    @field_validator("group_ids", mode="after")
    @classmethod
    def group_ids_validator(cls, v):
        return ListValidator.not_null_list(v, "group")


class UserModify(UserWithValidator):
    status: UserStatusModify | None = None
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "proxy_settings": {
                    "vmess": {"id": "35e4e39c-7d5c-4f4b-8b71-558e4f37ff53"},
                    "vless": {},
                },
                "group_ids": [1, 3, 5],
                "next_plan": {"data_limit": 0, "expire": 0, "add_remaining_traffic": False, "fire_on_either": True},
                "expire": 0,
                "data_limit": 0,
                "data_limit_reset_strategy": "no_reset",
                "status": "active",
                "note": "",
                "on_hold_timeout": "2023-11-03T20:30:00",
                "on_hold_expire_duration": 0,
            }
        }
    )

    @field_validator("group_ids", mode="after")
    @classmethod
    def group_ids_validator(cls, v):
        return ListValidator.nullable_list(v, "group")


class UserResponse(User):
    id: int
    username: str
    status: UserStatus
    used_traffic: int
    lifetime_used_traffic: int = 0
    created_at: datetime
    subscription_url: str = ""
    admin: AdminBaseInfo | None = None
    model_config = ConfigDict(from_attributes=True)

    @field_validator("used_traffic", "lifetime_used_traffic", "data_limit", mode="before")
    @classmethod
    def cast_to_int(cls, v):
        return NumericValidatorMixin.cast_to_int(v)


class SubscriptionUserResponse(UserResponse):
    admin: AdminBaseInfo | None = Field(default=None, exclude=True)
    note: str | None = Field(None, exclude=True)
    auto_delete_in_days: int | None = Field(None, exclude=True)
    model_config = ConfigDict(from_attributes=True)


class UsersResponse(BaseModel):
    users: list[UserResponse]
    total: int

    async def load_subscriptions(self, gen_sub_func):
        tasks = [gen_sub_func(user) for user in self.users]
        urls = await asyncio.gather(*tasks)

        for user, url in zip(self.users, urls):
            user.subscription_url = url


class RemoveUsersResponse(BaseModel):
    users: list[str]
    count: int
