from app import on_startup
from app.utils.store import DictStorage
from .xray import XRayConfig
from app.db import GetDB
from app.db.models import ProxyHostSecurity
from app.db.crud import get_hosts, get_or_create_inbound, get_host_by_id
from config import XRAY_JSON


config = XRayConfig(XRAY_JSON)


@DictStorage
async def hosts(storage: dict):
    storage.clear()
    async with GetDB() as db:
        db_hosts = await get_hosts(db)

        for host in db_hosts:
            if host.is_disabled or (config.get_inbound(host.inbound_tag) is None):
                continue
            downstream = None
            if host.transport_settings.xhttp_settings and (
                ds_host := host.transport_settings.xhttp_settings.download_settings
            ):
                downstream = await get_host_by_id(db, ds_host)

            host_data = {
                "remark": host.remark,
                "inbound_tag": host.inbound_tag,
                "address": [addr.strip() for addr in host.address.split(",")] if host.address else [],
                "port": host.port,
                "path": host.path or None,
                "sni": [s.strip() for s in host.sni.split(",")] if host.sni else [],
                "host": [h.strip() for h in host.host.split(",")] if host.host else [],
                "alpn": host.alpn.value,
                "fingerprint": host.fingerprint.value,
                "tls": None if host.security == ProxyHostSecurity.inbound_default else host.security.value,
                "allowinsecure": host.allowinsecure,
                "fragment_settings": host.fragment_settings,
                "noise_settings": host.noise_settings,
                "random_user_agent": host.random_user_agent,
                "use_sni_as_host": host.use_sni_as_host,
                "http_headers": host.http_headers,
                "mux_settings": host.mux_settings,
                "transport_settings": host.transport_settings,
            }

            if downstream:
                host_data["downloadSettings"] = {
                    "remark": downstream.remark,
                    "inbound_tag": downstream.inbound_tag,
                    "address": [addr.strip() for addr in downstream.address.split(",")] if downstream.address else [],
                    "port": downstream.port,
                    "path": downstream.path or None,
                    "sni": [s.strip() for s in downstream.sni.split(",")] if downstream.sni else [],
                    "host": [h.strip() for h in downstream.host.split(",")] if downstream.host else [],
                    "alpn": downstream.alpn.value,
                    "fingerprint": downstream.fingerprint.value,
                    "tls": None
                    if downstream.security == ProxyHostSecurity.inbound_default
                    else downstream.security.value,
                    "allowinsecure": downstream.allowinsecure,
                    "fragment_settings": downstream.fragment_settings,
                    "noise_settings": downstream.noise_settings,
                    "random_user_agent": downstream.random_user_agent,
                    "use_sni_as_host": downstream.use_sni_as_host,
                    "http_headers": downstream.http_headers,
                    "mux_settings": downstream.mux_settings,
                    "transport_settings": downstream.transport_settings,
                }
            else:
                host_data["downloadSettings"] = None

            storage[host.id] = host_data


async def check_inbounds():
    async with GetDB() as db:
        for tag in config.inbounds:
            await get_or_create_inbound(db, tag)


on_startup(hosts.update)
on_startup(check_inbounds)


__all__ = ["config", "hosts", "nodes", "XRayConfig"]
