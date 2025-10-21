#!/usr/bin/env python3
"""
Safari Tab Groups Duplicate Remover (macOS Sequoia/Tahoe)
Identifies and removes duplicate Safari tab groups by name.

IMPORTANT: This script modifies Safari's database. 
- Close Safari before running this script
- A backup will be created automatically
- Run at your own risk

Usage:
    python3 safari_tabgroup_dedup.py [--dry-run] [--backup-only]
"""

import sqlite3
import shutil
import os
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import argparse


def get_safari_db_path():
    """Get the path to Safari's tab groups database."""
    home = Path.home()
    db_path = home / "Library" / "Containers" / "com.apple.Safari" / "Data" / "Library" / "Safari" / "SafariTabs.db"
    return db_path


def backup_safari_db(db_path):
    """Create a backup of Safari database."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.parent / f"SafariTabs_Backup_{timestamp}.db"
    
    print(f"Creating backup at: {backup_path}")
    shutil.copy2(db_path, backup_path)
    print(f"✓ Backup created successfully")
    return backup_path


def get_tab_groups(db_path):
    """Fetch all tab groups from the Safari database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # The bookmarks table contains tab groups
    # Tab groups have a specific type and parent relationships
    query = """
    SELECT id, title, parent, type 
    FROM bookmarks 
    WHERE type IN (1, 0)
    ORDER BY id
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    # Get tab counts for each group
    tab_groups = []
    for row in results:
        group_id, title, parent, type_val = row
        
        # Count tabs in this group
        cursor.execute("""
            SELECT COUNT(*) 
            FROM bookmarks 
            WHERE parent = ? AND type = 0
        """, (group_id,))
        
        tab_count = cursor.fetchone()[0]
        
        tab_groups.append({
            'id': group_id,
            'title': title,
            'parent': parent,
            'type': type_val,
            'tab_count': tab_count
        })
    
    conn.close()
    return tab_groups


def find_duplicates(tab_groups):
    """Find duplicate tab groups by title."""
    # Filter to only actual tab groups (not individual tabs)
    # Tab groups typically have parent = None or specific parent ID
    title_to_groups = defaultdict(list)
    
    for group in tab_groups:
        title = group['title']
        if title and group['tab_count'] >= 0:  # Has a title and could contain tabs
            title_to_groups[title].append(group)
    
    # Filter to only duplicates
    duplicates = {title: groups for title, groups in title_to_groups.items() 
                  if len(groups) > 1}
    
    return duplicates


def display_duplicates(duplicates):
    """Display information about duplicate tab groups."""
    if not duplicates:
        print("\n✓ No duplicate tab groups found!")
        return False
    
    print(f"\n⚠️  Found {len(duplicates)} duplicate tab group names:")
    print("=" * 70)
    
    for title, groups in duplicates.items():
        print(f"\n📁 '{title}' ({len(groups)} copies)")
        for group in groups:
            print(f"   - ID {group['id']}: {group['tab_count']} tabs (parent: {group['parent']})")
    
    print("=" * 70)
    return True


def remove_duplicates(db_path, duplicates, keep_strategy='first'):
    """Remove duplicate tab groups from the database.
    
    Args:
        keep_strategy: 'first', 'last', or 'most_tabs'
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    ids_to_remove = set()
    removed_count = 0
    
    for title, groups in duplicates.items():
        if keep_strategy == 'first':
            # Keep first occurrence by ID
            groups_sorted = sorted(groups, key=lambda x: x['id'])
            to_remove = groups_sorted[1:]
        elif keep_strategy == 'last':
            # Keep last occurrence by ID
            groups_sorted = sorted(groups, key=lambda x: x['id'])
            to_remove = groups_sorted[:-1]
        elif keep_strategy == 'most_tabs':
            # Keep the one with most tabs
            groups_sorted = sorted(groups, key=lambda x: x['tab_count'], reverse=True)
            to_remove = groups_sorted[1:]
        
        for group in to_remove:
            group_id = group['id']
            
            # First, delete all tabs that belong to this group
            cursor.execute("DELETE FROM bookmarks WHERE parent = ?", (group_id,))
            
            # Then delete the group itself
            cursor.execute("DELETE FROM bookmarks WHERE id = ?", (group_id,))
            
            print(f"✓ Removed: '{group['title']}' (ID: {group_id}, had {group['tab_count']} tabs)")
            removed_count += 1
    
    conn.commit()
    conn.close()
    
    return removed_count


def main():
    parser = argparse.ArgumentParser(
        description="Remove duplicate Safari tab groups"
    )
    parser.add_argument(
        '--dry-run', 
        action='store_true',
        help='Show what would be removed without actually removing'
    )
    parser.add_argument(
        '--backup-only',
        action='store_true',
        help='Only create a backup, do not remove duplicates'
    )
    parser.add_argument(
        '--keep',
        choices=['first', 'last', 'most_tabs'],
        default='first',
        help='Which duplicate to keep (default: first)'
    )
    
    args = parser.parse_args()
    
    print("Safari Tab Groups Duplicate Remover")
    print("=" * 70)
    
    # Find the database file
    db_path = get_safari_db_path()
    
    if not db_path.exists():
        print(f"❌ Could not find Safari database at: {db_path}")
        print("\nPlease verify:")
        print("1. You're running macOS Sequoia/Tahoe or later")
        print("2. Safari has been opened at least once")
        print("3. You have tab groups created in Safari")
        return 1
    
    print(f"Found Safari database: {db_path}")
    
    # Create backup
    backup_path = backup_safari_db(db_path)
    
    if args.backup_only:
        print("\n✓ Backup created. Exiting (--backup-only mode)")
        return 0
    
    # Load tab groups
    try:
        tab_groups = get_tab_groups(db_path)
        print(f"Found {len(tab_groups)} total bookmark entries")
    except Exception as e:
        print(f"❌ Error reading database: {e}")
        return 1
    
    # Find duplicates
    duplicates = find_duplicates(tab_groups)
    has_duplicates = display_duplicates(duplicates)
    
    if not has_duplicates:
        return 0
    
    if args.dry_run:
        print("\n🔍 Dry run mode - no changes will be made")
        print(f"Would remove duplicates, keeping '{args.keep}' occurrence of each")
        return 0
    
    # Confirm before removing
    print(f"\nThis will keep the '{args.keep}' occurrence of each duplicate.")
    print("⚠️  WARNING: Safari MUST be closed before proceeding!")
    response = input("Proceed with removal? (yes/no): ").strip().lower()
    
    if response != 'yes':
        print("❌ Cancelled by user")
        return 0
    
    # Remove duplicates
    try:
        removed_count = remove_duplicates(db_path, duplicates, args.keep)
        print(f"\n✓ Successfully removed {removed_count} duplicate tab groups")
        print(f"✓ Backup saved at: {backup_path}")
        print("\n⚠️  Restart Safari to see the changes")
    except Exception as e:
        print(f"❌ Error removing duplicates: {e}")
        print(f"Your backup is safe at: {backup_path}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
