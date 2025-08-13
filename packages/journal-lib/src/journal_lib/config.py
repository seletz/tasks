"""
Configuration management for journal_lib.

This module provides centralized configuration management for the journal_lib package,
allowing users to customize behavior through environment variables while providing
sensible defaults. All configuration is handled through the JournalConfig class,
which supports customization of paths, repositories, GitHub organizations, and user settings.

Example usage:
    from journal_lib.config import config

    # Access configured values
    notes_path = config.notes_dir
    repo = config.default_repo
    orgs = config.github_orgs

Environment variables:
    JOURNAL_NOTES_DIR: Directory containing daily notes (default: ~/notes)
    JOURNAL_DEFAULT_REPO: Default GitHub repository in owner/repo format
    JOURNAL_GITHUB_ORGS: Comma-separated list of GitHub organizations to search
    JOURNAL_GITHUB_USER: GitHub username or '@me' for authenticated user
"""

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class JournalConfig:
    """
    Configuration class for journal_lib package.

    This class manages all configuration options through environment variables
    with sensible defaults, making the library portable across different
    environments and users.
    """

    notes_dir: Path = field(
        default_factory=lambda: Path(os.getenv("JOURNAL_NOTES_DIR", str(Path.home() / "notes")))
    )
    default_repo: str = field(default_factory=lambda: os.getenv("JOURNAL_DEFAULT_REPO", ""))
    github_orgs: list[str] = field(
        default_factory=lambda: os.getenv("JOURNAL_GITHUB_ORGS", "digitalgedacht,nexiles").split(
            ","
        )
    )
    github_user: str = field(default_factory=lambda: os.getenv("JOURNAL_GITHUB_USER", "@me"))

    def __post_init__(self):
        """Validate configuration after initialization."""
        # Ensure notes_dir is a Path object
        if isinstance(self.notes_dir, str):
            self.notes_dir = Path(self.notes_dir)

        # Clean up org list (remove empty strings and whitespace)
        self.github_orgs = [org.strip() for org in self.github_orgs if org.strip()]

        # If no default_repo is set, try to detect it from current directory
        if not self.default_repo:
            self.default_repo = self._detect_default_repo()

    def _detect_default_repo(self) -> str:
        """
        Attempt to detect default repository from current git repository.

        :return: Repository name in owner/repo format or empty string if not detected
        :rtype: str
        """
        try:
            import subprocess

            # Security: Validate current directory is safe
            cwd = Path.cwd()
            if not cwd.is_dir():
                return ""

            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True,
                text=True,
                check=True,
                cwd=cwd,
                timeout=10,  # Security: Add timeout
            )

            # Parse git URL to extract owner/repo
            url = result.stdout.strip()

            # Handle both SSH and HTTPS URLs
            if url.startswith("git@github.com:"):
                # SSH format: git@github.com:owner/repo.git
                repo_part = url.replace("git@github.com:", "").replace(".git", "")
            elif "github.com" in url:
                # HTTPS format: https://github.com/owner/repo.git
                repo_part = url.split("github.com/")[-1].replace(".git", "")
            else:
                return ""

            # Validate format
            if "/" in repo_part and len(repo_part.split("/")) == 2:
                return repo_part

        except (subprocess.CalledProcessError, FileNotFoundError, IndexError):
            pass

        return ""

    def get_daily_note_path(self, date: str | None = None) -> Path:
        """Get file system path to daily note file for specified date.

        Args:
            date: Date in YYYY-MM-DD format, defaults to today if None

        Returns:
            Path object pointing to daily note file
        """
        import re
        from datetime import datetime

        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        # Security: Validate date format to prevent path traversal
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
            raise ValueError("Invalid date format. Expected YYYY-MM-DD")

        # Additional validation of date value
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError as e:
            raise ValueError("Invalid date value") from e

        return self.notes_dir / "daily" / f"{date}.md"


# Global configuration instance
config = JournalConfig()
