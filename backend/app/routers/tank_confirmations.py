from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.confirmation_service import (
    MIN_PHOTO_COUNT,
    is_confirmation_valid,
    load_vat_with_latest_confirmation,
)
from app.database import get_db
from app.models.tank_confirmation import TankConfirmation
from app.models.user import User
from app.models.vat import Vat
from app.schemas.tank_confirmation import TankConfirmationCreate, TankConfirmationOut

router = APIRouter(prefix="/api/tank-confirmations", tags=["tank-confirmations"])


def _to_out(item: TankConfirmation, latest: Optional[TankConfirmation]) -> TankConfirmationOut:
    out = TankConfirmationOut.model_validate(item)
    out.is_valid = latest is not None and latest.id == item.id and is_confirmation_valid(latest)
    return out


@router.get("", response_model=List[TankConfirmationOut])
def list_confirmations(
    vat_id: Optional[int] = Query(None, alias="vatId"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """同缸保留历史确认单，以最新一张为准；isValid 按各缸最新单分别计算。"""
    q = db.query(TankConfirmation)
    if vat_id is not None:
        q = q.filter(TankConfirmation.vat_id == vat_id)
    items = q.order_by(TankConfirmation.id.desc()).all()
    # 列表按 id 倒序，每口缸第一次出现的即其最新确认单
    latest_ids = {}
    for item in items:
        latest_ids.setdefault(item.vat_id, item.id)
    return [
        _to_out(item, item if item.id == latest_ids.get(item.vat_id) else None)
        for item in items
    ]


@router.get("/latest", response_model=TankConfirmationOut)
def get_latest_confirmation(
    vat_id: int = Query(..., alias="vatId"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    vat, latest = load_vat_with_latest_confirmation(db, vat_id)
    if vat is None:
        raise HTTPException(status_code=404, detail="染缸不存在")
    if latest is None:
        raise HTTPException(status_code=404, detail="该染缸尚无清缸确认单")
    return _to_out(latest, latest)


@router.post("", response_model=TankConfirmationOut, status_code=status.HTTP_201_CREATED)
def create_confirmation(
    payload: TankConfirmationCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    vat = db.query(Vat).filter(Vat.id == payload.vat_id).first()
    if vat is None:
        raise HTTPException(status_code=400, detail="染缸不存在")
    # 不合格的确认单一律拒收（400）：残渣、管路必须勾“是”，照片至少 2 张
    if not payload.residue_cleared:
        raise HTTPException(status_code=400, detail="残渣已清必须勾“是”")
    if not payload.pipe_flushed:
        raise HTTPException(status_code=400, detail="管路已冲必须勾“是”")
    if payload.photo_count < MIN_PHOTO_COUNT:
        raise HTTPException(status_code=400, detail="照片至少 2 张")

    item = TankConfirmation(
        vat_id=payload.vat_id,
        residue_cleared=payload.residue_cleared,
        pipe_flushed=payload.pipe_flushed,
        photo_count=payload.photo_count,
        confirmed_at=payload.confirmed_at or datetime.now(timezone.utc),
        confirmer=payload.confirmer,
    )
    db.add(item)
    db.commit()

    # 用排液放行所用的同一查询回读最新确认，回写染缸“是否具备合格确认”
    vat, latest = load_vat_with_latest_confirmation(db, payload.vat_id)
    vat.has_valid_confirmation = is_confirmation_valid(latest)
    db.commit()
    db.refresh(item)
    return _to_out(item, latest)
