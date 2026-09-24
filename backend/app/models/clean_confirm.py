from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.vat import Vat

# 合格清缸确认：残渣与管路都必须勾是，且照片至少 2 张
REQUIRED_MIN_PHOTOS = 2


def is_qualified(*, residue_cleared: bool, pipe_flushed: bool, photo_count: int) -> bool:
    """一张确认单是否合格：残渣已清、管路已冲都勾是，照片 >= 2。"""
    return bool(residue_cleared and pipe_flushed and photo_count >= REQUIRED_MIN_PHOTOS)


class CleanConfirm(Base):
    """清缸确认单：排液前填写，与排液动作绑死；同缸保留历史，以最新一张为准。"""

    __tablename__ = "clean_confirms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    vat_id: Mapped[int] = mapped_column(ForeignKey("vats.id"), nullable=False, index=True)
    residue_cleared: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    pipe_flushed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    photo_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    confirmed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    confirmer_name: Mapped[str] = mapped_column(String(64), nullable=False)

    vat: Mapped["Vat"] = relationship("Vat", back_populates="clean_confirms")

    @property
    def qualified(self) -> bool:
        return is_qualified(
            residue_cleared=self.residue_cleared,
            pipe_flushed=self.pipe_flushed,
            photo_count=self.photo_count,
        )
