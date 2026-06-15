"""Helpers for the standalone email-verification flow.

Verification is decoupled from password/registration: ``EmailVerified`` is the
source of truth for the ssh push, set only by following a verification link.
A token lives on the ``Users`` row with 24h expiry; sends are rate-limited.
"""

from aurweb import config, time
from aurweb.models.user import generate_resetkey

# Token validity and cooldown period. The cooldown guards against mail-bombs.
TTL = config.getint("options", "email_verification_ttl", fallback=86400)
COOLDOWN = config.getint("options", "email_verification_cooldown", fallback=600)


def issue(user) -> None:
    """Issue a fresh verification token + expiry on ``user``."""
    user.EmailVerificationToken = generate_resetkey()
    user.EmailVerificationExpiry = time.utcnow() + TTL


def in_cooldown(user) -> bool:
    """True if a verification email was sent within the last ``COOLDOWN`` secs."""
    expiry = user.EmailVerificationExpiry
    if expiry is None:
        return False
    return time.utcnow() < expiry - TTL + COOLDOWN


def is_expired(user) -> bool:
    """True if the current verification token is missing or past its expiry."""
    expiry = user.EmailVerificationExpiry
    if expiry is None:
        return True
    return time.utcnow() >= expiry
