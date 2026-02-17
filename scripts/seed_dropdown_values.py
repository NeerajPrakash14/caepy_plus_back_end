#!/usr/bin/env python3
"""Script to seed initial dropdown values into the database.

Usage:
    python scripts/seed_dropdown_values.py
    python scripts/seed_dropdown_values.py --force  # Re-seed even if data exists
"""
from __future__ import annotations

import asyncio
import argparse
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.db.session import DatabaseManager
from app.services.dropdown_option_service import DropdownOptionService, INITIAL_DROPDOWN_VALUES

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def seed_dropdown_values(force: bool = False) -> None:
    """Seed initial dropdown values into the database."""
    
    logger.info("=" * 60)
    logger.info("Dropdown Values Seeder")
    logger.info("=" * 60)
    
    # Show what will be seeded
    total_values = sum(len(values) for values in INITIAL_DROPDOWN_VALUES.values())
    logger.info(f"Initial data contains {len(INITIAL_DROPDOWN_VALUES)} fields with {total_values} total values")
    
    for field_name, values in INITIAL_DROPDOWN_VALUES.items():
        logger.info(f"  - {field_name}: {len(values)} values")
    
    logger.info("-" * 60)
    
    # Create database manager and session
    db_manager = DatabaseManager()
    async with db_manager.session() as session:
        service = DropdownOptionService(session)
        
        try:
            results = await service.seed_initial_values(force=force)
            
            if not results:
                logger.info("No values were seeded (table already has data).")
                logger.info("Use --force to re-seed.")
                return
            
            logger.info("-" * 60)
            logger.info("Seeding Results:")
            
            for field_name, count in results.items():
                logger.info(f"  - {field_name}: {count} values created")
            
            total_created = sum(results.values())
            logger.info("-" * 60)
            logger.info(f"Total: {total_created} values seeded successfully!")
            
            await session.commit()
            
        except Exception as e:
            logger.error(f"Error seeding dropdown values: {e}")
            await session.rollback()
            raise
    
    await db_manager.close()
    
    logger.info("=" * 60)
    logger.info("Seeding complete!")
    logger.info("=" * 60)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Seed initial dropdown values into the database."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-seed even if data already exists",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be seeded without actually seeding",
    )
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("\n=== DRY RUN - Showing values that would be seeded ===\n")
        total = 0
        for field_name, values in INITIAL_DROPDOWN_VALUES.items():
            print(f"\n{field_name} ({len(values)} values):")
            for value in values[:5]:  # Show first 5
                print(f"  - {value}")
            if len(values) > 5:
                print(f"  ... and {len(values) - 5} more")
            total += len(values)
        print(f"\n=== Total: {total} values across {len(INITIAL_DROPDOWN_VALUES)} fields ===\n")
        return
    
    asyncio.run(seed_dropdown_values(force=args.force))


if __name__ == "__main__":
    main()
