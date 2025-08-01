import numpy as np
from shapely.geometry import Polygon
import geopandas as gpd
import matplotlib.pyplot as plt

def add_transaction_columns_to_gdf(gdf, london_df, postcode_column='postcode'):
    """
    Adds transaction count columns by year to the GeoDataFrame based on transaction data.

    Parameters:
        gdf (GeoDataFrame): GeoDataFrame with postcode geometries.
        london_df (DataFrame): DataFrame with 'postcode', 'year', and transaction records.
        postcode_column (str): Column name representing postcode in both DataFrames.

    Returns:
        GeoDataFrame: Updated GeoDataFrame with 'transactions_{year}' columns added.
    """

    gdf = gdf.copy()  # Avoid modifying in place

    # Loop over unique years
    for year in sorted(london_df['year'].unique()):
        col_name = f"transactions_{year}"

        # Count transactions per postcode for the year
        transaction_counts = (
            london_df[london_df['year'] == year]
            .groupby(postcode_column)
            .size()
            .reset_index(name=col_name)
        )

        # Merge with gdf
        gdf = gdf.merge(transaction_counts, on=postcode_column, how='left')

    # Replace NaN with 0 for all newly added columns
    trans_cols = [f"transactions_{y}" for y in london_df['year'].unique()]
    gdf[trans_cols] = gdf[trans_cols].fillna(0).astype(int)

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
    title=None
):
    """
    Create a hexbin heatmap of postcode transaction counts for a given year.

    Parameters:
        gdf (GeoDataFrame): GeoDataFrame with postcode centroids and transaction data.
        hexgrid (GeoDataFrame): Pre-generated hexagonal grid.
        boroughs_path (str): Path to the London boroughs shapefile.
        year (int): Year to select the transaction column, e.g., 2018 selects 'transactions_2018'.
        hex_size (float): Size of hexagon from center to vertex (in meters). Used only for title.
        cmap (str): Matplotlib colormap for non-zero bins.
        title (str, optional): Custom plot title. If None, a default title will be used.
    """

    col_name = f"transactions_{year}"

    # Filter out 0 or missing transactions
    gdf_filtered = gdf[gdf[col_name] > 0]

    # Spatial join to hexgrid
    joined = gpd.sjoin(gdf_filtered, hexgrid, how="left", predicate="within")

    # Aggregate transactions by hexbin
    agg = joined.groupby("index_right")[col_name].sum()

    # Map totals to hexgrid
    hexgrid = hexgrid.copy()
    hexgrid["transactions_sum"] = agg
    hexgrid["transactions_sum"] = hexgrid["transactions_sum"].fillna(0)

    # Load and clip to boroughs
    boroughs = gpd.read_file(boroughs_path)
    boroughs = boroughs.to_crs(hexgrid.crs)
    hexgrid_clipped = gpd.clip(hexgrid, boroughs)

    # Split for hollow vs colored hexes
    hex_zero = hexgrid_clipped[hexgrid_clipped["transactions_sum"] == 0]
    hex_nonzero = hexgrid_clipped[hexgrid_clipped["transactions_sum"] > 0]

    # Plot
    fig, ax = plt.subplots(figsize=(12, 12))

    hex_zero.plot(
        ax=ax,
        facecolor="none",
        edgecolor="lightgrey",
        linewidth=0.2
    )

    hex_nonzero.plot(
        ax=ax,
        column="transactions_sum",
        cmap=cmap,
        edgecolor="grey",
        linewidth=0.2,
        legend=True
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

    # Title and layout
    final_title = title or f"Hexbin Heatmap of Transactions ({year})"
    ax.set_title(final_title, fontsize=16)
    plt.axis("off")
    plt.show()
