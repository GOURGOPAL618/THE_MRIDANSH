"""
THE MRIDANSH : Interactive 2D/3D GIS Map Rendering Engine (Day 18)
Integrates Folium and Mapbox GL JS configurations for dynamic spatial raster overlays,
AOI polygon boundaries, and soil moisture surface maps.
"""

from typing import Any, Dict, List, Optional, Tuple
import folium
from folium import plugins

class GISMapRenderer:
    """Interactive GIS Map Rendering Engine for 2D/3D spatial visualizations."""

    def __init__(
        self,
        default_center: Tuple[float, float] = (20.2961, 85.8245),
        default_zoom: int = 12,
    ):
        """Initializes Renderer with default center coordinates (Latitude, Longitude) and zoom level.

        Default center: Bhubaneswar Corridor [20.2961 N, 85.8245 E]
        """

        self.default_center = default_center
        self.default_zoom = default_zoom

    def create_folium_2d_map(
        self,
        center: Optional[Tuple[float, float]] = None,
        zoom: Optional[int] = None,
    ) -> folium.Map:
        """Generates an interactive 2D Folium Map with multiple base tiles and layer controls."""
        map_center = center or self.default_center
        map_zoom = zoom or self.default_zoom

        # Base map Initialization
        m = folium.Map(
            location = map_center,
            zoom_start = map_zoom,
            control_scale = True,
            tiles = None,       # We manually add base layers below
        )

        # 1. Base layer; Open streetMap Standard
        folium.TileLayer(
            tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            attr = "&copy; OpenStreetMap contributors",
            name = "OpenStreetMap",
            overlay = False,
            control = True,
        ).add_to(m)

        # 2. Base Layer: Esri World Imagery (Satellite)
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community",
            name = "Esri Satellite Imagery",
            overlay = False,
            control = True,
        ).add_to(m)

        # Base Layer: CartoDB Dark Matter
        folium.TileLayer(
            tiles = "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
            attr="&copy; OpenStreetMap contributors &copy; CARTO",
            name = "CartoDB Dark Theme",
            overlay = False,
            control = True,
        ).add_to(m)

        # Add Fullscreen Plugin Control
        plugins.Fullscreen(
            position = "topright",
            title = "Expand Map",
            title_cancel = "Exit FullScreen",
            force_separate_button = True,
        ).add_to(m)
        
        # Add Measure Control Tool for GIS distance/area measurement
        plugins.MeasureControl(
            position = "topleft",
            primary_length_unit = "meters",
            primary_area_unit = "sqmeters",
        ).add_to(m)

        return m

    def add_geojson_aoi_overlay(
        self,
        folium_map: folium.Map,
        geojson_data: Dict[str, Any],
        layer_name: str = "Area Of Interest (AOI)",
        stroke_color: str = "#3388ff",
        fill_color: str = "#3388ff",
        fill_opacity: float = 0.2,
    ) -> folium.Map:
        """Overlays a GeoJSON Polygon boundary layer on the Folium map."""

        style_function = lambda feature: {
            "fillColor": fill_color,
            "color": stroke_color,
            "weight": 2.5,
            "fillOpacity": fill_opacity,
        }

        geojson_layer = folium.GeoJson(
            geojson_data, name = layer_name, style_function = style_function
        )

        geojson_layer.add_to(folium_map)

        return folium_map

    def generate_mapbox_3d_config(
        self,
        bbox: List[float],
        pitch: float = 60.0,
        bearing: float = -17.6,
        mapbox_token: str = "PK_PUBLIC_MOCK_TOKEN",
    ) -> Dict[str, Any]:
        """Generates configuration payload for Mapbox GL JS 3D Terrain & Satellite Vector rendering.

        Parameters:
            bbox: [min_lon, min_lat, max_lon, max_lat]
            pitch: Camera tilt angle in degrees (0-85)
            bearing: Camera orientation angle
        """

        center_lon = (bbox[0] + bbox[2]) / 2.0
        center_lat = (bbox[1] + bbox[3]) / 2.0

        return {
            "mapbox_token": mapbox_token,
            "style": "mapbox://styles/mapbox/satellite-streets-v12",
            "camera": {
                "center": [center_lon, center_lat],
                "zoom": 13.5,
                "pitch": pitch,
                "bearing": bearing,
            },

            "terrain": {"source": "mapbox-dem", "exaggeration": 1.5},
            "sources": {
                "mapbox-dem": {
                    "type": "raster-dem",
                    "url": "mapbox://mapbox.mapbox-terrain-dem-v1",
                    "tileSize": 512,
                    "maxzoom": 14,
                }
            },
        }


# Quick Verification Test
if __name__ == "__main__":
    print("🗺️ Testing Day 18 GIS Map Renderer Engine...")
    renderer = GISMapRenderer()

    # 1. Test Folium 2D Map Generation
    print("\n1. Initializing Folium 2D Interactive Map with Base Tiles...")
    f_map = renderer.create_folium_2d_map()

    # Sample AOI Polygon (Bhubaneswar Field Boundary GeoJSON)
    sample_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [85.75, 20.20],
                            [85.90, 20.20],
                            [85.90, 20.35],
                            [85.75, 20.35],
                            [85.75, 20.20],
                        ]
                    ],
                },
                "properties": {"name": "Bhubaneswar Spatial Corridor AOI"}
            }
        ],
    }

    print("\n2. Overlaying GeoJSON AOI Boundary Layer...")
    renderer.add_geojson_aoi_overlay(
        folium_map = f_map,
        geojson_data = sample_geojson,
        layer_name = "Bhubaneswar Target Zone",
    )

    # Add Layer Control to Map
    folium.LayerControl(collapsed = False).add_to(f_map)

    # Save verification HTML file
    output_html = "test_map_day18.html"
    f_map.save(output_html)
    print(f"   Saved Interactive Map HTML to: {output_html}")

    # 2. Test Mapbox 3D Config Generation
    print("\n3. Generating Mapbox GL JS 3D Terrain Config...")
    bhubaneswar_bbox = [85.75, 20.20, 85.90, 20.35]
    mapbox_cfg = renderer.generate_mapbox_3d_config(bbox=bhubaneswar_bbox)
    print(f"   3D Camera Center: {mapbox_cfg['camera']['center']}")
    print(f"   3D Camera Pitch: {mapbox_cfg['camera']['pitch']} deg")
    print(f"   Terrain Exaggeration: {mapbox_cfg['terrain']['exaggeration']}x")

    print("\n✅ Day 18 GIS Map Renderer Engine Complete!")

