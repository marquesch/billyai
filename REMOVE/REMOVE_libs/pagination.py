from sqlalchemy.orm.query import Query

MAX_LIMIT = 50


def paginate(query: Query, per_page: int = MAX_LIMIT, page: int = 1):
    limit = min(per_page, MAX_LIMIT)
    offset = limit * (page - 1)
    return query.limit(limit).offset(offset)
