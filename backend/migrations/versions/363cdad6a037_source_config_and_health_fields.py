"""source config and health fields

Revision ID: 363cdad6a037
Revises: 5b90bf393966
Create Date: 2026-09-08 14:36:08.310603

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '363cdad6a037'
down_revision: Union[str, None] = '5b90bf393966'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 源级配置（cookie/token/verify/timeout/rate_limit/depth）
    op.add_column('sources', sa.Column('config', sa.JSON(), nullable=True))
    # 增量爬取：上次爬取开始时间
    op.add_column('sources', sa.Column('last_crawl_at', sa.DateTime(), nullable=True))
    # 健康度：上次成功时间 / 连续失败次数 / 平均延迟秒
    op.add_column('sources', sa.Column('last_success_at', sa.DateTime(), nullable=True))
    op.add_column('sources', sa.Column('consecutive_failures', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('sources', sa.Column('avg_latency', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('sources', 'avg_latency')
    op.drop_column('sources', 'consecutive_failures')
    op.drop_column('sources', 'last_success_at')
    op.drop_column('sources', 'last_crawl_at')
    op.drop_column('sources', 'config')