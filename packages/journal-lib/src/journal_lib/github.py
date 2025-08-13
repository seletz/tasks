"""GitHub integration for daily journal automation."""

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import config

# Section headers for daily review
SECTION_ISSUES_CREATED = "**Heute erstellte Issues:**"
SECTION_PRS_CREATED = "**Heute erstellte PRs:**"
SECTION_ISSUES_CLOSED = "**Heute geschlossene Issues:**"
SECTION_ISSUES_WORKED = "**Heute bearbeitet:**"
SECTION_PRS_MERGED = "**Heute gemergte PRs:**"


def run_gh_command(cmd: list[str], single: bool = False) -> list[dict[str, Any]] | dict[str, Any]:
    """
    Run GitHub CLI command and return JSON result.

    :param cmd: Command arguments to pass to the gh CLI
    :type cmd: list[str]
    :param single: If True, return single dict; if False, return list
    :type single: bool
    :return: JSON response parsed as list or dictionary, empty result on error
    :rtype: list[dict[str, Any]] | dict[str, Any]
    """
    # Security: Validate command structure
    if not cmd or cmd[0] != "gh":
        raise ValueError("Only GitHub CLI commands are allowed")

    allowed_commands = ["issue", "pr", "repo", "auth"]
    if len(cmd) < 2 or cmd[1] not in allowed_commands:
        raise ValueError(f"Unsupported gh command: {cmd[1] if len(cmd) > 1 else 'none'}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout) if result.stdout.strip() else ([] if not single else {})
        return data
    except subprocess.CalledProcessError as e:
        error_msg = (
            f"GitHub CLI error: {e.stderr or e}. Check if 'gh' is installed and authenticated."
        )
        print(error_msg, file=sys.stderr)
        return {} if single else []
    except json.JSONDecodeError as e:
        print(f"Invalid JSON response from GitHub CLI: {e}", file=sys.stderr)
        return {} if single else []


def detect_repo_from_content(content: str) -> str:
    """
    Extract repository name from GitHub links found in markdown content.

    Searches for existing GitHub issue or PR links to determine which repository
    is being referenced. Falls back to configured default repo if no links found.

    :param content: Markdown content to search for GitHub links
    :type content: str
    :return: Repository name in format "owner/repo"
    :rtype: str
    """
    if not content or not isinstance(content, str):
        return config.default_repo

    # Look for existing GitHub links to infer repo
    link_pattern = r"\[(?:Issue|PR) #\d+\]\(https://github\.com/([^/]+/[^/]+)/"
    match = re.search(link_pattern, content)
    if match:
        return match.group(1)

    # Default fallback
    return config.default_repo


def get_date_range(period: str) -> str:
    """
    Convert period specification to date string for GitHub search queries.

    Accepts specific dates in YYYY-MM-DD format or period keywords.
    Currently only "today" is fully implemented, other periods default to today.

    :param period: Date period specification ("today", "this-week", "YYYY-MM-DD", etc.)
    :type period: str
    :return: Date string in YYYY-MM-DD format
    :rtype: str
    """
    if not period or not isinstance(period, str):
        return datetime.now().strftime("%Y-%m-%d")

    today = datetime.now()

    # Check if period is a specific date (YYYY-MM-DD format)
    try:
        datetime.strptime(period, "%Y-%m-%d")
        return period  # Valid date format, use as-is
    except ValueError:
        pass  # Not a date, continue with period logic

    if period == "today":
        return today.strftime("%Y-%m-%d")
    elif period == "this-week":
        # TODO: Implement week range
        return today.strftime("%Y-%m-%d")
    elif period == "this-month":
        # TODO: Implement month range
        return today.strftime("%Y-%m-%d")
    elif period == "this-quarter":
        # TODO: Implement quarter range
        return today.strftime("%Y-%m-%d")
    else:
        return today.strftime("%Y-%m-%d")


def get_default_daily_note(date: str | None = None) -> Path:
    """
    Get file system path to daily note file for specified date.

    :param date: Date in YYYY-MM-DD format, defaults to today if None
    :type date: Optional[str]
    :return: Path object pointing to daily note file
    :rtype: Path
    """
    return config.get_daily_note_path(date)


def fetch_issues_created(period: str = "today") -> list[dict[str, Any]]:
    """
    Retrieve GitHub issues created by the authenticated user in specified period.

    Searches across multiple organizations (digitalgedacht, nexiles) and personal
    repositories for issues authored by the user.

    :param period: Time period to search ("today", "this-week", or YYYY-MM-DD)
    :type period: str
    :return: List of issue dictionaries with number, title, url, and state
    :rtype: List[Dict[str, Any]]
    """
    date_range = get_date_range(period)
    all_issues = []

    for org in config.github_orgs:
        search_query = f"author:{config.github_user} org:{org} created:{date_range}"
        cmd = ["gh", "issue", "list", "--search", search_query, "--json", "number,title,url,state"]
        issues = run_gh_command(cmd)
        all_issues.extend(issues)

    # Also check personal repos if user is not @me
    if config.github_user != "@me":
        search_query = f"author:{config.github_user} user:{config.github_user} created:{date_range}"
        cmd = ["gh", "issue", "list", "--search", search_query, "--json", "number,title,url,state"]
        issues = run_gh_command(cmd)
        all_issues.extend(issues)

    return all_issues


def fetch_prs_created(period: str = "today") -> list[dict[str, Any]]:
    """
    Retrieve GitHub pull requests created by or assigned to the user in specified period.

    Searches across multiple organizations for PRs where the user is either
    the author or assignee.

    :param period: Time period to search ("today", "this-week", or YYYY-MM-DD)
    :type period: str
    :return: List of PR dictionaries with number, title, url, state, and timestamps
    :rtype: List[Dict[str, Any]]
    """
    date_range = get_date_range(period)
    orgs = config.github_orgs
    all_prs = []

    for org in orgs:
        search_query = f"author:{config.github_user} assignee:{config.github_user} org:{org} created:{date_range}"
        cmd = [
            "gh",
            "pr",
            "list",
            "--search",
            search_query,
            "--json",
            "number,title,url,state,createdAt,mergedAt",
        ]
        prs = run_gh_command(cmd)
        all_prs.extend(prs)

    return all_prs


def fetch_issues_worked_on(period: str = "today") -> list[dict[str, Any]]:
    """
    Retrieve GitHub issues the user was involved with in specified period.

    Uses GitHub's "involves:{config.github_user}" search to find issues where the user
    commented, was assigned, mentioned, or otherwise participated.

    :param period: Time period to search ("today", "this-week", or YYYY-MM-DD)
    :type period: str
    :return: List of issue dictionaries with number, title, url, and state
    :rtype: List[Dict[str, Any]]
    """
    date_range = get_date_range(period)
    orgs = config.github_orgs
    all_issues = []

    for org in orgs:
        search_query = f"involves:{config.github_user} org:{org} updated:{date_range}"
        cmd = ["gh", "issue", "list", "--search", search_query, "--json", "number,title,url,state"]
        issues = run_gh_command(cmd)
        all_issues.extend(issues)

    return all_issues


def fetch_issues_closed(period: str = "today") -> list[dict[str, Any]]:
    """
    Retrieve GitHub issues closed in specified period that were created by or assigned to user.

    Searches for all closed issues in the period, then filters to only include
    those authored by or assigned to the authenticated user.

    :param period: Time period to search ("today", "this-week", or YYYY-MM-DD)
    :type period: str
    :return: List of issue dictionaries with number, title, url, state, assignees, and author
    :rtype: List[Dict[str, Any]]
    """
    date_range = get_date_range(period)
    orgs = config.github_orgs
    all_issues = []

    for org in orgs:
        search_query = f"org:{org} closed:{date_range}"
        cmd = [
            "gh",
            "issue",
            "list",
            "--search",
            search_query,
            "--json",
            "number,title,url,state,assignees,author",
        ]
        issues = run_gh_command(cmd)

        # Filter for issues created by or assigned to user
        filtered_issues = []
        for issue in issues:
            # For @me, use actual unix username
            import getpass

            username = getpass.getuser() if config.github_user == "@me" else config.github_user
            is_author = issue.get("author", {}).get("login") == username
            is_assignee = any(
                assignee.get("login") == username for assignee in issue.get("assignees", [])
            )
            if is_author or is_assignee:
                # Since these are from closed search, ensure state is marked as closed
                issue["state"] = "closed"
                filtered_issues.append(issue)

        all_issues.extend(filtered_issues)

    return all_issues


def fetch_prs_merged(period: str = "today") -> list[dict[str, Any]]:
    """
    Retrieve GitHub pull requests merged in specified period that were authored by or assigned to user.

    Searches across multiple organizations for merged PRs where the user is
    either the author or assignee.

    :param period: Time period to search ("today", "this-week", or YYYY-MM-DD)
    :type period: str
    :return: List of PR dictionaries with number, title, url, state, and timestamps
    :rtype: List[Dict[str, Any]]
    """
    date_range = get_date_range(period)
    orgs = config.github_orgs
    all_prs = []

    for org in orgs:
        search_query = f"author:{config.github_user} assignee:{config.github_user} org:{org} merged:{date_range}"
        cmd = [
            "gh",
            "pr",
            "list",
            "--search",
            search_query,
            "--json",
            "number,title,url,state,createdAt,mergedAt",
        ]
        prs = run_gh_command(cmd)
        all_prs.extend(prs)

    return all_prs


def format_issue_ref(issue: dict[str, Any]) -> str:
    """
    Format GitHub issue as markdown link with visual indicator for closed state.

    Creates a markdown link in format: "[Issue #123](url) -- ✅ Title" for closed
    issues, or "[Issue #123](url) -- Title" for open issues.

    :param issue: Issue dictionary containing number, title, url, and state
    :type issue: Dict[str, Any]
    :return: Formatted markdown link string
    :rtype: str
    """
    title = issue["title"]
    if issue.get("state", "").lower() == "closed":
        title = f"✅ {title}"
    return f"[Issue #{issue['number']}]({issue['url']}) -- {title}"


def format_pr_ref(pr: dict[str, Any]) -> str:
    """
    Format GitHub pull request as markdown link with creation and merge timestamps.

    Creates a markdown link with timestamps showing when the PR was opened
    and optionally when it was merged.

    :param pr: PR dictionary containing number, title, url, createdAt, and optionally mergedAt
    :type pr: Dict[str, Any]
    :return: Formatted markdown link string with timestamps
    :rtype: str
    """
    created_at = datetime.fromisoformat(pr["createdAt"].replace("Z", "+00:00"))
    created_str = created_at.strftime("%Y-%m-%d %H:%M")

    result = f"[PR #{pr['number']}]({pr['url']}) -- {pr['title']}"

    if pr.get("mergedAt"):
        merged_at = datetime.fromisoformat(pr["mergedAt"].replace("Z", "+00:00"))
        merged_str = merged_at.strftime("%Y-%m-%d %H:%M")
        result += f" (opened {created_str}, merged {merged_str})"
    else:
        result += f" (opened {created_str})"

    return result


def add_checkmarks_to_closed_issues(content: str, repo: str, dry_run: bool = False) -> str:
    """
    Update existing GitHub issue links in markdown content to add checkmarks for closed issues.

    Searches for formatted GitHub issue links without checkmarks and queries
    GitHub to determine their current state, adding ✅ prefix to closed issues.

    :param content: Markdown content containing GitHub issue links
    :type content: str
    :param repo: Repository name in "owner/repo" format
    :type repo: str
    :param dry_run: If True, only print what would be changed without modifying content
    :type dry_run: bool
    :return: Updated markdown content with checkmarks added to closed issues
    :rtype: str
    """
    # Pattern to find existing GitHub issue links without checkmarks
    issue_pattern = (
        r"\[Issue #(\d+)\]\((https://github\.com/[^/]+/[^/]+/issues/\d+)\) -- (?!✅)([^\n]+)"
    )

    def update_issue_ref(match):
        number = match.group(1)
        url = match.group(2)
        title = match.group(3)

        if dry_run:
            print(f"Would check if Issue #{number} is closed and add ✅ if needed")
            return match.group(0)

        # Get issue state from GitHub
        gh_data = run_gh_command(
            ["gh", "issue", "view", number, "--repo", repo, "--json", "number,title,url,state"],
            single=True,
        )

        if gh_data and gh_data.get("state", "").lower() == "closed":
            return f"[Issue #{number}]({url}) -- ✅ {title}"
        else:
            return match.group(0)  # No change if not closed or error

    return re.sub(issue_pattern, update_issue_ref, content)


def format_unformatted_github_refs(content: str, repo: str, dry_run: bool = False) -> str:
    """
    Convert plain GitHub references to formatted markdown links with titles.

    Finds unformatted references like "Issue #123" or "PR #456" and converts
    them to proper markdown links with titles fetched from GitHub API.

    :param content: Markdown content containing unformatted GitHub references
    :type content: str
    :param repo: Repository name in "owner/repo" format
    :type repo: str
    :param dry_run: If True, only print what would be changed without modifying content
    :type dry_run: bool
    :return: Updated markdown content with formatted GitHub links
    :rtype: str
    """
    # Pattern to find unformatted references (not already in markdown links)
    # Use negative lookbehind to avoid matching inside existing links
    pattern = r"(?<!\[)(?:Issue|PR) #(\d+)(?!\]\()"

    def replace_ref(match):
        ref_type = "Issue" if match.group(0).startswith("Issue") else "PR"
        number = match.group(1)

        if dry_run:
            print(
                f"Would format: {match.group(0)} -> [{ref_type} #{number}](https://github.com/{repo}/{'issues' if ref_type == 'Issue' else 'pull'}/{number}) -- <title>"
            )
            return match.group(0)

        # Get title and state from GitHub
        gh_data = run_gh_command(
            [
                "gh",
                ref_type.lower(),
                "view",
                number,
                "--repo",
                repo,
                "--json",
                "number,title,url,state",
            ],
            single=True,
        )

        if gh_data and "title" in gh_data:
            title = gh_data["title"]
            url = gh_data["url"]

            # Add checkmark if it's a closed issue
            if ref_type == "Issue" and gh_data.get("state", "").lower() == "closed":
                title = f"✅ {title}"

            return f"[{ref_type} #{number}]({url}) -- {title}"
        else:
            print(f"Warning: Could not fetch data for {ref_type} #{number}", file=sys.stderr)
            return match.group(0)

    return re.sub(pattern, replace_ref, content)


def format_all_github_refs(content: str, repo: str | None = None, dry_run: bool = False) -> str:
    """
    Comprehensively format all GitHub references in markdown content.

    Performs two operations:
    1. Adds checkmarks to existing formatted issue links that are closed
    2. Converts unformatted references to proper markdown links

    :param content: Markdown content to process
    :type content: str
    :param repo: Repository name in "owner/repo" format, auto-detected if None
    :type repo: Optional[str]
    :param dry_run: If True, only print what would be changed without modifying content
    :type dry_run: bool
    :return: Updated markdown content with all GitHub references properly formatted
    :rtype: str
    """
    if repo is None:
        repo = detect_repo_from_content(content)

    # First, add checkmarks to existing formatted issue links that are closed
    content = add_checkmarks_to_closed_issues(content, repo, dry_run)

    # Then, format unformatted references
    content = format_unformatted_github_refs(content, repo, dry_run)

    return content


def update_daily_review_section(content: str, github_data: dict[str, list]) -> str:
    """
    Replace or append Daily Review section in markdown content with GitHub activity data.

    Creates a comprehensive daily review section showing issues created, PRs created,
    issues closed, issues worked on, and PRs merged. If the section exists, it's
    replaced; otherwise it's appended to the content.

    :param content: Existing markdown content
    :type content: str
    :param github_data: Dictionary containing lists of GitHub items by category
    :type github_data: Dict[str, List]
    :return: Updated markdown content with Daily Review section
    :rtype: str
    """

    # Format the new Daily Review content
    review_content = "## Daily Review\n\n"

    # Issues created today
    review_content += f"{SECTION_ISSUES_CREATED}\n"
    if github_data["issues_created"]:
        for issue in github_data["issues_created"]:
            review_content += f"- {format_issue_ref(issue)}\n"
    else:
        review_content += "NONE\n"
    review_content += "\n"

    # PRs created today
    review_content += f"{SECTION_PRS_CREATED}\n"
    if github_data["prs_created"]:
        for pr in github_data["prs_created"]:
            review_content += f"- {format_pr_ref(pr)}\n"
    else:
        review_content += "NONE\n"
    review_content += "\n"

    # Issues closed today
    review_content += f"{SECTION_ISSUES_CLOSED}\n"
    if github_data["issues_closed"]:
        for issue in github_data["issues_closed"]:
            review_content += f"- {format_issue_ref(issue)}\n"
    else:
        review_content += "NONE\n"
    review_content += "\n"

    # Issues worked on today
    review_content += f"{SECTION_ISSUES_WORKED}\n"
    if github_data["issues_worked_on"]:
        for issue in github_data["issues_worked_on"]:
            review_content += f"- {format_issue_ref(issue)} ({issue['state']})\n"
    else:
        review_content += "NONE\n"
    review_content += "\n"

    # PRs merged today
    review_content += f"{SECTION_PRS_MERGED}\n"
    if github_data["prs_merged"]:
        for pr in github_data["prs_merged"]:
            review_content += f"- {format_pr_ref(pr)}\n"
    else:
        review_content += "NONE\n"

    # Replace the Daily Review section
    pattern = r"(## Daily Review\n\n)(.*?)(?=\n###|\n## |$)"
    if re.search(pattern, content, re.DOTALL):
        return re.sub(pattern, review_content, content, flags=re.DOTALL)
    else:
        # If section doesn't exist, append it
        return content + "\n\n" + review_content
