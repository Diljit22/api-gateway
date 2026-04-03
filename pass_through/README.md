# pass_through

First working version of the gateway.

Super simple:

- recieve request
- routes are just a dict (via prefix)
- forwards the rest of the path + headers + body

Nothing fancy, just enough to get the gateway working end-to-end.

## How to run

1. Start the two backends and in a third terminal launch the gateway.
2. Open demo.http and click around

## architecture

```mermaid
graph TD
    A[Client] --> B[Gateway :8080]
    B --> C{Simple Dict Router}
    C -->|prefix /users| D[Users Backend :8001]
    C -->|prefix /orders| E[Orders Backend :8002]
    D --> B
    E --> B
    B --> A
```
