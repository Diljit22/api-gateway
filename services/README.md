# services

Two dummy backends so we can test the gateway.

- `users.py` : runs on localhost:8001
- `orders.py`: runs on localhost:8002

Each one replies with its name and the path it saw.  

## How to Demo

1. Use `make services` to start both backends
2. Launch `demo.http` and send requests
3. Stop services via `make services-stop`
