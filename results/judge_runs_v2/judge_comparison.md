# Judge comparison against the owner's labels

Each rule cell: agreement / misses of owner fails / false alarms. Misses on Rules 1 and 4 matter most.

| Judge | Rule 1 agree / misses / false alarms | Rule 2 | Rule 3 | Rule 4 | Cost per draft | Latency per draft (s, 8 in parallel) | Wall time (s) | Flakes (Rule 1/4) | Judge errors |
|---|---|---|---|---|---|---|---|---|---|
| code checks only | 24/40 · 16 of 16 · 0 | 39/40 · 1 of 2 · 0 | 24/40 · 15 of 23 · 1 | 40/40 · 0 of 14 · 0 | $0 | 0.0 | 0 | – | – |
| ⚠ claude-haiku-5-5 (errors: not comparable) | 33/40 · 0 of 16 · 7 | 39/40 · 0 of 2 · 1 | 30/40 · 6 of 23 · 4 | 40/40 · 0 of 14 · 0 | $0.00144 | 9.6 | 52 | 6 (3) | 3 |
| claude-sonnet-5-5 | 34/40 · 0 of 16 · 6 | 38/40 · 0 of 2 · 2 | 29/40 · 6 of 23 · 5 | 40/40 · 0 of 14 · 0 | $0.02376 | 11.8 | 62 | 3 (1) | 0 |
| claude-opus-5-5 | 39/40 · 0 of 16 · 1 | 38/40 · 0 of 2 · 2 | 29/40 · 6 of 23 · 5 | 40/40 · 0 of 14 · 0 | $0.04722 | 15.5 | 85 | 4 (0) | 0 |
