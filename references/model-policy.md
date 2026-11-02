# Model role policy — exam-specific

The official brief recommends Sol 6.1, Terra 5.6, Luna 6, and Sol 6.0.
Actual model availability must be verified in the provided Codex environment.

## Roles

### ORCHESTRATOR
Preferred: Terra 5.6.
Owns phase/checkpoint state and agent dispatch.
**No product-source edits.**

### MAIN_BUILDER
Preferred: Sol 6.1.
Owns problem understanding, specification, architecture, implementation, integration, difficult fixes, final explanation.
Sole product-source writer.

### CODE_RED
Preferred: fresh Terra context.
Reviews implementation, contract compatibility, regression, persistence/retry, and tests.
No product-source edits.

### CONSTRAINT_RED
Preferred: fresh independent Sol 6.1 context.
Reviews spec assumptions, grader contract, constraints, objective loopholes, and domain-specific realism only when applicable.
No product-source edits.

### RECORDER
Preferred: Luna 6.
Writes only evidence notes under .hackathon-kit/run/.

## Fallback

If a preferred model is unavailable:
1. keep the role boundaries
2. use the strongest allowed available model appropriate to the role
3. record the actual model used
4. never claim a model switch occurred without verifying it

## Review priority by task

- optimization/operations: Constraint Red is especially important
- debugging/web/API: Code Red may be the stronger CP2 reviewer
- algorithm/parser: exact contract and hidden-test behavior dominate
- ML/data science: metric/leakage/reproducibility dominate

CP1 and CP3 remain independent reviews regardless of type.
