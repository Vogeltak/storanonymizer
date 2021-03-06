"""empty message

Revision ID: 4b431588e321
Revises: 
Create Date: 2021-05-18 23:21:15.973402

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4b431588e321'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('contribution', sa.Column('submission_datetime', sa.DateTime(), nullable=True))
    op.add_column('round', sa.Column('init_datetime', sa.DateTime(), nullable=True))
    op.add_column('round', sa.Column('publish_datetime', sa.DateTime(), nullable=True))
    op.add_column('round', sa.Column('vote_datetime', sa.DateTime(), nullable=True))
    op.add_column('vote', sa.Column('bonus_type', sa.Enum('NONE', 'ORIGINALITY', 'STYLE', name='bonus'), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('vote', 'bonus_type')
    op.drop_column('round', 'vote_datetime')
    op.drop_column('round', 'publish_datetime')
    op.drop_column('round', 'init_datetime')
    op.drop_column('contribution', 'submission_datetime')
    # ### end Alembic commands ###
