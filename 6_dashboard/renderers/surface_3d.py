"""
THE MRIDANSH : 3D Soil Surface & Topography Rendering Engine (Day 21)
Generates 3D terrain mesh visualizations with Plotly, mapping soil state parameters
over Digital Elevation Models (DEM) and depth-resolved spatial grids.
"""

import numpy as np
import plotly.graph_objects as go


class Surface3DRenderer:
    """Renders 3D Terrain elevation meshes and soil volumetric Using Plotly."""

    def __init__(self, default_colorscale: str = "YlGnBu"):
        """Initializes 3D Surface Renderer with Default Colormap Scale."""

        self.default_colorscale = default_colorscale

    def create_terrain_soil_surface(
        self,
        elevation_matrix: np.ndarray,
        soil_parameter_matrix: np.ndarray,
        grid_resolution_m: float = 10.0,
        elevation_exaggeration: float = 1.5,
        title: str = "AETHER 3D Soil Moisture & Terrain Elevation Mesh",
        colorscale: str | None = None,
    ) -> go.Figure:
        """Generates a 3D Surface Plot layering soil predictions over DEM elevation contours.

        Parameters:
            elevation_matrix: 2D numpy array [H, W] representing DEM terrain heights (meters).
            soil_parameter_matrix: 2D numpy array [H, W] representing predicted soil values.
            grid_resolution_m: Spatial resolution per grid cell in meters (default 10m).
            elevation_exaggeration: Z-axis scale factor for terrain relief visualization.
        """

        if elevation_matrix.shape != soil_parameter_matrix.shape:
            raise ValueError(
                f"Shape mismatch: Elevation {elevation_matrix.shape} vs Soil Matrix {soil_parameter_matrix.shape}"
            )

        height, width = elevation_matrix.shape
        x_coords = np.arange(0, width) * grid_resolution_m
        y_coords = np.arange(0, height) * grid_resolution_m
        X, Y = np.meshgrid(x_coords, y_coords)

        # Scale Z Height For Visual Relief
        Z_scaled = elevation_matrix * elevation_exaggeration
        active_colorscale = colorscale or self.default_colorscale

        # Create Plotly 3D Surface
        fig = go.Figure(
            data=[
                go.Surface(
                    x=X,
                    y=Y,
                    z=Z_scaled,
                    surfacecolor=soil_parameter_matrix,
                    colorscale=active_colorscale,
                    colorbar=dict(
                        title=dict(
                            text="Soil State Value",
                            side="right",
                        ),
                        thickness=15,
                        len=0.75,
                    ),
                    contours=dict(
                        z=dict(
                            show=True,
                            usecolormap=True,
                            highlightcolor="limegreen",
                            project=dict(z=True),
                        )
                    ),
                    hovertemplate=(
                        "X: %{x:.1f} m<br>"
                        + "Y: %{y:.1f} m<br>"
                        + "Elevation: %{customdata:.2f} m<br>"
                        + "Soil Parameter: %{surfacecolor:.3f}<extra></extra>"
                    ),
                    customdata=elevation_matrix,
                )
            ]
        )

        # Apply 3D Camera & Scene Layout
        fig.update_layout(
            title=dict(text=title, x=0.5, y=0.92, xanchor="center"),
            autosize=True,
            margin=dict(l=20, r=20, b=20, t=50),
            scene=dict(
                xaxis=dict(title="X Spatial (m)", backgroundcolor="rgb(240, 242, 245)"),
                yaxis=dict(title="Y Spatial (m)", backgroundcolor="rgb(240, 242, 245)"),
                zaxis=dict(title="Elevation (m)", backgroundcolor="rgb(225, 230, 238)"),
                camera=dict(
                    eye=dict(x=1.5, y=-1.5, z=1.2), center=dict(x=1, y=0, z=-0.2)
                ),
                aspectratio=dict(x=1, y=1, z=0.4),
            ),
        )

        return fig


# Quick Verification Test
if __name__ == "__main__":
    print("[TEST] Testing Day 21 3D Soil Surface & Topography Engine...")
    renderer = Surface3DRenderer()

    # 1. Generate Synthetic Topography & soil Prediction (40 * 40 Grid)
    print("\n1. Generating Synthetic DEM Elevation & Soil Matrices (40x40)...")
    np.random.seed(42)
    grid_size = (40, 40)

    # Simulated DEM: Rolling hills elevation pattern (meters)
    x = np.linspace(-3, 3, grid_size[1])
    y = np.linspace(-3, 3, grid_size[0])
    X_grid, Y_grid = np.meshgrid(x, y)
    simulated_dem = (
        50.0
        + 15.0 * np.sin(X_grid) * np.cos(Y_grid)
        + 5.0 * np.exp(-(X_grid**2 + Y_grid**2))
    )

    # Simulated Soil Moisture (higher in lower elevation valleys)
    simulated_soil_state = 0.40 - 0.005 * (simulated_dem - 35.0)
    simulated_soil_state = np.clip(simulated_soil_state, 0.08, 0.48)

    # 2. Render 3D Surface
    print("\n2. Building Plotly 3D Surface Mesh Figure...")
    fig_3d = renderer.create_terrain_soil_surface(
        elevation_matrix=simulated_dem,
        soil_parameter_matrix=simulated_soil_state,
        grid_resolution_m=12.5,
        elevation_exaggeration=1.2,
        title="Bhubaneswar Sector - 3D Soil Moisture Over DEM",
    )

    # Save Verification HTML
    output_html = "test_surface_3d_day21.html"
    fig_3d.write_html(output_html)
    print(f"\n   Saved Interactive 3D Surface Mesh to: {output_html}")

    print("\n[DONE] Day 21 3D Soil Surface & Topography Engine Complete!")
