from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_db
from app.models.models import User, GroupUser, Group
from app.schemas.user import UserCreate, UserOut, UserUpdate, UserList
from app.core.security import generate_api_key, hash_password
from app.api.auth import admin_required
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


async def _get_user_group_ids(db, user_id):
    """获取用户所属的分组 ID 列表。"""
    result = await db.execute(
        select(GroupUser.group_id).where(GroupUser.user_id == user_id)
    )
    return [row[0] for row in result.all()]


async def _get_group_names_by_ids(db, group_ids):
    """根据分组 ID 列表获取分组名称映射。"""
    if not group_ids:
        return {}
    result = await db.execute(
        select(Group.id, Group.name).where(Group.id.in_(group_ids))
    )
    return {row[0]: row[1] for row in result.all()}


@router.get("/users/debug")
async def list_users_debug(db: AsyncSession = Depends(get_db)):
    """Debug endpoint to check group assignment data."""
    result = await db.execute(select(User))
    users = result.scalars().all()
    debug_info = []
    for u in users:
        gids = await _get_user_group_ids(db, u.id)
        debug_info.append({
            "id": u.id,
            "username": u.username,
            "group_ids": gids,
        })
    return {"users": debug_info, "note": "This shows raw group_ids from GroupUser table"}


@router.get("/users", response_model=UserList)
async def list_users(
    page: int = 1,
    page_size: int = 20,
    search: str = "",
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    if search:
        escaped = search.replace("%", "\\%").replace("_", "\\_")
        count_query = select(func.count(User.id)).where(
            (User.username.like(f"%{escaped}%", escape="\\"))
            | (User.display_name.like(f"%{escaped}%", escape="\\"))
        )
        result = await db.execute(count_query)
        total = result.scalar() or 0
        items_query = (
            select(User)
            .where(
                (User.username.like(f"%{escaped}%", escape="\\"))
                | (User.display_name.like(f"%{escaped}%", escape="\\"))
            )
            .order_by(User.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    else:
        count_query = select(func.count(User.id))
        result = await db.execute(count_query)
        total = result.scalar() or 0
        items_query = (
            select(User)
            .order_by(User.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

    result = await db.execute(items_query)
    users = result.scalars().all()

    # 批量获取所有用户的分组 ID（使用 IN 查询替代 N 次查询，修复 N+1）
    user_ids = [u.id for u in users]
    user_group_map: dict[int, list[int]] = {}
    all_group_ids: set[int] = set()
    if user_ids:
        gu_result = await db.execute(
            select(GroupUser.user_id, GroupUser.group_id).where(
                GroupUser.user_id.in_(user_ids)
            )
        )
        for uid, gid in gu_result.all():
            user_group_map.setdefault(uid, []).append(gid)
            all_group_ids.add(gid)

    # 批量获取所有分组的名称
    group_name_map = await _get_group_names_by_ids(db, list(all_group_ids)) if all_group_ids else {}

    items = []
    for u in users:
        user_out = UserOut.model_validate(u)
        user_out.group_ids = user_group_map.get(u.id, [])
        user_out.group_names = [group_name_map.get(gid, f"分组{gid}") for gid in user_group_map.get(u.id, [])]
        items.append(user_out)

    logger.info("list_users: %d users, group_ids_map=%s, group_names_map=%s", len(items), user_group_map, {k: [group_name_map.get(g, '') for g in v] for k, v in user_group_map.items()})

    return UserList(total=total, page=page, page_size=page_size, items=items)


@router.get("/users/{user_id}", response_model=UserOut)
async def get_user(
    user_id: int,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    group_ids = await _get_user_group_ids(db, user.id)
    group_names = []
    if group_ids:
        result = await db.execute(
            select(Group.id, Group.name).where(Group.id.in_(group_ids))
        )
        group_name_map = {row[0]: row[1] for row in result.all()}
        group_names = [group_name_map.get(gid, f"分组{gid}") for gid in group_ids]

    user_out = UserOut.model_validate(user)
    user_out.group_ids = group_ids
    user_out.group_names = group_names
    return user_out


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(User).where(User.username == data.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already exists")

    user = User(
        username=data.username,
        display_name=data.display_name,
        password_hash=hash_password(data.password),
        role=data.role,
        balance=data.initial_balance,
        allowed_ips=data.allowed_ips,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Generate user's API key
    api_key = generate_api_key("sk")
    from app.models.models import ApiKey

    api_key_obj = ApiKey(
        user_id=user.id,
        key=api_key,
        name=f"{user.username}'s key",
    )
    db.add(api_key_obj)
    await db.commit()
    await db.refresh(api_key_obj)

    group_ids = await _get_user_group_ids(db, user.id)
    group_names = []
    if group_ids:
        result = await db.execute(
            select(Group.id, Group.name).where(Group.id.in_(group_ids))
        )
        group_name_map = {row[0]: row[1] for row in result.all()}
        group_names = [group_name_map.get(gid, f"分组{gid}") for gid in group_ids]

    user_out = UserOut.model_validate(user)
    user_out.group_ids = group_ids
    user_out.group_names = group_names
    return user_out


@router.put("/users/{user_id}", response_model=UserOut)
async def update_user(
    user_id: int,
    data: UserUpdate,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "password":
            user.password_hash = hash_password(value)
        elif field == "initial_balance":
            user.balance = value
        else:
            setattr(user, field, value)

    await db.commit()
    await db.refresh(user)

    group_ids = await _get_user_group_ids(db, user.id)
    group_names = []
    if group_ids:
        result = await db.execute(
            select(Group.id, Group.name).where(Group.id.in_(group_ids))
        )
        group_name_map = {row[0]: row[1] for row in result.all()}
        group_names = [group_name_map.get(gid, f"分组{gid}") for gid in group_ids]

    user_out = UserOut.model_validate(user)
    user_out.group_ids = group_ids
    user_out.group_names = group_names
    return user_out


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await db.delete(user)
    await db.commit()
