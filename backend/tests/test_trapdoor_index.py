import pytest
from app.trapdoor_index import generate_trapdoor_key, compute_trapdoor, TrapdoorIndex

def test_same_token_same_trapdoor():
    key = generate_trapdoor_key()
    token = "secret"
    t1 = compute_trapdoor(token, key)
    t2 = compute_trapdoor(token, key)
    assert t1 == t2

def test_different_keys_different_trapdoors():
    key1 = generate_trapdoor_key()
    key2 = generate_trapdoor_key()
    token = "secret"
    t1 = compute_trapdoor(token, key1)
    t2 = compute_trapdoor(token, key2)
    assert t1 != t2

def test_add_and_search_document():
    index = TrapdoorIndex()
    key = generate_trapdoor_key()
    doc_id = "doc123"
    content = "The quick brown fox jumps over the lazy dog"
    
    index.add_document(doc_id, content, key)
    
    results = index.search("brown fox", key)
    assert doc_id in results

def test_search_word_not_in_any_document():
    index = TrapdoorIndex()
    key = generate_trapdoor_key()
    doc_id = "doc123"
    content = "The quick brown fox"
    
    index.add_document(doc_id, content, key)
    
    results = index.search("dog", key)
    assert len(results) == 0

def test_remove_document():
    index = TrapdoorIndex()
    key = generate_trapdoor_key()
    doc_id = "doc123"
    content = "The quick brown fox"
    
    index.add_document(doc_id, content, key)
    index.remove_document(doc_id)
    
    results = index.search("fox", key)
    assert len(results) == 0

def test_index_contains_no_plaintext():
    index = TrapdoorIndex()
    key = generate_trapdoor_key()
    doc_id = "doc123"
    content = "highly confidential secret mission"
    
    index.add_document(doc_id, content, key)
    
    for token in ["highly", "confidential", "secret", "mission"]:
        for trapdoor in index._index.keys():
            assert token not in trapdoor
            
        for doc_set in index._index.values():
            for doc in doc_set:
                assert doc == doc_id
