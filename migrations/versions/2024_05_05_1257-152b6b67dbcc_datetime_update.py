"""DateTime update

Revision ID: 152b6b67dbcc
Revises: bcc0784141e0
Create Date: 2024-05-05 12:57:49.341760

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '152b6b67dbcc'
down_revision: Union[str, None] = 'bcc0784141e0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('events', sa.Column('new_event_date', sa.Date))

    # Заполняем новый столбец значениями из существующего столбца
    op.execute("UPDATE events SET new_event_date = event_date::date")

    # Удаляем существующий столбец
    op.drop_column('events', 'event_date')

    # Переименовываем новый столбец
    op.alter_column('events', 'new_event_date', new_column_name='event_date')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('tickets', 'date',
               existing_type=sa.DateTime(),
               type_=sa.VARCHAR(),
               existing_nullable=False)
    op.alter_column('events', 'event_date',
               existing_type=sa.Date(),
               type_=sa.VARCHAR(),
               existing_nullable=True)
    # ### end Alembic commands ###
