from typing import List, TYPE_CHECKING

from sqlalchemy import String, Integer, Float, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.dye_house import DyeHouse
    from app.models.dye_lot import DyeLot
    from app.models.tank_confirmation import TankConfirmation


class Vat(Base):
    __tablename__ = "vats"
    __table_args__ = (UniqueConstraint("dye_house_id", "vat_code", name="uq_house_vat_code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    dye_house_id: Mapped[int] = mapped_column(ForeignKey("dye_houses.id"), nullable=False, index=True)
    vat_code: Mapped[str] = mapped_column(String(64), nullable=False)
    fiber_type: Mapped[str] = mapped_column(String(64), nullable=False)
    capacity_l: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ready")
    # 是否具备合格清缸确认（以该缸最新一张确认单是否合格为准）
    has_valid_confirmation: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    dye_house: Mapped["DyeHouse"] = relationship("DyeHouse", back_populates="vats")
    dye_lots: Mapped[List["DyeLot"]] = relationship(
        "DyeLot", back_populates="vat", cascade="all, delete-orphan"
    )
    tank_confirmations: Mapped[List["TankConfirmation"]] = relationship(
        "TankConfirmation",
        back_populates="vat",
        cascade="all, delete-orphan",
        order_by="TankConfirmation.id.desc()",
    )
