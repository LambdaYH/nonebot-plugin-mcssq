"""init_db

Revision ID: b744ec596cec
Revises: 
Create Date: 2023-02-20 11:03:02.980078

"""
import sqlmodel
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b744ec596cec"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "mc_query_mcservergroup",
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("host", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("port", sa.Integer(), nullable=True),
        sa.Column("sv_type", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.PrimaryKeyConstraint("group_id"),
    )
    op.create_table(
        "mc_query_mcserverprivate",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("host", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("port", sa.Integer(), nullable=True),
        sa.Column("sv_type", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.PrimaryKeyConstraint("user_id"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("mc_query_mcserverprivate")
    op.drop_table("mc_query_mcservergroup")
    # ### end Alembic commands ###
