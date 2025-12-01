import redis

pool = redis.ConnectionPool(host="redis", port=6379)


def get_cache():
    return Cache()


class Cache(redis.Redis):
    def __init__(self, db=0):
        super().__init__(connection_pool=pool, db=db)
