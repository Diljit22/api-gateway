from typing import Tuple, Optional

class TrieNode:
    def __init__(self, segment: str):
        self.segment = segment
        self.children = {}
        self.backend_url: Optional[str] = None
        self.is_wildcard = segment.startswith(":") or segment == "*"

class RadixRouter:
    """A Segment-based Radix Trie for API Gateway routing."""
    def __init__(self):
        self.root = TrieNode("")

    def insert(self, path: str, backend_url: str):
        """Inserts a route into the Trie."""
        # Split path into segments, ignoring empty strings (e.g., '/users/' -> ['users'])
        segments = [s for s in path.split('/') if s]
        current = self.root

        for seg in segments:
            if seg not in current.children:
                current.children[seg] = TrieNode(seg)
            current = current.children[seg]
        
        # Mark the end of the route with the target backend
        current.backend_url = backend_url

    def search(self, full_path: str) -> Tuple[Optional[str], str]:
        """Searches for the longest matching prefix; returns (backend_url, remaining_path)"""
        segments = [s for s in full_path.split('/') if s]
        current = self.root
        
        last_matched_backend = None
        matched_segments_count = 0

        for i, seg in enumerate(segments):
            # Try to find an exact segment match (e.g., "users")
            if seg in current.children:
                current = current.children[seg]
                
            # look for any wildcard child ("*" or ":id")
            else:
                wildcard_key = next((k for k, v in current.children.items() if v.is_wildcard), None)
                if wildcard_key:
                    current = current.children[wildcard_key]
                else:
                    # No exact match and no wildcard.
                    break

            # If we successfully moved down the tree check if this node registers a backend.
            if current.backend_url:
                last_matched_backend = current.backend_url
                matched_segments_count = i + 1

        # After the loop, return the longest match we found
        if last_matched_backend:
            # Reconstruct the remaining path that needs to be forwarded
            remaining_path = "/" + "/".join(segments[matched_segments_count:])
            return last_matched_backend, remaining_path

        return None, full_path