# api-gateway

Incremental implementation of a toy API-gateway.

## What is an API Gateway?

An API-Gateway is a highly-concurrent reverse proxy. It intercepts client requests to improve security, performance, & reliability. Instead of indivisual services duplicating logic for authentication, rate limiting, & load balancing, the Gateway abstracts those concerns away.

## The Format

Our toy API Gateway will evolve from a simple pass-through
implementation to an ever-more slightly more naunced model.

Each folder corrosponds to a topic we will discuss & will include a small overview of the what is being added & why, as well as the current high-level arch of whats been built.

Hopefully the weekly overviews will highlight architectural choices, trade-offs, & nuances.

## Prereqs

1. Install dependencies from the root of the project via: `pip install -r requirements.txt`
2. If on VS Code install the REST Client extension to get clickable "Send Request" buttons.

## Progress

| Folder           | What it adds       | Status |
|---               |---                 |---     |
| services         | dummy backends     | done   |
| pass_through     | basic dict routing | done   |
| trie_routing     | radix-trie router  | done   |
| load_balancing   |  --                | next   |
