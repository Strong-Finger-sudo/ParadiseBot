"""confirmed default have no status

Revision ID: 3a3712ce9665
Revises: 487242514e68
Create Date: 2024-03-02 03:49:20.433750

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3a3712ce9665'
down_revision: Union[str, None] = '487242514e68'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('tickets', 'confirmed',
               existing_type=sa.BOOLEAN(),
               nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('tickets', 'confirmed',
               existing_type=sa.BOOLEAN(),
               nullable=False)
    # ### end Alembic commands ###