===========================================================================
  Cryptographic JWT Verification & RBAC Benchmark
===========================================================================
Evaluating HS256 verification + JSON decoding over 10,000 runs...

   Crypto JWT Decode (HS256) + RBAC Check:
     mean: 2.89 µs   std: 0.63 µs   p50: 2.88 µs   p99: 3.21 µs

===========================================================================
Key Takeaway:
Even with true cryptographic signature verification and JSON decoding,
the entire flow takes less than 15 microseconds.
This confirms edge authentication remains extremely lightweight.
===========================================================================