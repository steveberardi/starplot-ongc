"""Creates SVG map plots of a few DSOs, using the built catalog (see `make plots`)."""

import math
from dataclasses import dataclass
from pathlib import Path

from starplot import callables, MapPlot, Miller, StereoSouth, StereoNorth, _
from starplot.data import Catalog
from starplot.styles import PlotStyle, extensions

from build import BUILD_PATH, __version__

CATALOG = Catalog(path=BUILD_PATH / f"ongc.{__version__}.parquet")
EXTENT = 8  # degrees around the DSO
GRID_STEP = 2  # degrees


@dataclass
class Target:
    filename: str
    name: str  # DSO name in the catalog
    projection: type
    ra: float
    dec: float
    also: tuple = ()  # names of additional DSOs to plot


TARGETS = [
    # also: M32 (NGC0221) and M110 (NGC0205)
    Target(
        "andromeda",
        "NGC0224",
        StereoNorth,
        10.6848,
        41.2691,
        also=("NGC0221", "NGC0205"),
    ),
    Target("triangulum", "NGC0598", StereoNorth, 23.4621, 30.6602),
    Target("orion-nebula", "NGC1976", Miller, 83.8187, -5.3897),
    Target("carina-nebula", "NGC3372", StereoSouth, 161.2855, -59.8667),
    Target("large-magellanic-cloud", "ESO056-115", StereoSouth, 80.8938, -69.7561),
]


def plot(t: Target):
    # RA degrees shrink with declination, so widen the RA extent to cover
    # EXTENT degrees on the sky
    ra_extent = min(EXTENT / math.cos(math.radians(t.dec)), 180)
    dec_min = max(t.dec - EXTENT, -90)
    dec_max = min(t.dec + EXTENT, 90)
    ra_min = t.ra - ra_extent
    ra_max = t.ra + ra_extent

    p = MapPlot(
        projection=t.projection(center_ra=t.ra, center_dec=t.dec),
        ra_min=ra_min,
        ra_max=ra_max,
        dec_min=dec_min,
        dec_max=dec_max,
        style=PlotStyle().extend(
            extensions.BLUE_NIGHT,
            extensions.MAP,
            {"dso_galaxy": {"marker": {"fill": "transparent"}}},
        ),
        resolution=3200,
    )
    p.gridlines(
        ra_locations=list(range(0, 360 + GRID_STEP, GRID_STEP)),
        dec_locations=list(range(-85, 90, GRID_STEP)),
        ra_label_fn=callables.rounded_degrees_label,  # RA labels in degrees, to match the 5 degree step
    )
    p.constellations()
    p.stars(where=[_.magnitude < 9], where_labels=[_.magnitude < 4])
    p.dsos(
        where=[_.name.isin([t.name, *t.also])],
        where_true_size=True,
        catalog=CATALOG,
    )

    out = BUILD_PATH / f"{t.filename}.svg"
    p.export(str(out))
    print(f"Exported {out}")


if __name__ == "__main__":
    for target in TARGETS:
        plot(target)
