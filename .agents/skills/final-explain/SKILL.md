---
name: final-explain
description: Stop feature work and prepare a non-developer for no-AI follow-up questions using only evidence from the actual solution.
---

Use actual code, config, tests, business-contact answers, and verified behavior.

Explain:
1. problem solved
2. input
3. processing flow
4. storage and persistence
5. output
6. external connections
7. frontend/backend/data boundaries
8. runtime/container role if present
9. important constraints and why
10. key decisions and alternatives
11. what was verified
12. what remains uncertain

Then compress to:
input → processing → storage → output → external

Quiz the user one question at a time.
Correction format:
- what was right
- only the incorrect/missing part
- one concrete example
