---
name: final-explain
description: Prepare the participant for the official no-AI written follow-up using only actual task evidence, code, tests, decisions, and directly verified behavior.
---

For confirmed finals or finals practice, use the explanation section of
`hackathon-finals` under FINALS_POLICY.md instead of the preliminary procedure below.
Do not inherit the preliminary role, gate or six-question rules into finals.

This skill produces the factual system explanation at CP3. It does not run a quiz or invoke `followup-prep`; the orchestrator invokes that skill once.

Use:
- actual task/spec
- GRADER.md / BASELINE.md / CONSTRAINTS.md / DECISIONS.md / VERIFY.md
- current code/config
- business-contact answers
- things the user actually verified

Follow citations back to original evidence. A note or MAIN's summary alone does not establish a fact. Distinguish CONFIRMED / ASSUMPTION / UNVERIFIED; missing evidence is not a passing check.

Use `references/participant-understanding.md` in the active kit. Explain the actual
material tools and algorithms, why selected over an applicable alternative, their
input/output and limits, with one observed case and source/config/run evidence.
For an optimizer, distinguish the library, actual solver/search/training method,
objective, constraints and observed termination/guarantee. A name or a lower loss
is not proof of global optimality. Explain proactively; do not certify human
understanding or add a mandatory extra quiz.

Explain only components that exist:
1. problem solved
2. input
3. processing
4. storage/persistence if any
5. output
6. external connections if any
7. actual system boundaries
8. runtime/container only if present
9. important confirmed constraints
10. key design decisions and alternatives
11. what was verified
12. what remains unverified / limited

For a nondeveloper participant, explain the distinctions needed to operate or hand off
the actual result: an authoritative update's changed and preserved behavior; the
confirmed objective/tie order and consequential preferences the contract expressly
excludes; and unfamiliar runtime terms. When a container exists, distinguish its
build step, image artifact, running container, and persistent data. Keep these
task-conditional, use plain language and existing input/expected/observed examples,
and cite the original evidence or mark the boundary unverified. This adds no quiz,
checkpoint, or technical design decision for the participant.

Compress to:
input → processing → storage(if any) → output → external(if any)

Trace one actual record/request through the relevant stages with consistent recorded
values. Mark any unobserved stage honestly; do not splice unrelated examples into a
claimed single verified run.

Cross-check material numbers, units and counts across the explanation, summary and
answer outlines against cited current outputs. Define different measures explicitly
(for example physical lines versus accepted records); do not silently equate them.
Give runnable commands exactly as supported by the inspected current interface and
target environment. Cite the execution that verified them, or mark them UNVERIFIED;
do not present a different platform's command as having run here.

Include two compact evidence anchors in the explanation actually delivered:
- **Before and now:** one actual pre-edit baseline outcome and the corresponding
  current check/result, with source/version and input/policy/checker scope. A setup
  failure or unavailable baseline with its reason is valid; it is not a fabricated
  initial score. If scope or check counts changed, describe the observations
  separately and do not calculate a score improvement.
- **A rule applied to a real case:** when the task selects, filters or rejects
  inputs, describe one actually observed retained/excluded case: the relevant input,
  decisive original rule, and observed result. Explain in ordinary task language why
  it stayed or was excluded; a list of rules or bug titles alone is insufficient.
  Prefer an actual exclusion or competing-input decision when available. A successful
  calculation alone does not explain a selection/filtering decision.
  For a task without that workflow, use an actual relevant validation/boundary case.
  If no such case was observed, say NOT OBSERVED / UNVERIFIED; do not invent a case,
  imply an unrun test passed, or start a costly new test just to fill the story.

These anchors belong in the existing short explanation, not a new quiz, checkpoint
or participant decision. Cite actual evidence and make them understandable without
memorizing code, identifiers or precise timestamps.

Return a concise explanation with source locations, verified results, and limitations to the orchestrator and Recorder. Recorder is the sole writer of explanation notes under `.hackathon-kit/run/`; do not race it with your own note edits.

The official follow-up is 6 questions × 5 minutes without AI/copy-paste. This explanation is preparation during task solving only. `followup-prep` owns any rehearsal within the remaining submission time.
