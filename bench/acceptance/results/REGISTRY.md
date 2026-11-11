# Acceptance results registry

One row per acceptance run. Raw results live on the branch named in "Source"; values are copied verbatim,
never recomputed or filled in. `null` means the run produced no value.

| Run | Scenario | Version | Status | Source |
|---|---|---|---|---|
| S-baseline | S | 917c66a | interrupted: ended `waiting_human` after 0.26 h, goal audit not run, `verify: null` | `baseline/S` @ f459260, `bench/acceptance/results/S-baseline.json` |
| S-cloud-1 | S | 7e11f7e | done after 0.09 h, 6/6 tasks, thresholds failed: expensive_token_share 0.275, expensive_call_share 0.176 (limit 0.05); `verify: null` | `bench/acceptance/results/S-cloud-1.json` |
| S-device-1 | S | 0.1.1 (PyPI) | done after 0.09 h, 5/5 tasks; thresholds failed: expensive_token_share 0.231, expensive_call_share 0.154 (limit 0.05); `verify`: not run (verifier runtime refused, 401) | test stand report of 2026-11-11, values copied from `arteliq metrics --json --scenario S` output in that report |

## S-baseline (reference point "before" for the rewrite)

Checks against `artel/data/acceptance/S.yaml`, verbatim from S-baseline.json:

| Metric | Value | Limit | ok |
|---|---|---|---|
| expensive_token_share_max | null | 0.05 | null |
| expensive_call_share_max | 0.161 | 0.05 | false |
| autonomy_min | 0.964 | 0.95 | true |
| owner_interventions_max | 0 | 1 | true |
| no_limit_stop | false | true | true |

Other recorded values: duration_h 0.26, ended waiting_human, tasks_done 1, success_rate 0.333, steps 56,
owner_asks 2, tokens_total 0, tokens_by_runtime {codex: 0}, cost_usd null, verdict null.

Break point: two tasks (t-709c1ae1 CSV import, t-ada719df HTML report) escalated after 3 replans without
progress; their checks call `python`, absent from PATH on the owner's machine (exit 127). The project never
reached done, so neither the goal audit nor independent verification ran. Token counters are unreliable for
this run (tokens_total 0), so U3 is not measured by it.

Defects found by this run are tracked in docs/SPEC.md §10.

## S-cloud-1 (2026-11-05, master 7e11f7e, runtime claude_code)

Checks against `artel/data/acceptance/S.yaml`, verbatim from S-cloud-1.json:

| Metric | Value | Limit | ok |
|---|---|---|---|
| expensive_token_share_max | 0.275 | 0.05 | false |
| expensive_call_share_max | 0.176 | 0.05 | false |
| autonomy_min | 1.0 | 0.95 | true |
| owner_interventions_max | 0 | 1 | true |
| no_limit_stop | false | true | true |

Other recorded values: duration_h 0.09, ended done, tasks_done 6, success_rate 1.0, steps 17, owner_asks 0,
tokens_total 356129, cached_tokens 1980785, usage_missing_runs 0, tokens_per_accepted 59355, cost_usd 2.310067,
verdict null.

Conditions: an ephemeral cloud container running as root (`IS_SANDBOX=1` passed through `agent_env.pass`), no
sandbox backend (commands ran unisolated), Codex absent, so `artel acceptance verify` on another runtime did not
run. The deliverable was checked by hand outside Artel: 57 tests pass, a repeated import adds 0 rows, the October
report builds with no external links.

Expensive tier use: planner (two runs) and auditor only. The second planner run was caused by a defect: plan checks
were split at `;`, `|` and newlines before quoting was applied, so `python3 -c "..."` code was read as 18 missing
programs (`manager/plan_checks_unavailable`). Fixed on branch `fix/check-program-parse`. Without that run the
expensive token share would have been about 0.19, still above the limit: one plan and one audit are a fixed cost that
dominates a six-task project.

## S-device-1 (2026-11-11, arteliq 0.1.1 from PyPI, runtime claude_code)

First run on the owner's hardware after stage B: a clean Ubuntu 24.04 machine, Arteliq installed with
`pip install arteliq`, both CLIs present. Values as printed by `arteliq metrics --json --scenario S` on that machine:

| Metric | Value | Limit | ok |
|---|---|---|---|
| expensive_token_share_max | 0.231 | 0.05 | false |
| expensive_call_share_max | 0.154 | 0.05 | false |
| autonomy_min | 1.0 | 0.95 | true |
| owner_interventions_max | 0 | 1 | true |
| no_limit_stop | false | true | true |

Other recorded values: duration_h 0.09, ended done, tasks_done 5, success_rate 1.0, steps 13, owner_asks 0,
tokens_total 364544, tokens_per_accepted 72909, cost_usd 2.18, verdict null.

Conditions and limits of this run:
- Independent verification did not run: `arteliq acceptance verify` returned
  `codex failed: workspace routing discovery unauthorized (401)` although the CLI reported a signed-in account.
  U1 is therefore not shown by this run.
- No isolation: `arteliq providers` reported that commands run without a sandbox on that machine
  (`bwrap: setting up uid map: Permission denied`, the default restriction of unprivileged user namespaces on
  Ubuntu 24.04).
- The deliverable was run by hand on the machine: the README's check `bash e2e.sh` exited 0 with `E2E OK`
  (19 operations imported and categorised).
- The run used version 0.1.1, before the orchestration v2 changes of milestone M1; the expensive share is the
  planner and the auditor, as in S-cloud-1.
