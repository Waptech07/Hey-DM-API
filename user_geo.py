import httpx
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from decouple import config

class GeoLocationService:
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def get_location(self, ip: str):
        url = f"https://ipinfo.io/{ip}/json?token={self.api_key}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    def get_client_ip(self, request: Request):
        """Retrieve the client's IP address from the request, accounting for proxies."""
        # Use X-Forwarded-For if available, otherwise use the remote address
        if request.headers.get("X-Forwarded-For"):
            ip = request.headers["X-Forwarded-For"].split(",")[0].strip()
        else:
            ip = request.client.host
        return ip

geo_router = APIRouter()

GEO_API_TOKEN = config('GEO_API_TOKEN')  # Make sure your environment variable is set
geo_service = GeoLocationService(api_key=GEO_API_TOKEN)

@geo_router.get("/get-user-location")
async def get_user_location(request: Request):
    ip = geo_service.get_client_ip(request)
    try:
        location_data = await geo_service.get_location(ip)
        
        # Determine if the user is using a VPN
        is_vpn = location_data.get("privacy", {}).get("vpn", False)

        return JSONResponse(content={
            "ip": ip,
            "location": location_data,
            "is_vpn": is_vpn
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail="Could not retrieve location data.")
