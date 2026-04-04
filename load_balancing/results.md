"Running load balancer benchmark..."

============================================================
  1. Hash Ring Distribution - Virtual Nodes Comparison
============================================================

   10 servers, 100,000 request keys

   Vnodes           CV       Min       Max    Spread     Ideal
   ---------- --------  --------  --------  --------  --------
   0             0.916        43    29,208    29,165    10,000
   10            0.296     6,186    14,366     8,180    10,000
   50            0.092     8,803    11,978     3,175    10,000
   150           0.061     8,712    11,053     2,341    10,000
   300           0.059     9,358    11,287     1,929    10,000

   CV = coefficient of variation (lower = more even)
   Spread = max - min requests across servers
   Ideal = perfect even split (100k / 10 servers)

   0 vnodes: one server may get 600x the load of another.
   150 vnodes: spread drops to ~2k out of 100k - nearly uniform.

============================================================
  2. Key Stability After Server Failure
============================================================

   Removing 1 server out of 10.

   Vnodes       Keys Remapped    % Moved     Ideal %
   ---------- --------------- ----------  ----------
   0                   29,208      29.2%       10.0%
   10                  10,080      10.1%       10.0%
   50                  10,379      10.4%       10.0%
   150                  9,996      10.0%       10.0%
   300                  9,676       9.7%       10.0%


   Vnodes       Keys Remapped    % Moved     Ideal %
   ---------- --------------- ----------  ----------
   0                   29,208      29.2%       10.0%
   10                  10,080      10.1%       10.0%
   50                  10,379      10.4%       10.0%
   150                  9,996      10.0%       10.0%
   300                  9,676       9.7%       10.0%

   10                  10,080      10.1%       10.0%
   50                  10,379      10.4%       10.0%
   150                  9,996      10.0%       10.0%
   300                  9,676       9.7%       10.0%

   300                  9,676       9.7%       10.0%


   Ideal: ~10.0% should move (only the dead server's share).
   0 vnodes moved 29% - nearly 2.9x the ideal. That extra 19%
   is keys that DIDN'T belong to the dead server but got
   reshuffled anyway because the ring was unbalanced.

============================================================
  3. Least Connections vs Round Robin - Skewed Latency
============================================================

   3 backends: 2 fast (5-15ms), 1 slow (30-70ms)
   5000 requests per trial, 10 trials

   Round Robin:
     http://fast-a:8001 (fast):    1667 avg  +/-    0  (33.3%)
     http://fast-b:8002 (fast):    1667 avg  +/-    0  (33.3%)
     http://slow-c:8003 (slow):    1666 avg  +/-    0  (33.3%)

   Least Conn:
     http://fast-a:8001 (fast):    2366 avg  +/-   10  (47.3%)
     http://fast-b:8002 (fast):    2172 avg  +/-   11  (43.4%)
     http://slow-c:8003 (slow):     461 avg  +/-    5  (9.2%)
