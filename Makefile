.PHONY: help install \
       services services-stop \
       pass-through pass-through-stop \
       trie trie-stop trie-bench \
       lb lb-backends lb-backends-stop lb-gateway lb-gateway-stop lb-stop lb-bench lb-chaos \
       rc rc-backends rc-backends-stop rc-gateway rc-gateway-stop rc-stop rc-bench \
       stop-all

###  Help ###

help:
	@echo ""
	@echo "  api-gateway Makefile"
	@echo "  ========================================"
	@echo ""
	@echo "  Setup:"
	@echo "    make install              install pip dependencies"
	@echo ""
	@echo "  Services (dummy backends):"
	@echo "    make services             start users :8001 + orders :8002"
	@echo "    make services-stop        kill them"
	@echo ""
	@echo "  Pass-Through phase:"
	@echo "    make pass-through         start gateway :8080 (needs services running)"
	@echo "    make pass-through-stop    kill gateway"
	@echo ""
	@echo "  Trie Routing phase:"
	@echo "    make trie                 start gateway :8080 (needs services running)"
	@echo "    make trie-stop            kill gateway"
	@echo "    make trie-bench           run trie vs dict benchmark (no servers needed)"
	@echo ""
	@echo "  Load Balancing phase:"
	@echo "    make lb                   start 6 backends + gateway (all-in-one)"
	@echo "    make lb-backends          start 6 backends only"
	@echo "    make lb-gateway           start gateway only"
	@echo "    make lb-stop              kill everything"
	@echo "    make lb-bench             run algorithm benchmark (no servers needed)"
	@echo "    make lb-chaos             run chaos demo (starts its own servers)"
	@echo ""
	@echo "  Request Channeling phase:"
	@echo "    make rc                   start 6 backends + request channeled gateway"
	@echo "    make rc-backends          start 6 backends (with 1s delay)"
	@echo "    make rc-gateway           start gateway only"
	@echo "    make rc-stop              kill everything"
	@echo "    make rc-bench             run the coalescing and bulkhead benchmark"
	@echo ""
	@echo "  Cleanup:"
	@echo "    make stop-all             kill all background processes"
	@echo ""

###  Setup ###

install:
	pip install -r requirements.txt

###  Services (shared backends for pass_through & trie_routing) ###

services:
	@echo "Starting Users backend :8001 ..."
	@cd services/src && python users.py &
	@echo "Starting Orders backend :8002 ..."
	@cd services/src && python orders.py &
	@sleep 1
	@echo "Backends ready."

services-stop:
	@echo "Stopping services..."
	@-pkill -f "users.py" 2>/dev/null || true
	@-pkill -f "orders.py" 2>/dev/null || true
	@echo "Done."

###  Pass-Through ###

pass-through: services
	@echo "Starting pass-through gateway :8080 ..."
	@cd pass_through/src && python api_gateway.py

pass-through-stop:
	@-pkill -f "pass_through/src/api_gateway.py" 2>/dev/null || true

###  Trie Routing ###

trie: services
	@echo "Starting trie-routing gateway :8080 ..."
	@cd trie_routing/src && python api_gateway.py

trie-stop:
	@-pkill -f "trie_routing/src/api_gateway.py" 2>/dev/null || true

trie-bench:
	@echo "Running trie vs dict benchmark..."
	@cd trie_routing/src && python benchmark.py

###  Load Balancing ###

lb-backends:
	@echo "Starting 6 backends..."
	@cd load_balancing/src && python backend.py 8001 users &
	@cd load_balancing/src && python backend.py 8003 users &
	@cd load_balancing/src && python backend.py 8005 users &
	@cd load_balancing/src && python backend.py 8002 orders &
	@cd load_balancing/src && python backend.py 8004 orders &
	@cd load_balancing/src && python backend.py 8006 orders &
	@sleep 2
	@echo "All 6 backends ready."

lb-gateway:
	@echo "Starting load-balanced gateway :8080 ..."
	@cd load_balancing/src && python api_gateway.py

lb: lb-backends
	@echo "Starting load-balanced gateway :8080 ..."
	@cd load_balancing/src && python api_gateway.py

lb-backends-stop:
	@-pkill -f "backend.py" 2>/dev/null || true

lb-gateway-stop:
	@-pkill -f "load_balancing/src/api_gateway.py" 2>/dev/null || true

lb-stop: lb-backends-stop lb-gateway-stop

lb-bench:
	@echo "Running load balancer benchmark..."
	@cd load_balancing/src && python benchmark.py

lb-chaos:
	@echo "Running chaos demo (starts its own servers)..."
	@cd load_balancing/src && python chaos_demo.py

### Request Channeling ###

rc-backends:
	@echo "Starting 6 backends for Request Channeling..."
	@cd req_chanelling/src && python backend.py 8001 users &
	@cd req_chanelling/src && python backend.py 8003 users &
	@cd req_chanelling/src && python backend.py 8005 users &
	@cd req_chanelling/src && python backend.py 8002 orders &
	@cd req_chanelling/src && python backend.py 8004 orders &
	@cd req_chanelling/src && python backend.py 8006 orders &
	@sleep 2
	@echo "All 6 backends ready."

rc-gateway:
	@echo "Starting request-channeled gateway :8080 ..."
	@cd req_chanelling/src && python api_gateway.py

rc: rc-backends
	@echo "Starting request-channeled gateway :8080 ..."
	@cd req_chanelling/src && python api_gateway.py

rc-backends-stop:
	@-pkill -f "req_chanelling/src/backend.py" 2>/dev/null || true

rc-gateway-stop:
	@-pkill -f "req_chanelling/src/api_gateway.py" 2>/dev/null || true

rc-stop: rc-backends-stop rc-gateway-stop

rc-bench:
	@echo "Running request channeler benchmark..."
	@cd req_chanelling/src && python benchmark.py

### Caching Layer ###

cache-backends:
	@echo "Starting 6 backends for Caching..."
	@cd cache_layer/src && python backend.py 8001 users &
	@cd cache_layer/src && python backend.py 8003 users &
	@cd cache_layer/src && python backend.py 8005 users &
	@cd cache_layer/src && python backend.py 8002 orders &
	@cd cache_layer/src && python backend.py 8004 orders &
	@cd cache_layer/src && python backend.py 8006 orders &
	@sleep 2
	@echo "All 6 backends ready."

cache-gateway:
	@echo "Starting caching-enabled gateway :8080 ..."
	@cd cache_layer/src && python api_gateway.py

cache: cache-backends
	@echo "Starting caching-enabled gateway :8080 ..."
	@cd cache_layer/src && python api_gateway.py

cache-backends-stop:
	@-pkill -f "cache_layer/src/backend.py" 2>/dev/null || true

cache-gateway-stop:
	@-pkill -f "cache_layer/src/api_gateway.py" 2>/dev/null || true

cache-stop: cache-backends-stop cache-gateway-stop

cache-bench:
	@echo "Running cache benchmark..."
	@cd cache_layer/src && python benchmark.py

###  Nuke everything ###

stop-all: services-stop pass-through-stop trie-stop lb-stop rc-stop cache-stop
	@echo "All processes stopped."