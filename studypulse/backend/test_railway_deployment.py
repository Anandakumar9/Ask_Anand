#!/usr/bin/env python3
"""
Railway Deployment Test Script
================================

This script tests your Railway deployment to verify it's working correctly.

USAGE:
    python test_railway_deployment.py <RAILWAY_URL>
    python test_railway_deployment.py https://your-app.railway.app

    Or using environment variable:
    export RAILWAY_URL=https://your-app.railway.app
    python test_railway_deployment.py

REQUIREMENTS:
    pip install requests colorama

WHAT IT TESTS:
    - /health endpoint (if available)
    - Root / endpoint
    - Response times
    - HTTP status codes
    - Server responsiveness
    - SSL/TLS connectivity
    - DNS resolution

EXIT CODES:
    0 - All tests passed
    1 - One or more tests failed
    2 - Invalid arguments or setup error
"""

import sys
import os
import time
import argparse
from typing import Dict, List, Tuple, Optional
from urllib.parse import urlparse

try:
    import requests
    from requests.exceptions import (
        ConnectionError,
        Timeout,
        TooManyRedirects,
        RequestException,
        SSLError
    )
except ImportError:
    print("ERROR: 'requests' library not found.")
    print("Install it with: pip install requests")
    sys.exit(2)

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    HAS_COLORAMA = True
except ImportError:
    print("WARNING: 'colorama' library not found. Install for colored output.")
    print("Install it with: pip install colorama")
    HAS_COLORAMA = False
    # Fallback to no colors
    class Fore:
        GREEN = RED = YELLOW = CYAN = MAGENTA = BLUE = WHITE = ""
    class Style:
        RESET_ALL = BRIGHT = ""


class DeploymentTester:
    """Tests Railway deployment endpoints and reports results."""

    def __init__(self, base_url: str, timeout: int = 10):
        """
        Initialize the tester.

        Args:
            base_url: The Railway deployment URL
            timeout: Request timeout in seconds (default: 10)
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.results: List[Dict] = []
        self.passed = 0
        self.failed = 0

    def print_header(self, text: str):
        """Print a formatted header."""
        print(f"\n{Fore.CYAN}{'=' * 70}")
        print(f"{Fore.CYAN}{text}")
        print(f"{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}\n")

    def print_success(self, text: str):
        """Print success message."""
        print(f"{Fore.GREEN}✓ {text}{Style.RESET_ALL}")

    def print_error(self, text: str):
        """Print error message."""
        print(f"{Fore.RED}✗ {text}{Style.RESET_ALL}")

    def print_warning(self, text: str):
        """Print warning message."""
        print(f"{Fore.YELLOW}⚠ {text}{Style.RESET_ALL}")

    def print_info(self, text: str):
        """Print info message."""
        print(f"{Fore.CYAN}ℹ {text}{Style.RESET_ALL}")

    def test_endpoint(
        self,
        endpoint: str,
        method: str = "GET",
        expected_status: int = 200,
        check_response_data: bool = True,
        required_keys: Optional[List[str]] = None
    ) -> Tuple[bool, Dict]:
        """
        Test a single endpoint.

        Args:
            endpoint: The endpoint path (e.g., '/health')
            method: HTTP method (default: GET)
            expected_status: Expected HTTP status code
            check_response_data: Whether to check for valid JSON response
            required_keys: List of required keys in JSON response

        Returns:
            Tuple of (success: bool, result_data: dict)
        """
        url = f"{self.base_url}{endpoint}"
        result = {
            'endpoint': endpoint,
            'url': url,
            'success': False,
            'status_code': None,
            'response_time': None,
            'error': None,
            'data': None
        }

        print(f"\n{Fore.MAGENTA}Testing:{Style.RESET_ALL} {method} {url}")

        try:
            start_time = time.time()
            response = requests.request(
                method=method,
                url=url,
                timeout=self.timeout,
                allow_redirects=True
            )
            response_time = time.time() - start_time

            result['status_code'] = response.status_code
            result['response_time'] = response_time

            # Check status code
            if response.status_code != expected_status:
                result['error'] = f"Expected status {expected_status}, got {response.status_code}"
                self.print_error(f"Status: {response.status_code} (expected {expected_status})")
                return False, result

            self.print_success(f"Status: {response.status_code}")
            self.print_success(f"Response time: {response_time:.3f}s")

            # Check response time (warn if > 5 seconds)
            if response_time > 5.0:
                self.print_warning(f"Slow response time: {response_time:.3f}s")

            # Check content
            if check_response_data:
                try:
                    data = response.json()
                    result['data'] = data
                    self.print_success("Valid JSON response received")

                    # Check for required keys
                    if required_keys:
                        missing_keys = [key for key in required_keys if key not in data]
                        if missing_keys:
                            result['error'] = f"Missing required keys: {missing_keys}"
                            self.print_error(f"Missing keys: {', '.join(missing_keys)}")
                            return False, result
                        self.print_success(f"All required keys present: {', '.join(required_keys)}")

                    # Print sample of response data
                    print(f"{Fore.CYAN}Response data:{Style.RESET_ALL}")
                    if isinstance(data, dict):
                        for key, value in list(data.items())[:5]:  # Show first 5 keys
                            print(f"  {key}: {value}")
                        if len(data) > 5:
                            print(f"  ... and {len(data) - 5} more keys")
                    else:
                        print(f"  {str(data)[:200]}")

                except ValueError:
                    # Not JSON, check if it's HTML or text
                    content_type = response.headers.get('content-type', '')
                    if 'html' in content_type.lower():
                        self.print_warning("Received HTML response (not JSON)")
                        print(f"{Fore.CYAN}Content preview:{Style.RESET_ALL}")
                        print(f"  {response.text[:200]}...")
                    elif response.text:
                        self.print_success("Received text response")
                        print(f"{Fore.CYAN}Content preview:{Style.RESET_ALL}")
                        print(f"  {response.text[:200]}...")
                    else:
                        self.print_warning("Empty response body")

            result['success'] = True
            return True, result

        except SSLError as e:
            result['error'] = f"SSL/TLS Error: {str(e)}"
            self.print_error(f"SSL/TLS Error: {str(e)}")
            return False, result

        except Timeout:
            result['error'] = f"Request timeout (>{self.timeout}s)"
            self.print_error(f"Request timeout after {self.timeout}s")
            return False, result

        except ConnectionError as e:
            error_msg = str(e)
            if "Name or service not known" in error_msg or "getaddrinfo failed" in error_msg:
                result['error'] = "DNS resolution failed"
                self.print_error("DNS resolution failed - cannot resolve hostname")
            elif "Connection refused" in error_msg:
                result['error'] = "Connection refused"
                self.print_error("Connection refused - server not accepting connections")
            else:
                result['error'] = f"Connection error: {error_msg}"
                self.print_error(f"Connection error: {error_msg}")
            return False, result

        except TooManyRedirects:
            result['error'] = "Too many redirects"
            self.print_error("Too many redirects - possible redirect loop")
            return False, result

        except RequestException as e:
            result['error'] = f"Request failed: {str(e)}"
            self.print_error(f"Request failed: {str(e)}")
            return False, result

        except Exception as e:
            result['error'] = f"Unexpected error: {str(e)}"
            self.print_error(f"Unexpected error: {str(e)}")
            return False, result

    def run_tests(self):
        """Run all deployment tests."""
        self.print_header(f"Testing Railway Deployment: {self.base_url}")

        # Test 1: Health endpoint
        self.print_info("Test 1/3: Health endpoint")
        success, result = self.test_endpoint(
            '/health',
            expected_status=200,
            check_response_data=True,
            required_keys=None  # Don't require specific keys, just check it responds
        )
        self.results.append(result)
        if success:
            self.passed += 1
        else:
            self.failed += 1
            # If health endpoint fails, it might not exist - that's okay
            if result.get('status_code') == 404:
                self.print_warning("Health endpoint not found (404) - this is optional")

        # Test 2: Root endpoint
        self.print_info("Test 2/3: Root endpoint")
        success, result = self.test_endpoint(
            '/',
            expected_status=200,
            check_response_data=True,
            required_keys=None
        )
        self.results.append(result)
        if success:
            self.passed += 1
        else:
            self.failed += 1

        # Test 3: Check for common error pages
        self.print_info("Test 3/3: Server responsiveness")
        # Just verify we can connect and don't get 502/503/504
        success, result = self.test_endpoint(
            '/',
            expected_status=200,
            check_response_data=False
        )
        if result.get('status_code') in [502, 503, 504]:
            self.print_error(f"Server error: {result['status_code']}")
            self.print_error("The server is not responding properly (bad gateway/service unavailable)")
            self.failed += 1
        elif result.get('status_code') == 500:
            self.print_error("Internal server error (500)")
            self.failed += 1
        else:
            self.print_success("Server is responsive")
            self.passed += 1

    def print_summary(self):
        """Print test summary."""
        self.print_header("Test Summary")

        total = self.passed + self.failed
        print(f"Total tests: {total}")
        print(f"{Fore.GREEN}Passed: {self.passed}{Style.RESET_ALL}")
        print(f"{Fore.RED}Failed: {self.failed}{Style.RESET_ALL}")

        if self.failed == 0:
            print(f"\n{Fore.GREEN}{Style.BRIGHT}✓ All tests passed!{Style.RESET_ALL}")
            print(f"{Fore.GREEN}Your Railway deployment is working correctly.{Style.RESET_ALL}")
            return 0
        else:
            print(f"\n{Fore.RED}{Style.BRIGHT}✗ Some tests failed.{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Please check the errors above and verify your deployment.{Style.RESET_ALL}")
            return 1


def validate_url(url: str) -> str:
    """
    Validate and normalize the URL.

    Args:
        url: The URL to validate

    Returns:
        Normalized URL

    Raises:
        ValueError: If URL is invalid
    """
    if not url:
        raise ValueError("URL cannot be empty")

    # Add https:// if no scheme provided
    if not url.startswith(('http://', 'https://')):
        url = f'https://{url}'

    # Parse and validate
    parsed = urlparse(url)
    if not parsed.netloc:
        raise ValueError(f"Invalid URL: {url}")

    return url


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Test Railway deployment endpoints',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_railway_deployment.py https://your-app.railway.app
  python test_railway_deployment.py your-app.railway.app
  RAILWAY_URL=https://your-app.railway.app python test_railway_deployment.py

Environment Variables:
  RAILWAY_URL    Railway deployment URL (can be used instead of argument)
        """
    )

    parser.add_argument(
        'url',
        nargs='?',
        help='Railway deployment URL (e.g., https://your-app.railway.app)'
    )

    parser.add_argument(
        '-t', '--timeout',
        type=int,
        default=10,
        help='Request timeout in seconds (default: 10)'
    )

    args = parser.parse_args()

    # Get URL from argument or environment variable
    url = args.url or os.environ.get('RAILWAY_URL')

    if not url:
        print(f"{Fore.RED}ERROR: No URL provided.{Style.RESET_ALL}")
        print("\nUsage:")
        print(f"  python {os.path.basename(__file__)} <RAILWAY_URL>")
        print(f"  python {os.path.basename(__file__)} https://your-app.railway.app")
        print("\nOr set RAILWAY_URL environment variable:")
        print(f"  export RAILWAY_URL=https://your-app.railway.app")
        print(f"  python {os.path.basename(__file__)}")
        sys.exit(2)

    # Validate URL
    try:
        url = validate_url(url)
    except ValueError as e:
        print(f"{Fore.RED}ERROR: {e}{Style.RESET_ALL}")
        sys.exit(2)

    # Run tests
    tester = DeploymentTester(url, timeout=args.timeout)

    try:
        tester.run_tests()
        exit_code = tester.print_summary()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Tests interrupted by user.{Style.RESET_ALL}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Fore.RED}Unexpected error: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        sys.exit(2)


if __name__ == '__main__':
    main()
