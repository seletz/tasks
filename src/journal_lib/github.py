"""GitHub integration for daily journal automation."""

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Global configuration
NOTES_DIR = Path("/Users/seletz/develop/notes")
DEFAULT_REPO = "digitalgedacht/careassist-odoo"

# Section headers for daily review
SECTION_ISSUES_CREATED = "**Heute erstellte Issues:**"
SECTION_PRS_CREATED = "**Heute erstellte PRs:**"
SECTION_ISSUES_CLOSED = "**Heute geschlossene Issues:**"
SECTION_ISSUES_WORKED = "**Heute bearbeitet:**"
SECTION_PRS_MERGED = "**Heute gemergte PRs:**"


def run_gh_command(cmd: List[str]) -> List[Dict[str, Any]]:
    """Run gh command and return JSON result as list."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout) if result.stdout.strip() else []
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        print(f"Error running gh command {' '.join(cmd)}: {e}", file=sys.stderr)
        return []


def run_gh_command_single(cmd: List[str]) -> Dict[str, Any]:
    """Run gh command and return JSON result as single dict."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout) if result.stdout.strip() else {}
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        print(f"Error running gh command {' '.join(cmd)}: {e}", file=sys.stderr)
        return {}


def detect_repo_from_content(content: str) -> str:
    """Detect repository from existing GitHub links in content."""
    # Look for existing GitHub links to infer repo
    link_pattern = r'\[(?:Issue|PR) #\d+\]\(https://github\.com/([^/]+/[^/]+)/'
    match = re.search(link_pattern, content)
    if match:
        return match.group(1)
    
    # Default fallback
    return DEFAULT_REPO


def get_date_range(period: str) -> str:
    """Get date range string for GitHub search based on period."""
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


def get_default_daily_note(date: Optional[str] = None) -> Path:
    """Get path to daily note for given date (defaults to today)."""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    return NOTES_DIR / "daily" / f"{date}.md"


def fetch_issues_created(period: str = "today") -> List[Dict[str, Any]]:
    """Fetch issues created by user in given period."""
    date_range = get_date_range(period)
    orgs = ["digitalgedacht", "nexiles"]
    all_issues = []
    
    for org in orgs:
        search_query = f"author:@me org:{org} created:{date_range}"
        cmd = ["gh", "issue", "list", "--search", search_query, 
               "--json", "number,title,url,state"]
        issues = run_gh_command(cmd)
        all_issues.extend(issues)
    
    # Also check personal repos
    search_query = f"author:@me user:seletz created:{date_range}"
    cmd = ["gh", "issue", "list", "--search", search_query, 
           "--json", "number,title,url,state"]
    issues = run_gh_command(cmd)
    all_issues.extend(issues)
    
    return all_issues


def fetch_prs_created(period: str = "today") -> List[Dict[str, Any]]:
    """Fetch PRs created by user (authored and assigned) in given period."""
    date_range = get_date_range(period)
    orgs = ["digitalgedacht", "nexiles"]
    all_prs = []
    
    for org in orgs:
        search_query = f"author:@me assignee:@me org:{org} created:{date_range}"
        cmd = ["gh", "pr", "list", "--search", search_query,
               "--json", "number,title,url,state,createdAt,mergedAt"]
        prs = run_gh_command(cmd)
        all_prs.extend(prs)
    
    return all_prs


def fetch_issues_worked_on(period: str = "today") -> List[Dict[str, Any]]:
    """Fetch issues user worked on (involved with) in given period."""
    date_range = get_date_range(period)
    orgs = ["digitalgedacht", "nexiles"]
    all_issues = []
    
    for org in orgs:
        search_query = f"involves:@me org:{org} updated:{date_range}"
        cmd = ["gh", "issue", "list", "--search", search_query,
               "--json", "number,title,url,state"]
        issues = run_gh_command(cmd)
        all_issues.extend(issues)
    
    return all_issues


def fetch_issues_closed(period: str = "today") -> List[Dict[str, Any]]:
    """Fetch issues closed in given period (created by or assigned to user)."""
    date_range = get_date_range(period)
    orgs = ["digitalgedacht", "nexiles"] 
    all_issues = []
    
    for org in orgs:
        search_query = f"org:{org} closed:{date_range}"
        cmd = ["gh", "issue", "list", "--search", search_query,
               "--json", "number,title,url,state,assignees,author"]
        issues = run_gh_command(cmd)
        
        # Filter for issues created by or assigned to user
        filtered_issues = []
        for issue in issues:
            is_author = issue.get("author", {}).get("login") == "seletz"
            is_assignee = any(assignee.get("login") == "seletz" 
                            for assignee in issue.get("assignees", []))
            if is_author or is_assignee:
                # Since these are from closed search, ensure state is marked as closed
                issue["state"] = "closed"
                filtered_issues.append(issue)
        
        all_issues.extend(filtered_issues)
    
    return all_issues


def fetch_prs_merged(period: str = "today") -> List[Dict[str, Any]]:
    """Fetch PRs merged in given period (authored and assigned to user)."""
    date_range = get_date_range(period)
    orgs = ["digitalgedacht", "nexiles"]
    all_prs = []
    
    for org in orgs:
        search_query = f"author:@me assignee:@me org:{org} merged:{date_range}"
        cmd = ["gh", "pr", "list", "--search", search_query,
               "--json", "number,title,url,state,createdAt,mergedAt"]
        prs = run_gh_command(cmd)
        all_prs.extend(prs)
    
    return all_prs


def format_issue_ref(issue: Dict[str, Any]) -> str:
    """Format issue as markdown link with checkmark if closed."""
    title = issue['title']
    if issue.get('state', '').lower() == 'closed':
        title = f"✅ {title}"
    return f"[Issue #{issue['number']}]({issue['url']}) -- {title}"


def format_pr_ref(pr: Dict[str, Any]) -> str:
    """Format PR as markdown link with timestamps."""
    created_at = datetime.fromisoformat(pr['createdAt'].replace('Z', '+00:00'))
    created_str = created_at.strftime("%Y-%m-%d %H:%M")
    
    result = f"[PR #{pr['number']}]({pr['url']}) -- {pr['title']}"
    
    if pr.get('mergedAt'):
        merged_at = datetime.fromisoformat(pr['mergedAt'].replace('Z', '+00:00'))
        merged_str = merged_at.strftime("%Y-%m-%d %H:%M")
        result += f" (opened {created_str}, merged {merged_str})"
    else:
        result += f" (opened {created_str})"
    
    return result


def add_checkmarks_to_closed_issues(content: str, repo: str, dry_run: bool = False) -> str:
    """Add checkmarks to already-formatted GitHub issue links that are closed."""
    # Pattern to find existing GitHub issue links without checkmarks
    issue_pattern = r'\[Issue #(\d+)\]\((https://github\.com/[^/]+/[^/]+/issues/\d+)\) -- (?!✅)([^\n]+)'
    
    def update_issue_ref(match):
        number = match.group(1)
        url = match.group(2)
        title = match.group(3)
        
        if dry_run:
            print(f"Would check if Issue #{number} is closed and add ✅ if needed")
            return match.group(0)
        
        # Get issue state from GitHub
        gh_data = run_gh_command_single([
            "gh", "issue", "view", number, 
            "--repo", repo, "--json", "number,title,url,state"
        ])
        
        if gh_data and gh_data.get("state", "").lower() == "closed":
            return f"[Issue #{number}]({url}) -- ✅ {title}"
        else:
            return match.group(0)  # No change if not closed or error
    
    return re.sub(issue_pattern, update_issue_ref, content)


def format_unformatted_github_refs(content: str, repo: str, dry_run: bool = False) -> str:
    """Format unformatted GitHub references (Issue #123, PR #456) into proper links."""
    # Pattern to find unformatted references (not already in markdown links)
    # Use negative lookbehind to avoid matching inside existing links
    pattern = r'(?<!\[)(?:Issue|PR) #(\d+)(?!\]\()'
    
    def replace_ref(match):
        ref_type = "Issue" if match.group(0).startswith("Issue") else "PR"
        number = match.group(1)
        
        if dry_run:
            print(f"Would format: {match.group(0)} -> [{ref_type} #{number}](https://github.com/{repo}/{'issues' if ref_type == 'Issue' else 'pull'}/{number}) -- <title>")
            return match.group(0)
        
        # Get title and state from GitHub
        gh_data = run_gh_command_single([
            "gh", ref_type.lower(), "view", number, 
            "--repo", repo, "--json", "number,title,url,state"
        ])
        
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


def format_all_github_refs(content: str, repo: Optional[str] = None, dry_run: bool = False) -> str:
    """Format all GitHub references in content: add checkmarks to closed issues and format unformatted refs."""
    if repo is None:
        repo = detect_repo_from_content(content)
    
    # First, add checkmarks to existing formatted issue links that are closed
    content = add_checkmarks_to_closed_issues(content, repo, dry_run)
    
    # Then, format unformatted references
    content = format_unformatted_github_refs(content, repo, dry_run)
    
    return content


def update_daily_review_section(content: str, github_data: Dict[str, List]) -> str:
    """Update the Daily Review section with GitHub activity."""
    
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
    pattern = r'(## Daily Review\n\n)(.*?)(?=\n###|\n## |$)'
    if re.search(pattern, content, re.DOTALL):
        return re.sub(pattern, review_content, content, flags=re.DOTALL)
    else:
        # If section doesn't exist, append it
        return content + "\n\n" + review_content