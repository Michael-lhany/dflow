#!/usr/bin/env bash

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    echo "Run this script with: source ./activate.sh"
    exit 1
fi

dflow_script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
dflow_activate_file="$dflow_script_dir/.venv/bin/activate"

if [[ ! -f "$dflow_activate_file" ]]; then
    echo "DFlow virtual environment not found. Create it with: python -m venv .venv"
    unset dflow_script_dir dflow_activate_file
    return 1
fi

source "$dflow_activate_file"
unset dflow_script_dir dflow_activate_file
