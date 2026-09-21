#!/usr/bin/env python3
import http.client
import http.server
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

LISTEN_HOST = "0.0.0.0"
LISTEN_PORT = 8124
CLICKHOUSE_HOST = "127.0.0.1"
CLICKHOUSE_PORT = 8123


class ClickHouseProxy(http.server.ThreadingHTTPServer):
    allow_reuse_address = True


class ProxyHandler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_POST(self):
        self._forward_request()

    def do_GET(self):
        self._forward_request()

    def _read_request_body(self):
        transfer_encoding = self.headers.get("Transfer-Encoding", "").lower()
        if "chunked" in transfer_encoding:
            chunks = []
            while True:
                line = self.rfile.readline().strip()
                if not line:
                    continue
                size = int(line.split(b";", 1)[0], 16)
                if size == 0:
                    self.rfile.readline()
                    break
                chunks.append(self.rfile.read(size))
                self.rfile.read(2)
            return b"".join(chunks)

        length = int(self.headers.get("Content-Length", "0"))
        return self.rfile.read(length) if length else b""

    def _forward_request(self):
        body = self._read_request_body()
        request_url = self.path
        query = parse_qsl(urlsplit(request_url).query, keep_blank_values=True)

        # ClickHouse 26.8 lets format=Native override a SQL FORMAT clause. The
        # Airbyte connector sends compressed SQL, so this must be done without
        # inspecting the request body.
        if any(key.lower() == "format" and value.lower() == "native" for key, value in query):
            query = [
                (key, value)
                for key, value in query
                if not (key.lower() == "format" and value.lower() == "native")
            ]
            parts = urlsplit(request_url)
            request_url = urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))

        headers = {
            key: value
            for key, value in self.headers.items()
            if key.lower() not in {"host", "content-length", "transfer-encoding", "connection"}
        }
        headers["Content-Length"] = str(len(body))
        headers["Connection"] = "close"

        try:
            connection = http.client.HTTPConnection(CLICKHOUSE_HOST, CLICKHOUSE_PORT, timeout=60)
            connection.request(self.command, request_url, body=body, headers=headers)
            response = connection.getresponse()
            response_body = response.read()

            self.send_response(response.status, response.reason)
            for key, value in response.getheaders():
                if key.lower() not in {"connection", "content-length", "transfer-encoding"}:
                    self.send_header(key, value)
            self.send_header("Content-Length", str(len(response_body)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(response_body)
        except Exception as error:
            self.send_error(502, "ClickHouse proxy error")
            self.log_error("%s", error)
        finally:
            try:
                connection.close()
            except UnboundLocalError:
                pass

    def log_message(self, format_string, *args):
        print("%s - %s" % (self.address_string(), format_string % args), flush=True)


if __name__ == "__main__":
    server = ClickHouseProxy((LISTEN_HOST, LISTEN_PORT), ProxyHandler)
    print(f"ClickHouse Airbyte compatibility proxy listening on {LISTEN_HOST}:{LISTEN_PORT}", flush=True)
    server.serve_forever()
