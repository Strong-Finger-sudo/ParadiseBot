"""ticket_table_update

Revision ID: b59737f0a41e
Revises: 7401ccdf6283
Create Date: 2024-03-16 23:43:48.854824

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b59737f0a41e'
down_revision: Union[str, None] = '7401ccdf6283'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('tickets', sa.Column('default_price', sa.Integer(), nullable=True))
    op.add_column('tickets', sa.Column('vip_price', sa.Integer(), nullable=True))
    op.add_column('tickets', sa.Column('deadline_price', sa.Integer(), nullable=True))
    op.add_column('tickets', sa.Column('event_id', sa.Integer(), nullable=True))
    op.add_column('tickets', sa.Column('ticket_type', sa.String(), nullable=True))
    op.create_foreign_key(None, 'tickets', 'events', ['event_id'], ['id'])
    op.drop_column('tickets', 'price')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('tickets', sa.Column('price', sa.INTEGER(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'tickets', type_='foreignkey')
    op.drop_column('tickets', 'ticket_type')
    op.drop_column('tickets', 'event_id')
    op.drop_column('tickets', 'deadline_price')
    op.drop_column('tickets', 'vip_price')
    op.drop_column('tickets', 'default_price')
    # ### end Alembic commands ###
