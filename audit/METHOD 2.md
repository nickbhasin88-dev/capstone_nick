# Moved

The model specification is now [`docs/SPEC.md`](../docs/SPEC.md): one current specification that matches the code,
merged from this file and the specification sections of `audit/logic_review/logic.md` (logic review IMP-20, L-36,
L-37).

The earlier text is in git history (`git show 2cfcb14:audit/METHOD.md`). It described the ART units rule only by its
capped branch, "raw = min(covered, eff_base_art / cost) x net / base". The code uses net / cost when donor money buys
fewer people than are covered. SPEC.md section 5 states both branches.
