"""empty message

Revision ID: b6b5e20b072d
Revises: 0da56ff9e390
Create Date: 2018-12-17 16:20:03.098667

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b6b5e20b072d'
down_revision = '0da56ff9e390'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('static_content')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('static_content',
    sa.Column('filename', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('content', sa.TEXT(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('filename', name='static_content_pkey')
    )
    # ### end Alembic commands ###