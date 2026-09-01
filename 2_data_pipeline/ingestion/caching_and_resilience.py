"""
THE MRIDANSH : Offline Caching & Rate-Limit Resilient Pipeline Engine (Day 17)
Provides disk/memory caching, exponential backoff retries, rate-limit management,
and offline fallback mechanisms for Earth Observation satellite APIs.
"""

import hashlib
import json
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any


class ResilientSatelliteIngestor:
    """Resilient wrapper for satellite Ingestion APIs with caching and automatic retry mechanisms."""

    def __init__(self, cache_dir: str = ".cache/satellite_data", max_retries: int = 3):
        """Initializes Cache Directory and Resilience Settings."""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_retries = max_retries

    def _generate_cache_key(self, endpoint_name: str, params: dict[str, Any]) -> str:
        """Generates a deterministic SHA256 cache key based on query parameters."""
        serialized = json.dumps(
            {"endpoint": endpoint_name, "params": params}, sort_keys=True
        )
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def get_cached_response(self, cache_key: str) -> dict[str, Any] | None:
        """Retrieves cached JSON payload if available."""
        cache_path = self.cache_dir / f"{cache_key}.json"
        if cache_path.exists():
            try:
                with open(cache_path, encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None
        return None

    def save_cache_response(self, cache_key: str, data: dict[str, Any]) -> None:
        """Saves successful API response payload to local disk cache."""
        cache_path = self.cache_dir / f"{cache_key}.json"
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def execute_with_resilience(
        self,
        endpoint_name: str,
        params: dict[str, Any],
        fetch_function: Callable[[dict[str, Any]], dict[str, Any]],
        fallback_data_generator: Callable[[dict[str, Any]], dict[str, Any]]
        | None = None,
    ) -> dict[str, Any]:
        """Executes satellite API calls with Caching -> Retry -> Exponential Backoff -> Offline Fallback chain."""
        cache_key = self._generate_cache_key(endpoint_name, params)

        # 1. Check Local Offline Cache First
        cached_result = self.get_cached_response(cache_key)
        if cached_result:
            cached_result["_source"] = "LOCAL_DISK_CACHE"
            return cached_result

        # 2. Network Attempt with Exponential Backoff
        attempt = 0
        backoff_delay = 1.0  # Start delay In seconds

        while attempt < self.max_retries:
            try:
                result = fetch_function(params)
                result["_source"] = "LIVE_API_NETWORK"

                # Save to cache on success
                self.save_cache_response(cache_key, result)
                return result

            except Exception:
                attempt += 1
                time.sleep(backoff_delay)
                backoff_delay *= 2.0  # Exponential increase

        # 3. Offline Fallback Strategy
        if fallback_data_generator:
            fallback_result = fallback_data_generator(params)
            fallback_result["_source"] = "OFFLINE FALLBACK_ENGINE"
            return fallback_result

        raise RuntimeError(
            f"API call to {endpoint_name} failed after {self.max_retries} retries and no fallback provided."
        )


# Quick Verification Test
if __name__ == "__main__":
    print("🛰️ Testing Day 17 Offline Cache & Resilient Pipeline...")
    resilient_engine = ResilientSatelliteIngestor(max_retries=2)

    sample_params = {"bbox": [85.75, 20.20, 85.90, 20.35]}

    # Dummy live fetch function that simulates API failure on first calls
    fetch_counter = {"calls": 0}

    def simulated_stac_api(params: dict[str, Any]) -> dict[str, Any]:
        fetch_counter["calls"] += 1
        if fetch_counter["calls"] == 1:
            raise ConnectionError("HTTP 429: Too Many Requests - Simulated Rate Limit")

        return {
            "status": "SUCCESS",
            "scenes_found": 5,
            "provider": "Copernicus_CDSE_STAC",
        }

    def offline_fallback_gen(params: dict[str, Any]) -> dict[str, Any]:
        return {
            "status": "FALLBACK_OFFLINE",
            "scenes_found": 1,
            "provider": "SYNTHETIC_OFFLINE_CACHE",
        }

    print("\n1. Executing Network API Call with Exponential Backoff Retry...")

    result_1 = resilient_engine.execute_with_resilience(
        endpoint_name="stac_sentinel_search",
        params=sample_params,
        fetch_function=simulated_stac_api,
        fallback_data_generator=offline_fallback_gen,
    )

    print(
        f"   Execution Result Source: {result_1['_source']} (Total Network Calls Attempted: {fetch_counter['calls']})"
    )

    print(f"   Status: {result_1['status']}")

    print("\n2. Executing Second Call (Testing Local Disk Cache hit)...")

    result_2 = resilient_engine.execute_with_resilience(
        endpoint_name="stac_sentinel_search",
        params=sample_params,
        fetch_function=simulated_stac_api,
        fallback_data_generator=offline_fallback_gen,
    )

    print(f"   Execution Result Source: {result_2['_source']}")
    print(f"   Cache Retrieval Verified: {result_2['status']}")

    print("\n✅ Day 17 Offline Cache & Resilience Pipeline Complete!")
