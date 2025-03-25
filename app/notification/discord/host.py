from app.notification.client import send_discord_webhook
from config import DISCORD_WEBHOOK_URL
from app.models.host import BaseHost


async def create_host(host: BaseHost, by: str):
    data = {
        "content": "",
        "embeds": [
            {
                "title": "Create Host",
                "description": f"**Remark:** {host.remark}\n"
                + f"**Address:** {host.address}\n"
                + f"**Inbound Tag:** {host.inbound_tag}\n"
                + f"**Port:** {host.port}",
                "color": 0x00ff00,
                "footer": {"text": f"ID: {host.id}\nBy: {by}"},
            }
        ],
    }
    if DISCORD_WEBHOOK_URL:
        await send_discord_webhook(data, DISCORD_WEBHOOK_URL)


async def modify_host(host: BaseHost, by: str):
    data = {
        "content": "",
        "embeds": [
            {
                "title": "Modify Host",
                "description": f"**Remark:** {host.remark}\n"
                + f"**Address:** {host.address}\n"
                + f"**Inbound Tag:** {host.inbound_tag}\n"
                + f"**Port:** {host.port}",
                "color": 0xffff00,
                "footer": {"text": f"ID: {host.id}\nBy: {by}"},
            }
        ],
    }
    if DISCORD_WEBHOOK_URL:
        await send_discord_webhook(data, DISCORD_WEBHOOK_URL)


async def remove_host(host: BaseHost, by: str):
    data = {
        "content": "",
        "embeds": [
            {
                "title": "Remove Host",
                "description": f"**Remark:** {host.remark}",
                "color": 0xff0000,
                "footer": {"text": f"ID: {host.id}\nBy: {by}"},
            }
        ],
    }
    if DISCORD_WEBHOOK_URL:
        await send_discord_webhook(data, DISCORD_WEBHOOK_URL)


async def update_hosts(by: str):
    data = {
        "content": "",
        "embeds": [
            {
                "title": "Update Hosts",
                "description": f"All hosts has been updated by **{by}**",
                "color": 0x00ffff,
            }
        ],
    }
    if DISCORD_WEBHOOK_URL:
        await send_discord_webhook(data, DISCORD_WEBHOOK_URL)
