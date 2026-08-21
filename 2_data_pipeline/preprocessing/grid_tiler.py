"""
THE MRIDANSH : Geospatial Indexing & Spatial Grid Tiling Engine (Day 22)
Splits large Area of Interest (AOI) boundaries into uniform computational sub-grid tiles
with unique geospatial indices, tile bounding boxes, and GeoJSON polygon exports.
"""

from typing import Dict, Any, Tuple, List
import json

class GeospatialGridTiler:
    """Splits continuous spatial AOI boundaries into computational sub-grids and indexes them."""

    def __init__(self):
        """Initializes Geospatial Grid Tiler Engine."""
        pass

    def create_spatial_subgrids(
        self,
        bbox: List[float],
        rows: int = 4,
        cols: int = 4,
    ) -> List[Dict[str, Any]]:
        """Splits a bounding box [min_lon, min_lat, max_lon, max_lat] into a grid of sub-tiles.

        Parameters:
            bbox: Bounding box extent [min_lon, min_lat, max_lon, max_lat]
            rows: Number of grid divisions along latitude (Y-axis)
            cols: Number of grid divisions along longitude (X-axis)

        Returns:
            List of indexed dictionary objects containing tile metadata and coordinates.
        """

        min_lon, min_lat, max_lon, max_lat = bbox

        lon_step = (max_lon - min_lon) / cols
        lat_step = (max_lat - min_lat) / rows

        tiles = []

        for r in range(rows):
            for c in range(cols):
                tile_min_lon = min_lon + (c * lon_step)
                tile_max_lon = tile_min_lon + lon_step
                tile_min_lat = min_lat + (r * lat_step)
                tile_max_lat = tile_min_lat + lat_step

                tile_bbox = [
                    round(tile_min_lon, 6),
                    round(tile_min_lat, 6),
                    round(tile_max_lon, 6),
                    round(tile_max_lat, 6),
                ]

                centroid = [
                    round((tile_min_lat + tile_max_lat) / 2.0, 6),
                    round((tile_min_lon + tile_max_lon) / 2.0, 6),
                ]

                tile_id = f"TILE_R{r}_C{c}"

                # Coordinates ring for GeoJSON Polygon (Closed Loop)
                polygon_coords = [
                    [
                        [tile_min_lon, tile_min_lat],
                        [tile_max_lon, tile_min_lat],
                        [tile_max_lon, tile_max_lat],
                        [tile_min_lon, tile_max_lat],
                        [tile_min_lon, tile_min_lat],
                    ]
                ]

                tiles.append({
                    "tile_id": tile_id,
                    "row": r,
                    "col": c,
                    "bbox": tile_bbox,
                    "centroid": centroid,
                    "polygon_coords": polygon_coords,
                })

        return tiles

    def export_tiles_to_geojson(self, tiles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Converts generated grid tile metadata into a standard GeoJSON FeatureCollection."""
        features = []

        for tile in tiles:
            feature = {
                "type": "Feature",
                "properties": {
                    "tile_id": tile["tile_id"],
                    "row": tile["row"],
                    "col": tile["col"],
                    "centroid": tile["centroid"],
                    "bbox": tile["bbox"]
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": tile["polygon_coords"],
                },
            }
            features.append(feature)

        return {"type": "FeatureCollection", "features": features}


# Quick Verification Test
if __name__ == "__main__":
    print("🧩 Testing Day 22 Geospatial Indexing & Grid Tiling Engine...")
    tiler = GeospatialGridTiler()

    # Bhubaneswar AOI Bounding Box
    bhubaneswar_bbox = [85.75, 20.20, 85.90, 20.35]

    print("\n1. Splitting Bhubaneswar Spatial Extent into 4x4 Computational Grid (16 Tiles)...")
    tiler_grid = tiler.create_spatial_subgrids(bhubaneswar_bbox, rows = 4, cols = 4)

    print(f"   Generated Total Sub-Grid Tiles: {len(tiler_grid)}")
    print(f"   Sample Tile 0 ID: {tiler_grid[0]['tile_id']}")
    print(f"   Sample Tile 0 Bounding Box: {tiler_grid[0]['bbox']}")
    print(f"   Sample Tile 0 Centroid (Lat, Lon): {tiler_grid[0]['centroid']}")

    print("\n2. Exporting Spatial Grid Mesh to GeoJSON Format...")
    geojson_grid = tiler.export_tiles_to_geojson(tiler_grid)
    

    output_json = "test_spatial_grid_day22.geojson"
    with open(output_json, "w") as f:
        json.dump(geojson_grid, f, indent=2)

    print(f"   Saved Indexed Spatial Grid Mesh to: {output_json}")

    print("\n✅ Day 22 Geospatial Indexing & Grid Tiling Engine Complete!")