"""
THE MRIDANSH : Interactive 2D/3D GIS Map Rendering Engine (Day 18)
Integrates Folium with Permanent Google Maps Hybrid Tiles,
AOI polygon boundaries, Measure Controls, Geocoder, and Draw Toolbar.
"""

from typing import Any, Dict, Optional, Tuple

import folium
from folium import plugins
from streamlit_folium import st_folium


class GISMapRenderer:
    """Interactive GIS Map Rendering Engine with Permanent Google Maps Hybrid Imagery."""

    def __init__(
        self,
        default_center: Tuple[float, float] = (20.5000, 86.4200),
        default_zoom: int = 12,
    ):
        self.default_center = default_center
        self.default_zoom = default_zoom

    def create_folium_2d_map(
        self,
        center: Optional[Tuple[float, float]] = None,
        zoom: Optional[int] = None,
    ) -> folium.Map:
        """Generates an interactive 2D Folium Map with permanent Google Maps Hybrid base."""
        map_center = center or self.default_center
        map_zoom = zoom or self.default_zoom

        # Permanent Base map Initialization: Google Maps Hybrid (Satellite + Roads/Villages)
        m = folium.Map(
            location=map_center,
            zoom_start=map_zoom,
            control_scale=True,
            tiles="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
            attr="Google Maps Hybrid &copy; 2026",
            name="Google Maps Hybrid",
        )

        # Optional Alternate Layer: Google Maps Pure Satellite
        folium.TileLayer(
            tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
            attr="Google Maps &copy; 2026",
            name="Google Maps Satellite (Pure)",
            overlay=False,
            control=True,
        ).add_to(m)

        # Add Instant Geocoder Search Box
        plugins.Geocoder(
            collapsed=False,
            position="topleft",
            add_marker=True,
            zoom=13,
        ).add_to(m)

        # Add Fullscreen Plugin Control
        plugins.Fullscreen(
            position="topright",
            title="Expand Map",
            title_cancel="Exit FullScreen",
            force_separate_button=True,
        ).add_to(m)

        # Add Measure Control Tool for GIS distance/area measurement
        plugins.MeasureControl(
            position="bottomleft",
            primary_length_unit="meters",
            primary_area_unit="sqmeters",
        ).add_to(m)

        # Add Folium Draw Toolbar (Polygon & Rectangle for Farm Boundary Delineation)
        plugins.Draw(
            export=False,
            position="topleft",
            filename="mridansh_farm_boundary.geojson",
            draw_options={
                "polyline": False,
                "polygon": {
                    "allowIntersection": False,
                    "showArea": True,
                    "shapeOptions": {
                        "color": "#00e5ff",
                        "weight": 3,
                        "fillColor": "#00e5ff",
                        "fillOpacity": 0.25,
                    },
                },
                "circle": False,
                "rectangle": {
                    "shapeOptions": {
                        "color": "#00e5ff",
                        "weight": 3,
                        "fillColor": "#00e5ff",
                        "fillOpacity": 0.25,
                    },
                },
                "circlemarker": False,
                "marker": False,
            },
            edit_options={"edit": True, "remove": True},
        ).add_to(m)

        return m

    def add_geojson_aoi_overlay(
        self,
        folium_map: folium.Map,
        geojson_data: dict[str, Any],
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
            geojson_data, name=layer_name, style_function=style_function, interactive=False
        )

        geojson_layer.add_to(folium_map)
        return folium_map


def render_heatmap_folium_map(
    lat: float = 20.5000,
    lon: float = 86.4200,
    zoom: int = 12,
    geojson_data: Optional[Dict[str, Any]] = None,
    domain_mode: str = "agronomy",
    is_demo: bool = False,
    aoi_bbox: Optional[list] = None,
    user_polygon: Optional[list] = None,
):
    """Bridge Helper with Permanent Google Maps Hybrid & Drawing Support."""
    renderer = GISMapRenderer(default_center=(lat, lon), default_zoom=zoom)
    f_map = renderer.create_folium_2d_map()

    # Add active coordinate marker with technical styling
    folium.CircleMarker(
        location=[lat, lon],
        radius=7,
        color="#00f0ff",
        weight=2,
        fill=True,
        fill_color="#00f0ff",
        fill_opacity=0.8,
        popup=f"Target: {lat:.4f}°N, {lon:.4f}°E",
        tooltip="Active Target Inspection Coordinate",
    ).add_to(f_map)

    # Optional AOI bounding box overlay
    if aoi_bbox and len(aoi_bbox) == 4:
        min_lon, min_lat, max_lon, max_lat = aoi_bbox
        aoi_geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"name": "Active AOI Extent Bounding Box"},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [min_lon, min_lat],
                                [max_lon, min_lat],
                                [max_lon, max_lat],
                                [min_lon, max_lat],
                                [min_lon, min_lat],
                            ]
                        ],
                    },
                }
            ],
        }
        renderer.add_geojson_aoi_overlay(
            f_map,
            aoi_geojson,
            layer_name="AOI Extent Bounding Box",
            stroke_color="#00f0ff",
            fill_color="#00f0ff",
            fill_opacity=0.03,
        )

    # Overlay user-drawn polygon if actively selected
    if user_polygon and len(user_polygon) >= 3:
        poly_latlon = [[pt[1], pt[0]] for pt in user_polygon]
        folium.Polygon(
            locations=poly_latlon,
            color="#00ff88",
            weight=3,
            fill=True,
            fill_color="#00e5ff",
            fill_opacity=0.28,
            popup="Active Custom Farm Boundary",
            tooltip="Active Farm Polygon",
        ).add_to(f_map)

    folium.LayerControl(collapsed=True).add_to(f_map)

    # Stable st_folium call: fixed key & no restrictive returned_objects filter
    return st_folium(
        f_map,
        width="100%",
        height=540,
        key="mridansh_permanent_google_hybrid_canvas",
    )
