"""photo_url nullable false

Revision ID: 7401ccdf6283
Revises: b53dd2a64b99
Create Date: 2024-03-11 02:26:47.840881

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7401ccdf6283'
down_revision: Union[str, None] = 'b53dd2a64b99'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('tickets', 'photo_url',
               existing_type=sa.VARCHAR(),
               nullable=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('tickets', 'photo_url',
               existing_type=sa.VARCHAR(),
               nullable=True)
    # ### end Alembic commands ###
