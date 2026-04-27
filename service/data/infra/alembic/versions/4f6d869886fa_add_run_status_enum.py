"""add run status enum

Revision ID: 4f6d869886fa
Revises: ce239f1f4b74
Create Date: 2026-04-25 00:25:14.447422

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4f6d869886fa'
down_revision: Union[str, None] = 'ce239f1f4b74'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    runstatus = sa.Enum('queued', 'running', 'completed', 'failed', name='runstatus')
    runstatus.create(op.get_bind(), checkfirst=True)
    op.alter_column('runs', 'status',
               existing_type=sa.VARCHAR(length=255),
               type_=runstatus,
               existing_nullable=False,
               postgresql_using='status::runstatus')


def downgrade() -> None:
    op.alter_column('runs', 'status',
               existing_type=sa.Enum('queued', 'running', 'completed', 'failed', name='runstatus'),
               type_=sa.VARCHAR(length=255),
               existing_nullable=False,
               postgresql_using='status::varchar')
    sa.Enum(name='runstatus').drop(op.get_bind(), checkfirst=True)
