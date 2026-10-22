#!/usr/bin/env python3
"""Vector map (Mercator) from Natural Earth country polygons, for the scene card.

Writes an SVG fragment with one <path> per country polygon, ids like
"c-ESP", "c-ITA-sicily", and a JSON projection so pins/routes can be placed by lat/lon.

Usage: python3 scripts/nerd/mapgen.py <ne_50m_admin_0_countries.geojson> <out.svg> \
         --bounds lon0,lon1,lat0,lat1 --size 1080x680
"""
import argparse
import json
import math


def merc(lat):
    return math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


class Proj:
    def __init__(self, lon0, lon1, lat0, lat1, w, h):
        self.lon0, self.lon1, self.w, self.h = lon0, lon1, w, h
        self.ytop, self.ybot = merc(lat1), merc(lat0)
        sx = w / math.radians(lon1 - lon0)
        sy = h / (self.ytop - self.ybot)
        self.s = min(sx, sy)
        self.ox = (w - self.s * math.radians(lon1 - lon0)) / 2
        self.oy = (h - self.s * (self.ytop - self.ybot)) / 2

    def __call__(self, lon, lat):
        x = self.ox + self.s * math.radians(lon - self.lon0)
        y = self.oy + self.s * (self.ytop - merc(max(min(lat, 85), -85)))
        return x, y


NAMED_ISLANDS = {("ITA", 14.0, 37.5): "sicily", ("ITA", 9.0, 40.0): "sardinia", ("FRA", 9.1, 42.1): "corsica",
                 ("GBR", -6.5, 54.6): "nireland", ("GRC", 24.9, 35.2): "crete"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("geojson")
    ap.add_argument("out")
    ap.add_argument("--bounds", default="-14,40,31,55")
    ap.add_argument("--size", default="1080x680")
    a = ap.parse_args()
    lon0, lon1, lat0, lat1 = map(float, a.bounds.split(","))
    w, h = map(int, a.size.split("x"))
    P = Proj(lon0, lon1, lat0, lat1, w, h)
    data = json.load(open(a.geojson))
    paths = []
    for f in data["features"]:
        props = f["properties"]
        iso = props.get("ADM0_A3") or props.get("ISO_A3")
        geom = f["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        for poly in polys:
            ring = poly[0]
            lons = [p[0] for p in ring]
            lats = [p[1] for p in ring]
            if max(lons) < lon0 - 5 or min(lons) > lon1 + 5 or max(lats) < lat0 - 5 or min(lats) > lat1 + 5:
                continue
            clon, clat = sum(lons) / len(lons), sum(lats) / len(lats)
            pid = f"c-{iso}"
            for (k_iso, ilon, ilat), name in NAMED_ISLANDS.items():
                if k_iso == iso and abs(clon - ilon) < 1.5 and abs(clat - ilat) < 1.2:
                    pid = f"c-{iso}-{name}"
            d = []
            for r in poly:
                pts = [P(lon, lat) for lon, lat in r]
                d.append("M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z")
            paths.append(f'<path class="land" data-id="{pid}" d="{"".join(d)}"/>')
    svg = (f'<svg class="map-svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg">'
           + "".join(paths) + "</svg>")
    open(a.out, "w").write(svg)
    json.dump({"bounds": [lon0, lon1, lat0, lat1], "size": [w, h]}, open(a.out + ".json", "w"))
    print(len(paths), "polygons", len(svg) // 1024, "KB")


if __name__ == "__main__":
    main()
