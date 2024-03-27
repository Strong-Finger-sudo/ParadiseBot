"""staff_db renamed

Revision ID: 53784926ea0d
Revises: 5adaf02f40fd
Create Date: 2024-03-27 17:52:56.541982

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '53784926ea0d'
down_revision: Union[str, None] = '5adaf02f40fd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('staff',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('staff_type', sa.String(), nullable=True),
    sa.Column('staff_name', sa.String(), nullable=True),
    sa.Column('user_id', sa.BigInteger(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_table('personal')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('personal',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('staff_type', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('user_id', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('staff_name', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='personal_pkey')
    )
    op.drop_table('staff')
    # ### end Alembic commands ###
