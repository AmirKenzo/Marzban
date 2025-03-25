from app.notification.client import send_telegram_message
from app.models.admin import Admin
from config import TELEGRAM_LOGGER_TOPIC_ID, TELEGRAM_LOGGER_CHANNEL_ID, TELEGRAM_ADMIN_ID, TELEGRAM_NOTIFY


async def add_admin(admin: Admin, by: str):
    data = (
        "*Add Admin*\n"
        + "➖➖➖➖➖➖➖➖➖\n"
        + f"**Username:** {admin.username}\n"
        + f"**Is Sudo:** {admin.is_sudo}\n"
        + f"**Is Disabled:** {admin.is_disabled}\n"
        + f"**User Usage:** {admin.users_usage}\n"
        + "➖➖➖➖➖➖➖➖➖\n"
        + f"_By: {by}_"
    )
    if TELEGRAM_NOTIFY:
        await send_telegram_message(data, TELEGRAM_ADMIN_ID, TELEGRAM_LOGGER_CHANNEL_ID, TELEGRAM_LOGGER_TOPIC_ID)


async def modify_admin(admin: Admin, by: str):
    data = (
        "*Modify Admin*\n"
        + "➖➖➖➖➖➖➖➖➖\n"
        + f"**Username:** {admin.username}\n"
        + f"**Is Sudo:** {admin.is_sudo}\n"
        + f"**Is Disabled:** {admin.is_disabled}\n"
        + f"**User Usage:** {admin.users_usage}\n"
        + "➖➖➖➖➖➖➖➖➖\n"
        + f"_By: {by}_"
    )
    if TELEGRAM_NOTIFY:
        await send_telegram_message(data, TELEGRAM_ADMIN_ID, TELEGRAM_LOGGER_CHANNEL_ID, TELEGRAM_LOGGER_TOPIC_ID)


async def remove_admin(username: str, by: str):
    data = "*Remove Admin*\n" + f"**Username:** {username}\n" + "➖➖➖➖➖➖➖➖➖\n" + f"_By: {by}_"
    if TELEGRAM_NOTIFY:
        await send_telegram_message(data, TELEGRAM_ADMIN_ID, TELEGRAM_LOGGER_CHANNEL_ID, TELEGRAM_LOGGER_TOPIC_ID)


async def admin_reset_usage(admin: Admin, by: str):
    data = "*Admin Usage Reset*\n" + f"**Username:** {admin.username}\n" + "➖➖➖➖➖➖➖➖➖\n" + f"_By: {by}_"
    if TELEGRAM_NOTIFY:
        await send_telegram_message(data, TELEGRAM_ADMIN_ID, TELEGRAM_LOGGER_CHANNEL_ID, TELEGRAM_LOGGER_TOPIC_ID)


async def admin_login(username: str, password: str, client_ip: str, success: bool):
    data = {
        "content": "",
        "embeds": [
            {
                "title": "Login Attempt",
                "description": f"**Username:** {username}\n"
                + f"**Password:** {'🔒' if success else password}\n"
                + f"**IP:** {client_ip}",
                "color": int("00ff00", 16) if success else int("ff0000", 16),
            }
        ],
    }
    data = (
        "Successful "
        if success
        else "Failed"
        + "*Login Attempt*\n"
        + "➖➖➖➖➖➖➖➖➖\n"
        + f"**Username:** {username}\n"
        + f"**Password:** {'🔒' if success else password}\n"
        + f"**IP:** {client_ip}\n"
    )
    if TELEGRAM_NOTIFY:
        await send_telegram_message(data, TELEGRAM_ADMIN_ID, TELEGRAM_LOGGER_CHANNEL_ID, TELEGRAM_LOGGER_TOPIC_ID)
