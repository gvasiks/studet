"""Вежливый обход источников (ревизия 2026-09-20, пункт 04).

Скрейперы бьют по сайтам вузов без ограничений; самая вероятная
неприятность — не юридическая, а техническая: блокировка по адресу в
неподходящий момент. Решение собирать данные без отдельной проверки
условий использования принято владельцем (CLAUDE.md), этот модуль лишь
снижает уже принятый риск.

Подключается ОДИН раз в main.py — `polite.install()`. Все 24 сборщика
создают страницы через `browser.new_page()` и ходят через `page.goto()`,
поэтому подмена двух методов Playwright заменяет правку каждого
сборщика. Что делает:

- честный User-Agent: "StudyPickBot/1.0 (+контакт)" — администратор,
  которому что-то не нравится, напишет письмо, а не заблокирует адрес.
  Контакт берётся из переменной SCRAPER_CONTACT (URL или почта);
  без неё User-Agent остаётся без контакта, и об этом предупреждают;
- пауза между страницами ОДНОГО домена: не меньше SCRAPE_DELAY_SECONDS
  (по умолчанию 1,5) и не меньше Crawl-delay из robots.txt — у niid.lv
  это 10 секунд. Сборщики идут по очереди, так что параллельных
  запросов к одному домену и так нет;
- robots.txt: запрещённые для нас адреса не открываются, а попадают в
  отчёт (SCRAPE_OBEY_ROBOTS=0 отключает, для отладки). Сам robots.txt — по
  RFC 9309: ответ 4xx — файла нет, ограничений нет; ответ 5xx или нет связи
  (после одного повтора) — повторяем через браузер сборщика: с сервера GitHub
  часть сайтов не отвечает на простой запрос. Не вышло и так — правила
  неизвестны, и сайт в этом прогоне не обходится (RobotsUnavailable;
  main.py записывает это как сбой источника). До 2026-10-25 в этом случае
  сайт обходился как разрешённый;
- картинки, шрифты и видео не загружаются — тексту они не нужны, а
  сайту это десятки лишних запросов на страницу;
- локальный кэш для отладки (SCRAPE_CACHE=1): страницы и XHR сутки
  лежат в pipeline/.cache/, повторный запуск сборщика идёт без сети.
  В CI кэш выключен — данные должны быть свежими.

Скрипты без браузера (файлы CSV, простые HTML-страницы) ходят через
open_url() и fetch_text() — по тем же правилам: User-Agent, robots.txt,
паузы. Своих запросов через urllib в конвейере нет (до 2026-10-25 их было
четыре, с разными правилами robots.txt).
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
import urllib.robotparser
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import Browser, Page, Route

PRODUCT_TOKEN = "StudyPickBot"
DEFAULT_DELAY_SECONDS = 1.5
CACHE_TTL_SECONDS = 24 * 3600
CACHE_DIR = Path(__file__).resolve().parent.parent / ".cache"
SKIPPED_RESOURCE_TYPES = {"image", "media", "font"}
CACHED_RESOURCE_TYPES = {"document", "xhr", "fetch"}
ROBOTS_RETRY_PAUSE_SECONDS = 5


class RobotsDisallowed(Exception):
    """robots.txt запрещает этот адрес для нашего User-Agent."""


class RobotsUnavailable(Exception):
    """robots.txt не получен (ответ 5xx или нет связи): по RFC 9309 правила
    обхода неизвестны, а не отсутствуют — сайт в этом прогоне не обходится."""


_installed = False
_last_finished: dict[str, float] = {}
_browser_goto = Page.goto  # настоящий Page.goto: install() его подменяет
_robots: dict[str, urllib.robotparser.RobotFileParser | RobotsUnavailable] = {}
_stats = {"pages": 0, "waited": 0.0, "assets_skipped": 0, "cache_hits": 0, "blocked": []}


def user_agent() -> str:
    contact = os.environ.get("SCRAPER_CONTACT", "").strip()
    return f"Mozilla/5.0 (compatible; {PRODUCT_TOKEN}/1.0" + (f"; +{contact}" if contact else "") + ")"


def _delay() -> float:
    try:
        return float(os.environ.get("SCRAPE_DELAY_SECONDS", DEFAULT_DELAY_SECONDS))
    except ValueError:
        return DEFAULT_DELAY_SECONDS


def _obey_robots() -> bool:
    return os.environ.get("SCRAPE_OBEY_ROBOTS", "1") != "0"


def _cache_enabled() -> bool:
    return os.environ.get("SCRAPE_CACHE", "") == "1"


def robots_unreachable_means_stop(status: int) -> bool:
    """Ответ на запрос robots.txt, при котором сайт не обходят (RFC 9309):
    4xx — файла нет, ограничений нет; 5xx — правила неизвестны."""
    return status >= 500


def robots_from(body: str | None) -> urllib.robotparser.RobotFileParser:
    """Правила обхода из текста robots.txt; None — файла нет (ответ 4xx),
    ограничений нет. Стандартный RobotFileParser.read() не годится: при
    401/403 он запрещает ВСЁ, и отказ сайта выглядел бы как запрет."""
    parser = urllib.robotparser.RobotFileParser()
    parser.parse((body or "").splitlines())
    return parser


def _robots_body(origin: str) -> str | None:
    """Текст robots.txt простым запросом; None — файла нет (ответ 4xx)."""
    problem = ""
    for attempt in (1, 2):
        try:
            request = urllib.request.Request(f"{origin}/robots.txt", headers={"User-Agent": user_agent()})
            return urllib.request.urlopen(request, timeout=15).read().decode("utf-8", "replace")
        except urllib.error.HTTPError as error:
            if not robots_unreachable_means_stop(error.code):
                return None
            problem = f"ответ {error.code}"
        except Exception as error:  # noqa: BLE001 — нет связи, таймаут
            # причина важна: URLError без неё ничего не объясняет (сбор 2026-10-26)
            problem = f"{type(error).__name__}: {getattr(error, 'reason', error)}"
        if attempt == 1:
            time.sleep(ROBOTS_RETRY_PAUSE_SECONDS)  # один повтор: сеть могла моргнуть
    raise RobotsUnavailable(f"{origin}/robots.txt не получен ({problem})")


def _robots_body_via_browser(origin: str, page: Page) -> str | None:
    """Текст robots.txt через браузер сборщика — тем же путём, которым он
    пойдёт за страницами. С сервера GitHub простой запрос к lbtu.lv, niid.lv,
    rai.lv и naa.mil.lv не проходит, а браузер туда попадает (сбор 2026-10-26:
    шесть источников упали на этом месте). Страницу занимаем ненадолго:
    сразу за этим сборщик уйдёт на свой адрес."""
    url = f"{origin}/robots.txt"
    try:
        response = _browser_goto(page, url, wait_until="domcontentloaded", timeout=30000)
    except Exception as error:  # noqa: BLE001 — браузер тоже не дошёл
        raise RobotsUnavailable(f"{url} не получен и через браузер ({type(error).__name__}) — сайт в этом прогоне не обходится")
    if response is None or robots_unreachable_means_stop(response.status):
        status = response.status if response is not None else "нет ответа"
        raise RobotsUnavailable(f"{url} не получен и через браузер (ответ {status}) — сайт в этом прогоне не обходится")
    return response.text() if response.ok else None


def _robots_for(url: str, page: Page | None = None) -> urllib.robotparser.RobotFileParser:
    """Правила сайта. page — страница Playwright, если запрос идёт из браузера:
    у неё есть запасной путь к robots.txt, у open_url() его нет."""
    parsed = urlparse(url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    known = _robots.get(origin)
    if isinstance(known, RobotsUnavailable):
        raise known
    if known is not None:
        return known

    try:
        try:
            body = _robots_body(origin)
        except RobotsUnavailable as unavailable:
            if page is None:
                raise
            print(f"polite: {unavailable}; читаю через браузер")
            body = _robots_body_via_browser(origin, page)
    except RobotsUnavailable as unavailable:
        _robots[origin] = unavailable
        raise

    parser = robots_from(body)
    _robots[origin] = parser
    return parser


def _cache_paths(url: str) -> tuple[Path, Path]:
    key = hashlib.sha256(url.encode("utf-8")).hexdigest()
    return CACHE_DIR / f"{key}.json", CACHE_DIR / f"{key}.bin"


def _cached(url: str) -> bool:
    if not _cache_enabled():
        return False
    meta, body = _cache_paths(url)
    return meta.exists() and body.exists() and time.time() - meta.stat().st_mtime < CACHE_TTL_SECONDS


def forget(url: str) -> None:
    """Убрать страницу из кэша: сборщик увидел, что она пришла неполной, и
    хочет запросить её заново, а не получить ту же копию с диска."""
    for path in _cache_paths(url):
        path.unlink(missing_ok=True)


def _wait_turn(url: str, page: Page | None = None) -> None:
    """Проверка robots.txt и пауза перед запросом к сайту."""
    host = urlparse(url).netloc
    try:
        parser = _robots_for(url, page)
    except RobotsUnavailable:
        if _obey_robots():
            raise
        parser = robots_from(None)  # отладка без robots.txt (SCRAPE_OBEY_ROBOTS=0)
    if _obey_robots() and not parser.can_fetch(PRODUCT_TOKEN, url):
        _stats["blocked"].append(url)
        raise RobotsDisallowed(url)

    crawl_delay = parser.crawl_delay(PRODUCT_TOKEN) or 0
    wait = _last_finished.get(host, 0.0) + max(_delay(), float(crawl_delay)) - time.monotonic()
    if wait > 0:
        time.sleep(wait)
        _stats["waited"] += wait


def _route_handler(route: Route) -> None:
    request = route.request
    if request.resource_type in SKIPPED_RESOURCE_TYPES:
        _stats["assets_skipped"] += 1
        route.abort()
        return

    if _cache_enabled() and request.method == "GET" and request.resource_type in CACHED_RESOURCE_TYPES:
        meta_path, body_path = _cache_paths(request.url)
        if _cached(request.url):
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            _stats["cache_hits"] += 1
            route.fulfill(status=meta["status"], headers=meta["headers"], body=body_path.read_bytes())
            return
        response = route.fetch()
        if response.status >= 400:
            # Ответ с ошибкой не запоминаем: иначе повторный запрос той же
            # страницы получил бы из кэша ту же ошибку.
            route.fulfill(response=response)
            return
        CACHE_DIR.mkdir(exist_ok=True)
        body_path.write_bytes(response.body())
        content_type = response.headers.get("content-type", "text/html; charset=utf-8")
        meta_path.write_text(
            json.dumps({"status": response.status, "headers": {"content-type": content_type}}),
            encoding="utf-8",
        )
        route.fulfill(response=response)
        return

    route.continue_()


def install() -> None:
    """Подмена Browser.new_page и Page.goto. Вызывать один раз, после load_dotenv()."""
    global _installed
    if _installed:
        return
    _installed = True

    if not os.environ.get("SCRAPER_CONTACT", "").strip():
        print(
            "polite: SCRAPER_CONTACT не задан — User-Agent уйдёт без контакта. Задайте URL или "
            "почту в pipeline/.env (и переменную SCRAPER_CONTACT в GitHub)."
        )

    global _browser_goto
    original_new_page = Browser.new_page
    original_goto = Page.goto
    _browser_goto = original_goto

    def new_page(self: Browser, **kwargs):  # type: ignore[no-untyped-def]
        kwargs.setdefault("user_agent", user_agent())
        page = original_new_page(self, **kwargs)
        page.route("**/*", _route_handler)
        return page

    def goto(self: Page, url: str, **kwargs):  # type: ignore[no-untyped-def]
        if not _cached(url):  # ответ из кэша сети не касается
            _wait_turn(url, self)
        try:
            response = original_goto(self, url, **kwargs)
            # Отказ сайта (403, 429, 503…) сборщики не замечают: страница
            # открылась, просто на ней нет программ, и в журнале остаётся
            # только "нашёл 0 программ". Так было 2026-10-03 с rtu.lv и
            # lma.lv на сервере GitHub — локально оба сайта отвечали нормально.
            if response is not None and response.status >= 400:
                print(f"polite: HTTP {response.status} — {url}")
            return response
        finally:
            _stats["pages"] += 1
            _last_finished[urlparse(url).netloc] = time.monotonic()

    Browser.new_page = new_page  # type: ignore[method-assign]
    Page.goto = goto  # type: ignore[method-assign]


def open_url(url: str, timeout: float = 60):  # type: ignore[no-untyped-def]
    """Запрос без браузера по тем же правилам, что page.goto: User-Agent,
    robots.txt, пауза. Возвращает ответ urllib — его открывают в `with` и
    могут читать потоком (большой CSV не ложится ни в память, ни на диск).
    Отказ сайта — urllib.error.HTTPError, как у urlopen."""
    _wait_turn(url)
    try:
        request = urllib.request.Request(url, headers={"User-Agent": user_agent()})
        return urllib.request.urlopen(request, timeout=timeout)
    finally:
        _stats["pages"] += 1
        _last_finished[urlparse(url).netloc] = time.monotonic()


def fetch_text(url: str, timeout: float = 60, encoding: str = "utf-8") -> str:
    """Страница или файл целиком, текстом (open_url и чтение до конца)."""
    with open_url(url, timeout) as response:
        return response.read().decode(encoding, "replace")


def _selftest() -> None:
    assert not robots_unreachable_means_stop(404) and not robots_unreachable_means_stop(403), "4xx — ограничений нет"
    assert robots_unreachable_means_stop(500) and robots_unreachable_means_stop(503), "5xx — сайт не обходится"
    resource = "https://data.gov.lt/datasets/2914/versions/729/dynamic-resource/Programa/csv/download/"
    allowed = robots_from("User-agent: *\nCrawl-delay: 5\nDisallow: /login\nDisallow: /datasets/stats\n")
    assert allowed.can_fetch(PRODUCT_TOKEN, resource) and allowed.crawl_delay(PRODUCT_TOKEN) == 5
    assert not allowed.can_fetch(PRODUCT_TOKEN, "https://data.gov.lt/datasets/stats/x")
    assert robots_from(None).can_fetch(PRODUCT_TOKEN, resource), "robots.txt нет — ограничений нет"
    assert not robots_from("User-agent: *\nDisallow: /\n").can_fetch(PRODUCT_TOKEN, resource), "запрет остаётся запретом"
    # недоступный robots.txt запоминается: следующий запрос к тому же сайту
    # падает сразу, без новой попытки
    _robots["https://down.example"] = RobotsUnavailable("down")
    for _ in range(2):
        try:
            _robots_for("https://down.example/page")
            raise AssertionError("ожидался RobotsUnavailable")
        except RobotsUnavailable:
            pass
    del _robots["https://down.example"]

    # простой запрос не прошёл (как с сервера GitHub) — запасной путь через браузер
    class FakeResponse:
        def __init__(self, status: int, body: str = "") -> None:
            self.status, self.ok, self._body = status, status < 400, body

        def text(self) -> str:
            return self._body

    def browser_answers(answer):  # type: ignore[no-untyped-def]
        def fake_goto(_page, _url, **_kwargs):  # type: ignore[no-untyped-def]
            if isinstance(answer, Exception):
                raise answer
            return answer

        return fake_goto

    def no_network(*_args, **_kwargs):  # type: ignore[no-untyped-def]
        raise urllib.error.URLError("connection refused")

    global _browser_goto, ROBOTS_RETRY_PAUSE_SECONDS
    real_urlopen, real_goto, real_pause = urllib.request.urlopen, _browser_goto, ROBOTS_RETRY_PAUSE_SECONDS
    urllib.request.urlopen, ROBOTS_RETRY_PAUSE_SECONDS = no_network, 0
    page = object()
    try:
        _browser_goto = browser_answers(FakeResponse(200, "User-agent: *\nDisallow: /closed\n"))
        rules = _robots_for("https://a.example/x", page)  # type: ignore[arg-type]
        assert rules.can_fetch(PRODUCT_TOKEN, "https://a.example/x")
        assert not rules.can_fetch(PRODUCT_TOKEN, "https://a.example/closed"), "правила из браузера действуют"

        _browser_goto = browser_answers(FakeResponse(404))
        assert _robots_for("https://b.example/x", page).can_fetch(PRODUCT_TOKEN, "https://b.example/x"), "4xx — ограничений нет"  # type: ignore[arg-type]

        for origin, answer in (("https://c.example", FakeResponse(503)), ("https://d.example", TimeoutError())):
            _browser_goto = browser_answers(answer)
            try:
                _robots_for(f"{origin}/x", page)  # type: ignore[arg-type]
                raise AssertionError("ожидался RobotsUnavailable")
            except RobotsUnavailable:
                pass

        # без браузера запасного пути нет, а причина сбоя видна в сообщении
        try:
            _robots_for("https://e.example/x")
            raise AssertionError("ожидался RobotsUnavailable")
        except RobotsUnavailable as error:
            assert "connection refused" in str(error), error
    finally:
        urllib.request.urlopen, _browser_goto, ROBOTS_RETRY_PAUSE_SECONDS = real_urlopen, real_goto, real_pause
        for name in "abcde":
            _robots.pop(f"https://{name}.example", None)
    print("selftest: OK")


def report_and_reset() -> str:
    """Одна строка для журнала после каждого источника."""
    blocked = _stats["blocked"]
    line = (
        f"polite: страниц {_stats['pages']}, ждали {_stats['waited']:.0f} с, "
        f"картинок/шрифтов пропущено {_stats['assets_skipped']}, из кэша {_stats['cache_hits']}, "
        f"закрыто robots.txt {len(blocked)}"
    )
    if blocked:
        line += " (" + ", ".join(blocked[:3]) + (" …" if len(blocked) > 3 else "") + ")"
    _stats.update(pages=0, waited=0.0, assets_skipped=0, cache_hits=0, blocked=[])
    return line


if __name__ == "__main__":
    import sys

    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    if "--selftest" in sys.argv[1:]:
        _selftest()
