Running request channeler benchmark...
===========================================================================
  Request Channeling Benchmark: Coalescing & Bulkhead Queuing
===========================================================================
Firing 10 concurrent requests to the Gateway...
Note: The backend has a fixed delay of 1.0 second.

Request  2 | Status: 200 | Time: 1.021s | Random ID: 5636 | Handled By: localhost:8001 | Coalesced: TRUE
Request  4 | Status: 200 | Time: 1.022s | Random ID: 5636 | Handled By: localhost:8001 | Coalesced: TRUE
Request  6 | Status: 200 | Time: 1.022s | Random ID: 5636 | Handled By: localhost:8001 | Coalesced: TRUE
Request  8 | Status: 200 | Time: 1.022s | Random ID: 5636 | Handled By: localhost:8001 | Coalesced: TRUE
Request  5 | Status: 200 | Time: 1.023s | Random ID: 5636 | Handled By: localhost:8001 | Coalesced: TRUE
Request  7 | Status: 200 | Time: 1.023s | Random ID: 5636 | Handled By: localhost:8001 | Coalesced: TRUE
Request  9 | Status: 200 | Time: 1.023s | Random ID: 5636 | Handled By: localhost:8001 | Coalesced: TRUE
Request  3 | Status: 200 | Time: 1.024s | Random ID: 5636 | Handled By: localhost:8001 | Coalesced: TRUE
Request 10 | Status: 200 | Time: 1.023s | Random ID: 5636 | Handled By: localhost:8001 | Coalesced: TRUE
Request  1 | Status: 200 | Time: 1.036s | Random ID: 5636 | Handled By: localhost:8001 | Coalesced: FALSE

===========================================================================
Total benchmark execution time: 1.051 seconds
===========================================================================

Key Takeaways:
1. All 10 requests completed in ~1.0 second total (rather than 10s or 4s queuing).
2. All parallel requests returned the exact same Random ID.
3. Duplicated requests carry the 'X-Request-Coalesced: TRUE' response header.
This confirms request coalescing successfully collapsed 10 parallel calls into 1 backend fetch!
