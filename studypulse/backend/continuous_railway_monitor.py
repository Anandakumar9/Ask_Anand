#!/usr/bin/env python3
"""
Continuous Railway Deployment Monitor
Automatically tests Railway deployment every 5 minutes until PostgreSQL connection succeeds.
"""
import sys
import time
import subprocess
import json
from datetime import datetime
from typing import Dict, List, Tuple

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_banner():
    """Print monitoring banner."""
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BOLD}🔍 CONTINUOUS RAILWAY DEPLOYMENT MONITOR{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")

def check_railway_cli() -> bool:
    """Check if Railway CLI is installed."""
    try:
        result = subprocess.run(['railway', '--version'],
                              capture_output=True,
                              text=True,
                              timeout=5)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False

def get_railway_logs() -> str:
    """Fetch latest Railway logs."""
    try:
        result = subprocess.run(
            ['railway', 'logs', '--service', 'backend', '--limit', '100'],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return result.stdout
        return ""
    except Exception as e:
        print(f"{RED}❌ Error fetching logs: {e}{RESET}")
        return ""

def analyze_logs(logs: str) -> Dict[str, bool]:
    """Analyze logs for key indicators."""
    indicators = {
        'cache_cleared': '✅ Python cache cleared' in logs,
        'deployment_marker': '🚂 RAILWAY DEPLOYMENT CHECK - POSTGRES ENABLED' in logs,
        'database_connected': '✓ Database engine created successfully' in logs or 'Database engine created successfully' in logs,
        'database_url_set': 'DATABASE_URL' in logs and 'postgresql' in logs,
        'attribute_error': 'AttributeError' in logs and 'DB_POOL_SIZE' in logs,
        'sqlalchemy_error': 'Could not parse SQLAlchemy URL' in logs,
        'connection_error': 'connection' in logs.lower() and 'error' in logs.lower()
    }
    return indicators

def print_status(iteration: int, indicators: Dict[str, bool]) -> bool:
    """Print current status. Returns True if all checks pass."""
    print(f"\n{BOLD}📊 Iteration #{iteration} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}")
    print(f"{BLUE}{'─'*80}{RESET}")

    # Check positive indicators
    checks_passed = 0
    total_checks = 3

    if indicators['cache_cleared']:
        print(f"{GREEN}✅ Cache Cleared: PASS{RESET}")
        checks_passed += 1
    else:
        print(f"{RED}❌ Cache Cleared: NOT FOUND{RESET}")

    if indicators['deployment_marker']:
        print(f"{GREEN}✅ Deployment Marker: PRESENT{RESET}")
        checks_passed += 1
    else:
        print(f"{RED}❌ Deployment Marker: MISSING{RESET}")

    if indicators['database_connected']:
        print(f"{GREEN}✅ Database Connection: SUCCESS{RESET}")
        checks_passed += 1
    else:
        print(f"{RED}❌ Database Connection: FAILED{RESET}")

    # Check for errors
    has_errors = False
    if indicators['attribute_error']:
        print(f"{RED}⚠️  AttributeError detected (DB_POOL_SIZE){RESET}")
        has_errors = True

    if indicators['sqlalchemy_error']:
        print(f"{RED}⚠️  SQLAlchemy URL parsing error{RESET}")
        has_errors = True

    if indicators['connection_error']:
        print(f"{YELLOW}⚠️  Connection-related error found{RESET}")
        has_errors = True

    # Summary
    print(f"\n{BOLD}Summary:{RESET} {checks_passed}/{total_checks} checks passed")

    success = checks_passed == total_checks and not has_errors

    if success:
        print(f"\n{GREEN}{BOLD}🎉 ALL CHECKS PASSED! PostgreSQL is working!{RESET}")
        return True
    else:
        print(f"\n{YELLOW}⏳ Waiting 5 minutes before next check...{RESET}")
        return False

def monitor_continuously(interval_seconds: int = 300):
    """Monitor Railway deployment continuously."""
    print_banner()

    # Check if Railway CLI is available
    if not check_railway_cli():
        print(f"{RED}❌ Railway CLI not found!{RESET}")
        print(f"\n{YELLOW}Please install Railway CLI:{RESET}")
        print("  npm i -g @railway/cli")
        print("  railway login")
        print("\nAlternatively, monitor manually in Railway dashboard.")
        return

    print(f"{GREEN}✅ Railway CLI detected{RESET}")
    print(f"{BLUE}Monitoring every {interval_seconds//60} minutes...{RESET}\n")

    iteration = 1

    while True:
        try:
            # Fetch logs
            print(f"{BLUE}Fetching Railway logs...{RESET}")
            logs = get_railway_logs()

            if not logs:
                print(f"{YELLOW}⚠️  No logs retrieved. Railway may be building...{RESET}")
                print(f"{BLUE}Waiting {interval_seconds//60} minutes...{RESET}\n")
                time.sleep(interval_seconds)
                iteration += 1
                continue

            # Analyze logs
            indicators = analyze_logs(logs)

            # Print status
            success = print_status(iteration, indicators)

            # Exit if all checks pass
            if success:
                print(f"\n{GREEN}{BOLD}✅ Monitoring complete. PostgreSQL connection verified!{RESET}\n")
                break

            # Wait before next iteration
            print(f"{BLUE}{'─'*80}{RESET}")
            for remaining in range(interval_seconds, 0, -60):
                mins = remaining // 60
                print(f"\r{YELLOW}⏱️  Next check in {mins} minute(s)...{RESET}", end='', flush=True)
                time.sleep(60)
            print()  # New line after countdown

            iteration += 1

        except KeyboardInterrupt:
            print(f"\n\n{YELLOW}⚠️  Monitoring stopped by user{RESET}")
            print(f"Total iterations: {iteration - 1}\n")
            break
        except Exception as e:
            print(f"\n{RED}❌ Error during monitoring: {e}{RESET}")
            print(f"{YELLOW}Retrying in 1 minute...{RESET}\n")
            time.sleep(60)

def main():
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h']:
        print("""
Continuous Railway Deployment Monitor

Usage:
  python continuous_railway_monitor.py [interval_minutes]

Arguments:
  interval_minutes    How often to check (default: 5 minutes)

Examples:
  python continuous_railway_monitor.py           # Check every 5 minutes
  python continuous_railway_monitor.py 10        # Check every 10 minutes
  python continuous_railway_monitor.py 1         # Check every 1 minute (for debugging)

Requirements:
  - Railway CLI installed: npm i -g @railway/cli
  - Logged in: railway login

Press Ctrl+C to stop monitoring at any time.
        """)
        return

    # Get interval from command line
    interval_minutes = 5
    if len(sys.argv) > 1:
        try:
            interval_minutes = int(sys.argv[1])
            if interval_minutes < 1:
                print(f"{RED}Error: Interval must be at least 1 minute{RESET}")
                return
        except ValueError:
            print(f"{RED}Error: Invalid interval. Must be a number.{RESET}")
            return

    interval_seconds = interval_minutes * 60

    # Start monitoring
    monitor_continuously(interval_seconds)

if __name__ == '__main__':
    main()
