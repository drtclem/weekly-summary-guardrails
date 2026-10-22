# Judge comparison against the owner's labels

Each rule cell: agreement / misses of owner fails / false alarms. Misses on Rules 1 and 4 matter most.

| Judge | Rule 1 agree / misses / false alarms | Rule 2 | Rule 3 | Rule 4 | Cost per draft | Latency per draft (s, 8 in parallel) | Wall time (s) | Flakes (Rule 1/4) | Judge errors |
|---|---|---|---|---|---|---|---|---|---|
| code checks only | 24/40 · 16 of 16 · 0 | 39/40 · 1 of 2 · 0 | 24/40 · 15 of 23 · 1 | 40/40 · 0 of 14 · 0 | $0 | 0.0 | 0 | – | – |
| ⚠ claude-haiku-5-5 (errors: not comparable) | 38/40 · 1 of 16 · 1 | 39/40 · 0 of 2 · 1 | 29/40 · 7 of 23 · 4 | 40/40 · 0 of 14 · 0 | $0.00139 | 9.5 | 52 | 6 (3) | 2 |
| claude-sonnet-5-5 | 38/40 · 2 of 16 · 0 | 38/40 · 0 of 2 · 2 | 30/40 · 5 of 23 · 5 | 40/40 · 0 of 14 · 0 | $0.02370 | 12.2 | 70 | 3 (0) | 0 |
| claude-opus-5-5 | 39/40 · 1 of 16 · 0 | 38/40 · 0 of 2 · 2 | 30/40 · 5 of 23 · 5 | 40/40 · 0 of 14 · 0 | $0.04620 | 15.3 | 84 | 1 (0) | 0 |
| ⚠ gpt-6-luna (errors: not comparable) | 37/40 · 3 of 16 · 0 | 37/40 · 0 of 2 · 3 | 30/40 · 1 of 23 · 9 | 40/40 · 0 of 14 · 0 | $0.00086 | 21.0 | 118 | 4 (2) | 1 |
| gpt-6.1-sol | 35/40 · 5 of 16 · 0 | 38/40 · 0 of 2 · 2 | 31/40 · 3 of 23 · 6 | 40/40 · 0 of 14 · 0 | $0.01217 | 14.9 | 84 | 3 (0) | 0 |
| gpt-6-astra | 35/40 · 5 of 16 · 0 | 39/40 · 0 of 2 · 1 | 31/40 · 1 of 23 · 8 | 40/40 · 0 of 14 · 0 | $0.05944 | 16.4 | 89 | 2 (0) | 0 |
