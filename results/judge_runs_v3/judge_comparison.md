# Judge comparison against the owner's labels

Each rule cell: agreement / misses of owner fails / false alarms. Misses on Rules 1 and 4 matter most.

| Judge | Rule 1 agree / misses / false alarms | Rule 2 | Rule 3 | Rule 4 | Cost per draft | Latency per draft (s, 8 in parallel) | Wall time (s) | Flakes (Rule 1/4) | Judge errors |
|---|---|---|---|---|---|---|---|---|---|
| code checks only | 24/40 · 16 of 16 · 0 | 36/40 · 4 of 5 · 0 | 24/40 · 15 of 23 · 1 | 40/40 · 0 of 14 · 0 | $0 | 0.0 | 0 | – | – |
| claude-haiku-5-5 | 39/40 · 0 of 16 · 1 | 38/40 · 2 of 5 · 0 | 29/40 · 7 of 23 · 4 | 40/40 · 0 of 14 · 0 | $0.00135 | 8.9 | 49 | 3 (1) | 0 |
| claude-sonnet-5-5 | 39/40 · 0 of 16 · 1 | 40/40 · 0 of 5 · 0 | 29/40 · 6 of 23 · 5 | 40/40 · 0 of 14 · 0 | $0.02329 | 11.4 | 64 | 3 (0) | 0 |
| claude-opus-5-5 | 39/40 · 0 of 16 · 1 | 38/40 · 2 of 5 · 0 | 29/40 · 6 of 23 · 5 | 40/40 · 0 of 14 · 0 | $0.04601 | 15.3 | 86 | 2 (0) | 0 |
