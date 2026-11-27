"""Download the public sources once (cache in data/raw/), then write small derived tables to data/public/.

Sources (all read on 27/11/2026, see docs/sources.md):
  URSSAF open data (ODbL)      auto-entrepreneurs by departement, by departement x sector, active self-employed
                               (national), self-employed income by departement
  INSEE BDM (Licence Ouverte)  monthly creations of sole proprietorships under the micro-entrepreneur scheme,
                               raw (010755410) and seasonally adjusted (010755411)
  Etalab (Licence Ouverte)     departement boundaries 2025
  Nager.Date                   French public holidays 2024-2026
At most one request per second per host (common.polite_get); neutral User-Agent; no account, no key.
Run from the repository root:  python src/download_public.py
"""
from __future__ import annotations

import io
import json
import sys
import xml.etree.ElementTree as ET

import pandas as pd

from common import PUBLIC, RAW, polite_get

sys.stdout.reconfigure(encoding="utf-8")
URSSAF = "https://open.urssaf.fr/api/explore/v2.1/catalog/datasets/{}/exports/csv?delimiter=%3B{}"
INSEE = "https://bdm.insee.fr/series/sdmx/data/SERIES_BDM/{}?startPeriod=2015-01"
GEO = "https://etalab-datasets.geo.data.gouv.fr/contours-administratifs/2025/geojson/departements-100m.geojson"
HOL = "https://date.nager.at/api/v3/PublicHolidays/{}/FR"


def urssaf(ds: str, where: str = "") -> pd.DataFrame:
    raw = polite_get(URSSAF.format(ds, where), timeout=180)
    df = pd.read_csv(io.BytesIO(raw), sep=";", dtype=str)
    for c in df.columns:  # values arrive as text ('2635.0'): cast what is numeric
        if c in ("annee", "trimestre") or c.startswith(("immatriculations", "radiations", "chiffres", "economiquement",
                                                         "administrativement", "nombre", "revenu")):
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def insee(idbank: str) -> pd.DataFrame:
    root = ET.fromstring(polite_get(INSEE.format(idbank)))
    rows = [(o.get("TIME_PERIOD"), float(o.get("OBS_VALUE"))) for o in root.iter() if o.tag.endswith("Obs") and o.get("OBS_VALUE")]
    return pd.DataFrame(rows, columns=["month", idbank])


def main() -> None:
    PUBLIC.mkdir(parents=True, exist_ok=True)
    keep = ["code_region", "region", "code_departement", "departement", "annee", "trimestre", "dernier_jour_du_trimestre"]

    ae = urssaf("auto-entrepreneurs-par-departement")
    ae = ae[keep + ["immatriculations", "radiations", "chiffres_d_affaires", "economiquement_actifs", "administrativement_actifs"]]
    ae.sort_values(["code_departement", "dernier_jour_du_trimestre"]).to_csv(PUBLIC / "urssaf_ae_departement.csv", index=False)

    sec = urssaf("auto-entrepreneurs-par-departement-secteur", "&where=annee%3E%3D%222019%22")
    sec = sec[["secteur_d_activite", *keep, "economiquement_actifs", "administrativement_actifs", "chiffres_d_affaires"]]
    # national sector series (sum of departements) + last quarter by departement x sector
    nat = (sec.groupby(["secteur_d_activite", "dernier_jour_du_trimestre"], as_index=False)
              [["economiquement_actifs", "administrativement_actifs", "chiffres_d_affaires"]].sum())
    nat.sort_values(["secteur_d_activite", "dernier_jour_du_trimestre"]).to_csv(PUBLIC / "urssaf_ae_secteur_national.csv", index=False)

    ti = urssaf("travailleurs-independants-actifs-trimestriels")
    ti.sort_values(["type_de_travailleur_independant", "dernier_jour_du_trimestre"]).to_csv(PUBLIC / "urssaf_ti_national.csv", index=False)

    rev = urssaf("les-revenus-des-travailleurs-independants-par-departement")
    rev = rev[["type_de_travailleur_independant", "code_region", "region", "code_departement", "departement", "annee", "nombre_de_ti", "revenu"]]
    rev.sort_values(["annee", "code_departement", "type_de_travailleur_independant"]).to_csv(PUBLIC / "urssaf_revenus_departement.csv", index=False)

    ins = insee("010755410").merge(insee("010755411"), on="month", how="outer")
    ins.columns = ["month", "creations_raw", "creations_sa"]
    ins.sort_values("month").to_csv(PUBLIC / "insee_micro_creations_monthly.csv", index=False)

    hol = []
    for y in (2024, 2025, 2026):
        hol += [(h["date"], h["localName"]) for h in json.loads(polite_get(HOL.format(y)))]
    pd.DataFrame(hol, columns=["date", "name"]).to_csv(PUBLIC / "holidays_fr.csv", index=False)

    geo = RAW / "departements-100m.geojson"
    if not geo.exists():
        geo.write_bytes(polite_get(GEO, timeout=180))
    try:  # simplified boundaries for the map (Licence Ouverte, Etalab)
        import geopandas as gpd  # noqa: PLC0415
        g = gpd.read_file(geo)[["code", "nom", "geometry"]]
        area = g.to_crs(6933).area / 1e6  # equal-area projection, km2
        pd.DataFrame({"code_departement": g.code, "area_km2": area.round(0)}).to_csv(PUBLIC / "departements_area.csv", index=False)
        g["geometry"] = g.geometry.simplify(0.01, preserve_topology=True)
        g.to_file(PUBLIC / "departements_simplified.geojson", driver="GeoJSON", COORDINATE_PRECISION=3)
    except ImportError:
        (PUBLIC / "departements_simplified.geojson").write_bytes(geo.read_bytes())

    print(f"URSSAF ae {len(ae):,} rows · sector {len(sec):,} rows · TI {len(ti)} · income {len(rev):,} · "
          f"INSEE {len(ins)} months (last {ins.month.max()}) · holidays {len(hol)}")


if __name__ == "__main__":
    main()
