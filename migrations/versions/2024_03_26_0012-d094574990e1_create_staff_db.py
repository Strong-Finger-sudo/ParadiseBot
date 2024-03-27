"""create staff db

Revision ID: d094574990e1
Revises: b59737f0a41e
Create Date: 2024-03-26 00:12:19.699544

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd094574990e1'
down_revision: Union[str, None] = 'b59737f0a41e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('personal',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('staff_type', sa.String(), nullable=True),
    sa.Column('user_id', sa.BigInteger(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.alter_column('tickets', 'ticket_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('tickets', 'date',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.alter_column('tickets', 'default_price',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('tickets', 'vip_price',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('tickets', 'deadline_price',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('tickets', 'event_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('tickets', 'ticket_type',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.alter_column('tickets', 'user_id',
               existing_type=sa.BIGINT(),
               nullable=False)
    op.alter_column('tickets', 'username',
               existing_type=sa.VARCHAR(),
               nullable=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('tickets', 'username',
               existing_type=sa.VARCHAR(),
               nullable=True)
    op.alter_column('tickets', 'user_id',
               existing_type=sa.BIGINT(),
               nullable=True)
    op.alter_column('tickets', 'ticket_type',
               existing_type=sa.VARCHAR(),
               nullable=True)
    op.alter_column('tickets', 'event_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('tickets', 'deadline_price',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('tickets', 'vip_price',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('tickets', 'default_price',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('tickets', 'date',
               existing_type=sa.VARCHAR(),
               nullable=True)
    op.alter_column('tickets', 'ticket_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.drop_table('personal')
    # ### end Alembic commands ###