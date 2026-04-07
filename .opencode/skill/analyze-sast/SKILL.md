---
name: analyze-sast
description: Analyze SAST findings from Semgrep to determine true vulnerabilities vs false positives. Use when the user wants to triage SAST results, analyze security findings, or generate final_results.json.
argument-hint: <results.json> <code-dir>
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, Bash(python *), Agent, Write
---
# SAST Finding Analyzer

You are analyzing SAST (Static Application Security Testing) findings to classify each as a true vulnerability or false positive.

## Inputs

- **Results file**: `$ARGUMENTS[0]` (Semgrep results.json)
- **Code directory**: `$ARGUMENTS[1]` (directory containing the scanned source code)

## Step 1: Preprocess findings

Run the preprocessing script to strip noise from the results file. This removes metavars, errors, fingerprints, and references — keeping only fields needed for analysis.

```
run python3 preprocess.py results.json
```

Save the output — this is your compact finding list.

## Step 2: Analyze each finding using parallel subagents

For EACH finding in the compact list, spawn a **parallel subagent** (using the Agent tool with `subagent_type: "sast-finding-analyzer"`) to analyze it in isolation. This prevents context overflow.

Pass each subagent a prompt containing:
1. The single compact finding as JSON
2. The code directory path: `$ARGUMENTS[1]`
3. Instructions to read ONLY 30 lines around the flagged line (`offset = max(0, line - 15)`, `limit = 30`)
4. Instructions to check one level of dependency if the flagged code calls another function (grep for the definition, read 20 lines around it)
5. Instructions to return a JSON object with exactly: `check_id`, `false_positive` (boolean), `reason` (plain text, no source code)

Launch ALL finding subagents in parallel (in a single message with multiple Agent tool calls).

## Step 3: Assemble output

Collect all subagent results. Write the final output as a JSON array to `final_results.json` in the same directory as the results file.

The output file must contain ONLY a valid JSON array:
```json
[
    {
        "check_id": "example-check-id",
        "false_positive": true,
        "reason": "Brief explanation of why this is or is not a vulnerability."
    }
]
```

## Analysis criteria for subagents to apply

When analyzing each finding, consider:
- **Input validation**: Is user input validated/sanitized before reaching the flagged code?
- **Framework protections**: Does the framework provide built-in protections (e.g., ORM parameterization, template auto-escaping)?
- **Code context**: Is the flagged pattern actually dangerous in this specific usage?
- **Exploitability**: Can an attacker realistically reach and exploit this code path?
- **shell=True vs list args**: For subprocess findings, `subprocess.run(cmd_list)` without `shell=True` is NOT vulnerable to shell injection
- **Regex patterns vs secrets**: Regex patterns containing key headers (e.g., `-----BEGIN.*KEY-----`) are NOT hardcoded secrets
- **Best practices vs vulnerabilities**: Findings in the "best-practice" category are recommendations, not exploitable vulnerabilities — classify them as NOT false positives (they are valid recommendations)