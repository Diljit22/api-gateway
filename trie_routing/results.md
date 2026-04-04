Running trie vs dict benchmark...
Benchmark: Dict Scan vs Radix Trie
Target path: /users/profile/123
Runs per test: 500 (+ 50 warmup)

============================================================
  100 routes registered
============================================================

   Dict scan:
     mean: 5.0 µs   std: 1.8 µs   p50: 4.7 µs   p99: 9.7 µs
   Radix Trie:
     mean: 1.2 µs   std: 1.9 µs   p50: 1.0 µs   p99: 4.7 µs

   Trie is 4x faster at 100 routes.

============================================================
  10,000 routes registered
============================================================

   Dict scan:
     mean: 492.4 µs   std: 153.1 µs   p50: 452.2 µs   p99: 997.6 µs    
   Radix Trie:
     mean: 1.0 µs   std: 0.5 µs   p50: 1.0 µs   p99: 1.4 µs

   Trie is 491x faster at 10,000 routes.

============================================================
  1,000,000 routes registered
============================================================

   Dict scan:
     mean: 54342.0 µs   std: 9051.5 µs   p50: 51573.4 µs   p99: 86733.7 µs
   Radix Trie:
     mean: 1.0 µs   std: 0.1 µs   p50: 1.0 µs   p99: 1.1 µs

   Trie is 55,565x faster at 1,000,000 routes.