# Run with: python -m tests.test_day2_cache_auth_demo
from core.services.cache import CacheService
from core.services.auth import AuthService

def main():
    cache = CacheService("data/store.json")
    auth = AuthService()

    # auth quick checks
    assert auth.login("you@example.com", "pass123") is True
    assert auth.login("you@example.com", "wrong") is False

    # cache quick checks
    cache.add_user("lee@example.com", "Lee", "pass123")
    assert cache.get_user("lee@example.com")["name"] == "Lee"

    cache.add_group("g1", "Trip to NYC")
    assert cache.get_group("g1")["name"] == "Trip to NYC"

    cache.save()
    print("Auth + Cache basic smoke test passed.")

if __name__ == "__main__":
    main()
