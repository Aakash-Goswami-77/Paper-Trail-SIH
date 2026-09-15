import asyncio
import json
from database import engine, async_session_maker, CertificateModel, Base
from core.phase1_keys_schema import process_student_record

async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    with open("mock_data.json", "r") as f:
        raw_records = json.load(f)

    async with async_session_maker() as session:
        for r in raw_records:
            processed = process_student_record(r)
            cert_db = CertificateModel(
                cert_id=r["cert_id"],
                student_name=r["degree_info"]["student_name"],
                degree_title=r["degree_info"]["degree_title"],
                institution=r["degree_info"]["institution"],
                leaf_hash=processed["degree_group"]["leaf_hash"],
                transcript_leaf_hash=processed["transcript_group"]["leaf_hash"],
                revocation_status="Valid"
            )
            session.add(cert_db)
        await session.commit()
    print("🌱 Successfully seeded PostgreSQL database with mock records!")

if __name__ == "__main__":
    asyncio.run(seed())
