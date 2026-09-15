import hashlib
import hmac


def generate_hmac(data: bytes, key: bytes) -> bytes:
	return hmac.new(key, data, hashlib.sha256).digest()


def verify_hmac(data: bytes, tag: bytes, key: bytes) -> bool:
	expected_tag = generate_hmac(data, key)
	return hmac.compare_digest(expected_tag, tag)
