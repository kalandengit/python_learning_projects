#!/bin/bash

set -eux -o pipefail

# Assumes this script is run from the project root
PROJECT_ROOT="$(pwd)"
KALANFA_HOME="$(mktemp -d)"
PYTHONPATH="${PYTHONPATH:-}"

# Prepend project root to python path
if [ -n "$PYTHONPATH" ]; then
  PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH}"
else
  PYTHONPATH="${PROJECT_ROOT}"
fi

export KALANFA_HOME
export PYTHONPATH

# Clean existing DBs and generate fresh DBs
rm -rf kalanfa/dist/home
(cd kalanfa && python -m kalanfa manage deprovision --destroy-all-user-data --permanent-irrevocable-data-loss)
mkdir -p kalanfa/dist/home
cp $KALANFA_HOME/*.sqlite3 kalanfa/dist/home/
rm -rf $KALANFA_HOME

# disable command echoing
set +x

# Verify DBs
declare -A QUERY_MATRIX
QUERY_MATRIX["select count(*) from morango_databaseidmodel;"]="db.sqlite3"
QUERY_MATRIX["select count(*) from morango_instanceidmodel;"]="db.sqlite3"
QUERY_MATRIX["select count(*) from discovery_networklocation;"]="networklocation.sqlite3"
QUERY_MATRIX["select count(*) from jobs;"]="job_storage.sqlite3"

echo "Verifying databases..."

for QUERY in "${!QUERY_MATRIX[@]}"; do
  DB=${QUERY_MATRIX[$QUERY]}
  ROW_COUNT=$(sqlite3 -cmd ".headers off" kalanfa/dist/home/$DB "$QUERY")
  if [ "$ROW_COUNT" -ne 0 ]; then
    echo "Preseeded DBs have existing data | $ROW_COUNT = $QUERY"
    exit 1
  fi
done

echo "Done! Preseeded databases generated"
