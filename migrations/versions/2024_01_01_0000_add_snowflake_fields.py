"""add snowflake fields

Revision ID: add_snowflake_fields
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'add_snowflake_fields'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create table if it doesn't exist (for fresh installations)
    # This migration handles both creating the table and adding new fields
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_exists = 'shorturl' in inspector.get_table_names()
    
    if not table_exists:
        # Create the full table structure
        op.create_table(
            'shorturl',
            sa.Column('snowflake_id', sa.BigInteger(), nullable=False),
            sa.Column('original_url', sa.String(), nullable=False),
            sa.Column('short_code', sa.String(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('snowflake_id')
        )
        # Create indexes
        op.create_index(op.f('ix_shorturl_short_code'), 'shorturl', ['short_code'], unique=True)
    else:
        # Table exists - check what columns exist
        columns = [col['name'] for col in inspector.get_columns('shorturl')]
        has_id_column = 'id' in columns
        has_snowflake_column = 'snowflake_id' in columns
        
        if has_id_column and not has_snowflake_column:
            # Old schema with id - migrate to snowflake_id as primary key
            # Note: This assumes you'll backfill snowflake_id values before running migration
            # For existing data, you need to generate Snowflake IDs for existing records first
            
            # Add snowflake_id column (temporarily nullable for backfill)
            op.add_column('shorturl', sa.Column('snowflake_id', sa.BigInteger(), nullable=True))
            
            # TODO: Backfill snowflake_id for existing records
            # You need to generate actual Snowflake IDs here, not just copy id values
            # Example: op.execute("UPDATE shorturl SET snowflake_id = <generated_snowflake_id> WHERE snowflake_id IS NULL")
            
            # After backfill, make it not null
            op.alter_column('shorturl', 'snowflake_id', nullable=False)
            
            # Drop old primary key
            op.drop_constraint('shorturl_pkey', 'shorturl', type_='primary')
            
            # Create new primary key on snowflake_id
            op.create_primary_key('shorturl_pkey', 'shorturl', ['snowflake_id'])
            
            # Drop old id column
            op.drop_column('shorturl', 'id')
        
        elif not has_snowflake_column:
            # No snowflake_id - add it as primary key
            op.add_column('shorturl', sa.Column('snowflake_id', sa.BigInteger(), nullable=False))
            if has_id_column:
                op.drop_constraint('shorturl_pkey', 'shorturl', type_='primary')
                op.drop_column('shorturl', 'id')
            op.create_primary_key('shorturl_pkey', 'shorturl', ['snowflake_id'])
        
        # Create index on short_code if it doesn't exist
        indexes = [idx['name'] for idx in inspector.get_indexes('shorturl')]
        if 'ix_shorturl_short_code' not in indexes:
            op.create_index(op.f('ix_shorturl_short_code'), 'shorturl', ['short_code'], unique=True)


def downgrade() -> None:
    # Drop indexes
    try:
        op.drop_index(op.f('ix_shorturl_short_code'), table_name='shorturl')
    except Exception:
        pass
    
    # For downgrade, we'd need to restore id column and make it primary key
    # This is complex and depends on whether you want to keep data
    # For now, we'll just note that downgrade would require manual intervention
    # to restore the old schema with id as primary key

