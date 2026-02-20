#!/usr/bin/env python3
"""
Send HN digest - just output the digest text
The cron agent will handle sending via message tool
"""
import subprocess
import sys

def main():
    # Run the digest generation
    result = subprocess.run(
        ['./run_digest.sh'],
        cwd='/Users/vb/.openclaw/workspace/hn-digest',
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"Error generating digest: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    
    # Read and output the digest
    with open('/Users/vb/.openclaw/workspace/hn-digest/digest.txt') as f:
        digest = f.read()
    
    print(digest)

if __name__ == "__main__":
    main()
