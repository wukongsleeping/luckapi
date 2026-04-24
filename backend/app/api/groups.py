from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_db
from app.models.models import Group, GroupUser
from app.schemas.group import (
    GroupCreate,
    GroupUpdate,
    GroupOut,
    GroupList,
    GroupAssignUser,
)
from app.api.auth import admin_required, User

router = APIRouter()


@router.get("/groups", response_model=GroupList)
async def list_groups(
    page: int = 1,
    page_size: int = 20,
    search: str = "",
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    base_query = select(Group)
    count_query = select(func.count(Group.id))

    if search:
        escaped = search.replace("%", "\\%").replace("_", "\\_")
        base_query = base_query.where(Group.name.like(f"%{escaped}%", escape="\\"))
        count_query = count_query.where(Group.name.like(f"%{escaped}%", escape="\\"))

    result = await db.execute(count_query)
    total = result.scalar() or 0

    base_query = (
        base_query.order_by(Group.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(base_query)
    items = result.scalars().all()

    # Batch query all member_ids for all groups (fix N+1)
    group_id_list = [g.id for g in items]
    member_map: dict[int, list[int]] = {}
    if group_id_list:
        member_result = await db.execute(
            select(GroupUser.group_id, GroupUser.user_id).where(
                GroupUser.group_id.in_(group_id_list)
            )
        )
        for gid, uid in member_result.all():
            member_map.setdefault(gid, []).append(uid)

    group_outs = []
    for g in items:
        group_outs.append(
            GroupOut(
                id=g.id,
                name=g.name,
                model_name=g.model_name,
                model_url=g.model_url,
                model_api_key=g.model_api_key,
                status=g.status,
                member_ids=member_map.get(g.id, []),
                created_at=g.created_at,
                updated_at=g.updated_at,
            )
        )

    return GroupList(total=total, page=page, page_size=page_size, items=group_outs)


@router.get("/groups/{group_id}", response_model=GroupOut)
async def get_group(
    group_id: int,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    member_result = await db.execute(
        select(GroupUser.user_id).where(GroupUser.group_id == group_id)
    )
    member_ids = [uid for (uid,) in member_result.fetchall()]

    return GroupOut(
        id=group.id,
        name=group.name,
        model_name=group.model_name,
        model_url=group.model_url,
        model_api_key=group.model_api_key,
        status=group.status,
        member_ids=member_ids,
        created_at=group.created_at,
        updated_at=group.updated_at,
    )


@router.post("/groups", response_model=GroupOut, status_code=status.HTTP_201_CREATED)
async def create_group(
    data: GroupCreate,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(Group).where(Group.name == data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Group name already exists")

    group = Group(
        name=data.name,
        model_name=data.model_name,
        model_url=data.model_url,
    )

    if data.model_api_key:
        group.model_api_key = data.model_api_key

    db.add(group)
    await db.commit()
    await db.refresh(group)

    return GroupOut(
        id=group.id,
        name=group.name,
        model_name=group.model_name,
        model_url=group.model_url,
        model_api_key=group.model_api_key,
        status=group.status,
        member_ids=[],
        created_at=group.created_at,
        updated_at=group.updated_at,
    )


@router.put("/groups/{group_id}", response_model=GroupOut)
async def update_group(
    group_id: int,
    data: GroupUpdate,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "model_api_key" and value:
            group.model_api_key = value
        else:
            setattr(group, field, value)

    await db.commit()
    await db.refresh(group)

    member_result = await db.execute(
        select(GroupUser.user_id).where(GroupUser.group_id == group_id)
    )
    member_ids = [uid for (uid,) in member_result.fetchall()]

    return GroupOut(
        id=group.id,
        name=group.name,
        model_name=group.model_name,
        model_url=group.model_url,
        model_api_key=group.model_api_key,
        status=group.status,
        member_ids=member_ids,
        created_at=group.created_at,
        updated_at=group.updated_at,
    )


@router.delete("/groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: int,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    await db.delete(group)
    await db.commit()


@router.post("/groups/{group_id}/models", response_model=GroupOut)
async def assign_group_model(
    group_id: int,
    data: dict,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    model_name = data.get("model_name") or data.get("api_name")
    api_url = data.get("api_url")
    api_key = data.get("api_key")

    if model_name:
        group.model_name = model_name
    if api_url:
        group.model_url = api_url
    if api_key:
        group.model_api_key = api_key

    await db.commit()
    await db.refresh(group)

    member_result = await db.execute(
        select(GroupUser.user_id).where(GroupUser.group_id == group_id)
    )
    member_ids = [uid for (uid,) in member_result.fetchall()]

    return GroupOut(
        id=group.id,
        name=group.name,
        model_name=group.model_name,
        model_url=group.model_url,
        model_api_key=group.model_api_key,
        status=group.status,
        member_ids=member_ids,
        created_at=group.created_at,
        updated_at=group.updated_at,
    )


@router.post("/groups/{group_id}/assign-user", response_model=GroupOut)
async def assign_group_user(
    group_id: int,
    data: GroupAssignUser,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    existing = await db.execute(
        select(GroupUser).where(
            GroupUser.group_id == group_id,
            GroupUser.user_id == data.user_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User already in this group")

    group_user = GroupUser(
        group_id=group_id,
        user_id=data.user_id,
    )
    db.add(group_user)
    await db.commit()
    await db.refresh(group_user)

    member_result = await db.execute(
        select(GroupUser.user_id).where(GroupUser.group_id == group_id)
    )
    member_ids = [uid for (uid,) in member_result.fetchall()]

    return GroupOut(
        id=group.id,
        name=group.name,
        model_name=group.model_name,
        model_url=group.model_url,
        model_api_key=group.model_api_key,
        status=group.status,
        member_ids=member_ids,
        created_at=group.created_at,
        updated_at=group.updated_at,
    )


@router.delete(
    "/groups/{group_id}/assign-user/{user_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_group_user(
    group_id: int,
    user_id: int,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(GroupUser).where(
            GroupUser.group_id == group_id,
            GroupUser.user_id == user_id,
        )
    )
    group_user = result.scalar_one_or_none()
    if not group_user:
        raise HTTPException(status_code=404, detail="User not in this group")
    await db.delete(group_user)
    await db.commit()
