"""empty message

Revision ID: 026ec67033ac
Revises: 
Create Date: 2019-11-22 10:50:44.067872

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '026ec67033ac'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('result_model',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('result', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('upload', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('rows', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('errors_by_column', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('errors_by_row', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('meta_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('result_model')
    # ### end Alembic commands ###
