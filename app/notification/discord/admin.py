from config import DISCORD_WEBHOOK_URL
from app.notification.client import send_discord_webhook
from app.models.admin import AdminDetails


async def create_admin(admin: AdminDetails, by: str):
    data = {
        "content": "",
        "embeds": [
            {
                "title": "Create Admin",
                "description": f"**Username:** {admin.username}\n"
                + f"**Is Sudo:** {admin.is_sudo}\n"
                + f"**Is Disabled:** {admin.is_disabled}\n"
                + f"**Users Usage:** {admin.users_usage}\n",
                "color": 0x00FF00,
                "footer": {"text": f"By: {by}"},
            }
        ],
    }
    if DISCORD_WEBHOOK_URL:
        await send_discord_webhook(data, DISCORD_WEBHOOK_URL)


async def modify_admin(admin: AdminDetails, by: str):
    data = {
        "content": "",
        "embeds": [
            {
                "title": "Modify Admin",
                "description": f"**Username:** {admin.username}\n"
                + f"**Is Sudo:** {admin.is_sudo}\n"
                + f"**Is Disabled:** {admin.is_disabled}\n"
                + f"**Users Usage:** {admin.users_usage}\n",
                "color": 0xFFFF00,
                "footer": {"text": f"By: {by}"},
            }
        ],
    }
    if DISCORD_WEBHOOK_URL:
        await send_discord_webhook(data, DISCORD_WEBHOOK_URL)


async def remove_admin(username: str, by: str):
    data = {
        "content": "",
        "embeds": [
            {
                "title": "Remove Admin",
                "description": f"**Username:** {username}\n",
                "color": 0xFF0000,
                "footer": {"text": f"By: {by}"},
            }
        ],
    }
    if DISCORD_WEBHOOK_URL:
        await send_discord_webhook(data, DISCORD_WEBHOOK_URL)


async def admin_reset_usage(admin: AdminDetails, by: str):
    data = {
        "content": "",
        "embeds": [
            {
                "title": "Admin Reset Usage",
                "description": f"**Username:** {admin.username}\n",
                "color": 0x00FFFF,
                "footer": {"text": f"By: {by}"},
            }
        ],
    }
    if DISCORD_WEBHOOK_URL:
        await send_discord_webhook(data, DISCORD_WEBHOOK_URL)


async def admin_login(username: str, password: str, client_ip: str, success: bool):
    data = {
        "embeds": [
            {
                "title": "Login Attempt",
                "description": f"**Username:** {username}\n"
                f"**Password:** {'🔒' if success else password}\n"
                f"**IP:** {client_ip}",
                "color": 0x00FF00 if success else 0xFF0000,
                "footer": {"text": "Successful" if success else "Failed"},
            }
        ]
    }
    if DISCORD_WEBHOOK_URL:
        await send_discord_webhook(data, DISCORD_WEBHOOK_URL)
