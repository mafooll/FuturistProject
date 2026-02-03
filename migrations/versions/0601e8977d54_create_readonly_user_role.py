"""create_readonly_user_role

Revision ID: 0601e8977d54
Revises: c95f7799a9e1
Create Date: 2026-02-03 16:43:53.840315

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0601e8977d54'
down_revision: Union[str, Sequence[str], None] = 'c95f7799a9e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    from src.core.settings import PostgresSettingsRO

    ro_database = PostgresSettingsRO()

    op.execute(
        f"""
        DO $$
        BEGIN
          IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'readonly_user') THEN
            CREATE ROLE readonly_user
              LOGIN
              PASSWORD '{ro_database.password_ro.get_secret_value()}'
              NOSUPERUSER
              NOCREATEDB
              NOCREATEROLE
              NOINHERIT;
          END IF;
        END
        $$;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
          EXECUTE format(
            'GRANT CONNECT ON DATABASE %I TO readonly_user',
            current_database()
          );
        END
        $$;
        """
    )

    op.execute("GRANT USAGE ON SCHEMA public TO readonly_user")

    op.execute(
        "GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user"  # black, не форматируй!
    )
    op.execute(
        "GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO readonly_user"
    )

    # на всякий случай
    op.execute(
        "REVOKE INSERT, UPDATE, DELETE, TRUNCATE "
        "ON ALL TABLES IN SCHEMA public FROM readonly_user"
    )
    op.execute("REVOKE CREATE ON SCHEMA public FROM readonly_user")


def downgrade() -> None:
    """Downgrade schema."""

    op.execute(
        "REVOKE SELECT ON ALL TABLES IN SCHEMA public FROM readonly_user"
    )
    op.execute(
        "REVOKE SELECT ON ALL SEQUENCES IN SCHEMA public FROM readonly_user"
    )
    op.execute("REVOKE USAGE ON SCHEMA public FROM readonly_user")

    op.execute(
        """
        DO $$
        BEGIN
          EXECUTE format(
            'REVOKE CONNECT ON DATABASE %I FROM readonly_user',
            current_database()
          );
        END
        $$;
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'readonly_user') THEN
            DROP ROLE readonly_user;
          END IF;
        END
        $$;
        """
    )
