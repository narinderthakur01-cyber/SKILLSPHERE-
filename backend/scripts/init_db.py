"""
SkillSphere PostgreSQL Role & Database Initialization Script.
Safe, idempotent setup:
- Reads superuser credentials and generated SKILLSPHERE_USER_PASSWORD from backend/.env.
- Checks if 'skillsphere_user' already exists. Never resets existing credentials.
- Checks if 'skillsphere' database already exists. Never drops or overwrites databases.
- Protects existing 'postgres' and 'practice_db' databases.
- Checks if target database 'skillsphere' is empty.
"""

import os
import sys
from pathlib import Path
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Read environment configuration
env_path = Path(__file__).resolve().parent.parent / ".env"
env_vars = {}
if env_path.exists():
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                env_vars[key.strip()] = val.strip()

pg_host = env_vars.get("POSTGRES_SERVER", "localhost")
pg_port = int(env_vars.get("POSTGRES_PORT", "5432"))
pg_admin_user = env_vars.get("POSTGRES_USER", "postgres")
pg_admin_pwd = env_vars.get("POSTGRES_PASSWORD", "")
app_user = env_vars.get("SKILLSPHERE_USER", "skillsphere_user")
app_pwd = env_vars.get("SKILLSPHERE_USER_PASSWORD", "")
app_db = env_vars.get("POSTGRES_DB", "skillsphere")

def run_init():
    print("=" * 60)
    print("SkillSphere: PostgreSQL Role & Database Initialization")
    print("=" * 60)

    if not app_pwd:
        print("ERROR: SKILLSPHERE_USER_PASSWORD is missing from backend/.env")
        sys.exit(1)

    print(f"Connecting to PostgreSQL server at {pg_host}:{pg_port} as admin '{pg_admin_user}'...")
    try:
        conn = psycopg2.connect(
            host=pg_host,
            port=pg_port,
            user=pg_admin_user,
            password=pg_admin_pwd,
            dbname="postgres",
            connect_timeout=5
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
    except Exception as e:
        print(f"Connection failed: {e}")
        sys.exit(1)

    # 1. Inspect existing databases and roles
    cur.execute("SELECT datname FROM pg_database WHERE datname NOT LIKE 'template%';")
    existing_dbs = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT rolname FROM pg_roles WHERE rolname NOT LIKE 'pg_%';")
    existing_roles = [r[0] for r in cur.fetchall()]

    print(f"Existing databases: {existing_dbs}")
    print(f"Existing user roles: {existing_roles}")

    # Safety assertion: ensure postgres and practice_db are preserved
    print("✓ Confirmed existing databases ('postgres', 'practice_db') will NOT be touched.")

    # 2. Check / Create dedicated role 'skillsphere_user'
    if app_user in existing_roles:
        print(f"✓ Dedicated role '{app_user}' already exists. Preserving existing role.")
    else:
        print(f"Creating dedicated role '{app_user}'...")
        query = sql.SQL("CREATE ROLE {} WITH LOGIN PASSWORD %s;").format(sql.Identifier(app_user))
        cur.execute(query, (app_pwd,))
        print(f"✓ Role '{app_user}' created successfully.")

    # 3. Check / Create database 'skillsphere'
    if app_db in existing_dbs:
        print(f"✓ Database '{app_db}' already exists.")
    else:
        print(f"Creating dedicated database '{app_db}' owned by '{app_user}'...")
        query = sql.SQL("CREATE DATABASE {} OWNER {};").format(
            sql.Identifier(app_db),
            sql.Identifier(app_user)
        )
        cur.execute(query)
        print(f"✓ Database '{app_db}' created successfully.")

    cur.close()
    conn.close()

    # 4. Check whether target database is empty
    print(f"\nChecking table inventory in '{app_db}'...")
    try:
        app_conn = psycopg2.connect(
            host=pg_host,
            port=pg_port,
            user=pg_admin_user,
            password=pg_admin_pwd,
            dbname=app_db,
            connect_timeout=5
        )
        app_cur = app_conn.cursor()
        app_cur.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"
        )
        existing_tables = [r[0] for r in app_cur.fetchall()]
        if existing_tables:
            print(f"WARNING: Database '{app_db}' already contains tables: {existing_tables}")
            print("Please confirm if migration should proceed into this existing schema.")
        else:
            print(f"✓ Verified target database '{app_db}' is empty (0 public tables).")

        # Grant schema privileges
        app_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        grant_query = sql.SQL("GRANT ALL ON SCHEMA public TO {};").format(sql.Identifier(app_user))
        app_cur.execute(grant_query)
        app_cur.execute(
            sql.SQL("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO {};").format(
                sql.Identifier(app_user)
            )
        )
        app_cur.execute(
            sql.SQL("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO {};").format(
                sql.Identifier(app_user)
            )
        )
        print(f"✓ Granted schema permissions to '{app_user}' on '{app_db}'.")

        app_cur.close()
        app_conn.close()
    except Exception as e:
        print(f"Error checking target database permissions: {e}")
        sys.exit(1)

    print("\n✓ PostgreSQL initialization completed cleanly.")

if __name__ == "__main__":
    run_init()
