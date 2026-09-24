from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.clean_confirm import CleanConfirm, is_qualified
from app.models.user import User
from app.models.vat import Vat
from app.schemas.clean_confirm import MIN_PHOTOS, CleanConfirmCreate, CleanConfirmOut
from app.services import get_vat_with_latest_confirm

router = APIRouter(prefix="/api", tags=["clean-confirms"])


@router.get("/vats/{vat_id}/clean-confirms/latest", response_model=Optional[CleanConfirmOut])
def latest_clean_confirm(
    vat_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = get_vat_with_latest_confirm(db, vat_id)
    if result is None:
        raise HTTPException(status_code=404, detail="染缸不存在")
    return result[1]


@router.get("/clean-confirms", response_model=List[CleanConfirmOut])
def list_clean_confirms(
    vat_id: Optional[int] = Query(None, alias="vatId"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(CleanConfirm)
    if vat_id is not None:
        q = q.filter(CleanConfirm.vat_id == vat_id)
    return q.order_by(CleanConfirm.id.desc()).all()


@router.post(
    "/vats/{vat_id}/clean-confirms",
    response_model=CleanConfirmOut,
    status_code=status.HTTP_201_CREATED,
)
def submit_clean_confirm(
    vat_id: int,
    payload: CleanConfirmCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """提交清缸确认单。残渣、管路必须勾是，照片至少 2 张，否则 400。"""
    vat = db.query(Vat).filter(Vat.id == vat_id).first()
    if not vat:
        raise HTTPException(status_code=404, detail="染缸不存在")

    if not payload.residue_cleared or not payload.pipe_flushed or payload.photo_count < MIN_PHOTOS:
        reasons = []
        if not payload.residue_cleared:
            reasons.append("「残渣已清」必须勾选")
        if not payload.pipe_flushed:
            reasons.append("「管路已冲」必须勾选")
        if payload.photo_count < MIN_PHOTOS:
            reasons.append(f"照片至少 {MIN_PHOTOS} 张")
        raise HTTPException(status_code=400, detail="清缸确认不合格：" + "；".join(reasons))

    item = CleanConfirm(
        vat_id=vat_id,
        residue_cleared=payload.residue_cleared,
        pipe_flushed=payload.pipe_flushed,
        photo_count=payload.photo_count,
        confirmed_at=payload.confirmed_at,
        confirmer_name=payload.confirmer_name,
    )
    db.add(item)
    # 同缸保留历史，以最新一张为准；同步染缸「具备合格确认」标记
    vat.has_valid_confirm = is_qualified(
        residue_cleared=item.residue_cleared,
        pipe_flushed=item.pipe_flushed,
        photo_count=item.photo_count,
    )
    db.commit()
    db.refresh(item)
    return item
