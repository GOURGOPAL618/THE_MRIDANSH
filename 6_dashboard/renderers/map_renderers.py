"""
THE MRIDANSH : Interactive 2D/3D GIS Map Rendering Engine (Day 18)
Integrates Folium and Mapbox GL JS configurations for dynamic spatial raster overlays,
AOI polygon boundaries, and soil moisture surface maps.
"""

from typing import Any, Dict, Optional, Tuple

import folium
from folium import plugins
from streamlit_folium import st_folium


class GISMapRenderer:
    """Interactive GIS Map Rendering Engine for 2D/3D spatial visualizations."""

    def __init__(
        self,
        default_center: tuple[float, float] = (20.2961, 85.8245),
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
            location=map_center,
            zoom_start=map_zoom,
            control_scale=True,
            tiles=None,  # We manually add base layers below
        )

        # 1. Base layer; Open streetMap Standard
        folium.TileLayer(
            tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            attr="&copy; OpenStreetMap contributors",
            name="OpenStreetMap",
            overlay=False,
            control=True,
        ).add_to(m)

        # 2. Base Layer: Esri World Imagery (Satellite)
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community",
            name="Esri Satellite Imagery",
            overlay=False,
            control=True,
        ).add_to(m)

        # 1. Primary Base Layer: Esri Dark Canvas (Watermark Free & High Contrast)
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}",
            attr="Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ",
            name="Esri Dark Canvas",
            overlay=False,
            control=True,
        ).add_to(m)

        # 2. Secondary Base Layer: Esri World Imagery (Satellite View)
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community",
            name="Esri Satellite Imagery",
            overlay=False,
            control=True,
        ).add_to(m)

        # 3. Tertiary Base Layer: OpenStreetMap Standard
        folium.TileLayer(
            tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            attr="&copy; OpenStreetMap contributors",
            name="OpenStreetMap",
            overlay=False,
            control=True,
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
            position="topleft",
            primary_length_unit="meters",
            primary_area_unit="sqmeters",
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
            geojson_data, name=layer_name, style_function=style_function
        )

        geojson_layer.add_to(folium_map)

        return folium_map


    def add_soil_moisture_heatmap_overlay(
        self,
        folium_map: folium.Map,
        geojson_data: Dict[str, Any],
        domain_mode: str = "agronomy",
        layer_name: str = "Soil Moisture Heatmap",
        is_demo: bool = False,
    ) -> folium.Map:
        """Domain-Aware Choropleth Styling Logic (Hardened against synthetic modulo data)."""

        import numpy as np

        def get_moisture_color(moisture: float, mode: str) -> str:
            if mode == "agronomy":
                # Agronomy Focus: Moisture range thresholds
                if moisture < 0.16:
                    return "#FF3333"  # Dry / Stress (Red)
                elif moisture < 0.22:
                    return "#FF9900"  # Low (Orange)
                elif moisture < 0.28:
                    return "#FFFF00"  # Medium (Yellow)
                elif moisture < 0.34:
                    return "#00FF66"  # Optimal (Green)
                else:
                    return "#0099FF"  # Saturated (Blue)
            else:
                # Civil Focus: Subgrade Stability range thresholds
                if moisture < 0.15:
                    return "#00FF66"  # High Bearing Capacity (Green)
                elif moisture < 0.25:
                    return "#FFFF00"  # Stable Moisture Range (Yellow)
                elif moisture < 0.32:
                    return "#FF9900"  # Moderate Shear Loss Risk (Orange)
                else:
                    return "#FF0055"  # High Saturation (Critical Red)

        if not geojson_data or not isinstance(geojson_data, dict):
            return folium_map

        # Check if geojson features actually have physical moisture measurements
        features = geojson_data.get("features", [])
        if not features:
            status_msg = geojson_data.get("properties", {}).get("message", "No spatial features available.")
            display_name = f"Spatial Layer (Unavailable: {status_msg})"
            geojson_layer = folium.GeoJson(
                geojson_data,
                name=display_name,
            )
            geojson_layer.add_to(folium_map)
            return folium_map

        has_real_moisture = any(
            f.get("properties", {}).get("moisture_m3m3") is not None
            for f in features if isinstance(f, dict)
        )

        def style_function(feature: Dict[str, Any]) -> Dict[str, Any]:
            props = feature.get("properties", {})
            raw_moisture = props.get("moisture_m3m3")

            if raw_moisture is None:
                # Neutral technical cyan styling for geometry-only grids
                return {
                    "fillColor": "#00f0ff",
                    "color": "#00b4d8",
                    "weight": 1.5,
                    "fillOpacity": 0.04,
                }

            try:
                m_val = float(raw_moisture)
                if np.isnan(m_val) or not np.isfinite(m_val):
                    return {
                        "fillColor": "transparent",
                        "color": "#64748b",
                        "weight": 1.0,
                        "fillOpacity": 0.0,
                    }
                return {
                    "fillColor": get_moisture_color(m_val, domain_mode),
                    "color": "#ffffff",
                    "weight": 1.5,
                    "fillOpacity": 0.55,
                }
            except (ValueError, TypeError):
                return {
                    "fillColor": "#00f0ff",
                    "color": "#00b4d8",
                    "weight": 1.5,
                    "fillOpacity": 0.04,
                }

        # Dynamic Tooltip reflecting geometry or observation status
        tooltip_fields = ["tile_id", "row", "col"]
        tooltip_aliases = ["Tile ID:", "Grid Row:", "Grid Col:"]

        if has_real_moisture:
            tooltip_fields.append("moisture_m3m3")
            tooltip_aliases.append("Moisture (m³/m³):")

        tooltip = folium.GeoJsonTooltip(
            fields=tooltip_fields,
            aliases=tooltip_aliases,
            style="background-color: #0b0e14; color: #00f0ff; font-family: monospace; font-size: 11px; padding: 6px; border: 1px solid #1e2638;",
            sticky=True,
        )

        display_name = (
            f"{layer_name} ({domain_mode.upper()})"
            if has_real_moisture
            else f"Computational Grid Mesh ({domain_mode.upper()} Geometry Only)"
        )
        if is_demo:
            display_name += " [DEMO DATA]"

        geojson_layer = folium.GeoJson(
            geojson_data,
            name=display_name,
            style_function=style_function,
            tooltip=tooltip,
        )

        geojson_layer.add_to(folium_map)
        return folium_map


def render_heatmap_folium_map(
    lat: float = 20.2961,
    lon: float = 85.8245,
    zoom: int = 11,
    geojson_data: Optional[Dict[str, Any]] = None,
    domain_mode: str = "agronomy",
    is_demo: bool = False,
    aoi_bbox: Optional[list] = None,
):
    """Bridge Helper With Multi-Domain Viewport Support (Industry-Grade Workstation Canvas)"""
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

    if geojson_data:
        renderer.add_soil_moisture_heatmap_overlay(
            folium_map=f_map,
            domain_mode=domain_mode,
            geojson_data=geojson_data,
            layer_name="Domain Soil Intelligence",
            is_demo=is_demo,
        )

    folium.LayerControl(collapsed=False).add_to(f_map)

    # Return st_folium click data
    return st_folium(
        f_map,
        width="100%",
        height=520,
        key=f"mridansh_map_{domain_mode}",
        returned_objects=["last_clicked"],
    )

