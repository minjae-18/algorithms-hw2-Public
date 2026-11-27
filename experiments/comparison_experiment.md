# Hash-table implementation comparison

- Python: 3.13.5
- Platform: Linux-6.8.0-1070-azure-x86_64-with-glibc2.41
- Build rounds: 3; lookup rounds: 5
- Keys are deterministic random-looking strings; every result is checked.
- Fresh string objects are used for each build round to avoid reusing cached string hashes.
- The built-in dictionary is used only as the benchmark comparison target.
- Times are measured on this runtime and machine; they are not portable guarantees.

| Entries | Chaining insert (us/key) | dict insert (us/key) | Chaining hit (us/op) | dict hit (us/op) | Chaining miss (us/op) | dict miss (us/op) |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2,048 | 8.231 | 0.110 | 3.539 | 0.071 | 2.866 | 0.036 |
| 8,192 | 9.443 | 0.112 | 3.148 | 0.081 | 2.847 | 0.047 |
| 16,384 | 8.150 | 0.114 | 3.169 | 0.088 | 2.876 | 0.051 |

The chaining table computes a deterministic Horner hash over each string and traverses linked lists; Python's dictionary uses its own optimized hash-table implementation. The benchmark does not call `hash()` itself. Timing differences include Python interpreter, allocator, and machine effects and should be interpreted as observations rather than algorithmic complexity proofs.
