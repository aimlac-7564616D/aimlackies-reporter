"""empty message

Revision ID: 9d29fab6fa31
Revises: 034f0f1632fc
Create Date: 2021-09-20 21:32:56.207451

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '9d29fab6fa31'
down_revision = '034f0f1632fc'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('trading', sa.Column('date_time', sa.DateTime(), nullable=False))
    op.create_unique_constraint(None, 'trading', ['date_time', 'Period'])
    op.drop_column('trading', 'Date, time')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('trading', sa.Column('Date, time', mysql.DATETIME(), nullable=False))
    op.drop_constraint(None, 'trading', type_='unique')
    op.drop_column('trading', 'date_time')
    # ### end Alembic commands ###
