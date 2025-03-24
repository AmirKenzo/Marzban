from collections import defaultdict
import asyncio
from datetime import datetime, timezone
from operator import attrgetter

from pymysql.err import OperationalError
from sqlalchemy import and_, bindparam, insert, select, update

from sqlalchemy.orm import Session
from sqlalchemy.sql.dml import Insert
from GozargahNodeBridge import GozargahNode, NodeAPIError

# from app import scheduler, node
from app import async_scheduler as scheduler
from app.node import node_manager as node_manager
from app.utils.logger import get_logger
from app.db import GetDB
from app.db.models import Admin, NodeUsage, NodeUserUsage, System, User
from config import (
    DISABLE_RECORDING_NODE_USAGE,
    JOB_RECORD_NODE_USAGES_INTERVAL,
    JOB_RECORD_USER_USAGES_INTERVAL,
)


logger = get_logger("record-usages")


async def safe_execute(db: Session, stmt, params=None):
    if db.bind.name == "mysql":
        if isinstance(stmt, Insert):
            stmt = stmt.prefix_with("IGNORE")

        tries = 0
        done = False
        while not done:
            try:
                db.connection().execute(stmt, params)
                db.commit()
                done = True
            except OperationalError as err:
                if err.args[0] == 1213 and tries < 3:  # Deadlock
                    db.rollback()
                    tries += 1
                    continue
                raise err

    else:
        db.connection().execute(stmt, params)
        db.commit()


async def record_user_stats(params: list, node_id: int, consumption_factor: int = 1):
    if not params:
        return

    created_at = datetime.fromisoformat(datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:00:00"))

    with GetDB() as db:
        # make user usage row if doesn't exist
        select_stmt = select(NodeUserUsage.user_id).where(
            and_(NodeUserUsage.node_id == node_id, NodeUserUsage.created_at == created_at)
        )
        existings = [r[0] for r in db.execute(select_stmt).fetchall()]
        uids_to_insert = set()

        for p in params:
            uid = int(p["uid"])
            if uid in existings:
                continue
            uids_to_insert.add(uid)

        if uids_to_insert:
            stmt = insert(NodeUserUsage).values(
                user_id=bindparam("uid"), created_at=created_at, node_id=node_id, used_traffic=0
            )
            await safe_execute(db, stmt, [{"uid": uid} for uid in uids_to_insert])

        # record
        stmt = (
            update(NodeUserUsage)
            .values(used_traffic=NodeUserUsage.used_traffic + bindparam("value") * consumption_factor)
            .where(
                and_(
                    NodeUserUsage.user_id == bindparam("uid"),
                    NodeUserUsage.node_id == node_id,
                    NodeUserUsage.created_at == created_at,
                )
            )
        )
        await safe_execute(db, stmt, params)


async def record_node_stats(params: dict, node_id: int):
    if not params:
        return

    created_at = datetime.fromisoformat(datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:00:00"))

    with GetDB() as db:
        # make node usage row if doesn't exist
        select_stmt = select(NodeUsage.node_id).where(
            and_(NodeUsage.node_id == node_id, NodeUsage.created_at == created_at)
        )
        notfound = db.execute(select_stmt).first() is None
        if notfound:
            stmt = insert(NodeUsage).values(created_at=created_at, node_id=node_id, uplink=0, downlink=0)
            await safe_execute(db, stmt)

        # record
        stmt = (
            update(NodeUsage)
            .values(uplink=NodeUsage.uplink + bindparam("up"), downlink=NodeUsage.downlink + bindparam("down"))
            .where(and_(NodeUsage.node_id == node_id, NodeUsage.created_at == created_at))
        )

        await safe_execute(db, stmt, params)


async def get_users_stats(node: GozargahNode):
    try:
        stats_respons = await node.get_users_stats(reset=True, timeout=30)
        params = defaultdict(int)
        for stat in filter(attrgetter("value"), stats_respons.stats):
            params[stat.name.split(".", 1)[0]] += stat.value
        params = list({"uid": uid, "value": value} for uid, value in params.items())
        return params
    except NodeAPIError as e:
        logger.error("Failed to get outbounds stats, error: %s", e.detail)
        return []
    except Exception as e:
        logger.error("Failed to get outbounds stats, unknown error: %s", e)
        return []


async def get_outbounds_stats(node: GozargahNode):
    try:
        stats_respons = await node.get_outbounds_stats(reset=True, timeout=10)
        params = [
            {"up": stat.value, "down": 0} if stat.link == "uplink" else {"up": 0, "down": stat.value}
            for stat in filter(attrgetter("value"), stats_respons.stats)
        ]
        return params
    except NodeAPIError as e:
        logger.error("Failed to get outbounds stats, error: %s", e.detail)
        return []
    except Exception as e:
        logger.error("Failed to get outbounds stats, unknown error: %s", e)
        return []


async def record_user_usages():
    nodes: tuple[int, GozargahNode] = await node_manager.get_healthy_nodes()
    tasks = {node_id: asyncio.create_task(get_users_stats(node)) for node_id, node in nodes}
    usage_coefficient = {node_id: (await node.get_extra()).get("usage_coefficient", 1) for node_id, node in nodes}

    await asyncio.gather(*tasks.values())

    api_params = {node_id: task.result() for node_id, task in tasks.items()}

    users_usage = defaultdict(int)
    for node_id, params in api_params.items():
        coefficient = usage_coefficient.get(node_id, 1)  # get the usage coefficient for the node
        for param in params:
            users_usage[param["uid"]] += int(param["value"] * coefficient)  # apply the usage coefficient
    users_usage = list({"uid": uid, "value": value} for uid, value in users_usage.items())
    if not users_usage:
        return

    with GetDB() as db:
        user_admin_map = dict(db.query(User.id, User.admin_id).all())

    admin_usage = defaultdict(int)
    for user_usage in users_usage:
        admin_id = user_admin_map.get(int(user_usage["uid"]))
        if admin_id:
            admin_usage[admin_id] += user_usage["value"]

    # record users usage
    with GetDB() as db:
        stmt = (
            update(User)
            .where(User.id == bindparam("uid"))
            .values(used_traffic=User.used_traffic + bindparam("value"), online_at=datetime.utcnow())
        )

        await safe_execute(db, stmt, users_usage)

        admin_data = [{"admin_id": admin_id, "value": value} for admin_id, value in admin_usage.items()]
        if admin_data:
            admin_update_stmt = (
                update(Admin)
                .where(Admin.id == bindparam("admin_id"))
                .values(users_usage=Admin.users_usage + bindparam("value"))
            )
            await safe_execute(db, admin_update_stmt, admin_data)

    if DISABLE_RECORDING_NODE_USAGE:
        return

    for node_id, params in api_params.items():
        await record_user_stats(params, node_id, usage_coefficient[node_id])


async def record_node_usages():
    # Create tasks for all nodes
    tasks = {
        node_id: asyncio.create_task(get_outbounds_stats(node))
        for node_id, node in await node_manager.get_healthy_nodes()
    }

    await asyncio.gather(*tasks.values())

    # Collect results
    api_params = {node_id: task.result() for node_id, task in tasks.items()}

    total_up = 0
    total_down = 0
    for node_id, params in api_params.items():
        for param in params:
            total_up += param["up"]
            total_down += param["down"]
    if not (total_up or total_down):
        return

    # record nodes usage
    with GetDB() as db:
        stmt = update(System).values(uplink=System.uplink + total_up, downlink=System.downlink + total_down)
        await safe_execute(db, stmt)

    if DISABLE_RECORDING_NODE_USAGE:
        return

    for node_id, params in api_params.items():
        await record_node_stats(params, node_id)


scheduler.add_job(
    record_user_usages, "interval", seconds=JOB_RECORD_USER_USAGES_INTERVAL, coalesce=True, max_instances=1
)
scheduler.add_job(
    record_node_usages, "interval", seconds=JOB_RECORD_NODE_USAGES_INTERVAL, coalesce=True, max_instances=1
)
