# cache_layer

Adds a simple in-memory caching layer to the gateway to store successful `GET` responses.

## What is being added and why?

Proxying requests over TCP to downstream backends introduces network latency. For read-heavy, slow, or expensive backend computations, retrieving values over the network every single time is inefficient.

### Implementation details

**In-Memory TTL Cache**: Stores response contents, status codes, and headers inside a dictionary. Each cached response is stored with an absolute expiry timestamp calculated from a configured Time-To-Live (TTL).

**Automated background sweeping**: To prevent memory leaks when unique client requests accumulate and never repeat, a background cleanup loop sweeps the cache store periodically, evicting expired items.

**Metadata injection**: Appends an `X-Cache: HIT` or `X-Cache: MISS` header to outgoing HTTP responses to help client-side verification.

---

## How to Run

1. Start 6 backends + cache-enabled gateway on :8080:
   ```bash
   make cache
   ```
2. Open `cache_layer/demo.http` and click around.
3. Run the performance benchmark to compare cache hits vs misses:
   ```bash
   make cache-bench
   ```
4. Stop all running services:
   ```bash
   make cache-stop
   ```

---

## Architecture

```text
               ┌─────────── GET /users/profile ───────────┐
               ▼                                          ▼
      [ Cache Lookup ]                             [ Cache Lookup ]
         (Cache Hit)                                 (Cache Miss)
               │                                          │
               ▼                                          ▼
   ┌───────────────────────┐                  ┌───────────────────────┐
   │ Return Cached Payload │                  │ Forward to Backend    │
   │   Header: X-Cache: HIT│                  │ Store in Cache        │
   └───────────────────────┘                  │ Header: X-Cache: MISS │
                                              └───────────────────────┘
```
