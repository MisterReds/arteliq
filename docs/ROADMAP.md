# Дорожная карта Arteliq

Сгенерировано из `roadmap.yaml` командой `arteliq roadmap render`. Правки — только в yaml. Что уже взято и откуда — [ADOPTED.md](ADOPTED.md); опоры — [ARCHITECTURE.md](ARCHITECTURE.md).

Режимы: **pillar** — опора, контракт закреплён `tests/test_invariants.py`; **design** — структурное изменение, делается вручную; **evolve** — реализует сам Arteliq (`arteliq evolve --roadmap`).

## Опоры

| Опора | Что | Источник | Статус |
|---|---|---|---|
| P1-modularity | Everything is a plugin — manifests, reversible effects, hot reload, swappable runtimes | DeepSeek Harness | готово |
| P2-skills | Self-improving skill library — create/patch after hard tasks, read-before-write, ledger, lifecycle, guard | Hermes Agent | готово |
| P3-goal-loop | Work until done — continuation, no-progress backoff, evidence, reviewer and auditor decide | Prime Agent | готово |
| P4-souls | Workers with souls — SOUL/IDENTITY/RULES/MEMORY and a private workspace | OpenClaw | готово |
| P5-transparency | Append-only event log; every model and tool call recorded; live dashboard | DeepSeek Harness | готово |
| P6-kanban | Kanban DAG with compare-and-swap claims | Hermes Agent | готово |
| P7-measured-evolution | Evolution through branches, tests, hidden-check benchmark, population screening and stacking | auto-harness / Gear / Ouroboros | готово |

## Волна 0 — 11/11 готово

| Пункт | Что | Откуда | Режим | Статус |
|---|---|---|---|---|
| D-self-update | Self-update from the dashboard and CLI, verified by the pillar tests before switching, rollback | Arteliq (`MisterReds/arteliq`) | design | готово |
| D-brand | Brand identity: A-frame mark, copper palette, bundled fonts, role icons, terminal colours | Arteliq (`MisterReds/arteliq`) | design | готово |
| D-codex-runtime | Codex runtime (ChatGPT subscription) with device-code login | Codex / Hermes Agent (`openai/codex`) | design | готово |
| D-providers | Провайдеры page: subscriptions, keys (set/unset only), local model, per-role routing, CLIs installed on demand without Node.js | Arteliq (`MisterReds/arteliq`) | design | готово |
| D-installers | Installers for Linux/macOS and Windows that install only what Arteliq needs | Arteliq (`MisterReds/arteliq`) | design | готово |
| D-failure-classes | No crash, no endless loop: auto executor, setup errors to a person, limits wait, replan cap | Arteliq (`MisterReds/arteliq`) | design | готово |
| D-evolution-ops | Evolution operations: adopt mode for roadmap items, resume after restart, pause on provider limits, journal on GitHub | Arteliq (`MisterReds/arteliq`) | design | готово |
| D-provider-failover | Provider failover on limits, disabling runtimes, model lists from the CLIs, Claude and Codex sign-in from the dashboard, live agents panel | Arteliq (`MisterReds/arteliq`) | design | готово |
| D-semantic-retrieval | Meaning-based search, local and private: EmbeddingGemma 2 via llama.cpp, hybrid with BM25, skills by relevance, `search` tool | Google EmbeddingGemma 2 (`google/embeddinggemma-2`) | design | готово |
| D-doctor | Diagnostician: when something fails, a read-only worker on an available model (not the failing one) explains the cause and the steps; rules without a model; automatic note in tasks that stop for a person; 'Почему?' buttons and arteliq why | Arteliq (`MisterReds/arteliq`) | design | готово |
| D-failure-reports | Failure reports: every failure is a redacted text report with the diagnosis — to the owner's Telegram, to the developers as a GitHub issue (one per failure, repeats as comments) | Arteliq (`MisterReds/arteliq`) | design | готово |

## Волна 1 — 8/8 готово

| Пункт | Что | Откуда | Режим | Статус |
|---|---|---|---|---|
| W1-loop-detector | Loop detector — identical tool calls in a row and repeated text stop the run with a corrective note | Qwen Code (`QwenLM/qwen-code`) | evolve | готово — evolve/gen-2 (evolve/g2-1-w1-loop-detector-loop-detector-i) |
| W1-evidence-window | Evidence window keeps head and tail, cuts the middle | Qwen Code (`QwenLM/qwen-code`) | evolve | готово — evolve/gen-2 (evolve/g2-2-w1-evidence-window-evidence-wind) |
| W1-output-spill | Oversized tool output spills to a file with a preview and the path | OpenCode (`anomalyco/opencode`) | evolve | готово — evolve/gen-3 (evolve/g3-1-w1-output-spill-oversized-tool-o) |
| W1-read-cache | Stale-edit guard — refuse edits to files changed since the agent last read them | Qwen Code (`QwenLM/qwen-code`) | evolve | готово — evolve/gen-2 (evolve/g2-4-w1-read-cache-stale-edit-guard-r) |
| W1-fuzzy-edit | Fuzzy edit application (whitespace-normalized, then block-anchor match) | OpenCode (`anomalyco/opencode`) | evolve | готово — evolve/gen-3 (evolve/g3-2-w1-fuzzy-edit-fuzzy-edit-applica) |
| W1-post-write-diagnostics | Diagnostics right after a write (py_compile / configured linters) | OpenCode (`anomalyco/opencode`) | evolve | готово — evolve/gen-3 (evolve/g3-3-w1-post-write-diagnostics-diagno) |
| W1-compaction | Context compaction for the native runtime — clear old tool outputs, then summarize | Claude Code / OpenCode (`anomalyco/opencode`) | evolve | готово — evolve/gen-3 (evolve/g3-4-w1-compaction-context-compaction) |
| W1-snapshots | Shadow-git snapshot per run; rejected attempt can be reverted | OpenCode (`anomalyco/opencode`) | evolve | готово — evolve/gen-3 (evolve/g3-5-w1-snapshots-shadow-git-snapshot) |

## Волна 2 — 9/10 готово

| Пункт | Что | Откуда | Режим | Статус |
|---|---|---|---|---|
| W2-worktree-isolation | Worker isolation — git worktree (or container) per task, merge on acceptance | Archon / Gas Town / Qwen Code (`QwenLM/qwen-code`) | design | готово — feat/isolation-sandbox: opt-in `isolation.worktrees` — a git worktree per task (artel/worktree.py), pre-review merge of the base, merge into shared/ on acceptance, discard on START OVER, conflicts go back to the worker as a task comment (never overwritten); containers not done |
| W2-execpolicy | Command policy rules allow/prompt/forbidden with match/not_match examples validated at load | Codex (`openai/codex`) | evolve | готово — evolve/gen-4 (merged by hand after a conflict with the System One change) |
| W2-guardian | Asynchronous trajectory risk reviewer; high risk switches later actions to blocking review | Codex (`openai/codex`) | evolve | готово — evolve/gen-5 (evolve/g5-1-w2-guardian-asynchronous-traject) |
| W2-sandbox | bubblewrap sandbox for worker bash | Codex (`openai/codex`) | design | готово — feat/isolation-sandbox: opt-in `sandbox.mode` (artel/sandbox.py) — bubblewrap on Linux (verified for real), sandbox-exec profile on macOS (built, not run on a Mac), unsandboxed fallback with a note or `require: true` refusal; gates sandboxed on `sandbox.gates` |
| W2-fs-grants | Explicit read/write grants per path | OpenScience (`synthetic-sciences/openscience`) | evolve | готово — evolve/gen-5 (evolve/g5-2-w2-fs-grants-explicit-read-write) |
| W2-cost-down | Bring cost back down — wave 1 raised the benchmark cost from $4.57 to $5.99 (+31%) | Claude Code / Codex (`anthropics/claude-code`) | evolve | готово — evolve/gen-4 (merged by hand after a conflict with the System One change) |
| W2-ci | CI on Linux, macOS and Windows — tests, installer and a scripted first run on every push | OpenHands / Codex (`openai/codex`) | design | частично — .github/workflows/ci.yml: ubuntu/macos/windows x Python 3.10/3.13 run the full suite, install.sh / install.ps1 into a temporary home cloning the checkout, then scripts/ci_smoke.py (scripted first run ends done, dashboard answers /api/ready). Code made portable (UTF-8 I/O, POSIX shell via Git Bash on Windows, process-tree stop, POSIX paths in journal keys, restart without execv on Windows). Open: a green run on macOS/Windows is not yet observed; blocking merges on CI needs branch protection, and the evolution publish gate is not wired to it. |
| W2-remote-and-notify | Use from the phone — authenticated remote dashboard and notifications (Telegram / webhook) | Hermes Agent / OpenClaw (`NousResearch/hermes-agent`) | design | готово — Telegram bot (control, answers, notifications, one-time pairing) and `arteliq web --remote`: token login (scrypt hash only, rotatable), server-side HttpOnly SameSite=Strict sessions, per-IP rate limit, HTTPS recipes (Caddy, Tailscale) with an insecure-connection banner; installable PWA (manifest, icons, shell-only service worker) |
| W2-timezone | User time zone for every time shown (dashboard, CLI, notifications), e.g. Asia/Sakhalin | Arteliq (`MisterReds/arteliq`) | evolve | готово — evolve/gen-4 (merged by hand after a conflict with the System One change) |
| W2-evolve-two-subscriptions | Evolution across two subscriptions (Claude Code and Codex) so one provider's limit does not stop it | Arteliq (`MisterReds/arteliq`) | design | готово — evolve.runtimes [claude_code, codex]: a limit moves implementation and benchmark to the next runtime, pause only when all are limited; baselines per (commit, runtime) (tests/test_evolve_runtimes.py) |

## Волна 3 — 7/7 готово

| Пункт | Что | Откуда | Режим | Статус |
|---|---|---|---|---|
| W3-acp-runtime | ACP runtime plugin — any ACP agent (Claude Code, Codex, Gemini, OpenHands) as a worker | OpenHands (`OpenHands/OpenHands`) | design | готово — feat/acp-runtime — runtime `acp` (artel/runtimes/acp.py): ACP v1 client over stdio with presets chosen per role (`acp:gemini`, `acp:claude`…); Arteliq's MCP proxy passed in session/new; session/update mirrored to the event log; permissions and fs/* by role policy; resume in the same session; tests with a stand-in ACP agent; handshake checked against the real Gemini CLI and the Claude ACP adapter. |
| W3-dsh-runtime | DeepSeek Harness as a runtime plugin, so dsh plugins work inside Arteliq workers | DeepSeek Harness (`deepseek-ai/deepseek-harness`) | design | готово — Runtime `dsh` (artel/runtimes/dsh.py) on the official Python SDK; dsh plugins (profile packages and patch layers) load unchanged, Arteliq tools over dsh-mcp-client; verified for real (boot, MCP tool discovery, missing-key classification, no key used) and end to end against a stand-in SDK (tests/test_dsh.py) |
| W3-plugin-packages | Plugin packages (install from git/pip), lifecycle events before_agent_start / session_shutdown | Pi (`badlogic/pi-mono`) | design | готово — feat/plugin-packages: arteliq plugins install|list|show|enable|disable|update|remove (git, pip, path; ARTEL_HOME/plugins + plugins.json; static manifest, installed disabled), lifecycle events project_start / before_agent_start / agent_end / task_done / project_end / session_shutdown, failing plugins disabled with the error, dashboard section, examples/artel-plugin-hello |
| C-agents-md | Project instruction files — AGENTS.md / CLAUDE.md / GEMINI.md / .clinerules read into every agent's context | Codex / Claude Code / Gemini CLI (`openai/codex`) | evolve | готово — AGENTS.md / CLAUDE.md / GEMINI.md / .clinerules, nearest wins, 16 KiB cap |
| C-mcp-client | External MCP servers for agents — configured once, available to every runtime (Playwright browser preset) | Claude Code / Gemini CLI / goose / Cline (`anomalyco/opencode`) | evolve | готово — external MCP servers per role; judges only read_only servers; secrets by variable name |
| C-rea-pack | Reverse-engineering pack (REA) — workers can investigate binaries, JS/Electron bundles, .NET, APKs and websites | REA (Reverse Engineer Anything) (`morluto/rea`) | evolve | готово — REA as skill + CLI (arteliq skills import morluto/rea); not MCP: 207 tool schemas would cost every run |
| A-munder-work-tokens | Count cache reads separately: budgets on work tokens, costs with cache prices | Munder Difflin (`chaitanyagiri/munder-difflin`) | evolve | готово — usage shape in/out/cached; budgets count in+out (stage B) |

## M0 · Чистый стол — 5/5 готово

| Пункт | Что | Откуда | Режим | Статус |
|---|---|---|---|---|
| M0-check-parse | Quote-aware parsing of plan checks (no false "missing programs", no needless expensive replan) | Arteliq (`MisterReds/arteliq`) | design | готово — merged b6f8451 |
| M0-run-lock | Cross-process run lock: a project runs in one process; the dashboard shows "running elsewhere" and refuses resume | Arteliq (`MisterReds/arteliq`) | design | готово — merged fe8cf81 |
| M0-release | First public release: PyPI 0.1.0, licence file, repository description and topics | Arteliq (`MisterReds/arteliq`) | design | готово — 0.1.1 on PyPI; Apache-2.0; repository description and topics are the owner's settings |
| M0-ci-flakes | Root causes of the two unexplained CI failures (Windows test_remote WinError 10053; macOS 3.13) | Arteliq (`MisterReds/arteliq`) | design | готово — merged fe8cf81: refused POST drains the body; run.pid written atomically |
| M0-dev-budget | Development token budget rules in CLAUDE.md; gate temp files ignored | Arteliq (`MisterReds/arteliq`) | design | готово — rules in CLAUDE.md; /setup.cfg and mutants/ ignored |

## M1 · Доказательство S — 1/9 готово

| Пункт | Что | Откуда | Режим | Статус |
|---|---|---|---|---|
| W3-plan-review | Plan review before execution; built-in Explore / Plan / Verification subagents | Fusion / Claude Code (`lintsinghua/claude-code-book`) | design | план |
| M1-expensive-diet | Planning and acceptance by orchestration v2: plan on the mid profile checked by a code plan lint; acceptance by another provider as a project step; no strong-model plan review | Arteliq (`MisterReds/arteliq`) | design | план |
| M1-thresholds | Re-specify U3 and U4: absolute expensive cap for S, share for L; U4 against the control arm | Arteliq (`MisterReds/arteliq`) | design | план |
| M1-preflight | Acceptance preflight: interpreter, sandbox backend, both runtimes, expected runtime per role | Arteliq (`MisterReds/arteliq`) | design | план |
| M1-control-arm | Three arms on one scenario and budget: one agent session without Arteliq, solo, team; goal with independent verdict, owner interventions, p50/p95 time, tokens by profile | Arteliq (`MisterReds/arteliq`) | design | план |
| M1-s-x3 | S three times in a row on the owner's machine with a cross-provider verdict | Arteliq (`MisterReds/arteliq`) | design | план |
| M1-solo-mode | Solo by default: one worker leads a low or medium goal in one session by a checklist with checks; the rest becomes board tasks when the session's context budget runs out | Arteliq (`MisterReds/arteliq`) | design | план |
| M1-effort-ladder | Escalation ladder for a task: first attempt at medium effort, retry at high effort, environment diagnosis on a repeated cause, then the strong profile in a new session, then the manager | Arteliq (`MisterReds/arteliq`) | design | план |
| M1-native-tiers | Defect: API runs put every role on the default strongest model because the native profile table is empty | Arteliq (`MisterReds/arteliq`) | design | готово |

## M2 · Профили качества (П10) — 0/5 готово

| Пункт | Что | Откуда | Режим | Статус |
|---|---|---|---|---|
| C-lsp | Diagnostics after every edit — language server or linter errors returned in the same turn | OpenCode / Crush / Qwen Code / Aider (`anomalyco/opencode`) | design | план |
| C-methodology-skills | Bundled methodology skills — brainstorm, bite-sized plan, TDD, verification, systematic debugging, spec | Superpowers / Spec Kit (`obra/superpowers`) | design | план |
| A-deerflow-typed-criteria | Machine-checkable acceptance criteria (file exists / non-empty / json-valid, tests_passed:<cmd>) decided in code | DeerFlow (`bytedance/deer-flow`) | design | план |
| P10-quality-profiles | Quality profiles: catalogue by result type and level, checks generated from the profile, reviewer checklist | Arteliq (`MisterReds/arteliq`) | design | план |
| P10-fix-discipline | Fix discipline for workers and reviewer (failing test as evidence); manager attacks the premise after a repeated failure | Arteliq (`MisterReds/arteliq`) | design | план |

## M3 · Ядро: каталог моделей, FSM, сторож (П4, П6) — 0/11 готово

| Пункт | Что | Откуда | Режим | Статус |
|---|---|---|---|---|
| W3-durable | Durable turns and idempotent run receipts — resume mid-turn after a crash | Pi / OpenScience (`badlogic/pi-mono`) | design | план |
| W3-state-machine | Task as a state machine with executable transition gates | StateM (`henryqin1997/statem`) | design | план |
| W3-tree-budget | Budget for the whole agent tree with threshold reminders | Codex (`openai/codex`) | design | план |
| A-ecc-run-heartbeat-watchdog | Silent-run watchdog: a CLI worker with no stream events for N minutes is killed and retried as 'hung' | ECC (`affaan-m/ECC`) | design | план |
| A-fusion-file-scope-lease | File-scope leases: tasks declare the paths they write; overlapping tasks never run at the same time | Fusion (`Runfusion/Fusion`) | design | план |
| A-fusion-novelty-loop-window | Loop detector catches alternating loops: low-novelty window over recent tool-call fingerprints | Fusion (`Runfusion/Fusion`) | design | план |
| P4-model-catalog | Model catalogue and capability profiles in config; select_model is a pure function; no vendor names in logic | Arteliq (`MisterReds/arteliq`) | design | план |
| P6-fsm-orchestrator | Task and project state machine with an effect-only orchestrator; team scheduling per profession; Manager removed | Arteliq (`MisterReds/arteliq`) | design | план |
| M3-watchdog-resume | Project watchdog for progress and drift; resume after a crash or machine sleep without repeating side effects | Arteliq (`MisterReds/arteliq`) | design | план |
| M3-arch-zero | Empty archcheck baselines: import cycles and module-level mutable state removed | Arteliq (`MisterReds/arteliq`) | design | план |
| M3-project-requests | A project lives long and holds many requests: bound to an existing folder or repository; a request runs on its own branch; accepting it merges and makes a rollback point | Arteliq (`MisterReds/arteliq`) | design | план |

## M4 · Управление и внимание владельца (П7) — 0/17 готово

| Пункт | Что | Откуда | Режим | Статус |
|---|---|---|---|---|
| W3-two-phase-memory | Two-phase memory — per-run extraction with secret redaction, then consolidation | Codex (`openai/codex`) | design | план |
| C-rewind | Rewind from the dashboard — every accepted step is a checkpoint a person can return a task or the deliverables to | Claude Code / Cline / Gemini CLI (`anomalyco/opencode`) | design | план |
| C-spec-artifacts | Spec artifacts — constitution and spec per project, kept in sync with the plan and audited against | Spec Kit / OpenSpec / MetaGPT (`github/spec-kit`) | design | план |
| A-hive-chat-reply | Answer a waiting task from the phone: Telegram reply routed back to the task by an HMAC reference | Hive (`aden-hive/hive`) | design | план |
| A-hive-escalation-filter | Filter spurious 'ask a human' blocks: a cheap check sends permission-seeking back to work | Hive (`aden-hive/hive`) | design | план |
| A-agentteams-secret-free-env | Workers never see provider secrets: tool and CLI environments are scrubbed of keys and tokens | AgentTeams (`agentscope-ai/AgentTeams`) | design | план |
| A-omc-clarify-gate | Clarify vague goals before planning: ambiguity score, up to three questions to the owner | oh-my-claudecode (`Yeachan-Heo/oh-my-claudecode`) | design | план |
| A-omc-secret-redaction | Redact secrets from the event log, tool results and notifications | oh-my-claudecode (`Yeachan-Heo/oh-my-claudecode`) | design | план |
| P7-intent | Intent with versions and owner confirmation in the dashboard and Telegram | Arteliq (`MisterReds/arteliq`) | design | план |
| P7-decision-log | Decision Log: every manager decision records why and what next | Arteliq (`MisterReds/arteliq`) | design | план |
| P7-controls | Pause, step rollback, autonomy modes off/observe/auto, budget from the dashboard — as state machine events | Arteliq (`MisterReds/arteliq`) | design | план |
| P7-knowledge-scopes | Knowledge by scope: project, shared library (read-only for agents), owner skills; promotion on evidence | Arteliq (`MisterReds/arteliq`) | design | план |
| P7-attention-outbox | Requests to the owner as structured Attention records; outgoing messages through an outbox with receipts | Arteliq (`MisterReds/arteliq`) | design | план |
| P7-secrets | Secrets never enter model context; secrets redacted from the event log, tool results and notifications | Arteliq (`MisterReds/arteliq`) | design | план |
| P7-proactive-observe | Proactive work in observe mode: rules from the owner, a 'would have done' record with a cost forecast in the Decision Log, a separate hard budget | Arteliq (`MisterReds/arteliq`) | design | план |
| M4-connections | Connections of a project: environments, keys in the system keychain, a per-project SSH key; workers use a credential without seeing its value | Arteliq (`MisterReds/arteliq`) | design | план |
| M4-actions | Named project actions (run, tests, publish to an environment, logs, rollback) detected from the project or saved after a first run; external and irreversible ones behind a confirmation sheet | Arteliq (`MisterReds/arteliq`) | design | план |

## M5 · Долгий горизонт: приложения над оболочкой, L, провайдеры (П8, U2, U7) — 0/5 готово

| Пункт | Что | Откуда | Режим | Статус |
|---|---|---|---|---|
| P8-apps-over-shell | Dashboard routes, CLI and Telegram over the shell API; no direct imports of core or adapters | Arteliq (`MisterReds/arteliq`) | design | план |
| M5-l-run | Scenario L: six hours or more on the owner's machine without a limit stop | Arteliq (`MisterReds/arteliq`) | design | план |
| M5-u7 | S on the second provider and with a local model as executor | Arteliq (`MisterReds/arteliq`) | design | план |
| M5-conversation-ui | Conversation-first interface: the request stream with result cards in the centre, preview, changes and files beside it; the board and the journal as a secondary view | Arteliq (`MisterReds/arteliq`) | design | план |
| M5-c-run | Scenario C (ongoing project): an existing repository and a series of ten requests including a publish and a rollback | Arteliq (`MisterReds/arteliq`) | design | план |

## M6 · Выпуск 1.0 (П9) — 0/4 готово

| Пункт | Что | Откуда | Режим | Статус |
|---|---|---|---|---|
| P9-acceptance | Acceptance report v2: U1-U8 against thresholds with the control arm | Arteliq (`MisterReds/arteliq`) | design | план |
| M6-docs | English documentation, SECURITY.md, CONTRIBUTING, changelog; versioned data schema of the home directory with migration | Arteliq (`MisterReds/arteliq`) | design | план |
| M6-security-review | External review of sandbox, command policy, root wrapper and remote mode | Arteliq (`MisterReds/arteliq`) | design | план |
| M6-onboarding | First run for a stranger: one command on a clean machine to a first verified result | Arteliq (`MisterReds/arteliq`) | design | план |

## После 1.0 (найдено разбором проектов) — 0/24 готово

| Пункт | Что | Откуда | Режим | Статус |
|---|---|---|---|---|
| D-multimodal-retrieval | Multimodal memory: images, audio and video in deliverables and across projects; fully local RAG with Gemma 4 | Google EmbeddingGemma 2 (`google/embeddinggemma-2`) | design | план |
| W3-fresh-context-steps | Fresh context per step, verified state outside the context | LongHorizon-Harness (`AMAP-ML/LongHorizon-Harness`) | evolve | план |
| W3-mailbox | Agent mailbox and teams | Claude Code / Gas Town (`lintsinghua/claude-code-book`) | evolve | план |
| W3-automations | Automations — schedule and event triggers | OpenHands / Qwen Code (`QwenLM/qwen-code`) | evolve | план |
| C-task-tool | Subagents on demand — a worker delegates a sub-question to a child agent with a fresh context and gets a summary back | Claude Code / OpenCode / Deep Agents / Hermes (`anomalyco/opencode`) | design | план |
| C-web-tools | web_search and web_fetch for the native runtime (CLI runtimes already have their own) | Gemini CLI / OpenCode (`anomalyco/opencode`) | evolve | план |
| C-user-hooks | User hooks from the config — shell commands on before_tool / after_tool / task_done / project_end, can block a tool call | Claude Code / Crush / Qwen Code (`anthropics/claude-code`) | evolve | план |
| C-headless-ci | Headless runs and GitHub — `arteliq run --json`, a GitHub Action, @artel in issues and pull requests | Claude Code / Gemini CLI / Codex / OpenHands (`openai/codex`) | design | план |
| C-repo-map | Repo map — a ranked map of the codebase's files and symbols in the worker's context | Aider (`Aider-AI/aider`) | evolve | план |
| C-user-profile | Owner profile (USER.md) — what the team knows about the person it works for, learned and editable | OpenClaw / Hermes Agent (`NousResearch/hermes-agent`) | evolve | план |
| C-channels | More channels — Slack and Discord next to Telegram, one channel interface | OpenClaw / Hermes Agent (`openclaw/openclaw`) | evolve | план |
| C-exec-backends | Execution backends — Docker container and SSH host per task next to the local sandbox | OpenHands / Hermes Agent / DeerFlow (`OpenHands/OpenHands`) | design | план |
| C-worker-screen | Each worker has its own screen — a private virtual display in its workspace, never the owner's screen | Anthropic computer-use reference / OpenClaw (`anthropics/claude-quickstarts`) | design | план |
| C-best-of-n | Best of N for hard tasks — several workers (or runtimes) on one task in separate worktrees, the reviewer picks | Orca / Qwen Code Agent Arena (`stablyai/orca`) | design | план |
| C-evolution-archive | Evolution keeps an archive of variants, not only a champion — parents sampled for diversity | Darwin Gödel Machine / OpenEvolve (`jennyzzt/dgm`) | design | план |
| A-ecc-paired-promotion | Free hypotheses win only on paired repeats: minimum samples, mean delta and per-task win rate | ECC (`affaan-m/ECC`) | design | план |
| A-fusion-external-obstacle-classes | Failure classes for network and host problems: transient network retries free, full disk goes to a person | Fusion (`Runfusion/Fusion`) | evolve | план |
| A-fusion-review-dispute | Workers can dispute a review finding; the next reviewer must rule on each dispute | Fusion (`Runfusion/Fusion`) | evolve | план |
| A-omc-review-tiers | Review effort scaled to the change: light review for small diffs, full review for large or sensitive ones | oh-my-claudecode (`Yeachan-Heo/oh-my-claudecode`) | evolve | план |
| X-evolution-unfreeze | Unfreeze evolution: candidates chosen on a working set, confirmed on a held-out set | Arteliq (`MisterReds/arteliq`) | design | план |
| X-relay-android | Relay server with end-to-end encryption and the Android client, SPEC П8b | Arteliq (`MisterReds/arteliq`) | design | план |
| X-native-shell | Native desktop shell with tray, only if the installed web app is not enough, SPEC П8a step 2 | Arteliq (`MisterReds/arteliq`) | design | план |
| X-proactive | Proactive work in auto mode: verified results only, usefulness measured, a rule below the threshold switches itself off (SPEC §14) | Arteliq (`MisterReds/arteliq`) | design | план |
| X-ui-english | English interface next to Russian | Arteliq (`MisterReds/arteliq`) | design | план |

## Изученные проекты — 7

Код прочитан агентом-аналитиком (`arteliq absorb` / `arteliq evolve --cycle`); найденное стало пунктами выше.

| Проект | Лицензия | Найдено | В карту | Итог |
|---|---|---|---|---|
| `affaan-m/ECC` | MIT | 7 | A-ecc-paired-promotion, A-ecc-run-heartbeat-watchdog | Plugin/skill bundle for Claude Code plus an alpha Rust control plane (ecc2): SQLite sessions, daemon, worktrees, deterministic risk scoring, notifications with  |
| `Runfusion/Fusion` | MIT | 9 | A-fusion-file-scope-lease, A-fusion-novelty-loop-window, A-fusion-external-obstacle-classes, A-fusion-review-dispute | TypeScript kanban 'software factory': PROMPT.md plans with file scope, worktree per task, plan/execute/review gates, stuck-task detector, external-obstacle clas |
| `bytedance/deer-flow` | MIT | 4 | A-deerflow-typed-criteria | LangGraph super-agent: lead agent, sub-agents with acceptance criteria checked in code, sandboxes, skills, memory backends, goals evaluated after each run, doct |
| `aden-hive/hive` | Apache-2.0 | 5 | A-hive-chat-reply, A-hive-escalation-filter | Python colony runtime: a Queen agent loop clones itself into workers, tracker ledger, crash-safe park/resume, Sentinel out-of-band escalation over Telegram/Slac |
| `agentscope-ai/AgentTeams` | Apache-2.0 | 4 | A-agentteams-secret-free-env | Kubernetes-native manager/worker platform: Matrix rooms for human visibility, MinIO shared files, Higress gateway holding credentials, TeamHarness task transiti |
| `Yeachan-Heo/oh-my-claudecode` | MIT | 7 | A-omc-clarify-gate, A-omc-review-tiers, A-omc-secret-redaction | Claude Code plugin: team pipeline plan/prd/exec/verify/fix, deep-interview ambiguity gate, verification tiers, notifications with a reply listener and token red |
| `chaitanyagiri/munder-difflin` | MIT | 6 | A-munder-work-tokens | Electron desktop app wrapping many terminal agent CLIs as an office: git-backed hive mailbox with a single committer, markdown memory, runaway circuit breaker ( |

Итого: 41/116 пунктов готово.
