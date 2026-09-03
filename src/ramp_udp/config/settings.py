import os


DEVELOPMENT_SECRET_KEY = b"ramp-udp-development-key"


def get_secret_key() -> bytes:
	"""Return RAMP_SECRET_KEY, using a development-only fallback locally."""
	configured_key = os.environ.get("RAMP_SECRET_KEY")
	if configured_key is None:
		return DEVELOPMENT_SECRET_KEY
	return configured_key.encode("utf-8")


def authentication_enabled() -> bool:
	return os.environ.get("RAMP_AUTH_ENABLED", "1") != "0"
