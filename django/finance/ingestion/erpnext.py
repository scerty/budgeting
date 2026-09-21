import json
from http.cookiejar import CookieJar
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import HTTPCookieProcessor, Request, build_opener


class ERPNextAPIError(RuntimeError):
    """Raised when ERPNext returns an API or transport error."""


class ERPNextClient:
    def __init__(self, base_url, username, password, timeout=30, opener=None):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.timeout = timeout
        self.opener = opener or build_opener(HTTPCookieProcessor(CookieJar()))

    def _request(self, method, path, payload=None, query=None):
        url = f"{self.base_url}{path}"
        if query:
            url = f"{url}?{urlencode(query)}"
        data = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = Request(url, data=data, headers=headers, method=method)
        try:
            with self.opener.open(request, timeout=self.timeout) as response:
                body = response.read().decode("utf-8")
        except (HTTPError, URLError, TimeoutError) as exc:
            detail = getattr(exc, "reason", exc)
            raise ERPNextAPIError(f"ERPNext request failed: {detail}") from exc
        try:
            result = json.loads(body)
        except json.JSONDecodeError as exc:
            raise ERPNextAPIError("ERPNext returned invalid JSON") from exc
        if result.get("exc_type") or result.get("exception"):
            message = result.get("_server_messages") or result.get("exception")
            raise ERPNextAPIError(f"ERPNext API error: {message}")
        return result

    def login(self):
        self._request(
            "POST",
            "/api/method/login",
            {"usr": self.username, "pwd": self.password},
        )

    def iter_resource(self, doctype, fields, filters=None, page_size=100):
        start = 0
        encoded_doctype = quote(doctype, safe="")
        while True:
            query = {
                "fields": json.dumps(fields, separators=(",", ":")),
                "limit_start": start,
                "limit_page_length": page_size,
                "order_by": "name asc",
            }
            if filters:
                query["filters"] = json.dumps(filters, separators=(",", ":"))
            result = self._request("GET", f"/api/resource/{encoded_doctype}", query=query)
            rows = result.get("data", [])
            yield from rows
            if len(rows) < page_size:
                break
            start += page_size