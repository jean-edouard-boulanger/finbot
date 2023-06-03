"""add password_hash column

Revision ID: bbce6d728c64
Revises: de2430bc2abe
Create Date: 2023-06-03 09:52:40.275046

"""
from alembic import op
from sqlalchemy import orm, text

import bcrypt

from finbot.core import environment, secure


# revision identifiers, used by Alembic.
revision = 'bbce6d728c64'
down_revision = 'de2430bc2abe'
branch_labels = None
depends_on = None


def get_users_clear_passwords(session: orm.Session) -> dict[int, str]:
    user_id_to_password: dict[int, str] = {}
    fernet_key = environment.get_secret_key()
    for row in session.execute(text("SELECT id, encrypted_password FROM finbot_user_accounts")):
        user_id_to_password[row[0]] = secure.fernet_decrypt(row[1], fernet_key.encode()).decode()
    return user_id_to_password


def upgrade():
    bind = op.get_bind()
    session = orm.Session(bind=bind)
    op.execute("""
        ALTER TABLE finbot_user_accounts
        ADD password_hash BYTEA
    """)
    session.commit()
    users_clear_passwords = get_users_clear_passwords(session)
    for user_id, clear_password in users_clear_passwords.items():
        password_hash = bcrypt.hashpw(clear_password.encode(), bcrypt.gensalt())
        session.execute(text("""
            UPDATE finbot_user_accounts
               SET password_hash = :password_hash,
                   updated_at = now()
             WHERE id = :user_account_id
        """), {"password_hash": password_hash, "user_account_id": user_id})
        session.commit()
    op.execute("""
        ALTER TABLE finbot_user_accounts
        DROP COLUMN encrypted_password
    """)
    op.execute("""
        ALTER TABLE finbot_user_accounts
        ALTER COLUMN password_hash SET NOT NULL
    """)
    session.commit()


def downgrade():
    op.execute("""
        ALTER TABLE finbot_user_accounts
        DROP COLUMN IF EXISTS password_hash
    """)
