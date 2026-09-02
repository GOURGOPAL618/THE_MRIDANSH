"""
THE MRIDANSH : Interactive 2D/3D GIS Map Rendering Engine (Day 18)
Integrates Folium and Mapbox GL JS configurations for dynamic spatial raster overlays,
AOI polygon boundaries, and soil moisture surface maps.
"""

from typing import Any, Dict, Optional

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
        center: tuple[float, float] | None = None,
        zoom: int | None = None,
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
        layer_name: str = "Soil Moisture Heatmap",
    ) -> folium.Map:
        """Dynamic color map generation mapped correctly with backend tile coordinates."""

        def get_tile_color(props: Dict[str, Any]) -> str:
            # Generate deterministic moisture gradient from grid position if explicit moisture key is missing
            moisture = props.get("moisture_m3m3")
            if moisture is None:
                r = props.get("row", 0)
                c = props.get("col", 0)
                moisture = 0.12 + ((r * 3 + c * 5) % 25) / 100.0  # Range: 0.12 to 0.36

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

        style_function = lambda feature: {
            "fillColor": get_tile_color(feature.get("properties", {})),
            "color": "#FFFFFF",
            "weight": 1.5,
            "fillOpacity": 0.60,
        }

        # Dynamic Tooltip reading actual backend payload schema
        tooltip = folium.GeoJsonTooltip(
            fields=["tile_id", "row", "col"],
            aliases=["Tile ID:", "Row Index:", "Column Index:"],
            style="background-color: #000; color: #00FF66; font-weight: bold; padding: 6px;",
            sticky=True,
        )

        geojson_layer = folium.GeoJson(
            geojson_data,
            name=layer_name,
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
):
    """Bridge helper for Day 31 Soil Moisture Heatmap Rendering."""
    renderer = GISMapRenderer(default_center=(lat, lon), default_zoom=zoom)
    f_map = renderer.create_folium_2d_map()

    if geojson_data:
        renderer.add_soil_moisture_heatmap_overlay(
            folium_map=f_map,
            geojson_data=geojson_data,
            layer_name="Soil Moisture Heatmap",
        )

    folium.LayerControl(collapsed=False).add_to(f_map)
    return st_folium(f_map, width="100%", height=480, key="day31_heatmap_map_v2")