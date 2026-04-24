from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_db
from app.models.models import GlobalModel
from app.schemas.admin_model import (
    GlobalModelCreate,
    GlobalModelUpdate,
    GlobalModelOut,
    GlobalModelList,
)
from app.api.auth import admin_required, User

router = APIRouter()


@router.get("/models", response_model=GlobalModelList)
async def list_global_models(
    page: int = 1,
    page_size: int = 20,
    search: str = "",
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    base_query = select(GlobalModel)
    count_query = select(func.count(GlobalModel.id))

    if search:
        escaped = search.replace("%", "\\%").replace("_", "\\_")
        base_query = base_query.where(
            GlobalModel.model_name.like(f"%{escaped}%", escape="\\")
        )
        count_query = count_query.where(
            GlobalModel.model_name.like(f"%{escaped}%", escape="\\")
        )

    result = await db.execute(count_query)
    total = result.scalar() or 0

    base_query = (
        base_query.order_by(GlobalModel.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(base_query)
    items = [GlobalModelOut.model_validate(m) for m in result.scalars().all()]

    return GlobalModelList(total=total, page=page, page_size=page_size, items=items)


@router.get("/models/{model_id}", response_model=GlobalModelOut)
async def get_global_model(
    model_id: int,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(GlobalModel).where(GlobalModel.id == model_id))
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Global model not found")
    return GlobalModelOut.model_validate(model)


@router.post(
    "/models", response_model=GlobalModelOut, status_code=status.HTTP_201_CREATED
)
async def create_global_model(
    data: GlobalModelCreate,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(GlobalModel).where(GlobalModel.model_name == data.model_name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Model name already exists")

    model = GlobalModel(
        model_name=data.model_name,
        api_url=data.api_url.rstrip("/"),
        api_key=data.api_key,
        status=data.status,
    )
    db.add(model)
    await db.commit()
    await db.refresh(model)
    return GlobalModelOut.model_validate(model)


@router.put("/models/{model_id}", response_model=GlobalModelOut)
async def update_global_model(
    model_id: int,
    data: GlobalModelUpdate,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(GlobalModel).where(GlobalModel.id == model_id))
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Global model not found")

    update_data = data.model_dump(exclude_unset=True)
    if "api_key" in update_data:
        model.api_key = update_data.pop("api_key")
    for field, value in update_data.items():
        setattr(model, field, value)

    await db.commit()
    await db.refresh(model)
    return GlobalModelOut.model_validate(model)


@router.delete("/models/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_global_model(
    model_id: int,
    current_user: User = Depends(admin_required),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(GlobalModel).where(GlobalModel.id == model_id))
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Global model not found")
    await db.delete(model)
    await db.commit()
