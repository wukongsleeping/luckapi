from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_db
from app.models.models import UserModel, ApiKey, User
from app.schemas.model import UserModelCreate, UserModelOut, UserModelList, ApiKeyOut
from app.api.auth import admin_required

router = APIRouter()


@router.get("/users/{user_id}/models", response_model=UserModelList)
async def list_user_models(
    user_id: int,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    # Verify user exists
    user_result = await db.execute(select(User).where(User.id == user_id))
    if not user_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="User not found")

    count_query = select(func.count(UserModel.id)).where(UserModel.user_id == user_id)
    result = await db.execute(count_query)
    total = result.scalar() or 0

    items_query = (
        select(UserModel)
        .where(UserModel.user_id == user_id)
        .order_by(UserModel.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(items_query)
    items = result.scalars().all()
    return UserModelList(total=total, page=page, page_size=page_size, items=items)


@router.get("/users/{user_id}/models/{model_id}", response_model=UserModelOut)
async def get_user_model(
    user_id: int,
    model_id: int,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserModel).where(
            UserModel.id == model_id,
            UserModel.user_id == user_id,
        )
    )
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.post("/users/{user_id}/models", response_model=UserModelOut, status_code=201)
async def add_user_model(
    user_id: int,
    data: UserModelCreate,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    # Verify user exists
    user_result = await db.execute(select(User).where(User.id == user_id))
    if not user_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="User not found")

    model = UserModel(
        user_id=user_id,
        model_name=data.model_name,
        api_url=data.api_url.rstrip("/"),
        api_key=data.api_key,
    )
    db.add(model)
    await db.commit()
    await db.refresh(model)
    return model


@router.put("/users/{user_id}/models/{model_id}", response_model=UserModelOut)
async def update_user_model(
    user_id: int,
    model_id: int,
    data: UserModelCreate,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserModel).where(
            UserModel.id == model_id,
            UserModel.user_id == user_id,
        )
    )
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    model.model_name = data.model_name
    model.api_url = data.api_url.rstrip("/")
    model.api_key = data.api_key
    await db.commit()
    await db.refresh(model)
    return model


@router.delete("/users/{user_id}/models/{model_id}", status_code=204)
async def delete_user_model(
    user_id: int,
    model_id: int,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserModel).where(
            UserModel.id == model_id,
            UserModel.user_id == user_id,
        )
    )
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    await db.delete(model)
    await db.commit()


@router.get("/users/{user_id}/api-keys", response_model=list[ApiKeyOut])
async def list_api_keys(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ApiKey).where(ApiKey.user_id == user_id).order_by(ApiKey.id.desc())
    )
    keys = result.scalars().all()
    return keys


@router.post("/users/{user_id}/api-keys/renew", response_model=ApiKeyOut)
async def renew_api_key(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    from app.core.security import generate_api_key

    user_result = await db.execute(select(User).where(User.id == user_id))
    if not user_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="User not found")

    # Revoke all existing keys
    await db.execute(
        ApiKey.__table__.update()
        .where(ApiKey.user_id == user_id)
        .values(status="revoked")
    )

    # Create new key
    new_key = generate_api_key("sk")
    api_key_obj = ApiKey(
        user_id=user_id,
        key=new_key,
        name="Renewed key",
    )
    db.add(api_key_obj)
    await db.commit()
    await db.refresh(api_key_obj)
    return api_key_obj
