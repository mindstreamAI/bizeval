from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func

revision = 'add_settings_1765572489'
down_revision = '714db47f17f6'

def upgrade():
    op.create_table('settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(100), nullable=False),
        sa.Column('value', sa.Text()),
        sa.Column('updated_at', sa.DateTime(), server_default=func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key')
    )

def downgrade():
    op.drop_table('settings')
