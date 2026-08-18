"""
THE MRIDANSH : Interactive AOI Polygon Drawing & Spatial Boundary Extractor (Day 19)
Integrates Folium Draw plugins to allow users to draw custom spatial boundaries (Polygons/Rectangles)
and extracts bounding boxes, area metrics, and GeoJSON parameters for downstream satellite ingestion.
"""

import json
from typing import Any, Dict, List, Tuple
import folium
from folium import plugins

class AOIPolygonSelector:
    """ Interactive AOI Drawing Tool and Spatial Coordinate Parser."""

    def __init__(self):
        """Initializes AOI Selector engine."""
        pass

    def add_drawing_control(
        self,
        folium_map: folium.Map,
        export_geojson: bool = True,
        position: str = "topleft",
    ) -> folium.Map:
        """Embeds Leaflet.draw controls into an existing Folium map instance."""
        draw_tool = plugins.Draw(
            export=export_geojson,
            position=position,
            draw_options={
                "polyline": False,
                "circle": False,
                "circlemarker": False,
                "marker": False,
                "polygon": {
                    "allowIntersection": False,
                    "showArea": True,
                    "drawError": {
                        "color": "#e1e100",
                        "message": "<strong>Error:</strong> Polygon edges cannot intersect!",
                    },
                    "shapeOptions": {"color": "#10b981", "fillOpacity": 0.3},
                },
                "rectangle": {
                    "shapeOptions": {"color": "#3b82f6", "fillOpacity": 0.25}
                },
            },
            edit_options={"poly": {"allowIntersection": False}},
        )
        draw_tool.add_to(folium_map)
        return folium_map

    def parse_drawn_geojson(
        self, geojson_feature: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parses raw GeoJSON feature drawn by user and extracts key GIS spatial metrics."""
        geometry = geojson_feature.get("geometry", {})
        geom_type = geometry.get("type", "")
        coords = geometry.get("coordinates", [])

        if geom_type not in ["Polygon", "MultiPolygon"] or not coords:
            raise ValueError(
                f"Unsupported or Empty Geometry Type: {geom_type}"
            )

        # Extract all coordinates pairs to calculate Bounding Box
        all_lons = []
        all_lats = []

        if geom_type == "Polygon":
            ring = coords[0]
            for lon, lat in ring:
                all_lons.append(lon)
                all_lats.append(lat)

        elif geom_type == "MultiPolygon":
            for poly in coords:
                for ring in poly:
                    for lon, lat in ring:
                        all_lons.append(lon)
                        all_lats.append(lat)

        min_lon, max_lon = min(all_lons), max(all_lons)
        min_lat, max_lat = min(all_lats), max(all_lats)

        bbox = [min_lon, min_lat, max_lon, max_lat]
        center_coords = [(min_lat + max_lat) / 2.0, (min_lon + max_lon) / 2.0]

        # Approximate Area Calculation In Hectares & Sq meters (Equirectangular Approximation)
        lat_dist = (max_lat - min_lat) * 111000.0    # Meters per degree lat
        lon_dist = (
            (max_lon - min_lon) * 111000.0 * 0.939
        )  # Cos (20 deg lat) approx 0.939

        area_sqm = abs(lat_dist * lon_dist)
        area_hectares = area_sqm / 10000.0

        return {
            "geometry_type": geom_type,
            "bbox": bbox,
            "center": center_coords,
            "approx_area_sqm": round(area_sqm, 2),
            "approx_area_hectares": round(area_hectares, 2),
            "vertices_count": len(all_lons),
            "raw_geojson": geojson_feature,
        }


# Quick Verification Test
if __name__ == "__main__":
    print("[*] Testing Day 19 AOI Polygon Drawing Engine...")
    selector = AOIPolygonSelector()

    # 1. Initialize  Base Map
    print("\n1. Initializing Folium Map with Leaflet Draw Plugin...")
    base_map = folium.Map(location = [20.2961, 85.8245], zoom_start = 13)
    selector.add_drawing_control(base_map)

    # Save Verification HTML File
    output_html ="test_aoi_draw_day19.html"
    base_map.save(output_html)
    print(f"   Saved Interactive Drawing Map to: {output_html}")

    # 2. Simulate User-Drawn Polygon Feature Parsing
    print("\n2. Parsing Simulated User-Drawn Field Boundary GeoJSON...")
    simulated_drawn_polygon = {
        "type": "Feature",
        "properties": {"name": "User Field Sector Alpha"},
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [85.810, 20.290],
                    [85.830, 20.290],
                    [85.830, 20.310],
                    [85.810, 20.310],
                    [85.810, 20.290],
                ]
            ],
        },
    }

    parsed_metrics = selector.parse_drawn_geojson(simulated_drawn_polygon)
    print(f"   Geometry Type: {parsed_metrics['geometry_type']}")
    print(
        f"   Bounding Box [min_lon, min_lat, max_lon, max_lat]: {parsed_metrics['bbox']}"
    )
    print(f"   Center Coordinates (Lat, Lon): {parsed_metrics['center']}")
    print(
        f"   Estimated Field Surface Area: {parsed_metrics['approx_area_hectares']} Hectares ({parsed_metrics['approx_area_sqm']} m^2)"
    )

    print("\n[OK] Day 19 AOI Polygon Drawing Engine Complete!")