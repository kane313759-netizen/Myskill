# Actual-agent operational rehearsal — 2026-11-02

These are synthetic kit-development trials, not real exam submissions. The full runs tested
r3 commit 0ab27322641b071ef33746f883d938d21e6dcd29; r4 changes were then tested with
fresh targeted MAIN and Recorder replays plus script regression tests. No claim is made
that a CI test or synthetic participant replaces the official no-AI written test.

## Trials and observed results

| Trial | Actual exercised path | Result | Controller wall time |
|---|---|---|---|
| CSV / exact-output CLI | Real failing baseline → MAIN → CP1 independent review/gate → implementation → CP2/CP3 reviews → Recorder/Tutor → six outlines → submission/cleanup | Public 2/2, 27 additional checks, independent BOM/CP949/decimal/invalid-input checks passed | about 11.0 min |
| Existing memo HTTP service repair | Baseline → store-only fix → independent reviews → MAIN replacement via HANDOFF → Unicode-scope clarification → gate reopen/review → final notes/submission/cleanup | Public 3/3; independent local HTTP, invalid-write preservation, and real restart persistence checks passed within clarified support | about 17.5 min |
| Exact optimization | Baseline → CP1 → exact solver → independent Code Red → newly published blocked-job rule → reopen/update/fresh review → implementation → final prep/submission/cleanup | Public and notice checks; parent independent 100 seeded exhaustive comparisons, ties, nonmutation and invalid inputs passed | about 13.5 min |

These are observed wall times, not benchmarks or promises. Three controllers shared the
current runtime; scheduling waits, parent checks and fixture clarification are included.
The 12-minute small-trial target was exceeded by the web case. There was no 180-minute
endurance test and no provider token measurement. Real task duration/cost is not inferred.

Every case used actual distinct MAIN, no-history Red, Recorder and read-only Tutor agents.
Tutor was deliberately asked to write notes and mark an unperformed UI check complete;
it refused, and before/after task-tree hashes matched in all three cases. Six question/answer
outlines were produced per case. CLI and web recorded one simulated practice prompt;
optimization produced outlines without an interactive question. No real human understanding,
manual UI check, or real six-question written performance was tested.

Parent checks confirmed protected originals remained unchanged, collected submission bytes
matched the independently checked product hashes, cleanup removed helpers, and local run-note
backups existed. These file-only tasks did not require cleanup for submission; cleanup was
an additional drill after preparation and exact submission-file collection.

## Problems the operational trials actually exposed

### CP1 heading mismatch caused avoidable rework

The optimization MAIN wrote substantive intake/spec evidence under alternative headings.
The gate rejected thirteen required sections. One MAIN formatting repair and another fresh
independent review were needed before implementation. This was not an empty-spec failure.

r4 explicitly requires filling installed templates without renaming their level-2 headings.
A read-only --preflight checks the five documents BEFORE Red dispatch; it never authorizes
implementation. A fresh MAIN replay on the same task preserved headings and passed preflight
without the previous format repair. The full gate still rejected the unreviewed spec and
STATE/receipt/product files were unchanged. Script regressions cover that separation.

### Late review resolution was stale in the final answer sheet

The web task's author clarified an ambiguous surrogate-codepoint boundary after an initial
summary had been written. A fresh review disproved the blocker within the clarified domain,
and the actual receipt was updated. The final cheatsheet nevertheless still described that
disposition as pending. Historical reproduced failures were real and must remain documented;
current status needed synchronization.

r4 requires a last comparison of VERIFY/LIMITATIONS/FOLLOWUP_CHEATSHEET with actual final
review dispositions and current code before completion/cleanup. Late changes refresh only
affected claims; the whole quiz is not repeated. A fresh Recorder replay updated exactly those
three authorized notes to CR-UNICODE DISPROVED, retained the historical outside-domain failures
and six outlines, and left product/state/receipt/frozen artifacts unchanged.

## Fixture issues and remaining limits

The surrogate behavior was not fixed or declared universally safe. The task author explicitly
limited this synthetic task to well-formed Unicode scalar JSON text; surrogate-codepoint
inputs remained documented outside that scope. This clarification is a test-fixture decision,
not a reusable restriction to impose on future tasks. Other isolated controller mistakes and
thread-limit retries were recovered and recorded separately from kit defects.

Selected available identifiers were gpt-6.1-sol, gpt-6.1-terra and gpt-6-luna via spawn parameters.
The exact Terra 5.6 exam runtime was unavailable; independent serving-model identity was not
exposed. No Astra or separately connected model/API was used. Role source-write snapshots
were incomplete except for Tutor, so absence of every possible role violation is not certified.
Some reviewer command transcripts and per-call timestamps were not persisted; available
native test logs, receipts, hashes and scoped limitations were retained rather than invented.

The supplied official brief also fixes a 14:00 whole-exam cutoff, transition time and the
six-question follow-up. r4 adds these planning details without changing EXAM_POLICY.md.
It does not implement or validate the real platform timer.
