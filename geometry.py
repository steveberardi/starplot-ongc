import math

import numpy as np
import pyproj
from shapely.geometry import Polygon

from starplot.constants import PROJ_R

GEOD = pyproj.Geod(f"+a={PROJ_R} +f=0.0", sphere=True)

PRECISION = 4

def distance_m(distance_degrees: float, lat: float = 0, lon: float = 0):
    _, _, distance = GEOD.inv(lon, lat, lon + distance_degrees, lat)
    return distance


def away_from_poles(dec):
    # for some reason cartopy does not like plotting things EXACTLY at the poles
    # so, this is a little hack to avoid the bug (or maybe a misconception?) by
    # plotting a tiny bit away from the pole
    if dec == 90:
        dec -= 0.00000001
    if dec == -90:
        dec += 0.00000001

    return dec


def _unwrap_lons(lons: list) -> list:
    """
    Corrects for pyproj's Geod.fwd() always returning longitude normalized to
    (-180, 180]. For a shape whose points are generated in angular order
    (e.g. sweeping around its center), this seam is invisible except when the
    shape happens to sit near the antimeridian (raw longitude +/-180) --
    there, adjacent points that are actually close together on the sphere can
    come back on opposite sides of the seam (e.g. 179.5 and -179.5), which
    would otherwise register as a fake ~360-degree jump.

    Unwraps each point relative to the previous one so the sequence stays
    continuous, regardless of where in the 0-360 longitude range the shape sits.
    """
    lons = list(lons)
    for i in range(1, len(lons)):
        while lons[i] - lons[i - 1] > 180:
            lons[i] -= 360
        while lons[i] - lons[i - 1] < -180:
            lons[i] += 360
    return lons

def ellipse(
    center: tuple,
    height_degrees: float,
    width_degrees: float,
    angle: float = 0,
    num_pts: int = 100,
    start_angle: int = 0,
    end_angle: int = 360,
) -> Polygon:
    """
    Returns an ellipse polygon on a sphere, with coordinates in degrees.

    If the ellipse crosses the meridian at X=0, then the X coordinates will extend past 360.

    Args:
        center: Center of ellipse (x, y) in degrees
        height_degrees: Height of ellipse in degrees
        width_degrees: Width of ellipse in degrees
        angle: Angle to rotate ellipse, in degrees
        num_pts: Number of evenly-spaced points to generate for the ellipse. At least 100 is recommended to ensure good-looking curves.
        start_angle: Parametric angle to start drawing the ellipse, measured from the height axis
        end_angle: Parametric angle to stop drawing the ellipse

    Returns:
        Polygon of ellipse
    """

    ra, dec = center
    dec = away_from_poles(dec)
    angle = 180 - angle

    height = distance_m(height_degrees / 2)  # b
    width = distance_m(width_degrees / 2)  # a
    step_size = (end_angle - start_angle) / num_pts

    lons = []
    lats = []
    points = []
    for t in np.arange(start_angle, end_angle + step_size, step_size):
        radians = math.radians(t)
        along_height = height * math.cos(radians)
        along_width = width * math.sin(radians)

        # sample by the parametric angle (instead of the polar angle) to keep
        # points dense at the tips of a long ellipse, where the curve is sharpest
        radius = math.hypot(along_height, along_width)
        offset = math.degrees(math.atan2(along_width, along_height))
        lon, lat, _ = GEOD.fwd([ra], [dec], angle + offset, radius)

        lons.append(lon[0])
        lats.append(lat[0])

    lons = _unwrap_lons(lons)
    if min(lons) < 0:
        lons = [lon + 360 for lon in lons]

    points = list(zip(lons, lats))
    points = [
        (round(ra, PRECISION), round(dec, PRECISION))
        for ra, dec in points
    ]
    points.append(points[0])
    return Polygon(points)
