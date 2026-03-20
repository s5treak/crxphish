"""
mitmproxy addon that intercepts HTTP requests and redirects
matching domains to internal Flask routes.

Usage:
    mitmdump -p 8080 --mode regular -s proxy.py
"""

import requests as req
from mitmproxy import http
from utils import get_config, extract_domain


class PhishingProxy:
    """
    mitmproxy addon that reads config.json and reroutes
    HTTP requests for configured domains to internal Flask routes.
    """

    def __init__(self):
        self.config = get_config()
        self.settings = self.config.get("settings", {})
        self.internal_host = self.config.get("internal_host", "http://127.0.0.1:9000")
        self._build_domain_map()

    def _build_domain_map(self):
        """Build a lookup from each domain key to its internal route."""
        self.domain_map = {}
        for key, entry in self.settings.items():
            if isinstance(entry, str):
                route = entry
            else:
                route = entry["route"]
            self.domain_map[key] = route

    def reload_config(self):
        """Reload config from disk (call if config changes at runtime)."""
        self.config = get_config()
        self.settings = self.config.get("settings", {})
        self.internal_host = self.config.get("internal_host", "http://127.0.0.1:9000")
        self._build_domain_map()

    def request(self, flow: http.HTTPFlow) -> None:
        """
        Intercept every HTTP request.
        If the domain is in config settings, fetch the response
        from the matching internal Flask route and return it
        directly to the client.
        """

        print(f"Intercepted request to: {flow.request.pretty_url}")
        domain = extract_domain(flow.request.pretty_url)

        # Match against all catch domains (including www. variants)
        matched_route = None
        if domain in self.domain_map:
            matched_route = self.domain_map[domain]
        elif domain.startswith("www."):
            bare = domain[4:]
            if bare in self.domain_map:
                matched_route = self.domain_map[bare]

        if matched_route is None:
            return  # let it pass through normally

        internal_route = matched_route

        # If the route is a relative path, prepend the internal host
        if internal_route.startswith("/"):
            target_url = f"{self.internal_host}{internal_route}"
        else:
            target_url = internal_route

        try:
            # Forward original headers (minus hop-by-hop ones)
            headers = dict(flow.request.headers)
            headers.pop("host", None)
            headers.pop("Host", None)

            if flow.request.method == "GET":
                resp = req.get(target_url, headers=headers, timeout=10)
            elif flow.request.method == "POST":
                resp = req.post(
                    target_url,
                    headers=headers,
                    data=flow.request.content,
                    timeout=10,
                )
            else:
                resp = req.request(
                    flow.request.method,
                    target_url,
                    headers=headers,
                    data=flow.request.content,
                    timeout=10,
                )

            # Build mitmproxy response from internal response
            response_headers = {
                k: v for k, v in resp.headers.items()
                if k.lower() not in ("transfer-encoding", "content-encoding", "content-length")
            }

            flow.response = http.Response.make(
                resp.status_code,
                resp.content,
                response_headers,
            )

        except req.RequestException as e:
            flow.response = http.Response.make(
                502,
                f"Internal route error: {e}".encode(),
                {"Content-Type": "text/plain"},
            )


# mitmproxy discovers addons via this module-level list
addons = [PhishingProxy()]
