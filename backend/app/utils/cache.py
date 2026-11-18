from app.extensions import cache

def invalidate_cache_pattern(pattern: str):
    """
    Clears cache keys matching a pattern via Redis or cache backend fallback.
    Ensures keys prefixed by Flask-Caching (e.g. 'flask_cache_') are also matched.
    """
    try:
        client = getattr(getattr(cache, 'cache', None), '_read_client', None)
        if client and hasattr(client, 'keys') and hasattr(client, 'delete'):
            clean_pattern = pattern.strip('*')
            keys_to_delete = set()
            for p in (pattern, f"*{clean_pattern}*", f"flask_cache_*{clean_pattern}*"):
                found = client.keys(p)
                if found:
                    keys_to_delete.update(found)
            if keys_to_delete:
                client.delete(*keys_to_delete)
        else:
            cache.clear()
    except Exception:
        cache.clear()

def invalidate_treks_cache():
    invalidate_cache_pattern('treks')
    invalidate_cache_pattern('admin:dashboard')
    invalidate_cache_pattern('staff:dashboard')
    invalidate_cache_pattern('trekker:dashboard')

def invalidate_dashboard_cache():
    invalidate_cache_pattern('admin')
    invalidate_cache_pattern('staff')
    invalidate_cache_pattern('trekker')

