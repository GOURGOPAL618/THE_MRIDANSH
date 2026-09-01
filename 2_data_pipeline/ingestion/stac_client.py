"""
THE MRIDANSH : Satellite STAC API Engine (Day 13)
Handles searching and metadata extraction for Copernicus Sentinel-1 (SAR)
and Sentinel-2 (Optical) satellite products via STAC endpoints.
"""

from typing import Any

from pystac_client import Client


class SatelliteSTACClient:
    """Client wrapper for SpatioTemporal Asset Catalog (STAC) Queries."""

    STAC_ENDPOINT_URL = "https://earth-search.aws.element84.com/v1"

    def __init__(self, catalog_url: str | None = None):
        """Initialize Connection To the STAC Catalog."""
        self.catalog_url = catalog_url or self.STAC_ENDPOINT_URL
        self.client = Client.open(self.catalog_url)

    def search_sentinel2_optical(
        self,
        bbox: list[float],
        start_date: str,
        end_date: str,
        max_cloud_cover: float = 20.0,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Searches Sentinel-2 L2A (Optical/Multispectral) scene.

        Parameters:
            bbox: [min_lon, min_lat, max_lon, max_lat]
            start_date: 'YYYY-MM-DD'
            end_date: 'YYYY-MM-DD'
            max_cloud_cover: Cloud cover threshold percentage (0-100)
            limit: Maximum scenes to return
        """

        datetime_range = f"{start_date}/{end_date}"

        search = self.client.search(
            collections=["sentinel-2-l2a"],
            bbox=bbox,
            datetime=datetime_range,
            query={"eo:cloud_cover": {"lt": max_cloud_cover}},
            limit=limit,
        )

        items = list(search.items())
        results = []

        for item in items:
            results.append(
                {
                    "scene_id": item.id,
                    "datetime": item.datetime.isoformat() if item.datetime else None,
                    "cloud_cover": item.properties.get("eo:cloud_cover", 0.0),
                    "bbox": item.bbox,
                    "assets": {
                        "red": item.assets.get("red", {}).href
                        if "red" in item.assets
                        else None,
                        "nir": item.assets.get("nir", {}).href
                        if "nir" in item.assets
                        else None,
                        "swir16": item.assets.get("swir16", {}).href
                        if "swir16" in item.assets
                        else None,
                        "visual": item.assets.get("visual", {}).href
                        if "visual" in item.assets
                        else None,
                    },
                }
            )
        return results

    def search_sentinel1_sar(
        self,
        bbox: list[float],
        start_date: str,
        end_date: str,
        polarization: str = "VV",
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Searches Sentinel-1 Ground Range Detected (GRD) SAR scenes.

        Parameters:
            bbox: [min_lon, min_lat, max_lon, max_lat]
            start_date: 'YYYY-MM-DD'
            end_date: 'YYYY-MM-DD'
            polarization: Desired radar polarization ('VV' or 'VH')
            limit: Maximum scenes to return
        """

        datetime_range = f"{start_date}/{end_date}"

        search = self.client.search(
            collections=["sentinel-1-grd"],
            bbox=bbox,
            datetime=datetime_range,
            limit=limit,
        )

        items = list(search.items())
        results = []

        for item in items:
            assets = item.assets
            selected_asset = None

            # Look For Requested Polarization Channel
            for key in assets.keys():
                if polarization.lower() in key.lower():
                    selected_asset = assets[key].href
                    break

            results.append(
                {
                    "scene_id": item.id,
                    "datetime": item.datetime.isoformat() if item.datetime else None,
                    "platform": item.properties.get("platform", "sentinel-1"),
                    "orbit_direction": item.properties.get(
                        "sat.orbit_state", "descending"
                    ),
                    "bbox": item.bbox,
                    "sar_href": selected_asset,
                }
            )

        return results


# Quick Execution Test
if __name__ == "__main__":
    print("🛰️ Testing Satellite STAC Client Connection...")
    stac_engine = SatelliteSTACClient()

    # Bhubaneswar Corrioder Bounding Box Example
    bhubaneswar_bbox = [85.75, 20.20, 85.90, 20.35]

    print("\n1. Searching Sentinel-2 Optical Scenes...")
    opt_scenes = stac_engine.search_sentinel2_optical(
        bbox=bhubaneswar_bbox,
        start_date="2026-01-01",
        end_date="2026-08-01",
        max_cloud_cover=15.0,
        limit=2,
    )

    print(f"   Found {len(opt_scenes)} optical scenes.")

    if opt_scenes:
        print(f"   Latest Scene ID: {opt_scenes[0]['scene_id']}")
        print(f"   Cloud Cover: {opt_scenes[0]['cloud_cover']:.2f}%")

    print("\n2. Searching Sentinel-1 SAR Radar Scenes...")
    sar_scenes = stac_engine.search_sentinel1_sar(
        bbox=bhubaneswar_bbox,
        start_date="2026-01-01",
        end_date="2026-08-01",
        limit=2,
    )

    print(f"   Found {len(sar_scenes)} SAR scenes.")
    if sar_scenes:
        print(f"   Latest SAR Scene ID: {sar_scenes[0]['scene_id']}")

    print("\n✅ Day 13 STAC Engine Verification Complete!")
