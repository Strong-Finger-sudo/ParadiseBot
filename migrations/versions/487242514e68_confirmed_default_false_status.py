"""confirmed default false status

Revision ID: 487242514e68
Revises: 76de164d04f6
Create Date: 2024-03-02 00:47:46.341025

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '487242514e68'
down_revision: Union[str, None] = '76de164d04f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('tickets', 'passed',
               existing_type=sa.BOOLEAN(),
               nullable=False)
    op.alter_column('tickets', 'confirmed',
               existing_type=sa.BOOLEAN(),
               nullable=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('tickets', 'confirmed',
               existing_type=sa.BOOLEAN(),
               nullable=True)
    op.alter_column('tickets', 'passed',
               existing_type=sa.BOOLEAN(),
               nullable=True)
    # ### end Alembic commands ###