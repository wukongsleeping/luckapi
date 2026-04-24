"""
修改 qa_records 表的 request_body 和 response_body 字段为 LongText

原因：Text 类型最大 64KB，opencode 等工具的请求体包含完整 system prompt、
工具定义、JSON Schema 等，可能超过 64KB，导致保存失败。
"""

import sys
import os

# Add parent dir to path so we can import the app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import asyncio
from app.db.session import engine
from sqlalchemy import text


async def upgrade():
    async with engine.connect() as conn:
        await conn.execute(text("ALTER TABLE qa_records MODIFY COLUMN request_body LONGTEXT NOT NULL"))
        await conn.execute(text("ALTER TABLE qa_records MODIFY COLUMN response_body LONGTEXT"))
        await conn.commit()
        print("✅ qa_records table columns upgraded to LongText")


async def downgrade():
    async with engine.connect() as conn:
        await conn.execute(text("ALTER TABLE qa_records MODIFY COLUMN request_body TEXT NOT NULL"))
        await conn.execute(text("ALTER TABLE qa_records MODIFY COLUMN response_body TEXT"))
        await conn.commit()
        print("⬅️  qa_records table columns downgraded to Text")


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "upgrade"
    if action == "upgrade":
        asyncio.run(upgrade())
    elif action == "downgrade":
        asyncio.run(downgrade())
