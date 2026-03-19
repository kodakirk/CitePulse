#!/usr/bin/env python3
"""
CitePulse Management CLI

Standalone admin tool for database maintenance without restarting the stack.

Usage (from inside the api container):
    python -m backend.manage <command>

Commands:
    create-tables    Create all database tables
    drop-tables      Drop all database tables (DESTRUCTIVE)
    reset-db         Drop and recreate all tables (DESTRUCTIVE)
    list-users       List all registered users
    delete-user      Delete a user by email
    promote-user     Grant superuser to a user by email
    user-stats       Show per-user analysis counts
    reset-quotas     Reset all users' monthly analysis counters
    db-info          Show table names and row counts
"""
import asyncio
import sys
import os

# Ensure .env is loaded when running standalone
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import AsyncSession

from .database import engine, async_session_maker, Base, create_db_and_tables
from .db_models import User, Analysis


async def create_tables():
    """Create all tables (safe to run repeatedly — skips existing)."""
    await create_db_and_tables()
    print("[OK] All tables created.")


async def drop_tables():
    """Drop all tables. DESTRUCTIVE."""
    confirm = input("This will DELETE all data. Type 'yes' to confirm: ")
    if confirm.strip().lower() != "yes":
        print("[ABORT] No changes made.")
        return
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    print("[OK] All tables dropped.")


async def reset_db():
    """Drop and recreate all tables. DESTRUCTIVE."""
    confirm = input("This will DELETE all data and recreate tables. Type 'yes' to confirm: ")
    if confirm.strip().lower() != "yes":
        print("[ABORT] No changes made.")
        return
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await create_db_and_tables()
    print("[OK] Database reset complete.")


async def list_users():
    """Print all registered users."""
    async with async_session_maker() as session:
        result = await session.execute(text(
            "SELECT id, email, full_name, is_active, is_superuser, created_at "
            "FROM users ORDER BY id"
        ))
        rows = result.fetchall()
        if not rows:
            print("No users found.")
            return
        print(f"{'ID':<6} {'Email':<35} {'Name':<20} {'Active':<8} {'Admin':<7} {'Created'}")
        print("-" * 110)
        for r in rows:
            print(f"{r[0]:<6} {r[1]:<35} {str(r[2] or ''):<20} {str(r[3]):<8} {str(r[4]):<7} {r[5]}")


async def delete_user():
    """Delete a user by email (cascades to their analyses)."""
    if len(sys.argv) < 3:
        print("Usage: python -m backend.manage delete-user <email>")
        return
    email = sys.argv[2]
    async with async_session_maker() as session:
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            print(f"[ERROR] No user found with email: {email}")
            return
        confirm = input(f"Delete user '{email}' and all their analyses? Type 'yes': ")
        if confirm.strip().lower() != "yes":
            print("[ABORT] No changes made.")
            return
        await session.delete(user)
        await session.commit()
        print(f"[OK] Deleted user: {email}")


async def promote_user():
    """Grant superuser privileges to a user by email."""
    if len(sys.argv) < 3:
        print("Usage: python -m backend.manage promote-user <email>")
        return
    email = sys.argv[2]
    async with async_session_maker() as session:
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            print(f"[ERROR] No user found with email: {email}")
            return
        user.is_superuser = True
        await session.commit()
        print(f"[OK] {email} is now a superuser.")


async def user_stats():
    """Show analysis counts per user."""
    async with async_session_maker() as session:
        result = await session.execute(text(
            "SELECT u.email, u.current_month_analyses, COUNT(a.id) AS total_analyses "
            "FROM users u LEFT JOIN analyses a ON u.id = a.user_id "
            "GROUP BY u.id, u.email, u.current_month_analyses "
            "ORDER BY total_analyses DESC"
        ))
        rows = result.fetchall()
        if not rows:
            print("No users found.")
            return
        print(f"{'Email':<35} {'This Month':<12} {'All Time'}")
        print("-" * 60)
        for r in rows:
            print(f"{r[0]:<35} {r[1]:<12} {r[2]}")


async def reset_quotas():
    """Reset monthly analysis counters for all users."""
    confirm = input("Reset all users' monthly quotas to 0? Type 'yes': ")
    if confirm.strip().lower() != "yes":
        print("[ABORT] No changes made.")
        return
    async with async_session_maker() as session:
        await session.execute(text(
            "UPDATE users SET current_month_analyses = 0, last_reset_date = NOW()"
        ))
        await session.commit()
    print("[OK] All monthly quotas reset.")


async def db_info():
    """Show table names and row counts."""
    async with engine.connect() as conn:
        def _get_tables(connection):
            insp = inspect(connection)
            return insp.get_table_names()

        tables = await conn.run_sync(_get_tables)
        if not tables:
            print("No tables found. Run 'create-tables' first.")
            return
        print(f"{'Table':<30} {'Rows'}")
        print("-" * 45)
        for table in sorted(tables):
            result = await conn.execute(text(f"SELECT COUNT(*) FROM \"{table}\""))
            count = result.scalar()
            print(f"{table:<30} {count}")


COMMANDS = {
    "create-tables": create_tables,
    "drop-tables": drop_tables,
    "reset-db": reset_db,
    "list-users": list_users,
    "delete-user": delete_user,
    "promote-user": promote_user,
    "user-stats": user_stats,
    "reset-quotas": reset_quotas,
    "db-info": db_info,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        print("Available commands:")
        for name in COMMANDS:
            print(f"  {name:<18} {COMMANDS[name].__doc__}")
        sys.exit(1)

    asyncio.run(COMMANDS[sys.argv[1]]())


if __name__ == "__main__":
    main()
