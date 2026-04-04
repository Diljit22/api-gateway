# api-gateway

Incremental implementation of a toy API-gateway.

## What is an API Gateway?

An API Gateway is a highly-concurrent reverse proxy. It intercepts client requests to improve security, performance, & reliability. Instead of individual services duplicating logic for authentication, rate limiting, & load balancing, the Gateway abstracts those concerns away.

## What is this?

Our toy API Gateway will evolve from a simple pass-through implementation to a slightly more nuanced model.

Each folder corresponds to a topic discussed and includes a small overview of the addition, why it is beneficial, and the current high-level architecture of what has been built. Hopefully, these weekly overviews will highlight architectural choices, trade-offs, & nuances.

## Prereqs

- Python 3.12+
- WSL (Windows only): install via `wsl --install` in PowerShell to use the Makefile
- REST Client (VS Code) extension for clickable "Send Request" buttons in demo.http files
- See `requirements.txt` for python dependencies

## Getting Started

```bash
git clone https://github.com/diljit22/api-gateway.git
cd api-gateway                  # navigate to the dir
python3 -m venv venv            # create virtual environment
source venv/bin/activate        # activate venv
pip install -r requirements.txt # install python deps
```

## Workflow

```bash
make help              # list all available commands

make pass-through      # start backends + dict-based gateway
make trie              # start backends + radix-trie gateway
make trie-bench        # benchmark: dict scan vs trie lookup

make lb                # start 6 backends + load-balanced gateway
make lb-bench          # benchmark: distribution, stability, least-conn
make lb-chaos          # automated chaos demo (starts its own servers)

make stop-all          # kill all running processes
```

**NB**: Always run `make stop-all` before switching phases to prevent port conflicts.

## Progress

| Folder           | What it adds       | Status |
|---               |---                 |---     |
| services         | dummy backends     | done   |
| pass_through     | basic dict routing | done   |
| trie_routing     | radix-trie router  | done   |
| load_balancing   | const hash + vnode | done   |
| req_chanelling   | .............      | todo   |
| cache_layer      | .............      | todo   |
| authentication   | .............      | todo   |
| rate_limiting    | .............      | todo   |
