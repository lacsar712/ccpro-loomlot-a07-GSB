from typing import List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.tank_confirmation import TankConfirmation
from app.models.vat import Vat

MIN_PHOTO_COUNT = 2


def is_confirmation_valid(item: Optional[TankConfirmation]) -> bool:
    """清缸确认合格条件：残渣已清、管路已冲均勾“是”，且照片至少 2 张。"""
    return (
        item is not None
        and item.residue_cleared
        and item.pipe_flushed
        and item.photo_count >= MIN_PHOTO_COUNT
    )


def latest_confirmation_subquery(db: Session):
    """每口缸最新一张确认单（id 最大）的子查询；同缸历史确认以最新为准。"""
    return (
        db.query(
            TankConfirmation.vat_id.label("vat_id"),
            func.max(TankConfirmation.id).label("max_id"),
        )
        .group_by(TankConfirmation.vat_id)
        .subquery()
    )


def _vat_latest_query(db: Session):
    latest_subq = latest_confirmation_subquery(db)
    return (
        db.query(Vat, TankConfirmation)
        .outerjoin(latest_subq, latest_subq.c.vat_id == Vat.id)
        .outerjoin(TankConfirmation, TankConfirmation.id == latest_subq.c.max_id)
    )


def load_vat_with_latest_confirmation(
    db: Session, vat_id: int
) -> Tuple[Optional[Vat], Optional[TankConfirmation]]:
    """同一查询内读出染缸及其最新一张清缸确认单（无确认时第二项为 None）。

    排液放行判断与“读最新确认单”必须共用本查询，避免两者依据不一致。
    """
    row = _vat_latest_query(db).filter(Vat.id == vat_id).first()
    return row if row is not None else (None, None)


def list_vats_with_latest(
    db: Session, status: Optional[str] = None
) -> List[Tuple[Vat, Optional[TankConfirmation]]]:
    """列出染缸及其最新确认单（供看板与确认单参与对账使用）。"""
    q = _vat_latest_query(db)
    if status is not None:
        q = q.filter(Vat.status == status)
    return q.order_by(Vat.id).all()
