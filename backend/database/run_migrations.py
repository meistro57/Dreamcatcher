#!/usr/bin/env python3
"""
Database Migration Runner for Dreamcatcher
Runs SQL migrations to update database schema
"""

import os
import sys
import logging
from pathlib import Path
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Add parent directory to path to import modules
sys.path.append(str(Path(__file__).parent.parent))

from database.database import DATABASE_URL
from database.models import Base

logger = logging.getLogger(__name__)

class MigrationRunner:
    """Handles database migrations for Dreamcatcher"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.migrations_dir = Path(__file__).parent / "migrations"
        
    def ensure_migrations_table(self):
        """Create migrations table if it doesn't exist"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        id SERIAL PRIMARY KEY,
                        filename VARCHAR(255) NOT NULL UNIQUE,
                        applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        success BOOLEAN DEFAULT TRUE
                    )
                """))
                conn.commit()
            logger.info("Migrations table ensured")
        except Exception as e:
            logger.error(f"Failed to create migrations table: {e}")
            raise
    
    def get_applied_migrations(self) -> set:
        """Get list of already applied migrations"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT filename FROM schema_migrations WHERE success = TRUE"))
                return {row[0] for row in result.fetchall()}
        except Exception as e:
            logger.error(f"Failed to get applied migrations: {e}")
            return set()
    
    def apply_migration(self, migration_file: Path) -> bool:
        """Apply a single migration file"""
        try:
            logger.info(f"Applying migration: {migration_file.name}")
            
            # Read migration file
            with open(migration_file, 'r') as f:
                migration_sql = f.read()
            
            # Execute migration
            with self.engine.connect() as conn:
                # Split by semicolon and execute each statement
                statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
                
                for statement in statements:
                    if statement:
                        conn.execute(text(statement))
                
                # Record successful migration
                conn.execute(text("""
                    INSERT INTO schema_migrations (filename, applied_at, success)
                    VALUES (:filename, NOW(), TRUE)
                    ON CONFLICT (filename) DO UPDATE SET
                        applied_at = NOW(),
                        success = TRUE
                """), {"filename": migration_file.name})
                
                conn.commit()
            
            logger.info(f"Successfully applied migration: {migration_file.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply migration {migration_file.name}: {e}")
            
            # Record failed migration
            try:
                with self.engine.connect() as conn:
                    conn.execute(text("""
                        INSERT INTO schema_migrations (filename, applied_at, success)
                        VALUES (:filename, NOW(), FALSE)
                        ON CONFLICT (filename) DO UPDATE SET
                            applied_at = NOW(),
                            success = FALSE
                    """), {"filename": migration_file.name})
                    conn.commit()
            except:
                pass
            
            return False
    
    def run_migrations(self, force: bool = False) -> bool:
        """Run all pending migrations"""
        try:
            # Ensure migrations table exists
            self.ensure_migrations_table()
            
            # Get applied migrations
            applied_migrations = self.get_applied_migrations()
            
            # Get all migration files
            migration_files = []
            if self.migrations_dir.exists():
                migration_files = sorted([
                    f for f in self.migrations_dir.glob("*.sql")
                    if f.is_file()
                ])
            
            if not migration_files:
                logger.info("No migration files found")
                return True
            
            # Apply pending migrations
            pending_migrations = [
                f for f in migration_files 
                if f.name not in applied_migrations or force
            ]
            
            if not pending_migrations:
                logger.info("No pending migrations")
                return True
            
            logger.info(f"Found {len(pending_migrations)} pending migrations")
            
            success_count = 0
            for migration_file in pending_migrations:
                if self.apply_migration(migration_file):
                    success_count += 1
                else:
                    logger.error(f"Migration failed: {migration_file.name}")
                    if not force:
                        return False
            
            logger.info(f"Successfully applied {success_count}/{len(pending_migrations)} migrations")
            return success_count == len(pending_migrations)
            
        except Exception as e:
            logger.error(f"Failed to run migrations: {e}")
            return False
    
    def create_tables(self):
        """Create all SQLAlchemy tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Successfully created all tables")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise
    
    def check_database_connection(self) -> bool:
        """Check if database connection is working"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection successful")
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False

def main():
    """Main migration runner"""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Parse arguments
    import argparse
    parser = argparse.ArgumentParser(description='Run database migrations')
    parser.add_argument('--force', action='store_true', help='Force re-run all migrations')
    parser.add_argument('--create-tables', action='store_true', help='Create SQLAlchemy tables')
    parser.add_argument('--check-connection', action='store_true', help='Check database connection')
    args = parser.parse_args()
    
    # Create migration runner
    runner = MigrationRunner(DATABASE_URL)
    
    # Check connection if requested
    if args.check_connection:
        if runner.check_database_connection():
            print("✅ Database connection successful")
            sys.exit(0)
        else:
            print("❌ Database connection failed")
            sys.exit(1)
    
    # Create tables if requested
    if args.create_tables:
        try:
            runner.create_tables()
            print("✅ Tables created successfully")
        except Exception as e:
            print(f"❌ Failed to create tables: {e}")
            sys.exit(1)
    
    # Run migrations
    try:
        if runner.run_migrations(force=args.force):
            print("✅ All migrations completed successfully")
        else:
            print("❌ Some migrations failed")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()