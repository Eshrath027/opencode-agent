#!/usr/bin/env python3
"""Strip SAST results.json to only fields needed for analysis.

Removes metavars, errors, fingerprints, and other noise that
bloats context. Output is a compact JSON array of findings.

Usage: python preprocess.py <results.json>
"""

import json
import sys

def compact_finding(item: dict) -> dict:
    """Extract only the fields needed for security analysis."""
    extra = item.get("extra", {})
    metadata = extra.get("metadata", {})

    compact = {
        "check_id": item.get("check_id", ""),
        "path": item.get("path", ""),
        "line": item.get("start", {}).get("line", 0),
        "end_line": item.get("end", {}).get("line", 0),
        "category": metadata.get("category", ""),
        "message": extra.get("message", ""),
        "lines": extra.get("lines", ""),
        "severity": extra.get("severity", "")
    }

    # Include CWE if present (important for security classification)
    cwe = metadata.get("cwe")
    if cwe:
        compact["cwe"] = cwe

    # Include confidence/likelihood/impact if present
    for field in ("confidence", "likelihood", "impact"):
        val = metadata.get(field)
        if val:
            compact[field] = val

    # Include dataflow trace source/sink (compact form) if present
    trace = extra.get("dataflow_trace")
    if trace:
        source = trace.get("taint_source")
        if source and len(source) >= 2:
            src_info = source[1]
            if isinstance(src_info, list) and len(src_info) >= 2:
                compact["taint_source"] = src_info[1]
        sink = trace.get("taint_sink")
        if sink and len(sink) >= 2:
            sink_info = sink[1]
            if isinstance(sink_info, list) and len(sink_info) >= 2:
                compact["taint_sink"] = sink_info[1]

    # Include suggested fix if present
    fix = extra.get("fix")
    if fix:
        compact["fix"] = fix

    return compact


def main():
    if len(sys.argv) < 2:
        print("Usage: preprocess.py <results.json>", file=sys.stderr)
        sys.exit(1)

    with open(sys.argv[1], "r") as f:
        data = json.load(f)

    results = data.get("results", [])
    compact_results = [compact_finding(r) for r in results]

    print(json.dumps(compact_results, indent=2))


if __name__ == "__main__":
    main()
