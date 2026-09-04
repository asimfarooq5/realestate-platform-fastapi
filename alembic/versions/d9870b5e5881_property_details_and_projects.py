"""property details (subtype/features/drafts/installments) and projects table

Revision ID: d9870b5e5881
Revises: 57b84c6800cf
Create Date: 2026-09-04 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd9870b5e5881'
down_revision: Union[str, None] = '57b84c6800cf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('properties', sa.Column('subtype', sa.String(), nullable=True))
    op.add_column('properties', sa.Column('installments_available', sa.Boolean(), nullable=True))
    op.add_column('properties', sa.Column('is_draft', sa.Boolean(), nullable=True))
    op.add_column('properties', sa.Column('features', sa.Text(), nullable=True))

    op.create_table('projects',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('slug', sa.String(), nullable=False),
        sa.Column('developer', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('cover_image', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('price_starting', sa.Float(), nullable=True),
        sa.Column('city_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.ForeignKeyConstraint(['city_id'], ['cities.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug'),
    )
    op.create_index(op.f('ix_projects_id'), 'projects', ['id'], unique=False)

    # A duplicate favorite (same user + property) is possible today at the DB
    # level; close that gap. batch_alter_table so this also works on SQLite (dev).
    with op.batch_alter_table('favorites') as batch_op:
        batch_op.create_unique_constraint('uq_favorites_user_property', ['user_id', 'property_id'])


def downgrade() -> None:
    with op.batch_alter_table('favorites') as batch_op:
        batch_op.drop_constraint('uq_favorites_user_property', type_='unique')
    op.drop_index(op.f('ix_projects_id'), table_name='projects')
    op.drop_table('projects')
    op.drop_column('properties', 'features')
    op.drop_column('properties', 'is_draft')
    op.drop_column('properties', 'installments_available')
    op.drop_column('properties', 'subtype')
