"""empty message

Revision ID: 993cc56e2c67
Revises: 3ae1bcd3f731
Create Date: 2018-11-28 10:03:58.636869

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '993cc56e2c67'
down_revision = '3ae1bcd3f731'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.rename_table('organisation', 'brownfield_site_register')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.rename_table('brownfield_site_register', 'organisation')
    # ### end Alembic commands ###
