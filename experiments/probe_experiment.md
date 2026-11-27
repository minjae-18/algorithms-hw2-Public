# Linear probing and chaining search-cost experiment

- Capacity: 8,192; same deterministic key set per load factor.
- Cost is the average number of nodes or slots examined per lookup.
- Successful and unsuccessful queries use separate, deterministic key sets.
- Theory assumes uniform hashing for chaining and the standard approximation for linear probing; finite samples and primary clustering cause differences.
- Theory: chaining hit = 1 + α/2; miss = α. Linear probing hit = 0.5 × (1 + 1/(1-α)); miss = 0.5 × (1 + 1/(1-α)^2).
- Graph legend: blue/green = chaining hit/miss; orange/red = linear-probing hit/miss; solid = measured, dashed = theory.

| Load α | Chaining hit measured / theory | Chaining miss measured / theory | Linear hit measured / theory | Linear miss measured / theory |
| ---: | ---: | ---: | ---: | ---: |
| 0.1 | 1.044 / 1.050 | 0.099 / 0.100 | 1.051 / 1.056 | 1.117 / 1.117 |
| 0.2 | 1.105 / 1.100 | 0.195 / 0.200 | 1.136 / 1.125 | 1.287 / 1.281 |
| 0.3 | 1.162 / 1.150 | 0.295 / 0.300 | 1.240 / 1.214 | 1.543 / 1.520 |
| 0.4 | 1.205 / 1.200 | 0.392 / 0.400 | 1.338 / 1.333 | 1.857 / 1.888 |
| 0.5 | 1.259 / 1.250 | 0.496 / 0.500 | 1.528 / 1.500 | 2.561 / 2.500 |
| 0.6 | 1.312 / 1.300 | 0.605 / 0.600 | 1.824 / 1.750 | 3.780 / 3.625 |
| 0.7 | 1.358 / 1.350 | 0.701 / 0.700 | 2.266 / 2.166 | 6.542 / 6.054 |
| 0.8 | 1.406 / 1.400 | 0.796 / 0.800 | 3.181 / 2.999 | 13.417 / 12.991 |
| 0.9 | 1.457 / 1.450 | 0.895 / 0.900 | 5.731 / 5.495 | 62.851 / 50.402 |
