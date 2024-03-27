"""staff_db staff_username update

Revision ID: e60cbfe3fac7
Revises: 2efbca801ba0
Create Date: 2024-03-27 18:32:41.899504

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e60cbfe3fac7'
down_revision: Union[str, None] = '2efbca801ba0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('staff', 'staff_username',
               existing_type=sa.BIGINT(),
               type_=sa.String(),
               existing_nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('staff', 'staff_username',
               existing_type=sa.String(),
               type_=sa.BIGINT(),
               existing_nullable=True)
    # ### end Alembic commands ###