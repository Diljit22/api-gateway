===========================================================================
  Token Bucket Rate Limiter Benchmark
===========================================================================
Evaluating in-memory bucket checks over 10,000 runs...

   Token Bucket Decision:
     mean: 0.24 µs   std: 0.10 µs   p50: 0.25 µs   p99: 0.29 µs

===========================================================================
Key Takeaway:
In-memory mathematical token bucket evaluations take around 1 microsecond.
This highlights that rate limiting introduces practically zero CPU overhead
to the active gateway request routing pipeline.
===========================================================================