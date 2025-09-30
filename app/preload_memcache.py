import os
import time
import memcache
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_pw(pw: str) -> str:
    return pwd_context.hash(pw)

# Demo users (hashed at import)
fake_users_db = {
    "john": {
        "username": "john",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": hash_pw("johnpword"),
        "admin": True,
        "disabled": False,
    },
    "jane": {
        "username": "jane",
        "full_name": "Jane Doe",
        "email": "janedoe@example.com",
        "hashed_password": hash_pw("janepword"),
        "admin": False,
        "disabled": False,
    },
}

MEMCACHED_ADDR = os.getenv("MEMCACHED_ADDR", "memcached:11211")

def wait_for_memcached(addr: str, attempts: int = 30, delay: float = 1.0) -> memcache.Client:
    mc = memcache.Client([addr], debug=0)
    for _ in range(attempts):
        try:
            mc.set("_health", "ok", time=5)
            if mc.get("_health") == "ok":
                return mc
        except Exception:
            pass
        time.sleep(delay)
    raise RuntimeError(f"Memcached not ready at {addr}")

if __name__ == "__main__":
    mc = wait_for_memcached(MEMCACHED_ADDR)
    for username, user in fake_users_db.items():
        mc.set(f"user:{username}", user, time=0)  # 0 = no expiry (demo)
    mc.set("users:index", list(fake_users_db.keys()), time=0)
    print(f"Loaded {len(fake_users_db)} users into Memcached at {MEMCACHED_ADDR}")