# services

Two tiny dummy backends so we can actually test the gateway.

- `users.py` : runs on localhost:8001
- `orders.py`: runs on localhost:8002

Each one just replies with its name and the path it saw.  

## How to run

1. Start backend services
2. Run the gateway
3. Launch demo.http
