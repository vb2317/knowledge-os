#!/usr/bin/env python3
"""
Send HN digest - just output the digest text
The cron agent will handle sending via message tool
"""
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent

def main():
    # Run the digest generation
    result = subprocess.run(
        ['./run_digest.sh'],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"Error generating digest: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    
    # Read and output the digest
    with open(PROJECT_ROOT / 'digest.txt') as f:
        digest = f.read()
    
    print(digest)

if __name__ == "__main__":
    main()
