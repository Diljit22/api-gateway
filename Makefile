.PHONY: help install \
       services services-stop \
       pass-through pass-through-stop \
       trie trie-stop trie-bench \
       lb lb-backends lb-backends-stop lb-gateway lb-gateway-stop lb-stop lb-bench lb-chaos \
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

###  Nuke everything ###

stop-all: services-stop pass-through-stop trie-stop lb-stop
	@echo "All processes stopped."