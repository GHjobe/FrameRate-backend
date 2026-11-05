"""initial schema

Revision ID: 8c4f0bce5234
Revises: 
Create Date: 2026-11-04 23:04:41.058594

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8c4f0bce5234'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('movies',
    sa.Column('tmdb_id', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('year', sa.Integer(), nullable=True),
    sa.Column('runtime', sa.Integer(), nullable=True),
    sa.Column('overview', sa.Text(), nullable=True),
    sa.Column('poster_path', sa.String(length=255), nullable=True),
    sa.Column('backdrop_path', sa.String(length=255), nullable=True),
    sa.Column('genres', sa.JSON(), nullable=False),
    sa.Column('fetched_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('tmdb_id', name=op.f('pk_movies'))
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=20), nullable=False),
    sa.Column('email', sa.String(length=254), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('role', sa.String(length=16), server_default='user', nullable=False),
    sa.Column('email_verified', sa.Boolean(), server_default=sa.text('0'), nullable=False),
    sa.Column('onboarding_completed', sa.Boolean(), server_default=sa.text('0'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint("role IN ('user', 'moderator', 'admin')", name=op.f('ck_users_role_valid')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_users'))
    )
    # Added by hand: Alembic cannot detect expression indexes on SQLite, so autogenerate skipped them.
    # They make usernames and emails unique ignoring case ("Demo" and "demo" are the same).
    op.create_index('uq_users_username_lower', 'users', [sa.text('lower(username)')], unique=True)
    op.create_index('uq_users_email_lower', 'users', [sa.text('lower(email)')], unique=True)
    op.create_table('ratings',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('tmdb_id', sa.Integer(), nullable=False),
    sa.Column('score', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=16), server_default='active', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint("status IN ('active', 'quarantined', 'removed')", name=op.f('ck_ratings_status_valid')),
    sa.CheckConstraint('score BETWEEN 1 AND 5', name=op.f('ck_ratings_score_range')),
    sa.ForeignKeyConstraint(['tmdb_id'], ['movies.tmdb_id'], name=op.f('fk_ratings_tmdb_id_movies'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_ratings_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_ratings')),
    sa.UniqueConstraint('user_id', 'tmdb_id', name='uq_ratings_user_movie')
    )
    with op.batch_alter_table('ratings', schema=None) as batch_op:
        batch_op.create_index('ix_ratings_tmdb_status', ['tmdb_id', 'status'], unique=False)

    op.create_table('user_preferences',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('region', sa.String(length=2), server_default='PH', nullable=False),
    sa.Column('language', sa.String(length=8), server_default='en', nullable=False),
    sa.Column('blur_spoilers', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.Column('genres', sa.JSON(), nullable=False),
    sa.Column('services', sa.JSON(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_user_preferences_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('user_id', name=op.f('pk_user_preferences'))
    )
    op.create_table('watchlist',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('tmdb_id', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=16), server_default='plan', nullable=False),
    sa.Column('added_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint("status IN ('plan', 'watched', 'on_hold', 'dropped')", name=op.f('ck_watchlist_status_valid')),
    sa.ForeignKeyConstraint(['tmdb_id'], ['movies.tmdb_id'], name=op.f('fk_watchlist_tmdb_id_movies'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_watchlist_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('user_id', 'tmdb_id', name=op.f('pk_watchlist'))
    )
    op.create_table('reviews',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('rating_id', sa.Integer(), nullable=False),
    sa.Column('body', sa.Text(), nullable=False),
    sa.Column('contains_spoiler', sa.Boolean(), server_default=sa.text('0'), nullable=False),
    sa.Column('is_hidden', sa.Boolean(), server_default=sa.text('0'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint('length(trim(body)) > 0', name=op.f('ck_reviews_body_not_blank')),
    sa.ForeignKeyConstraint(['rating_id'], ['ratings.id'], name=op.f('fk_reviews_rating_id_ratings'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_reviews')),
    sa.UniqueConstraint('rating_id', name=op.f('uq_reviews_rating_id'))
    )


def downgrade():
    op.drop_table('reviews')
    op.drop_table('watchlist')
    op.drop_table('user_preferences')
    with op.batch_alter_table('ratings', schema=None) as batch_op:
        batch_op.drop_index('ix_ratings_tmdb_status')

    op.drop_table('ratings')
    op.drop_index('uq_users_email_lower', table_name='users')
    op.drop_index('uq_users_username_lower', table_name='users')
    op.drop_table('users')
    op.drop_table('movies')