import requests
import aiohttp
import asyncio
import logging
from typing import Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from config.settings import YUANTA_BASE_URL, API_TIMEOUT, API_MAX_RETRIES

logger = logging.getLogger(__name__)

class YuantaAPIClient:
    """Client to interact with Yuanta API with built-in retry and error handling."""
    
    def __init__(self):
        self.session = requests.Session()
        # Default headers based on standard browser requests to avoid being blocked
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8',
            'Referer': 'https://radar.yuanta.com.vn/',
            'Origin': 'https://radar.yuanta.com.vn'
        })
        
    @retry(
        stop=stop_after_attempt(API_MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.exceptions.RequestException, ValueError))
    )
    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None) -> Any:
        url = f"{YUANTA_BASE_URL}/{endpoint}"
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                timeout=API_TIMEOUT
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                logger.warning(f"Rate limited by Yuanta API. Retrying... URL: {url}")
            else:
                logger.error(f"HTTP Error: {e} - URL: {url}")
            raise
        except Exception as e:
            logger.error(f"Request failed: {e} - URL: {url}")
            raise

    def get(self, endpoint: str, params: Optional[Dict] = None) -> Any:
        """Thực hiện GET request tới Yuanta API"""
        return self._make_request("GET", endpoint, params)

class AsyncYuantaAPIClient:
    """Asynchronous Client to interact with Yuanta API."""
    def __init__(self, concurrency: int = 20):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8',
            'Referer': 'https://radar.yuanta.com.vn/',
            'Origin': 'https://radar.yuanta.com.vn'
        }
        self.semaphore = asyncio.Semaphore(concurrency)
        
    async def get(self, session: aiohttp.ClientSession, endpoint: str, params: Optional[Dict] = None) -> Any:
        url = f"{YUANTA_BASE_URL}/{endpoint}"
        async with self.semaphore:
            try:
                async with session.get(url, params=params, timeout=API_TIMEOUT) as response:
                    if response.status == 429:
                        logger.warning(f"Rate limited (async). URL: {url}")
                        await asyncio.sleep(2)
                        return await self.get(session, endpoint, params)
                    response.raise_for_status()
                    return await response.json()
            except Exception as e:
                logger.error(f"Async Request failed: {e} - URL: {url}")
                return None

# Instantiate singleton clients
yuanta_client = YuantaAPIClient()
async_yuanta_client = AsyncYuantaAPIClient()
