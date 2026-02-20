#!/bin/bash
# Simple wrapper that generates digest and outputs it
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Run digest generation (v2 with new storage)
bash run_digest_v2.sh 2>/dev/null

# Output is already printed by run_digest_v2.sh
