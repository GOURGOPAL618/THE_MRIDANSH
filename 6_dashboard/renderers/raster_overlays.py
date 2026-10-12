"""
THE MRIDANSH : Satellite Imagery & Spatial Heatmap Raster Overlay Engine (Day 20)
Generates georeferenced raster image overlays, continuous colormaps for soil state predictions,
and dynamic density heatmaps for point-source sensor observations on Folium maps.
"""

import folium
import numpy as np
from folium import plugins


class SpatialRasterOverlayEngine:
    """Renders georeferenced raster overlays, color legends, and spatial heatmaps on GIS maps."""

    def __init__(self):
        """Initializes Spatial Raster Overlay Engine."""

    def add_soil_moisture_raster_overlay(
        self,
        folium_map: folium.Map,
        matrix_data: np.ndarray,
        bbox: list[float],
        layer_name: str = "AETHER Soil Moisture Map (m³/m³)",
        opacity: float = 0.7,
        colormap_name: str = "YlGnBu_09",
    ) -> folium.Map:
        """Converts a 2D soil moisture prediction numpy array into a georeferenced PNG overlay

        and mounts it to the Folium map using the specified bounding box.

        Parameters:
            matrix_data: 2D numpy array [height, width] of soil values.
            bbox: Bounding box [min_lon, min_lat, max_lon, max_lat].
            colormap_name: Folium/branca colormap name (e.g., 'YlGnBu', 'viridis', 'Spectral').
        """

        # Check for empty or all-NaN matrix data safely
        if matrix_data is None or matrix_data.size == 0 or np.all(np.isnan(matrix_data)):
            # No valid raster pixels available; do not fabricate data
            return folium_map

        import branca.colormap as cm

        # Extract Spatial Extent: Folium ImageOverlay Expects [[min_lat, min_lon], [max_lat, max_lon]]
        min_lon, min_lat, max_lon, max_lat = bbox
        bounds = [[min_lat, min_lon], [max_lat, max_lon]]

        # Normalizes Matrix data for colormap mapping
        min_val = float(np.nanmin(matrix_data))
        max_val = float(np.nanmax(matrix_data))

        if min_val == max_val:
            # Prevent zero-range colormap error
            max_val = min_val + 1e-4

        # Create branca colormap for the map legend
        try:
            colormap_factory = getattr(cm.linear, colormap_name)
        except (AttributeError, TypeError):
            colormap_factory = cm.linear.YlGnBu_09

        colormap = colormap_factory.scale(min_val, max_val)
        colormap.caption = f"{layer_name} Scale"

        # Apply colormap to matrix producing RGBA float array
        H, W = matrix_data.shape
        rgba_image = np.zeros((H, W, 4), dtype=np.float32)
        for r in range(H):
            for c in range(W):
                val = matrix_data[r, c]
                if np.isnan(val) or np.isinf(val):
                    rgba_image[r, c] = (0.0, 0.0, 0.0, 0.0)
                else:
                    rf, gf, bf, _ = colormap.rgba_floats_tuple(float(val))
                    rgba_image[r, c] = (rf, gf, bf, opacity)

        # Mount Image Overlay to map
        folium.raster_layers.ImageOverlay(
            image=rgba_image,
            bounds=bounds,
            opacity=opacity,
            name=layer_name,
            interactive=True,
            cross_origin=False,
            zindex=1,
        ).add_to(folium_map)

        # Add Colormap Legend To Map
        colormap.add_to(folium_map)

        return folium_map

    def add_sensor_heatmap_layer(
        self,
        folium_map: folium.Map,
        point_data: list[tuple[float, float, float]],
        layer_name: str = "In-Situ Sensor Density Heatmap",
        radius: int = 15,
        blur: int = 10,
    ) -> folium.Map:
        """Adds a dynamic point density heatmap layer from sensor observations.

        Parameters:
            point_data: List of tuples [(lat, lon, intensity_weight), ...]
        """

        heatmap_group = folium.FeatureGroup(name=layer_name, overlay=True)

        plugins.HeatMap(
            data=point_data,
            radius=radius,
            blur=blur,
            min_opacity=0.3,
            gradient={0.2: "blue", 0.4: "lime", 0.6: "yellow", 1.0: "red"},
        ).add_to(heatmap_group)

        heatmap_group.add_to(folium_map)
        return folium_map


# Quick Verification Test
if __name__ == "__main__":
    print("🛰️ Testing Day 20 Spatial Raster Overlay Engine...")
    engine = SpatialRasterOverlayEngine()

    # 1. Initialize Base Map
    print("\n1. Initializing Folium Base Map...")
    target_center = [20.2961, 85.8245]
    f_map = folium.Map(location=target_center, zoom_start=12)

    # 2. Simulate Spatial Soil Moisture Matrix (50x50 spatial grid)
    print("\n2. Generating Synthetic Soil Moisture Prediction Array (50x50)...")
    np.random.seed(42)
    grid_size = (50, 50)

    # Volumetric soil moisture values between 0.10 and 0.45 m3/m3
    simulated_sm_matrix = np.random.uniform(0.10, 0.45, size=grid_size)

    # Bounding Box Around Bhubaneswar
    bhubaneswar_bbox = [85.75, 20.20, 85.90, 20.35]

    print("\n3. Mounting Georeferenced Soil Moisture Overlay & Color Legend...")
    engine.add_soil_moisture_raster_overlay(
        folium_map=f_map,
        matrix_data=simulated_sm_matrix,
        bbox=bhubaneswar_bbox,
        layer_name="Simulated Soil Moisture (m³/m³)",
        opacity=0.65,
        colormap_name="YlGnBu_09",
    )

    # 3. Simulate In-Situ Sensor Measurements (Lat, Lon, Soil Moisture Value)
    print("\n4. Adding In-Situ Sensor Heatmap Point Layer...")
    simulated_sensor_points = [
        (20.22, 85.78, 0.35),
        (20.25, 85.80, 0.42),
        (20.28, 85.83, 0.18),
        (20.31, 85.86, 0.22),
        (20.33, 85.88, 0.39),
    ]

    engine.add_sensor_heatmap_layer(
        folium_map=f_map,
        point_data=simulated_sensor_points,
        layer_name="Ground Sensor Moisture Density",
    )

    # Add Layer Control UI
    folium.LayerControl(collapsed=False).add_to(f_map)

    # Save Verification HTML
    output_html = "test_raster_overlay_day20.html"
    f_map.save(output_html)

    print(f"\n   Saved Interactive Raster Overlay Map to: {output_html}")

    print("\n✅ Day 20 Spatial Raster Overlay Engine Complete!")
