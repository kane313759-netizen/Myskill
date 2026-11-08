# Understanding the actual tools and algorithms

Use during permitted task solving and preparation when the participant is a
nondeveloper. The agent retains responsibility for technical selection,
implementation and testing. The participant should be able to explain what the
chosen method does and why it fits, without reading code or becoming its engineer.
Stop assistance during any officially designated no-AI phase.

## Explain proactively at the useful moment

When choosing a material unfamiliar tool/algorithm, give a brief Korean explanation
before or alongside implementation. Refresh it after a significant method,
constraint, parameter or guarantee changes, and reconcile it with the final
candidate. Do not wait for the participant to discover the unfamiliar term or
postpone all explanation until submission. Routine edits do not need a new lesson.

Inspect actual imports, calls, configuration and execution evidence first. A
dependency manifest or earlier plan alone does not prove a method is used.
Distinguish the planned choice from the implemented and actually executed method.
Explain the parts that materially affect the result, not every library/import.

## A compact explanation grounded in this solution

For each material method, connect these facts in a few plain-language sentences:

- **Role and identity:** the actual tool/library and the algorithm or solver it
  invokes, with code/config evidence. If no separate solver exists, say so.
- **Input and output:** what this component receives, produces and contributes to
  the result; distinguish preprocessing, search/training and validation.
- **Goal and restrictions:** what is being increased/decreased and which confirmed
  constraints may not be violated. A metric, a constraint and a tie-breaker differ.
- **Why chosen:** why this method fits the actual data, task scale, tool rules and
  time budget; name one meaningful alternative and the relevant trade-off.
- **How it works here:** trace one real small input through the important step to
  its observed output. Use the same values throughout and link the source/run.
- **Limits and evidence:** what the algorithm can guarantee, what the current run
  actually established, when it may fail, and which relevant case/check supports
  the explanation. State UNKNOWN or UNVERIFIED where needed.

Give the participant a short sentence they can use to describe the actual choice.
One likely explanation question and its evidence-based answer can help clarify a
material concept; it does not require the participant to respond or pass a quiz.
Avoid code trivia, a generic glossary, unsupported runtime claims and invented
production benefits. Introduce an unfamiliar term with its concrete role.

## When the word “optimizer” appears

Determine which meaning exists in the code before teaching it:

| Actual evidence | Explain to the participant | Do not claim |
|---|---|---|
| Resource assignment/scheduling solver | It chooses decisions to improve the stated objective while obeying modeled constraints; identify the actual library, formulation and solver settings | That a library name establishes the algorithm, correct business rules or a globally optimal run |
| Greedy search, local search or another heuristic | It uses a particular selection/improvement rule to find a useful answer quickly; show its rule and an actual comparison | That “optimization” means it checked every valid answer or proved the best possible result |
| Explicit enumeration or dynamic programming | Explain the actual candidate/state space, how choices are compared and which scale assumptions make it feasible | That a separately installed optimizer was used when the code is ordinary loops or a custom algorithm |
| ML training optimizer such as an actually configured Adam/SGD | It updates model parameters to reduce training loss; distinguish this from the prediction metric and from an assignment solver | That lower training loss guarantees better held-out performance or a globally optimal model |

For an exact solver, inspect the actual termination status, objective/bound/gap
and limits when available. Distinguish a valid feasible answer, a proven optimum
under the model, a local optimum, an infeasible result and timeout/interruption
with or without a retained candidate. “Exact method” is not proof that this run
finished with an optimality guarantee. Even a proven optimum is conditional on
the correctness of the modeled problem and data.

For a heuristic, identify its actual rule and tested behavior. For a trained
model, identify the loss, parameter update and evaluation separation only where
these exist; do not force ML concepts onto a scheduling task. Seed, tolerance,
time limit or learning rate need explanation when they change a consequential
result or guarantee, not as an exhaustive parameter list.

## Example style, not an event to invent

If the actual task selects work under a capacity limit, explain along these lines
using its real names and observed values: “이 부분은 가능한 배정 중에서 목표값이
좋은 조합을 고릅니다. 다만 반드시 지켜야 하는 조건을 먼저 적용합니다. 단순히
점수가 큰 항목부터 고르면 필수 항목을 빠뜨릴 수 있어 이 방식을 골랐습니다.”
Then name the real algorithm, show an actual case and state its actual guarantee.
Do not use this story when the code or task does something else.

## Preserve participant agency without inventing understanding

Provide the explanation automatically; do not turn it into a request for the
participant to select the algorithm, debug the code or approve every change.
If they ask a question or show material confusion, answer from current evidence
and offer one short, low-pressure understanding check when useful. Continue
independent implementation; do not impose a mandatory teach-back, extra stage or
six-question rehearsal beyond the active event's requirements/request.

Record what explanation was actually delivered, the relevant candidate and any
genuine question/answer. Internal prepared notes are not delivered explanation.
Silence, agreement, a forwarded AI answer or correct assistant wording does not
prove participant understanding or manual verification. Do not manufacture those
claims. Important unresolved conceptual gaps should be explained plainly; report
remaining limits honestly instead of certifying human comprehension.
