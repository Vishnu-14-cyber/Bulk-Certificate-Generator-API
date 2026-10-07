#!/usr/bin/env python
"""
CertiForge Automated Test Suite Runner
Runs pytest programmatically and reports summary.
"""
import sys
import pytest

if __name__ == "__main__":
    print("=" * 65)
    print("  CertiForge Test Suite Execution")
    print("=" * 65)
    
    args = ["tests/", "-v", "--tb=short"]
    if len(sys.argv) > 1:
        args = sys.argv[1:]
        
    exit_code = pytest.main(args)
    sys.exit(exit_code)



