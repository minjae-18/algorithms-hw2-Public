# Hash-table load-factor experiment

- Target capacity: 8,192; insertion rounds: 3; lookup rounds: 3
- Average chain length includes empty buckets; nonempty-chain average is shown separately.
- Theory uses the measured final load factor, not only the configured resize threshold.

| Threshold | Entries | Actual α | Avg chain | Avg nonempty chain | Successful comparisons (measured / theory) | Unsuccessful comparisons (measured / theory) | Insert (µs/key) | Hit lookup (µs/op) | Miss lookup (µs/op) |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.25 | 2,048 | 0.250 | 0.250 | 1.133 | 1.126 / 1.125 | 0.267 / 0.250 | 5.873 | 2.737 | 2.803 |
| 0.50 | 4,096 | 0.500 | 0.500 | 1.272 | 1.250 / 1.250 | 0.486 / 0.500 | 6.430 | 2.776 | 2.940 |
| 0.75 | 6,144 | 0.750 | 0.750 | 1.415 | 1.361 / 1.375 | 0.766 / 0.750 | 5.837 | 2.757 | 2.867 |
| 0.90 | 7,372 | 0.900 | 0.900 | 1.523 | 1.452 / 1.450 | 0.889 / 0.900 | 5.719 | 2.776 | 2.878 |
| 1.00 | 8,192 | 1.000 | 1.000 | 1.573 | 1.503 / 1.500 | 1.008 / 1.000 | 6.865 | 2.896 | 3.636 |
| 1.50 | 12,288 | 1.500 | 1.500 | 1.929 | 1.749 / 1.750 | 1.480 / 1.500 | 6.367 | 2.802 | 3.853 |
| 2.00 | 16,384 | 2.000 | 2.000 | 2.312 | 2.001 / 2.000 | 1.996 / 2.000 | 6.058 | 2.830 | 3.065 |
| 3.00 | 24,576 | 3.000 | 3.000 | 3.151 | 2.495 / 2.500 | 3.006 / 3.000 | 6.430 | 2.905 | 3.908 |
| 4.00 | 32,768 | 4.000 | 4.000 | 4.076 | 2.995 / 3.000 | 4.005 / 4.000 | 6.875 | 2.876 | 3.150 |

The theoretical comparison counts assume uniformly distributed keys and queries. Differences in the measured values reflect this table's deterministic string hash, finite sample, and query distribution; lookup times also include Python/runtime and machine noise.
