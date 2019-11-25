"""empty message

Revision ID: 4090f61222e6
Revises: 
Create Date: 2019-11-19 14:28:10.006500

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '4090f61222e6'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('validation_report',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('raw_result', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('original_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('validated_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('errors_by_column', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('errors_by_row', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('additional_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('validation_report')
    # ### end Alembic commands ###