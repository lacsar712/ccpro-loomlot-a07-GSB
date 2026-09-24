from datetime import datetime, timedelta, timezone

from sqlalchemy import text

from app.auth import hash_password
from app.database import SessionLocal
from app.models.dye_house import DyeHouse
from app.models.dye_lot import DyeLot
from app.models.fastness_check import FastnessCheck
from app.models.tank_confirmation import TankConfirmation
from app.models.user import User
from app.models.vat import Vat


def ensure_schema() -> None:
    """对已有数据库做幂等的轻量补列（项目未使用 Alembic）。

    create_all 只建新表、不改已存在的 vats 表；老库需补合格确认标记列。
    """
    db = SessionLocal()
    try:
        if db.bind.dialect.name == "sqlite":
            cols = {row[1] for row in db.execute(text("PRAGMA table_info(vats)"))}
            missing = "has_valid_confirmation" not in cols
            if missing:
                db.execute(
                    text(
                        "ALTER TABLE vats "
                        "ADD COLUMN has_valid_confirmation BOOLEAN NOT NULL DEFAULT 0"
                    )
                )
        else:
            exists = db.execute(
                text(
                    "SELECT 1 FROM information_schema.columns "
                    "WHERE table_name='vats' AND column_name='has_valid_confirmation'"
                )
            ).first()
            missing = not exists
            if missing:
                db.execute(
                    text(
                        "ALTER TABLE vats "
                        "ADD COLUMN has_valid_confirmation BOOLEAN NOT NULL DEFAULT false"
                    )
                )
        if missing:
            db.commit()
            print("Added column vats.has_valid_confirmation.")
    finally:
        db.close()


def seed() -> None:
    ensure_schema()
    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            db.add_all(
                [
                    User(
                        username="admin",
                        hashed_password=hash_password("123456"),
                        role="admin",
                        display_name="染坊主管",
                    ),
                    User(
                        username="dyer",
                        hashed_password=hash_password("123456"),
                        role="dyer",
                        display_name="染程操作员",
                    ),
                ]
            )
            db.commit()

        if db.query(DyeHouse).count() == 0:
            h1 = DyeHouse(
                name="蓝靛一号坊",
                water_note="软化井水，硬度约 80ppm",
                notes="主做棉麻靛蓝与草木染",
            )
            h2 = DyeHouse(
                name="青石二号坊",
                water_note="河溪砂滤水，日供约 12 吨",
                notes="专职丝绢与混纺缸染",
            )
            db.add_all([h1, h2])
            db.flush()

            v1 = Vat(
                dye_house_id=h1.id,
                vat_code="V-01",
                fiber_type="棉",
                capacity_l=800.0,
                status="dyeing",
            )
            v2 = Vat(
                dye_house_id=h1.id,
                vat_code="V-02",
                fiber_type="麻",
                capacity_l=600.0,
                status="ready",
            )
            v3 = Vat(
                dye_house_id=h2.id,
                vat_code="S-01",
                fiber_type="丝",
                capacity_l=350.0,
                status="ready",
            )
            v4 = Vat(
                dye_house_id=h2.id,
                vat_code="S-02",
                fiber_type="混纺",
                capacity_l=500.0,
                status="drain",
                # 已排液：历史上凭一张合格清缸确认单放行
                has_valid_confirmation=True,
            )
            db.add_all([v1, v2, v3, v4])
            db.flush()

            now = datetime.now(timezone.utc)
            lot1 = DyeLot(
                vat_id=v1.id,
                recipe_name="靛蓝冷染三浸",
                fabric_kg=42.5,
                started_at=now - timedelta(hours=6),
                operator_name="染程操作员",
            )
            lot2 = DyeLot(
                vat_id=v3.id,
                recipe_name="青蓝套染",
                fabric_kg=18.0,
                started_at=now - timedelta(days=2),
                operator_name="染坊主管",
            )
            db.add_all([lot1, lot2])
            db.flush()

            # lot2 was on ready vat historically — keep v3 ready for demo create path
            # Re-set: creating lot2 would have set dyeing; for seed we leave one dyeing + one ready
            v3.status = "ready"
            db.add_all(
                [
                    FastnessCheck(
                        dye_lot_id=lot1.id,
                        checked_at=now - timedelta(hours=1),
                        wash_fastness=4,
                        rub_fastness=3.5,
                        temp_c=40.0,
                        notes="湿摩略偏，可出货",
                    ),
                    FastnessCheck(
                        dye_lot_id=lot2.id,
                        checked_at=now - timedelta(days=1),
                        wash_fastness=5,
                        rub_fastness=4.0,
                        temp_c=37.0,
                        notes=None,
                    ),
                ]
            )
            # v4 排液前的清缸确认历史：早先一张不合格（照片仅 1 张），
            # 补做的最新一张合格——同缸保留历史，以最新为准，故 v4 可排液。
            # v1（染程中）刻意不建确认单：看板“染程中且尚无合格确认”应为 1。
            db.add_all(
                [
                    TankConfirmation(
                        vat_id=v4.id,
                        residue_cleared=True,
                        pipe_flushed=False,
                        photo_count=1,
                        confirmed_at=now - timedelta(days=3),
                        confirmer="染程操作员",
                    ),
                    TankConfirmation(
                        vat_id=v4.id,
                        residue_cleared=True,
                        pipe_flushed=True,
                        photo_count=3,
                        confirmed_at=now - timedelta(days=3) + timedelta(minutes=20),
                        confirmer="染坊主管",
                    ),
                ]
            )
            db.commit()
            print("Seed data inserted.")
        else:
            print("Seed skipped (data exists).")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
