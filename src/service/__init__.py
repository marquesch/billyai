from cfg import Session
from libs.cache import Cache


class Service:
    def __init__(self, session: Session, cache: Cache, base_url: str = "localhost:8080"):
        self.session = session
        self.cache = cache
        self.base_url = base_url
