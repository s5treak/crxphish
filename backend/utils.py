from urllib.parse import urlparse
import json
import os

config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),'config.json')


def extract_domain(url):
    # Parse the URL
    parsed_url = urlparse(url)
    
    # Extract and return the domain (netloc)
    domain = parsed_url.netloc
    
    # Return the domain name without the "www." prefix, if present
    if domain.startswith('www.'):
        domain = domain[4:]
    
    return domain


def get_config():
        
    with open(config_path,"r") as f:

        return json.load(f)


def get_rules():
    """Build declarativeNetRequest rules + PAC proxy config from config.json."""

    rules = []
    proxy_config = [] 

    data = get_config()
    settings = data.get("settings", {})

    # Proxy address = 127.0.0.1:<proxy_port>  (where mitmproxy listens)
    proxy_port = data.get("proxy_port", 8080)
    proxy = f"127.0.0.1:{proxy_port}"

    # Collect all configured domains to build exclusion lists
    all_domains = list(settings.keys())
    internal_host = data.get("internal_host", "http://127.0.0.1:9000")

    for index, (key, entry) in enumerate(settings.items()):
        # Support both old format (string) and new format (object with route)
        if isinstance(entry, str):
            route = entry
            is_hsts = False
        else:
            route = entry["route"]
            is_hsts = entry.get("hsts", False)

        # HSTS-preloaded domains: redirect straight to internal Flask route
        # (Chrome blocks HTTP downgrade for these domains)
        if is_hsts:
            redirect_url = f"{internal_host}{route}"
        else:
            redirect_url = f"http://{key}"
            # Only need PAC proxy config for non-HSTS domains
            proxy_config.append(f"host == '{key}'")
            proxy_config.append(f"host == 'www.{key}'")

        condition = {
            "urlFilter": "|https://",
            "requestDomains": [key],
            "resourceTypes": ["main_frame"],
        }

        rules.append(
            {
                "id": index + 1,
                "priority": 1,
                "action": {"type": "redirect", "redirect": {"url": redirect_url}},
                "condition": condition,
            }
        )

    return {
        "proxy": proxy,
        "rules": rules,
        "proxy_config": " || ".join(proxy_config),
    }
