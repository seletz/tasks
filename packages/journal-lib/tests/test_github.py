"""Tests for journal_lib.github module."""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

import pytest

from journal_lib import github


class TestGitHubCommands:
    """Test GitHub CLI command execution functions."""

    def test_run_gh_command_success(self):
        """Test successful gh command execution returning list."""
        mock_result = Mock()
        mock_result.stdout = '[{"number": 1, "title": "Test"}]'
        mock_result.returncode = 0
        
        with patch('subprocess.run', return_value=mock_result) as mock_run:
            result = github.run_gh_command(['gh', 'issue', 'list'])
            
            assert result == [{"number": 1, "title": "Test"}]
            mock_run.assert_called_once_with(
                ['gh', 'issue', 'list'], capture_output=True, text=True, check=True
            )

    def test_run_gh_command_empty_output(self):
        """Test gh command execution with empty output."""
        mock_result = Mock()
        mock_result.stdout = ''
        mock_result.returncode = 0
        
        with patch('subprocess.run', return_value=mock_result):
            result = github.run_gh_command(['gh', 'issue', 'list'])
            assert result == []

    def test_run_gh_command_subprocess_error(self):
        """Test gh command execution with subprocess error."""
        with patch('subprocess.run', side_effect=subprocess.CalledProcessError(1, 'gh')) as mock_run:
            with patch('builtins.print') as mock_print:
                result = github.run_gh_command(['gh', 'issue', 'list'])
                
                assert result == []
                mock_print.assert_called_once()

    def test_run_gh_command_json_decode_error(self):
        """Test gh command execution with invalid JSON."""
        mock_result = Mock()
        mock_result.stdout = 'invalid json'
        mock_result.returncode = 0
        
        with patch('subprocess.run', return_value=mock_result):
            with patch('builtins.print') as mock_print:
                result = github.run_gh_command(['gh', 'issue', 'list'])
                
                assert result == []
                mock_print.assert_called_once()

    def test_run_gh_command_single_success(self):
        """Test successful gh command execution returning single dict."""
        mock_result = Mock()
        mock_result.stdout = '{"number": 1, "title": "Test"}'
        mock_result.returncode = 0
        
        with patch('subprocess.run', return_value=mock_result):
            result = github.run_gh_command_single(['gh', 'issue', 'view', '1'])
            assert result == {"number": 1, "title": "Test"}

    def test_run_gh_command_single_empty_output(self):
        """Test gh command single execution with empty output."""
        mock_result = Mock()
        mock_result.stdout = ''
        mock_result.returncode = 0
        
        with patch('subprocess.run', return_value=mock_result):
            result = github.run_gh_command_single(['gh', 'issue', 'view', '1'])
            assert result == {}


class TestRepositoryDetection:
    """Test repository detection from content."""

    def test_detect_repo_from_content_with_issue_link_old_format(self):
        """Test repository detection from issue link in old format."""
        content = "Some text [Issue #123](https://github.com/owner/repo/issues/123) more text"
        result = github.detect_repo_from_content(content)
        assert result == "owner/repo"

    def test_detect_repo_from_content_with_issue_link_new_format(self):
        """Test repository detection from issue link in new format."""
        content = "Some text [owner/repo#123](https://github.com/owner/repo/issues/123) more text"
        result = github.detect_repo_from_content(content)
        assert result == "owner/repo"

    def test_detect_repo_from_content_with_pr_link_old_format(self):
        """Test repository detection from PR link in old format."""
        content = "Some text [PR #456](https://github.com/owner/repo/pull/456) more text"
        result = github.detect_repo_from_content(content)
        assert result == "owner/repo"

    def test_detect_repo_from_content_with_pr_link_new_format(self):
        """Test repository detection from PR link in new format."""
        content = "Some text [owner/repo#456](https://github.com/owner/repo/pull/456) more text"
        result = github.detect_repo_from_content(content)
        assert result == "owner/repo"

    def test_detect_repo_from_content_no_links(self):
        """Test repository detection with no GitHub links."""
        content = "Some text with no GitHub links"
        result = github.detect_repo_from_content(content)
        assert result == github.DEFAULT_REPO

    def test_detect_repo_from_content_empty(self):
        """Test repository detection with empty content."""
        content = ""
        result = github.detect_repo_from_content(content)
        assert result == github.DEFAULT_REPO


class TestDateRangeHandling:
    """Test date range conversion for GitHub searches."""

    def test_get_date_range_today(self):
        """Test date range for 'today' period returns current date."""
        result = github.get_date_range("today")
        # Should return a valid date string in YYYY-MM-DD format
        datetime.strptime(result, "%Y-%m-%d")  # Will raise if invalid format

    def test_get_date_range_specific_date(self):
        """Test date range with specific date."""
        result = github.get_date_range("2023-12-15")
        assert result == "2023-12-15"

    def test_get_date_range_this_week(self):
        """Test date range for 'this-week' period (currently defaults to today)."""
        result = github.get_date_range("this-week")
        # Should return a valid date string in YYYY-MM-DD format  
        datetime.strptime(result, "%Y-%m-%d")  # Will raise if invalid format

    def test_get_date_range_invalid_date(self):
        """Test date range with invalid date format defaults to today."""
        result = github.get_date_range("invalid-date-format")
        # Should return a valid date string in YYYY-MM-DD format (today's date)
        datetime.strptime(result, "%Y-%m-%d")  # Will raise if invalid format


class TestDailyNoteHandling:
    """Test daily note file path generation."""

    def test_get_default_daily_note_with_date(self):
        """Test daily note path with specific date."""
        result = github.get_default_daily_note("2023-12-15")
        expected = Path("/Users/seletz/develop/notes/daily/2023-12-15.md")
        assert result == expected

    def test_get_default_daily_note_without_date(self):
        """Test daily note path without date (uses today)."""
        result = github.get_default_daily_note()
        # Should return path with today's date
        today = datetime.now().strftime("%Y-%m-%d")
        expected = Path(f"/Users/seletz/develop/notes/daily/{today}.md")
        assert result == expected


class TestGitHubDataFetching:
    """Test GitHub data fetching functions."""

    @patch('journal_lib.github.run_gh_command')
    @patch('journal_lib.github.get_date_range')
    def test_fetch_issues_created(self, mock_get_date, mock_run_gh):
        """Test fetching created issues."""
        mock_get_date.return_value = "2023-12-01"
        mock_run_gh.return_value = [{"number": 1, "title": "Test Issue"}]
        
        result = github.fetch_issues_created("today")
        
        # Should be called 3 times (2 orgs + 1 personal)
        assert mock_run_gh.call_count == 3
        assert len(result) == 3  # Each call returns 1 item

    @patch('journal_lib.github.run_gh_command')
    @patch('journal_lib.github.get_date_range')
    def test_fetch_prs_created(self, mock_get_date, mock_run_gh):
        """Test fetching created PRs."""
        mock_get_date.return_value = "2023-12-01"
        mock_run_gh.return_value = [{"number": 1, "title": "Test PR"}]
        
        result = github.fetch_prs_created("today")
        
        # Should be called 2 times (2 orgs)
        assert mock_run_gh.call_count == 2
        assert len(result) == 2

    @patch('journal_lib.github.run_gh_command')
    @patch('journal_lib.github.get_date_range')
    def test_fetch_issues_worked_on(self, mock_get_date, mock_run_gh):
        """Test fetching issues worked on."""
        mock_get_date.return_value = "2023-12-01"
        mock_run_gh.return_value = [{"number": 1, "title": "Test Issue"}]
        
        result = github.fetch_issues_worked_on("today")
        
        assert mock_run_gh.call_count == 2  # 2 orgs
        assert len(result) == 2

    @patch('journal_lib.github.run_gh_command')
    @patch('journal_lib.github.get_date_range')
    def test_fetch_issues_closed(self, mock_get_date, mock_run_gh):
        """Test fetching closed issues with filtering."""
        mock_get_date.return_value = "2023-12-01"
        mock_run_gh.return_value = [
            {
                "number": 1, 
                "title": "Test Issue",
                "author": {"login": "seletz"},
                "assignees": []
            },
            {
                "number": 2,
                "title": "Other Issue", 
                "author": {"login": "other"},
                "assignees": [{"login": "seletz"}]
            },
            {
                "number": 3,
                "title": "Unrelated Issue",
                "author": {"login": "other"},
                "assignees": []
            }
        ]
        
        result = github.fetch_issues_closed("today")
        
        # Should filter to only issues by or assigned to user
        assert len(result) == 4  # 2 orgs * 2 filtered issues
        for issue in result:
            assert issue["state"] == "closed"

    @patch('journal_lib.github.run_gh_command')
    @patch('journal_lib.github.get_date_range')  
    def test_fetch_prs_merged(self, mock_get_date, mock_run_gh):
        """Test fetching merged PRs."""
        mock_get_date.return_value = "2023-12-01"
        mock_run_gh.return_value = [{"number": 1, "title": "Test PR"}]
        
        result = github.fetch_prs_merged("today")
        
        assert mock_run_gh.call_count == 2  # 2 orgs
        assert len(result) == 2


class TestSecurityFunctions:
    """Test security-related functions."""

    def test_escape_markdown_basic(self):
        """Test basic markdown escaping."""
        text = "This has *bold* and [link](url) and `code`"
        result = github.escape_markdown(text)
        expected = "This has \\\\*bold\\\\* and \\\\[link\\\\]\\\\(url\\\\) and \\\\`code\\\\`"
        assert result == expected


    def test_escape_markdown_non_string(self):
        """Test escaping with non-string input."""
        result = github.escape_markdown(123)
        assert result == "123"

    def test_escape_markdown_empty(self):
        """Test escaping empty string."""
        result = github.escape_markdown("")
        assert result == ""


class TestRepositoryExtraction:
    """Test repository extraction from URLs."""

    def test_extract_repo_from_url_issue(self):
        """Test extracting repository from issue URL."""
        url = "https://github.com/owner/repo/issues/123"
        result = github.extract_repo_from_url(url)
        assert result == "owner/repo"

    def test_extract_repo_from_url_pr(self):
        """Test extracting repository from PR URL."""
        url = "https://github.com/digitalgedacht/careassist-odoo/pull/456"
        result = github.extract_repo_from_url(url)
        assert result == "digitalgedacht/careassist-odoo"

    def test_extract_repo_from_url_invalid(self):
        """Test extracting repository from invalid URL."""
        url = "https://not-github.com/something"
        result = github.extract_repo_from_url(url)
        assert result == "unknown/repo"

    def test_extract_repo_from_url_non_string(self):
        """Test extracting repository from non-string input."""
        result = github.extract_repo_from_url(123)
        assert result == "unknown/repo"

    def test_extract_repo_from_url_malformed(self):
        """Test extracting repository from malformed URL."""
        url = "not-a-url-at-all"
        result = github.extract_repo_from_url(url)
        assert result == "unknown/repo"

    def test_extract_repo_from_url_with_www(self):
        """Test extracting repository from GitHub URL with www prefix."""
        url = "https://www.github.com/owner/repo/issues/123"
        result = github.extract_repo_from_url(url)
        assert result == "owner/repo"


class TestFormatting:
    """Test GitHub reference formatting functions."""

    def test_format_issue_ref_open(self):
        """Test formatting open issue reference with repository prefix."""
        issue = {
            "number": 123,
            "title": "Test Issue",
            "url": "https://github.com/owner/repo/issues/123",
            "state": "open"
        }
        result = github.format_issue_ref(issue)
        expected = "[owner/repo#123](https://github.com/owner/repo/issues/123) -- Test Issue"
        assert result == expected

    def test_format_issue_ref_with_markdown_characters(self):
        """Test formatting issue reference with markdown characters in title."""
        issue = {
            "number": 123,
            "title": "Fix *bold* issue with [links]",
            "url": "https://github.com/owner/repo/issues/123",
            "state": "open"
        }
        result = github.format_issue_ref(issue)
        expected = "[owner/repo#123](https://github.com/owner/repo/issues/123) -- Fix \\\\*bold\\\\* issue with \\\\[links\\\\]"
        assert result == expected

    def test_format_issue_ref_closed(self):
        """Test formatting closed issue reference with repository prefix."""
        issue = {
            "number": 123,
            "title": "Test Issue",
            "url": "https://github.com/owner/repo/issues/123", 
            "state": "closed"
        }
        result = github.format_issue_ref(issue)
        expected = "[owner/repo#123](https://github.com/owner/repo/issues/123) -- ✅ Test Issue"
        assert result == expected

    def test_format_pr_ref_open(self):
        """Test formatting open PR reference with repository prefix."""
        pr = {
            "number": 456,
            "title": "Test PR",
            "url": "https://github.com/owner/repo/pull/456",
            "createdAt": "2023-12-01T10:00:00Z"
        }
        result = github.format_pr_ref(pr)
        expected = "[owner/repo#456](https://github.com/owner/repo/pull/456) -- Test PR (opened 2023-12-01 10:00)"
        assert result == expected

    def test_format_pr_ref_with_markdown_characters(self):
        """Test formatting PR reference with markdown characters in title."""
        pr = {
            "number": 456,
            "title": "Add `code` support for *features*",
            "url": "https://github.com/owner/repo/pull/456",
            "createdAt": "2023-12-01T10:00:00Z"
        }
        result = github.format_pr_ref(pr)
        expected = "[owner/repo#456](https://github.com/owner/repo/pull/456) -- Add \\\\`code\\\\` support for \\\\*features\\\\* (opened 2023-12-01 10:00)"
        assert result == expected

    def test_format_pr_ref_merged(self):
        """Test formatting merged PR reference with repository prefix."""
        pr = {
            "number": 456,
            "title": "Test PR", 
            "url": "https://github.com/owner/repo/pull/456",
            "createdAt": "2023-12-01T10:00:00Z",
            "mergedAt": "2023-12-01T15:00:00Z"
        }
        result = github.format_pr_ref(pr)
        expected = "[owner/repo#456](https://github.com/owner/repo/pull/456) -- Test PR (opened 2023-12-01 10:00, merged 2023-12-01 15:00)"
        assert result == expected


class TestContentFormatting:
    """Test content formatting and GitHub reference updating."""

    @patch('journal_lib.github.run_gh_command_single')
    def test_add_checkmarks_to_closed_issues_old_format(self, mock_run_gh_single):
        """Test adding checkmarks to closed issues in old format."""
        content = "[Issue #123](https://github.com/owner/repo/issues/123) -- Test Issue"
        mock_run_gh_single.return_value = {
            "number": 123,
            "title": "Test Issue", 
            "state": "closed"
        }
        
        result = github.add_checkmarks_to_closed_issues(content, "owner/repo")
        expected = "[owner/repo#123](https://github.com/owner/repo/issues/123) -- ✅ Test Issue"
        assert result == expected

    @patch('journal_lib.github.run_gh_command_single')
    def test_add_checkmarks_to_closed_issues_new_format(self, mock_run_gh_single):
        """Test adding checkmarks to closed issues in new format."""
        content = "[owner/repo#123](https://github.com/owner/repo/issues/123) -- Test Issue"
        mock_run_gh_single.return_value = {
            "number": 123,
            "title": "Test Issue", 
            "state": "closed"
        }
        
        result = github.add_checkmarks_to_closed_issues(content, "owner/repo")
        expected = "[owner/repo#123](https://github.com/owner/repo/issues/123) -- ✅ Test Issue"
        assert result == expected

    @patch('journal_lib.github.run_gh_command_single')
    def test_add_checkmarks_to_closed_issues_dry_run(self, mock_run_gh_single):
        """Test dry run mode for adding checkmarks."""
        content = "[Issue #123](https://github.com/owner/repo/issues/123) -- Test Issue"
        
        with patch('builtins.print') as mock_print:
            result = github.add_checkmarks_to_closed_issues(content, "owner/repo", dry_run=True)
            
            assert result == content  # No changes in dry run
            mock_print.assert_called_once()
            mock_run_gh_single.assert_not_called()

    @patch('journal_lib.github.run_gh_command_single')
    def test_format_unformatted_github_refs(self, mock_run_gh_single):
        """Test formatting unformatted GitHub references with repository prefix."""
        content = "Fixed Issue #123 and PR #456"
        mock_run_gh_single.side_effect = [
            {
                "number": 123,
                "title": "Test Issue",
                "url": "https://github.com/owner/repo/issues/123",
                "state": "closed"
            },
            {
                "number": 456, 
                "title": "Test PR",
                "url": "https://github.com/owner/repo/pull/456",
                "state": "open"
            }
        ]
        
        result = github.format_unformatted_github_refs(content, "owner/repo")
        expected = "Fixed [owner/repo#123](https://github.com/owner/repo/issues/123) -- ✅ Test Issue and [owner/repo#456](https://github.com/owner/repo/pull/456) -- Test PR"
        assert result == expected

    @patch('journal_lib.github.run_gh_command_single')
    def test_format_unformatted_github_refs_dry_run(self, mock_run_gh_single):
        """Test dry run mode for formatting unformatted references."""
        content = "Fixed Issue #123"
        
        with patch('builtins.print') as mock_print:
            result = github.format_unformatted_github_refs(content, "owner/repo", dry_run=True)
            
            assert result == content  # No changes in dry run
            mock_print.assert_called_once()
            mock_run_gh_single.assert_not_called()

    @patch('journal_lib.github.detect_repo_from_content')
    @patch('journal_lib.github.add_checkmarks_to_closed_issues')
    @patch('journal_lib.github.format_unformatted_github_refs')
    def test_format_all_github_refs(self, mock_format_unformatted, mock_add_checkmarks, mock_detect_repo):
        """Test comprehensive GitHub reference formatting."""
        content = "Some content"
        mock_detect_repo.return_value = "owner/repo"
        mock_add_checkmarks.return_value = "content with checkmarks"
        mock_format_unformatted.return_value = "final formatted content"
        
        result = github.format_all_github_refs(content)
        
        mock_detect_repo.assert_called_once_with(content)
        mock_add_checkmarks.assert_called_once_with(content, "owner/repo", False)
        mock_format_unformatted.assert_called_once_with("content with checkmarks", "owner/repo", False)
        assert result == "final formatted content"

    @patch('journal_lib.github.add_checkmarks_to_closed_issues')
    @patch('journal_lib.github.format_unformatted_github_refs')
    def test_format_all_github_refs_with_repo(self, mock_format_unformatted, mock_add_checkmarks):
        """Test comprehensive GitHub reference formatting with provided repo."""
        content = "Some content"
        mock_add_checkmarks.return_value = "content with checkmarks"
        mock_format_unformatted.return_value = "final formatted content"
        
        result = github.format_all_github_refs(content, repo="specified/repo")
        
        mock_add_checkmarks.assert_called_once_with(content, "specified/repo", False)
        mock_format_unformatted.assert_called_once_with("content with checkmarks", "specified/repo", False)
        assert result == "final formatted content"


class TestDailyReviewUpdate:
    """Test daily review section updating."""

    def test_update_daily_review_section_replace_existing(self):
        """Test replacing existing Daily Review section."""
        content = """# Some Title

## Daily Review

Old content here

## Other Section

Other content"""
        
        github_data = {
            "issues_created": [{"number": 1, "title": "Test", "url": "http://test.com", "state": "open"}],
            "prs_created": [],
            "issues_closed": [],
            "issues_worked_on": [],
            "prs_merged": []
        }
        
        result = github.update_daily_review_section(content, github_data)
        
        assert "## Daily Review" in result
        assert "**Heute erstellte Issues:**" in result
        assert "[unknown/repo#1](http://test.com) -- Test" in result
        assert "NONE" in result  # For empty sections
        assert "## Other Section" in result
        assert "Old content here" not in result

    def test_update_daily_review_section_append_new(self):
        """Test appending Daily Review section when it doesn't exist."""
        content = """# Some Title

Some existing content"""
        
        github_data = {
            "issues_created": [],
            "prs_created": [],
            "issues_closed": [],
            "issues_worked_on": [],
            "prs_merged": []
        }
        
        result = github.update_daily_review_section(content, github_data)
        
        assert content in result  # Original content preserved
        assert "## Daily Review" in result
        assert "**Heute erstellte Issues:**" in result
        assert result.count("NONE") == 5  # All sections should show NONE

    def test_update_daily_review_section_with_all_data(self):
        """Test Daily Review section with all types of GitHub data."""
        content = "# Test"
        
        github_data = {
            "issues_created": [{"number": 1, "title": "Created Issue", "url": "http://test.com/1", "state": "open"}],
            "prs_created": [{"number": 2, "title": "Created PR", "url": "http://test.com/2", "createdAt": "2023-12-01T10:00:00Z"}],
            "issues_closed": [{"number": 3, "title": "Closed Issue", "url": "http://test.com/3", "state": "closed"}], 
            "issues_worked_on": [{"number": 4, "title": "Worked Issue", "url": "http://test.com/4", "state": "open"}],
            "prs_merged": [{"number": 5, "title": "Merged PR", "url": "http://test.com/5", "createdAt": "2023-12-01T10:00:00Z", "mergedAt": "2023-12-01T15:00:00Z"}]
        }
        
        result = github.update_daily_review_section(content, github_data)
        
        assert "[unknown/repo#1](http://test.com/1) -- Created Issue" in result
        assert "[unknown/repo#2](http://test.com/2) -- Created PR" in result
        assert "[unknown/repo#3](http://test.com/3) -- ✅ Closed Issue" in result
        assert "[unknown/repo#4](http://test.com/4) -- Worked Issue (open)" in result
        assert "[unknown/repo#5](http://test.com/5) -- Merged PR" in result
        assert "NONE" not in result  # No sections should be empty


class TestConstants:
    """Test module constants and configuration."""

    def test_notes_dir_constant(self):
        """Test NOTES_DIR constant is properly set."""
        assert github.NOTES_DIR == Path("/Users/seletz/develop/notes")

    def test_default_repo_constant(self):
        """Test DEFAULT_REPO constant is properly set."""
        assert github.DEFAULT_REPO == "digitalgedacht/careassist-odoo"

    def test_section_headers_constants(self):
        """Test all section header constants are properly set."""
        assert github.SECTION_ISSUES_CREATED == "**Heute erstellte Issues:**"
        assert github.SECTION_PRS_CREATED == "**Heute erstellte PRs:**"
        assert github.SECTION_ISSUES_CLOSED == "**Heute geschlossene Issues:**"
        assert github.SECTION_ISSUES_WORKED == "**Heute bearbeitet:**"
        assert github.SECTION_PRS_MERGED == "**Heute gemergte PRs:**"