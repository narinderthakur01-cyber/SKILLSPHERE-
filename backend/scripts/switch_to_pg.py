"""
SkillSphere Database Switch Script: SQLite -> PostgreSQL
Activates PostgreSQL credentials in backend/.env after migration and verification have succeeded.
"""

from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
env_path = backend_dir / ".env"

def switch_to_postgresql():
    if not env_path.exists():
        print("ERROR: backend/.env not found.")
        return False

    with open(env_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Extract generated SKILLSPHERE_USER and SKILLSPHERE_USER_PASSWORD
    app_user = "skillsphere_user"
    app_pwd = None
    for line in lines:
        if line.startswith("SKILLSPHERE_USER_PASSWORD="):
            app_pwd = line.split("=", 1)[1].strip()

    if not app_pwd:
        print("ERROR: SKILLSPHERE_USER_PASSWORD not found in backend/.env")
        return False

    new_lines = []
    for line in lines:
        if line.startswith("POSTGRES_USER="):
            new_lines.append(f"POSTGRES_USER={app_user}\n")
        elif line.startswith("POSTGRES_PASSWORD="):
            new_lines.append(f"POSTGRES_PASSWORD={app_pwd}\n")
        else:
            new_lines.append(line)

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    print("✓ Successfully updated backend/.env to target PostgreSQL with dedicated 'skillsphere_user' credentials.")
    return True

if __name__ == "__main__":
    switch_to_postgresql()
