import time
from functools import wraps

def retry_with_backoff(retries=3, backoff_in_seconds=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    print(f"Error: {e}. Retrying {attempts}/{retries}...")
                    time.sleep(backoff_in_seconds * (2 ** (attempts - 1)))
            return func(*args, **kwargs)
        return wrapper
    return decorator
                    
