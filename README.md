# SK hynix AI Hackathon Starter Kit

This repository is a **task-domain-agnostic workflow kit for the SK hynix AI hackathon exam format**.
It is intentionally exam-specific about rules and follow-up preparation, but it does **not** assume the task itself is routing, web, Docker, ML, or any other domain.

## Official-exam priorities

Read `EXAM_POLICY.md` first.

Core confirmed constraints include:
- task solving up to 180 minutes
- no Computer Use / automated UI control
- no external AI/model connection
- no external transmission of problem/files/results
- no Git Push
- public GitHub tools / Skills / MCP / Plugins may be downloaded subject to those restrictions
- follow-up written test is 6 × 5 minutes without AI/copy-paste
- recommended provided models include Sol 6.1, Terra 5.6, Luna 6, Sol 6.0

Newer official exam/task instructions always override this kit.

## Role policy

- **ORCHESTRATOR — Terra 5.6 when available:** state/checkpoint management only; no product-source edits.
- **MAIN_BUILDER — persistent Sol 6.1 when available:** sole product-source writer from specification through implementation.
- **CODE_RED — fresh Terra context:** code/contract/regression review only.
- **CONSTRAINT_RED — fresh independent Sol 6.1 context:** spec/assumption/objective review only.
- **RECORDER — Luna when available:** writes evidence notes only under `.hackathon-kit/run/`.

If an exact model is unavailable, preserve the role separation and use the strongest allowed available substitute. Verify actual model selection in the provided Codex environment.

## Safe install — clone outside the task repository

Linux / cloud shell:

```bash
KIT_DIR="$(mktemp -d)"
git clone --depth 1 https://github.com/kane313759-netizen/Myskill.git "$KIT_DIR"
bash "$KIT_DIR/install.sh" .
```

PowerShell:

```powershell
$KitDir = Join-Path $env:TEMP ("Myskill-" + [guid]::NewGuid())
git clone --depth 1 https://github.com/kane313759-netizen/Myskill.git $KitDir
powershell -ExecutionPolicy Bypass -File (Join-Path $KitDir "install.ps1") -Target .
```

The installer:
- does not overwrite an existing skill directory
- copies exam policy/support files into `.hackathon-kit/`
- initializes runtime notes under `.hackathon-kit/run/` without overwriting them on reinstall
- adds kit paths to local `.git/info/exclude` when a Git worktree exists
- records exactly which skill directories it installed

Offline backup: keep a frozen ZIP of this repository before exam day.

## First Codex message

```text
Use the hackathon-orchestrator skill.
Read .hackathon-kit/EXAM_POLICY.md first.
Start from grader intake and baseline.
Do not implement product logic until CP1 Spec Freeze closes the constraint gate.
```

## Fixed checkpoints

- **CP1 SPEC FREEZE:** fresh Constraint Red before implementation.
- **CP2 FIRST END-TO-END:** fresh Code Red + Recorder; Constraint Red only if risk warrants.
- **CP3 PRE-SUBMIT:** final Code Red + Constraint Red + Recorder + verification + final-explain.

No review agent should be spawned for every small edit.

## Core vs conditional playbooks

Always-start core:
- grader-intake
- immutable-inventory
- task-router
- problem-intake
- constraint-discovery
- verification
- final-explain

Conditional only when task evidence supports them:
- optimization
- web-app
- api-integration
- agent-chatbot
- automation
- debugging
- data-profiler
- algorithm-cli
- ml-data-science
- document-processing
- security-review

## Before submission

Run:

```bash
bash .hackathon-kit/scripts/doctor.sh
```

Use cleanup only after final explanation prep and only if the submission format requires removing local helper files:

```bash
bash .hackathon-kit/scripts/clean.sh --apply
```

The cleanup script backs up `.hackathon-kit/run/` to a local temp directory before removal.

## Mental rule

> **First learn what is scored. Then freeze the contract. Then implement. Then attack the code and the problem separately. Finally explain only what actually exists.**
