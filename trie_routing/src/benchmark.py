import time
from radix_trie import RadixRouter

# Note: more of a "fake" benchmark by isolating to routing
# alg its essentially comparison of two search which
# we know complexity (and constants).

# Generate routes

NUM_ROUTES = 1_000_000
print(f"Generating {NUM_ROUTES} dummy routes to simulate a massive API Gateway...")

dict_routes = {}
trie_router = RadixRouter()

# Populate with dummy data
for i in range(NUM_ROUTES):
    path = f"/api/v1/dummy_service_{i}/endpoint"
    backend = f"http://localhost:8001/dummy_{i}"
    
    dict_routes[path] = backend
    trie_router.insert(path, backend)

# Insert the route we are actually going to look for
target_prefix = "/users"
dict_routes[target_prefix] = "http://localhost:8001"
trie_router.insert(target_prefix, "http://localhost:8001")

target_path = "/users/profile/123"
RUNS = 20

print(f"Target Path: {target_path}")
print(f"Number of runs: {RUNS}\n")
print("Benchmarking... please wait...\n")

# Bench Pass-Through

pass_through_times =[]

for _ in range(RUNS):
    start = time.perf_counter()
    
    matched_backend = None
    matched_prefix = ""
    for prefix in sorted(dict_routes.keys(), key=len, reverse=True):
        if target_path.startswith(prefix):
            matched_backend = dict_routes[prefix]
            matched_prefix = prefix
            break
            
    end = time.perf_counter()
    pass_through_times.append(end - start)

avg_dict_time = sum(pass_through_times) / RUNS

# Bench Trie Routing
trie_times =[]

for _ in range(RUNS):
    start = time.perf_counter()
    
    matched_backend, remaining = trie_router.search(target_path)
    
    end = time.perf_counter()
    trie_times.append(end - start)

avg_trie_time = sum(trie_times) / RUNS


print("=== RESULTS ===")
print(f"Pass-Through (Dict) Avg Time : {avg_dict_time:.6f} seconds per request")
print(f"Radix Trie Avg Time          : {avg_trie_time:.6f} seconds per request")

speedup = avg_dict_time / avg_trie_time if avg_trie_time > 0 else float('inf')
print(f"\nbThe Radix Trie is {speedup:,.0f}x faster.")