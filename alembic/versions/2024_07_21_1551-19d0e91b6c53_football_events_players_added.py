"""football events players added

Revision ID: 19d0e91b6c53
Revises: cc5bc20be543
Create Date: 2024-07-21 15:51:52.475191

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "19d0e91b6c53"
down_revision: Union[str, None] = "cc5bc20be543"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "football_event", sa.Column("assist_tackle_player", sa.Integer(), nullable=True)
    )
    op.add_column(
        "football_event", sa.Column("score_player", sa.Integer(), nullable=True)
    )
    op.add_column(
        "football_event", sa.Column("defence_score_player", sa.Integer(), nullable=True)
    )
    op.add_column(
        "football_event", sa.Column("kickoff_player", sa.Integer(), nullable=True)
    )
    op.add_column(
        "football_event", sa.Column("return_player", sa.Integer(), nullable=True)
    )
    op.add_column(
        "football_event", sa.Column("pat_one_player", sa.Integer(), nullable=True)
    )
    op.add_column(
        "football_event", sa.Column("flagged_player", sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        None, "football_event", "player_match", ["score_player"], ["id"]
    )
    op.create_foreign_key(
        None, "football_event", "player_match", ["kickoff_player"], ["id"]
    )
    op.create_foreign_key(
        None, "football_event", "player_match", ["return_player"], ["id"]
    )
    op.create_foreign_key(
        None, "football_event", "player_match", ["flagged_player"], ["id"]
    )
    op.create_foreign_key(
        None, "football_event", "player_match", ["assist_tackle_player"], ["id"]
    )
    op.create_foreign_key(
        None, "football_event", "player_match", ["pat_one_player"], ["id"]
    )
    op.create_foreign_key(
        None, "football_event", "player_match", ["defence_score_player"], ["id"]
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, "football_event", type_="foreignkey")
    op.drop_constraint(None, "football_event", type_="foreignkey")
    op.drop_constraint(None, "football_event", type_="foreignkey")
    op.drop_constraint(None, "football_event", type_="foreignkey")
    op.drop_constraint(None, "football_event", type_="foreignkey")
    op.drop_constraint(None, "football_event", type_="foreignkey")
    op.drop_constraint(None, "football_event", type_="foreignkey")
    op.drop_column("football_event", "flagged_player")
    op.drop_column("football_event", "pat_one_player")
    op.drop_column("football_event", "return_player")
    op.drop_column("football_event", "kickoff_player")
    op.drop_column("football_event", "defence_score_player")
    op.drop_column("football_event", "score_player")
    op.drop_column("football_event", "assist_tackle_player")
    # ### end Alembic commands ###
