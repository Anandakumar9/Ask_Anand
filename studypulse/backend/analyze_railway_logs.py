#!/usr/bin/env python3
"""
Railway Logs Analyzer for PostgreSQL Errors
============================================

This script analyzes Railway logs to identify and summarize PostgreSQL database
connection issues, deployment markers, and other critical events.

Usage:
    # From stdin (piped from Railway CLI)
    railway logs --service backend | python analyze_railway_logs.py

    # From a file
    python analyze_railway_logs.py railway_logs.txt

    # Save Railway logs to a file first
    railway logs --service backend > logs.txt
    python analyze_railway_logs.py logs.txt

Installation:
    # Install Railway CLI
    npm i -g @railway/cli

    # Login to Railway
    railway login

    # Link to your project (if needed)
    railway link

    # Get logs
    railway logs --service backend
    railway logs --service backend --follow  # Follow mode (live)
"""

import sys
import re
from collections import defaultdict
from datetime import datetime
from typing import List, Dict, Tuple
import argparse
import os

# Fix Windows console encoding for emojis and Unicode characters
if sys.platform == 'win32':
    try:
        # Set console to UTF-8 mode
        os.system('chcp 65001 > nul 2>&1')
        # Reconfigure stdout to use UTF-8
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass  # Fallback to default encoding if this fails


class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'

    # Background colors
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'


def colorize(text: str, color: str, bold: bool = False) -> str:
    """Add color to text"""
    prefix = Colors.BOLD if bold else ''
    return f"{prefix}{color}{text}{Colors.RESET}"


def safe_print(text: str) -> None:
    """Print text with fallback for encoding errors"""
    try:
        print(text)
    except UnicodeEncodeError:
        # Fallback: replace problematic characters
        try:
            print(text.encode('utf-8', errors='replace').decode('utf-8'))
        except Exception:
            # Last resort: ASCII only
            print(text.encode('ascii', errors='replace').decode('ascii'))


def get_status_icon(label: str, count: int) -> str:
    """Get status icon with fallback for systems that don't support emojis"""
    try:
        if count > 0 and "Error" in label:
            return "❌"
        elif count > 0:
            return "✅"
        else:
            return "⚪"
    except UnicodeEncodeError:
        # Fallback to ASCII markers
        if count > 0 and "Error" in label:
            return "[X]"
        elif count > 0:
            return "[OK]"
        else:
            return "[ ]"


class LogEntry:
    """Represents a single log entry"""
    def __init__(self, timestamp: str, content: str, line_number: int):
        self.timestamp = timestamp
        self.content = content
        self.line_number = line_number
        self.raw_line = content


class LogAnalyzer:
    """Analyzes Railway logs for patterns and errors"""

    def __init__(self):
        self.logs: List[LogEntry] = []
        self.attribute_errors: List[LogEntry] = []
        self.database_url_messages: List[LogEntry] = []
        self.deployment_markers: List[LogEntry] = []
        self.database_success: List[LogEntry] = []
        self.cache_cleared: List[LogEntry] = []
        self.other_errors: List[LogEntry] = []
        self.connection_attempts: List[LogEntry] = []

        # Patterns to search for
        self.patterns = {
            'attribute_error': re.compile(r'AttributeError', re.IGNORECASE),
            'database_url': re.compile(r'DATABASE_URL', re.IGNORECASE),
            'deployment_marker': re.compile(r'🚂\s*RAILWAY\s*DEPLOYMENT\s*CHECK', re.IGNORECASE),
            'database_success': re.compile(r'Database engine created successfully', re.IGNORECASE),
            'cache_cleared': re.compile(r'✅\s*Python cache cleared', re.IGNORECASE),
            'error': re.compile(r'\b(error|exception|failed|failure)\b', re.IGNORECASE),
            'connection': re.compile(r'(connect|connection|database)', re.IGNORECASE),
        }

    def parse_logs(self, lines: List[str]) -> None:
        """Parse log lines into structured entries"""
        for i, line in enumerate(lines, 1):
            line = line.rstrip()
            if not line:
                continue

            # Try to extract timestamp (Railway logs format)
            timestamp_match = re.match(r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)', line)
            timestamp = timestamp_match.group(1) if timestamp_match else "Unknown"

            entry = LogEntry(timestamp, line, i)
            self.logs.append(entry)

            # Categorize the log entry
            self._categorize_entry(entry)

    def _categorize_entry(self, entry: LogEntry) -> None:
        """Categorize a log entry based on patterns"""
        content = entry.content

        # Check for AttributeError
        if self.patterns['attribute_error'].search(content):
            self.attribute_errors.append(entry)

        # Check for DATABASE_URL messages
        if self.patterns['database_url'].search(content):
            self.database_url_messages.append(entry)

        # Check for deployment markers
        if self.patterns['deployment_marker'].search(content):
            self.deployment_markers.append(entry)

        # Check for database success
        if self.patterns['database_success'].search(content):
            self.database_success.append(entry)

        # Check for cache cleared
        if self.patterns['cache_cleared'].search(content):
            self.cache_cleared.append(entry)

        # Check for connection attempts
        if self.patterns['connection'].search(content):
            self.connection_attempts.append(entry)

        # Check for other errors (excluding AttributeError which is already caught)
        if self.patterns['error'].search(content) and not self.patterns['attribute_error'].search(content):
            self.other_errors.append(entry)

    def extract_database_url_info(self, entry: LogEntry) -> str:
        """Extract DATABASE_URL information from log entry"""
        # Try to extract the actual URL or relevant info
        patterns = [
            r'DATABASE_URL:\s*(\S+)',
            r'DATABASE_URL\s*=\s*(\S+)',
            r'Using DATABASE_URL:\s*(\S+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, entry.content)
            if match:
                url = match.group(1)
                # Mask sensitive info
                url_masked = re.sub(r'://([^:]+):([^@]+)@', r'://***:***@', url)
                return url_masked

        return "No URL extracted"

    def print_section(self, title: str, color: str) -> None:
        """Print a section header"""
        safe_print("\n" + "=" * 80)
        safe_print(colorize(f"  {title}", color, bold=True))
        safe_print("=" * 80)

    def print_log_entry(self, entry: LogEntry, highlight_pattern: str = None) -> None:
        """Print a log entry with optional highlighting"""
        line_num = colorize(f"[Line {entry.line_number}]", Colors.CYAN)
        timestamp = colorize(entry.timestamp, Colors.BLUE)

        content = entry.content
        if highlight_pattern:
            # Highlight the pattern in the content
            content = re.sub(
                f'({highlight_pattern})',
                lambda m: colorize(m.group(1), Colors.YELLOW, bold=True),
                content,
                flags=re.IGNORECASE
            )

        safe_print(f"{line_num} {timestamp}")
        safe_print(f"  {content}")
        safe_print("")

    def print_analysis(self) -> None:
        """Print complete analysis of logs"""
        safe_print("\n" + colorize("=" * 80, Colors.BOLD))
        safe_print(colorize("  RAILWAY LOGS ANALYSIS REPORT", Colors.CYAN, bold=True))
        safe_print(colorize("=" * 80, Colors.BOLD))
        safe_print(f"\nTotal log lines analyzed: {colorize(str(len(self.logs)), Colors.WHITE, bold=True)}")

        # Summary Statistics
        self.print_section("SUMMARY STATISTICS", Colors.MAGENTA)

        stats = [
            ("AttributeErrors Found", len(self.attribute_errors), Colors.RED),
            ("DATABASE_URL Messages", len(self.database_url_messages), Colors.YELLOW),
            ("Deployment Markers", len(self.deployment_markers), Colors.GREEN),
            ("Database Success Messages", len(self.database_success), Colors.GREEN),
            ("Cache Cleared Messages", len(self.cache_cleared), Colors.GREEN),
            ("Other Errors", len(self.other_errors), Colors.RED),
            ("Connection Attempts", len(self.connection_attempts), Colors.BLUE),
        ]

        for label, count, color in stats:
            status_icon = get_status_icon(label, count)
            safe_print(f"  {status_icon} {label:.<50} {colorize(str(count), color, bold=True)}")

        # Error Rate
        safe_print("\n" + colorize("ERROR RATE:", Colors.BOLD))
        total_errors = len(self.attribute_errors) + len(self.other_errors)
        success_count = len(self.database_success)

        if total_errors > 0 or success_count > 0:
            error_rate = (total_errors / (total_errors + success_count)) * 100 if (total_errors + success_count) > 0 else 0
            success_rate = 100 - error_rate

            error_color = Colors.RED if error_rate > 50 else Colors.YELLOW if error_rate > 20 else Colors.GREEN
            safe_print(f"  Errors: {colorize(f'{error_rate:.1f}%', error_color, bold=True)} ({total_errors} errors)")
            safe_print(f"  Success: {colorize(f'{success_rate:.1f}%', Colors.GREEN, bold=True)} ({success_count} successes)")
        else:
            safe_print("  No errors or success messages found")

        # Detailed Sections
        if self.deployment_markers:
            self.print_section(f"🚂 DEPLOYMENT MARKERS ({len(self.deployment_markers)})", Colors.GREEN)
            for entry in self.deployment_markers:
                self.print_log_entry(entry, r'🚂.*RAILWAY.*DEPLOYMENT.*CHECK')

        if self.attribute_errors:
            self.print_section(f"❌ ATTRIBUTEERRORS ({len(self.attribute_errors)})", Colors.RED)
            for entry in self.attribute_errors:
                self.print_log_entry(entry, r'AttributeError')

        if self.database_url_messages:
            self.print_section(f"🔧 DATABASE_URL MESSAGES ({len(self.database_url_messages)})", Colors.YELLOW)
            for entry in self.database_url_messages:
                self.print_log_entry(entry, r'DATABASE_URL')
                url_info = self.extract_database_url_info(entry)
                if url_info != "No URL extracted":
                    safe_print(f"  Extracted: {colorize(url_info, Colors.CYAN)}\n")

        if self.database_success:
            self.print_section(f"✅ DATABASE SUCCESS ({len(self.database_success)})", Colors.GREEN)
            for entry in self.database_success:
                self.print_log_entry(entry, r'Database engine created successfully')

        if self.cache_cleared:
            self.print_section(f"✅ CACHE CLEARED ({len(self.cache_cleared)})", Colors.GREEN)
            for entry in self.cache_cleared:
                self.print_log_entry(entry, r'✅.*Python cache cleared')

        if self.other_errors:
            self.print_section(f"⚠️  OTHER ERRORS ({len(self.other_errors)})", Colors.YELLOW)
            # Show first 10 to avoid overwhelming output
            shown = min(10, len(self.other_errors))
            for entry in self.other_errors[:shown]:
                self.print_log_entry(entry, r'\b(error|exception|failed|failure)\b')

            if len(self.other_errors) > shown:
                safe_print(colorize(f"  ... and {len(self.other_errors) - shown} more errors", Colors.YELLOW))

        # Recommendations
        self.print_section("RECOMMENDATIONS", Colors.CYAN)

        if len(self.attribute_errors) > 0:
            safe_print(colorize("  ⚠️  AttributeErrors detected!", Colors.RED, bold=True))
            safe_print("     - Check if database connection is properly initialized")
            safe_print("     - Verify DATABASE_URL environment variable is set correctly")
            safe_print("     - Review database.py for attribute access issues\n")

        if len(self.database_url_messages) == 0:
            safe_print(colorize("  ⚠️  No DATABASE_URL messages found!", Colors.RED, bold=True))
            safe_print("     - DATABASE_URL may not be set in Railway environment")
            safe_print("     - Check Railway dashboard > Variables > DATABASE_URL\n")

        if len(self.database_success) == 0:
            safe_print(colorize("  ⚠️  No successful database connections!", Colors.RED, bold=True))
            safe_print("     - Database initialization may be failing")
            safe_print("     - Check PostgreSQL service is running in Railway\n")

        if len(self.database_success) > 0 and len(self.attribute_errors) > 0:
            safe_print(colorize("  🔍 Mixed Results Detected", Colors.YELLOW, bold=True))
            safe_print("     - Database connects successfully but has AttributeErrors")
            safe_print("     - This suggests a code issue, not a connection issue")
            safe_print("     - Review the code paths that trigger AttributeErrors\n")

        if len(self.deployment_markers) > 0:
            safe_print(colorize("  ✅ Deployment markers found", Colors.GREEN, bold=True))
            safe_print(f"     - Code is being deployed successfully ({len(self.deployment_markers)} deployments)\n")

        if len(self.database_success) > len(self.attribute_errors):
            safe_print(colorize("  ✅ More successes than errors!", Colors.GREEN, bold=True))
            safe_print("     - System is mostly healthy\n")

        # Footer
        safe_print("\n" + colorize("=" * 80, Colors.BOLD))
        safe_print(colorize("  End of Analysis", Colors.CYAN, bold=True))
        safe_print(colorize("=" * 80, Colors.BOLD) + "\n")


def print_usage_instructions():
    """Print detailed usage instructions"""
    safe_print(colorize("\nRAILWAY LOGS ANALYZER - USAGE INSTRUCTIONS", Colors.CYAN, bold=True))
    safe_print("=" * 80 + "\n")

    safe_print(colorize("1. Install Railway CLI:", Colors.YELLOW, bold=True))
    safe_print("   npm i -g @railway/cli\n")

    safe_print(colorize("2. Login to Railway:", Colors.YELLOW, bold=True))
    safe_print("   railway login\n")

    safe_print(colorize("3. Link your project (if needed):", Colors.YELLOW, bold=True))
    safe_print("   railway link\n")

    safe_print(colorize("4. Get and analyze logs:", Colors.YELLOW, bold=True))
    safe_print("   # Direct pipe (analyzes in real-time)")
    safe_print("   railway logs --service backend | python analyze_railway_logs.py\n")

    safe_print("   # Save to file first, then analyze")
    safe_print("   railway logs --service backend > logs.txt")
    safe_print("   python analyze_railway_logs.py logs.txt\n")

    safe_print("   # Follow mode (live logs)")
    safe_print("   railway logs --service backend --follow | python analyze_railway_logs.py\n")

    safe_print(colorize("5. Additional Railway CLI commands:", Colors.YELLOW, bold=True))
    safe_print("   railway status              # Check deployment status")
    safe_print("   railway logs --help         # See all log options")
    safe_print("   railway variables           # List environment variables")
    safe_print("   railway up                  # Deploy current directory\n")

    safe_print("=" * 80 + "\n")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Analyze Railway logs for PostgreSQL errors and deployment issues",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  railway logs --service backend | python analyze_railway_logs.py
  python analyze_railway_logs.py railway_logs.txt
  railway logs --service backend > logs.txt && python analyze_railway_logs.py logs.txt
        """
    )

    parser.add_argument(
        'logfile',
        nargs='?',
        help='Path to log file (if not provided, reads from stdin)'
    )

    parser.add_argument(
        '--help-railway',
        action='store_true',
        help='Show Railway CLI usage instructions'
    )

    parser.add_argument(
        '--no-color',
        action='store_true',
        help='Disable colored output'
    )

    args = parser.parse_args()

    # Disable colors if requested
    if args.no_color:
        for attr in dir(Colors):
            if not attr.startswith('_'):
                setattr(Colors, attr, '')

    # Show Railway CLI help
    if args.help_railway:
        print_usage_instructions()
        return 0

    # Read logs from file or stdin
    try:
        if args.logfile:
            print(colorize(f"\nReading logs from: {args.logfile}", Colors.CYAN))
            with open(args.logfile, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
        else:
            if sys.stdin.isatty():
                print(colorize("\nError: No input provided!", Colors.RED, bold=True))
                print("\nUsage:")
                print("  python analyze_railway_logs.py <logfile>")
                print("  railway logs --service backend | python analyze_railway_logs.py")
                print("\nFor more help:")
                print("  python analyze_railway_logs.py --help")
                print("  python analyze_railway_logs.py --help-railway")
                return 1

            print(colorize("\nReading logs from stdin...", Colors.CYAN))
            lines = sys.stdin.readlines()

        if not lines:
            print(colorize("\nError: No log data to analyze!", Colors.RED, bold=True))
            return 1

        print(colorize(f"Analyzing {len(lines)} log lines...\n", Colors.CYAN))

        # Analyze the logs
        analyzer = LogAnalyzer()
        analyzer.parse_logs(lines)
        analyzer.print_analysis()

        return 0

    except FileNotFoundError:
        print(colorize(f"\nError: File '{args.logfile}' not found!", Colors.RED, bold=True))
        return 1

    except KeyboardInterrupt:
        print(colorize("\n\nAnalysis interrupted by user.", Colors.YELLOW))
        return 1

    except Exception as e:
        print(colorize(f"\nError: {str(e)}", Colors.RED, bold=True))
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
