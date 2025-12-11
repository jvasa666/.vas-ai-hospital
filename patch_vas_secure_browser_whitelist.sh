#!/usr/bin/env bash
set -euo pipefail

FILE="vas_secure_browser.py"

echo "[VAS] Patching whitelist logic in $FILE ..."

# 1) Patch VASRequestInterceptor.interceptRequest
python3 - << 'PY'
from pathlib import Path

path = Path("vas_secure_browser.py")
text = path.read_text()

old = """        url = info.requestUrl().toString()
        domain = urlparse(url).netloc

        if domain.startswith("www."):
            domain = domain[4:]

        is_allowed = any(
            allowed == domain or domain.endswith("." + allowed)
            for allowed in SecurityConfig.ALLOWED_DOMAINS
        )
"""

new = """        url = info.requestUrl().toString()
        parsed = urlparse(url)
        domain = parsed.hostname or ""

        if domain.startswith("www."):
            domain = domain[4:]

        is_allowed = any(
            allowed == domain or domain.endswith("." + allowed)
            for allowed in SecurityConfig.ALLOWED_DOMAINS
        )
"""

if old not in text:
    raise SystemExit("[VAS] interceptRequest block not found; aborting to avoid corrupting file.")

text = text.replace(old, new)
path.write_text(text)
PY

# 2) Patch VASSecurePage.acceptNavigationRequest
python3 - << 'PY'
from pathlib import Path

path = Path("vas_secure_browser.py")
text = path.read_text()

old = """        domain = urlparse(url.toString()).netloc

        # Check whitelist
        is_allowed = any(
            allowed in domain 
            for allowed in SecurityConfig.ALLOWED_DOMAINS
        )

        if not is_allowed and is_main_frame:
"""

new = """        parsed = urlparse(url.toString())
        domain = parsed.hostname or ""

        if domain.startswith("www."):
            domain = domain[4:]

        # Check whitelist
        is_allowed = any(
            allowed == domain or domain.endswith("." + allowed)
            for allowed in SecurityConfig.ALLOWED_DOMAINS
        )

        if not is_allowed and is_main_frame:
"""

if old not in text:
    raise SystemExit("[VAS] acceptNavigationRequest block not found; aborting to avoid corrupting file.")

text = text.replace(old, new)
path.write_text(text)
PY

echo "[VAS] Patch complete."
