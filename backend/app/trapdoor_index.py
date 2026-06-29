"""
Trapdoor Index for Searchable Symmetric Encryption (SSE).

Security Properties and Limits:
This implements a deterministic searchable encryption index using HMAC-SHA256 trapdoors.
The primary security property is that the plaintext content is never stored in the index;
only non-invertible, keyed hashes (trapdoors) are stored. Without the specific HMAC key,
the index reveals nothing about the original words.

LIMITS: This scheme leaks the "search pattern" and "access pattern". An adversary watching
the index and queries over time can observe which trapdoors co-occur and infer term
frequency or query patterns. This is a known, expected leakage profile of deterministic SSE,
not a bug to be hidden. Visibility into query patterns (via audit logging) is the mitigation,
not pretending the leakage doesn't exist.
"""

import os
import hmac
import hashlib
import re
from typing import Set

STOPWORDS = {"a", "an", "the", "and", "or", "but", "is", "are", "was", "were", "to", "in", "for", "on", "with", "as", "by", "at", "of"}

def generate_trapdoor_key() -> bytes:
    """Generates a fresh 256-bit (32 bytes) HMAC key for a dataset's trapdoors."""
    return os.urandom(32)

def tokenize(text: str) -> list[str]:
    """Lowercase, strip punctuation, split on whitespace, remove stopwords, return unique."""
    # Lowercase
    text = text.lower()
    # Strip punctuation (keep alphanumerics and whitespace)
    text = re.sub(r'[^\w\s]', '', text)
    # Split on whitespace
    tokens = text.split()
    # Remove stopwords and make unique
    unique_tokens = list(set(t for t in tokens if t not in STOPWORDS))
    return unique_tokens

def compute_trapdoor(token: str, hmac_key: bytes) -> str:
    """
    Computes deterministic encrypted token (trapdoor) via HMAC-SHA256.
    Same token + same key = same trapdoor hex string.
    """
    h = hmac.new(hmac_key, token.encode('utf-8'), hashlib.sha256)
    return h.hexdigest()

class TrapdoorIndex:
    def __init__(self):
        # Maps trapdoor (str) -> set of doc_ids
        self._index: dict[str, Set[str]] = {}
        # Reverse index to allow O(N_tokens) removal instead of O(N_trapdoors * N_docs)
        self._doc_to_trapdoors: dict[str, Set[str]] = {}

    def add_document(self, doc_id: str, content: str, hmac_key: bytes) -> None:
        """Tokenizes content, computes trapdoors, and updates the index mappings."""
        tokens = tokenize(content)
        trapdoors = set()
        for token in tokens:
            trapdoor = compute_trapdoor(token, hmac_key)
            trapdoors.add(trapdoor)
            
            if trapdoor not in self._index:
                self._index[trapdoor] = set()
            self._index[trapdoor].add(doc_id)
            
        self._doc_to_trapdoors[doc_id] = trapdoors

    def search(self, query: str, hmac_key: bytes) -> set[str]:
        """
        Tokenizes query, computes trapdoors, returns union of matching doc_ids.
        Note: returning the union for now. Returning the intersection would
        enforce stricter matching (AND instead of OR).
        """
        tokens = tokenize(query)
        matching_docs = set()
        for token in tokens:
            trapdoor = compute_trapdoor(token, hmac_key)
            if trapdoor in self._index:
                matching_docs.update(self._index[trapdoor])
        return matching_docs

    def remove_document(self, doc_id: str) -> None:
        """Removes a document from all trapdoor mappings."""
        if doc_id in self._doc_to_trapdoors:
            trapdoors = self._doc_to_trapdoors[doc_id]
            for trapdoor in trapdoors:
                if trapdoor in self._index:
                    self._index[trapdoor].discard(doc_id)
                    if not self._index[trapdoor]:
                        del self._index[trapdoor]
            del self._doc_to_trapdoors[doc_id]
