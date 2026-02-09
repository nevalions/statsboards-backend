"""stab196_sport_scoreboard_preset_foundation

Revision ID: ed575af6cbb8
Revises: 0d5c8d27b732
Create Date: 2026-02-09 13:56:26.281833

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ed575af6cbb8"
down_revision: Union[str, None] = "0d5c8d27b732"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sport_scoreboard_preset",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("gameclock_max", sa.Integer(), nullable=True, server_default="720"),
        sa.Column("direction", sa.String(length=10), nullable=False, server_default="down"),
        sa.Column(
            "on_stop_behavior",
            sa.String(length=10),
            nullable=False,
            server_default="hold",
        ),
        sa.Column("is_qtr", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_time", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_playclock", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_downdistance", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )

    op.add_column("sport", sa.Column("scoreboard_preset_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_sport_scoreboard_preset_id",
        "sport",
        "sport_scoreboard_preset",
        ["scoreboard_preset_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.add_column(
        "gameclock",
        sa.Column("direction", sa.String(length=10), nullable=False, server_default="down"),
    )
    op.add_column(
        "gameclock",
        sa.Column(
            "on_stop_behavior",
            sa.String(length=10),
            nullable=False,
            server_default="hold",
        ),
    )
    op.add_column(
        "gameclock",
        sa.Column(
            "use_sport_preset",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )

    op.add_column(
        "scoreboard",
        sa.Column(
            "use_sport_preset",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )


def downgrade() -> None:
    op.drop_column("scoreboard", "use_sport_preset")

    op.drop_column("gameclock", "use_sport_preset")
    op.drop_column("gameclock", "on_stop_behavior")
    op.drop_column("gameclock", "direction")

    op.drop_constraint("fk_sport_scoreboard_preset_id", "sport", type_="foreignkey")
    op.drop_column("sport", "scoreboard_preset_id")

    op.drop_table("sport_scoreboard_preset")
