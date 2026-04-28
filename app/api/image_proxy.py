import ipaddress
import socket
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

router = APIRouter(prefix="/image-proxy", tags=["image-proxy"])

_ALLOWED_SCHEMES = {"http", "https"}
# Content-types we're willing to proxy.
_IMAGE_CONTENT_TYPES = {
    "image/jpeg", "image/png", "image/gif", "image/webp",
    "image/svg+xml", "image/avif", "image/bmp",
}
# Hard cap on response size (5 MB) to prevent abuse.
_MAX_BYTES = 5 * 1024 * 1024


def _is_private_host(hostname: str) -> bool:
    """Block SSRF attempts targeting private/loopback addresses."""
    try:
        addr = socket.gethostbyname(hostname)
        ip = ipaddress.ip_address(addr)
        return ip.is_private or ip.is_loopback or ip.is_link_local
    except Exception:
        return False


@router.get("/")
async def proxy_image(url: str = Query(..., description="Absolute image URL to proxy")) -> Response:
    parsed = urlparse(url)

    if parsed.scheme not in _ALLOWED_SCHEMES:
        raise HTTPException(status_code=400, detail="Only http/https URLs are supported")

    hostname = parsed.hostname or ""
    if not hostname or _is_private_host(hostname):
        raise HTTPException(status_code=400, detail="URL resolves to a private address")

    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=httpx.Timeout(10.0),
            headers={"User-Agent": "Mozilla/5.0 (compatible; CollectiveAction/1.0)"},
        ) as client:
            response = await client.get(url)

        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Image not found")

        content_type = response.headers.get("content-type", "image/jpeg").split(";")[0].strip()

        if len(response.content) > _MAX_BYTES:
            raise HTTPException(status_code=413, detail="Image too large")

        return Response(
            content=response.content,
            media_type=content_type if content_type in _IMAGE_CONTENT_TYPES else "image/jpeg",
            headers={
                "Access-Control-Allow-Origin": "*",
                "Cache-Control": "public, max-age=86400",
                "X-Content-Type-Options": "nosniff",
            },
        )

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Image request timed out")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch image: {e}")
