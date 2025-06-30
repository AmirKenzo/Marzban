from datetime import datetime, timezone
from typing import Optional, Union

from sqlalchemy import and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Node, NodeStat, NodeStatus, NodeUsage, NodeUserUsage
from app.models.node import NodeCreate, NodeModify, UsageTable
from app.models.stats import NodeStats, NodeStatsList, NodeUsageStat, NodeUsageStatsList, Period

from .general import _build_trunc_expression


async def get_node(db: AsyncSession, name: str) -> Optional[Node]:
    """
    Retrieves a node by its name.

    Args:
        db (AsyncSession): The database session.
        name (str): The name of the node to retrieve.

    Returns:
        Optional[Node]: The Node object if found, None otherwise.
    """
    return (await db.execute(select(Node).where(Node.name == name))).unique().scalar_one_or_none()


async def get_node_by_id(db: AsyncSession, node_id: int) -> Optional[Node]:
    """
    Retrieves a node by its ID.

    Args:
        db (AsyncSession): The database session.
        node_id (int): The ID of the node to retrieve.

    Returns:
        Optional[Node]: The Node object if found, None otherwise.
    """
    return (await db.execute(select(Node).where(Node.id == node_id))).unique().scalar_one_or_none()


async def get_nodes(
    db: AsyncSession,
    status: Optional[Union[NodeStatus, list]] = None,
    enabled: bool | None = None,
    core_id: int | None = None,
    offset: int | None = None,
    limit: int | None = None,
) -> list[Node]:
    """
    Retrieves nodes based on optional status and enabled filters.

    Args:
        db (AsyncSession): The database session.
        status (Optional[Union[app.db.models.NodeStatus, list]]): The status or list of statuses to filter by.
        enabled (bool): If True, excludes disabled nodes.

    Returns:
        List[Node]: A list of Node objects matching the criteria.
    """
    query = select(Node)

    if status:
        if isinstance(status, list):
            query = query.where(Node.status.in_(status))
        else:
            query = query.where(Node.status == status)

    if enabled:
        query = query.where(Node.status != NodeStatus.disabled)

    if core_id:
        query = query.where(Node.core_config_id == core_id)

    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(limit)

    return (await db.execute(query)).scalars().all()


async def get_nodes_usage(
    db: AsyncSession, start: datetime, end: datetime, period: Period, node_id: int | None = None
) -> NodeUsageStatsList:
    """
    Retrieves usage data for all nodes within a specified time range.

    Args:
        db (AsyncSession): The database session.
        start (datetime): The start time of the usage period.
        end (datetime): The end time of the usage period.

    Returns:
        NodeUsageStatsList: A NodeUsageStatsList contain list of NodeUsageResponse objects containing usage data.
    """
    trunc_expr = _build_trunc_expression(period, NodeUsage.created_at)

    conditions = [NodeUsage.created_at >= start, NodeUsage.created_at <= end]

    if node_id is not None:
        conditions.append(NodeUsage.node_id == node_id)

    stmt = (
        select(
            trunc_expr.label("period_start"),
            func.sum(NodeUsage.downlink).label("downlink"),
            func.sum(NodeUsage.uplink).label("uplink"),
        )
        .where(and_(*conditions))
        .group_by(trunc_expr)
        .order_by(trunc_expr)
    )

    result = await db.execute(stmt)
    return NodeUsageStatsList(
        period=period, start=start, end=end, stats=[NodeUsageStat(**row) for row in result.mappings()]
    )


async def get_node_stats(
    db: AsyncSession, node_id: int, start: datetime, end: datetime, period: Period
) -> NodeStatsList:
    trunc_expr = _build_trunc_expression(period, NodeStat.created_at)
    conditions = [NodeStat.created_at >= start, NodeStat.created_at <= end, NodeStat.node_id == node_id]

    stmt = (
        select(
            trunc_expr.label("period_start"),
            func.avg(NodeStat.mem_used / NodeStat.mem_total * 100).label("mem_usage_percentage"),
            func.avg(NodeStat.cpu_usage).label("cpu_usage_percentage"),  # CPU usage is already in percentage
            func.avg(NodeStat.incoming_bandwidth_speed).label("incoming_bandwidth_speed"),
            func.avg(NodeStat.outgoing_bandwidth_speed).label("outgoing_bandwidth_speed"),
        )
        .where(and_(*conditions))
        .group_by(trunc_expr)
        .order_by(trunc_expr)
    )

    result = await db.execute(stmt)

    return NodeStatsList(period=period, start=start, end=end, stats=[NodeStats(**row) for row in result.mappings()])


async def create_node(db: AsyncSession, node: NodeCreate) -> Node:
    """
    Creates a new node in the database.

    Args:
        db (AsyncSession): The database session.
        node (NodeCreate): The node creation model containing node details.

    Returns:
        Node: The newly created Node object.
    """
    db_node = Node(**node.model_dump())

    db.add(db_node)
    await db.commit()
    await db.refresh(db_node)
    return db_node


async def remove_node(db: AsyncSession, db_node: Node) -> Node:
    """
    Removes a node from the database.

    Args:
        db (AsyncSession): The database session.
        dbnode (Node): The Node object to be removed.

    Returns:
        Node: The removed Node object.
    """
    await db.delete(db_node)
    await db.commit()


async def modify_node(db: AsyncSession, db_node: Node, modify: NodeModify) -> Node:
    """
    modify an existing node with new information.

    Args:
        db (AsyncSession): The database session.
        dbnode (Node): The Node object to be updated.
        modify (NodeModify): The modification model containing updated node details.

    Returns:
        Node: The modified Node object.
    """

    node_data = modify.model_dump(exclude_none=True)

    for key, value in node_data.items():
        setattr(db_node, key, value)

    db_node.xray_version = None
    db_node.message = None
    db_node.node_version = None

    if db_node.status != NodeStatus.disabled:
        db_node.status = NodeStatus.connecting

    await db.commit()
    await db.refresh(db_node)
    return db_node


async def update_node_status(
    db: AsyncSession,
    db_node: Node,
    status: NodeStatus,
    message: str = "",
    xray_version: str = "",
    node_version: str = "",
) -> Node:
    """
    Updates the status of a node.

    Args:
        db (AsyncSession): The database session.
        dbnode (Node): The Node object to be updated.
        status (app.db.models.NodeStatus): The new status of the node.
        message (str, optional): A message associated with the status update.
        version (str, optional): The version of the node software.

    Returns:
        Node: The updated Node object.
    """
    db_node.status = status
    db_node.message = message
    db_node.xray_version = xray_version
    db_node.node_version = node_version
    db_node.last_status_change = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(db_node)
    return db_node


async def clear_usage_data(db: AsyncSession, table: UsageTable):
    if table == UsageTable.node_user_usages:
        await db.execute(delete(NodeUserUsage))
    elif table == UsageTable.node_usages:
        await db.execute(delete(NodeUsage))
    await db.commit()
