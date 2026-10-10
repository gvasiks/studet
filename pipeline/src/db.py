import os
from collections.abc import Callable
from typing import Any

from supabase import Client, create_client

# PostgREST отдаёт не больше 1000 строк за запрос и не сообщает, что остальное
# отрезано (.limit(2000) этого не меняет — предел стоит на сервере).
PAGE_ROWS = 1000


def get_service_client() -> Client:
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    return create_client(url, key)


def fetch_all(make_query: Callable[[], Any]) -> list[dict]:
    """Все строки запроса, страницами по PAGE_ROWS.

    make_query — функция, которая собирает запрос заново: один и тот же
    объект запроса повторно не используется. В запросе должен быть
    однозначный порядок (.order по уникальной колонке), иначе строка на
    границе страниц может попасть в обе или ни в одну.
    """
    rows: list[dict] = []
    start = 0
    while True:
        page = make_query().range(start, start + PAGE_ROWS - 1).execute().data
        rows.extend(page)
        if len(page) < PAGE_ROWS:
            return rows
        start += PAGE_ROWS
