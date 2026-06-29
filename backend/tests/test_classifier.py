import pytest
from app.classifier import classify_chunk

def test_classifier_api_key_sk():
    res = classify_chunk("Here is my key sk-12345678901234567890ab")
    assert res.is_sensitive
    assert "api_key" in res.matched_patterns

def test_classifier_api_key_aws():
    res = classify_chunk("My AWS key is AKIAIOSFODNN7EXAMPLE")
    assert res.is_sensitive
    assert "api_key" in res.matched_patterns

def test_classifier_api_key_generic():
    res = classify_chunk("The token is 1234567890abcdef1234567890abcdef1")
    assert res.is_sensitive
    assert "api_key" in res.matched_patterns

def test_classifier_email():
    res = classify_chunk("Contact me at test@example.com.")
    assert res.is_sensitive
    assert "email" in res.matched_patterns

def test_classifier_credit_card():
    res = classify_chunk("My card is 4111-1111-1111-1111")
    assert res.is_sensitive
    assert "credit_card" in res.matched_patterns

def test_classifier_phone_india():
    res = classify_chunk("Call me at +91 9876543210")
    assert res.is_sensitive
    assert "phone" in res.matched_patterns

def test_classifier_phone_intl():
    res = classify_chunk("Call me at +1 800 555 0199")
    assert res.is_sensitive
    assert "phone" in res.matched_patterns

def test_classifier_keyword():
    res = classify_chunk("This is a confidential document.")
    assert res.is_sensitive
    assert "keyword" in res.matched_patterns

def test_classifier_keyword_phrase():
    res = classify_chunk("Please do not share this info.")
    assert res.is_sensitive
    assert "keyword" in res.matched_patterns

def test_classifier_aadhaar():
    res = classify_chunk("Aadhaar: 1234 5678 9012")
    assert res.is_sensitive
    assert "aadhaar" in res.matched_patterns

def test_classifier_normal_text_1():
    res = classify_chunk("Doug is the groom, the wedding is Sunday")
    assert not res.is_sensitive
    assert len(res.matched_patterns) == 0

def test_classifier_normal_text_2():
    res = classify_chunk("The weather in Vegas is very hot during summer.")
    assert not res.is_sensitive

def test_classifier_normal_text_3():
    res = classify_chunk("I like to eat apples and bananas.")
    assert not res.is_sensitive

def test_classifier_normal_text_4():
    res = classify_chunk("Can you send me the latest quarterly report?")
    assert not res.is_sensitive
