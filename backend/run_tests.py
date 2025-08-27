#!/usr/bin/env python3
"""
Test runner script for the FocusFlow backend.

This script demonstrates the comprehensive testing setup for the CRUD layer.
It showcases production-ready testing practices for data scientists and AI engineers.
"""

import subprocess
import sys
from typing import List


def run_command(command: List[str], description: str) -> bool:
    """Run a command and return True if successful."""
    print(f"\n{'='*50}")
    print(f"🧪 {description}")
    print(f"{'='*50}")
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False


def main():
    """Run comprehensive test suite."""
    print("🚀 FocusFlow Backend Test Suite")
    print("Demonstrating production-ready testing practices")
    
    test_commands = [
        (
            ["pytest", "tests/test_crud/", "-v", "--tb=short"],
            "Running CRUD Layer Unit Tests"
        ),
        (
            ["pytest", "tests/test_crud/", "--tb=short", "-q"],
            "Quick Test Run (Summary)"
        ),
        (
            ["pytest", "tests/test_crud/test_session_crud.py::TestCRUDSession::test_create_session", "-v"],
            "Running Single Test Example"
        ),
        (
            ["pytest", "tests/", "--collect-only", "-q"],
            "Test Discovery (Show all available tests)"
        )
    ]
    
    results = []
    
    for command, description in test_commands:
        success = run_command(command, description)
        results.append((description, success))
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")
    
    for description, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} - {description}")
    
    total_passed = sum(1 for _, success in results if success)
    print(f"\nOverall: {total_passed}/{len(results)} test suites passed")
    
    # Final message
    print(f"\n{'='*60}")
    print("🎯 PRODUCTION-READY FEATURES DEMONSTRATED:")
    print("   • Comprehensive unit testing with pytest")
    print("   • Test isolation with fresh database sessions")
    print("   • Fixture-based test data management")
    print("   • Full CRUD operation coverage")
    print("   • Edge case and error condition testing")
    print("   • Relationship and cascade testing")
    print("   • Database-agnostic testing (SQLite for tests)")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
