import numpy as np
from shapely.geometry import Polygon
import geopandas as gpd
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.colors import TwoSlopeNorm
from matplotlib.colors import Normalize

def add_transaction_columns_to_gdf(gdf, london_df, postcode_column='postcode'):
    """
    Adds yearly transaction count columns and a % change column (transactions_delta) to gdf.

    Parameters:
        gdf (GeoDataFrame): GeoDataFrame with postcode geometries.
        london_df (DataFrame): DataFrame with 'postcode', 'year', and transaction records.
        postcode_column (str): Common postcode column in both gdf and london_df.

    Returns:
        GeoDataFrame: gdf with transaction columns and a 'transactions_delta' column.
    """
    gdf = gdf.copy()
    years = sorted(london_df['year'].unique())

    for year in years:
        col_name = f"transactions_{year}"
        counts = (
            london_df[london_df['year'] == year]
            .groupby(postcode_column)
            .size()
            .reset_index(name=col_name)
        )
        gdf = gdf.merge(counts, on=postcode_column, how='left')

    # Fill NaNs and convert to int
    trans_cols = [f"transactions_{y}" for y in years]
    gdf[trans_cols] = gdf[trans_cols].fillna(0).astype(int)

    # Compute percentage change from 2018 to 2024
    if 'transactions_2018' in gdf.columns and 'transactions_2024' in gdf.columns:
        gdf["transactions_delta"] = np.where(
            gdf["transactions_2018"] > 0,
            100 * (gdf["transactions_2024"] - gdf["transactions_2018"]) / gdf["transactions_2018"],
            np.nan  # or 0 if preferred
        )
    else:
        gdf["transactions_delta"] = np.nan

    return gdf


def generate_hexgrid(gdf, hex_size=1000):
    """
    Generate a pointy-topped hexagonal grid covering the bounding box of a GeoDataFrame.

    Parameters:
        gdf (GeoDataFrame): Input GeoDataFrame to define the area.
        hex_size (float): Radius of hexagon from center to vertex, in CRS units (e.g., meters).

    Returns:
        GeoDataFrame: A GeoDataFrame containing the hexagon grid.
    """
    # Bounding box
    minx, miny, maxx, maxy = gdf.total_bounds

    # Horizontal and vertical spacing
    dx = 3/2 * hex_size
    dy = np.sqrt(3) * hex_size

    # Estimate grid size
    cols = int((maxx - minx) / dx) + 2
    rows = int((maxy - miny) / dy) + 2

    # Function to create hexagon at (x, y)
    def create_hexagon(x, y, size):
        angles = np.linspace(0, 2 * np.pi, 7)[:-1]
        return Polygon([
            (x + size * np.cos(a), y + size * np.sin(a)) for a in angles
        ])

    # Generate hexes
    hexes = []
    for col in range(cols):
        for row in range(rows):
            x = minx + col * dx
            y = miny + row * dy
            if col % 2 == 1:  # Stagger odd columns
                y += dy / 2
            hexes.append(create_hexagon(x, y, hex_size))

    # Return as GeoDataFrame
    return gpd.GeoDataFrame(geometry=hexes, crs=gdf.crs)



def plot_transaction_heatmap(
    gdf,
    hexgrid,
    boroughs_path,
    year,
    hex_size=1000,
    cmap='coolwarm',
    title=None,
    mode='total'  # 'total' or 'delta'
):
    """
    Plot a hexbin heatmap of total transactions or % change from 2018 to 2024.

    Parameters:
        gdf (GeoDataFrame): Postcode-level data with transaction columns.
        hexgrid (GeoDataFrame): Precomputed hex grid.
        boroughs_path (str): Path to London borough shapefile.
        year (int): Year for 'total' mode; ignored in 'delta' mode.
        hex_size (float): Used in plot title.
        cmap (str): Colormap (will be overridden in delta mode).
        title (str): Optional custom title.
        mode (str): 'total' for transactions_{year}, or 'delta' for percent change.
    """
    if mode == 'delta':
        value_col = 'transactions_delta'
        gdf_filtered = gdf[~gdf[value_col].isna()]
    else:
        value_col = f"transactions_{year}"
        gdf_filtered = gdf[gdf[value_col] > 0]

    # Spatial join
    joined = gpd.sjoin(gdf_filtered, hexgrid, how="left", predicate="within")
    agg = joined.groupby("index_right")[value_col].mean()

    # Map to hexgrid
    hexgrid = hexgrid.copy()
    hexgrid["transactions_sum"] = agg
    hexgrid["transactions_sum"] = hexgrid["transactions_sum"].fillna(0)

    # Load boroughs and clip
    boroughs = gpd.read_file(boroughs_path).to_crs(hexgrid.crs)
    hexgrid_clipped = gpd.clip(hexgrid, boroughs)

    hex_zero = hexgrid_clipped[hexgrid_clipped["transactions_sum"] == 0]
    hex_nonzero = hexgrid_clipped[hexgrid_clipped["transactions_sum"] != 0]

    # Set up plot
    fig, ax = plt.subplots(figsize=(10, 10))
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="3%", pad=0.1)

    # Plot zero hexes
    hex_zero.plot(
        ax=ax,
        facecolor="none",
        edgecolor="lightgrey",
        linewidth=0.2
    )

    # Define diverging colormap for delta mode
    if mode == 'delta':
        cmap = 'RdBu_r'
        vmin = hex_nonzero["transactions_sum"].min()
        vmax = hex_nonzero["transactions_sum"].max()
        abs_max = max(abs(vmin), abs(vmax))
        norm = TwoSlopeNorm(vmin=-abs_max, vcenter=0, vmax=abs_max)
    else:
        norm = None  # No diverging normalization for totals

    # Plot non-zero hexes
    hex_nonzero.plot(
        ax=ax,
        column="transactions_sum",
        cmap=cmap,
        edgecolor="grey",
        linewidth=0.2,
        legend=True,
        cax=cax,
        norm=norm
    )

    boroughs.boundary.plot(ax=ax, color="black", linewidth=1)

    # Borough labels
    for idx, row in boroughs.iterrows():
        centroid = row.geometry.centroid
        ax.text(
            centroid.x,
            centroid.y,
            row["BOROUGH"],
            fontsize=8,
            ha="center",
            va="center"
        )

    # Title
    if title:
        final_title = title
    elif mode == 'delta':
        final_title = "Hexbin Heatmap of % Change in Transactions (2018–2024)"
    else:
        final_title = f"Hexbin Heatmap of Transactions ({year})"

    ax.set_title(final_title, fontsize=16)
    ax.set_aspect("equal")
    ax.axis("off")
    plt.tight_layout()
    plt.show()

    
def facet_transaction_heatmaps_by_year(
    gdf,
    hexgrid,
    boroughs_path,
    years=range(2018, 2026),
    hex_size=1000,
    cmap='coolwarm',
    cols=4,
    figsize_per_plot=(5, 5)
):
    """
    Plot total transaction hexbin heatmaps for each year as facets in a single figure.

    Parameters:
        gdf (GeoDataFrame): Must include 'transactions_{year}' columns.
        hexgrid (GeoDataFrame): Pre-generated hex grid.
        boroughs_path (str): Path to the borough shapefile.
        years (iterable): List of years to plot.
        hex_size (int): Size of hex used for title only.
        cmap (str): Matplotlib colormap.
        cols (int): Number of columns in the facet layout.
        figsize_per_plot (tuple): Size (width, height) per subplot.
    """
    rows = int(np.ceil(len(years) / cols))
    fig, axes = plt.subplots(rows, cols, figsize=(figsize_per_plot[0]*cols, figsize_per_plot[1]*rows))
    axes = axes.flatten()

    # Load boroughs
    boroughs = gpd.read_file(boroughs_path).to_crs(hexgrid.crs)

    # Normalize color scale across all years
    vmax = max(gdf[f"transactions_{y}"].max() for y in years)
    norm = Normalize(vmin=0, vmax=vmax)

    for i, year in enumerate(years):
        ax = axes[i]
        col_name = f"transactions_{year}"

        gdf_filtered = gdf[gdf[col_name] > 0]
        joined = gpd.sjoin(gdf_filtered, hexgrid, how="left", predicate="within")
        agg = joined.groupby("index_right")[col_name].sum()

        hexgrid_plot = hexgrid.copy()
        hexgrid_plot["transactions_sum"] = agg
        hexgrid_plot["transactions_sum"] = hexgrid_plot["transactions_sum"].fillna(0)

        hexgrid_clipped = gpd.clip(hexgrid_plot, boroughs)
        hex_zero = hexgrid_clipped[hexgrid_clipped["transactions_sum"] == 0]
        hex_nonzero = hexgrid_clipped[hexgrid_clipped["transactions_sum"] > 0]

        hex_zero.plot(ax=ax, facecolor="none", edgecolor="lightgrey", linewidth=0.2)
        hex_nonzero.plot(
            ax=ax,
            column="transactions_sum",
            cmap=cmap,
            edgecolor="grey",
            linewidth=0.2,
            norm=norm
        )

        boroughs.boundary.plot(ax=ax, color="black", linewidth=1)
        ax.set_title(f"Transactions {year}", fontsize=12)
        ax.set_aspect("equal")
        ax.axis("off")

    # Remove unused axes
    for j in range(i + 1, len(axes)):
        fig.delaxes(axes[j])

    # Shared colorbar
    fig.subplots_adjust(right=0.9)
    cbar_ax = fig.add_axes([0.92, 0.25, 0.015, 0.5])
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm._A = []
    fig.colorbar(sm, cax=cbar_ax, label="Transactions")

    # Title and layout
    plt.suptitle("Hexbin Facet Heatmaps of Transactions (2018–2025)", fontsize=16)
    plt.tight_layout(rect=[0, 0, 0.9, 0.95])
    plt.show()