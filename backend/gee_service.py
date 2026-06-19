from __future__ import annotations

import datetime as dt
import os
from typing import Any

import ee
from dotenv import load_dotenv

from ml_model import train_lst_model

load_dotenv()

AOI_PRESETS = {
    "mumbai": {"name": "Mumbai", "state": "Maharashtra", "bbox": [72.75, 18.85, 73.05, 19.30]},
    "delhi": {"name": "Delhi NCR", "state": "Delhi", "bbox": [76.84, 28.40, 77.35, 28.90]},
    "bengaluru": {"name": "Bengaluru", "state": "Karnataka", "bbox": [77.42, 12.80, 77.78, 13.15]},
    "chennai": {"name": "Chennai", "state": "Tamil Nadu", "bbox": [80.10, 12.90, 80.32, 13.20]},
    "hyderabad": {"name": "Hyderabad", "state": "Telangana", "bbox": [78.25, 17.20, 78.65, 17.60]},
    "kolkata": {"name": "Kolkata", "state": "West Bengal", "bbox": [88.20, 22.40, 88.55, 22.75]},
    "pune": {"name": "Pune", "state": "Maharashtra", "bbox": [73.65, 18.35, 74.05, 18.75]},
    "ahmedabad": {"name": "Ahmedabad", "state": "Gujarat", "bbox": [72.40, 22.85, 72.75, 23.20]},
}
MUMBAI_BBOX = AOI_PRESETS["mumbai"]["bbox"]
SCALE = 90
MAX_SAMPLE_POINTS = 900

LAYER_VIS = {
    "lst": {"min": 25, "max": 48, "palette": ["2c7bb6", "abd9e9", "ffffbf", "fdae61", "d7191c"]},
    "heat_risk": {"min": 0, "max": 1, "palette": ["1a9850", "fee08b", "f46d43", "a50026"]},
    "priority": {"min": 0, "max": 1, "palette": ["edf8fb", "b2e2e2", "66c2a4", "238b45", "00441b"]},
    "cooling_reduction": {"min": 0, "max": 4, "palette": ["ffffcc", "a1dab4", "41b6c4", "225ea8"]},
    "hotspots": {"min": 0, "max": 1, "palette": ["00000000", "ff2b2b"]},
    "ndvi": {"min": -0.2, "max": 0.8, "palette": ["8c510a", "f6e8c3", "7fbf7b", "01665e"]},
    "ndbi": {"min": -0.4, "max": 0.6, "palette": ["2166ac", "f7f7f7", "b2182b"]},
    "greening_reduction": {"min": 0, "max": 3, "palette": ["f7fcf5", "74c476", "00441b"]},
    "cool_roof_reduction": {"min": 0, "max": 2, "palette": ["fff7ec", "fdbb84", "b30000"]},
    "blue_green_reduction": {"min": 0, "max": 2, "palette": ["f7fbff", "6baed6", "08306b"]},
}

SCENARIO_META = {
    "greening": {"label": "+20% vegetation", "relative_cost": 3.0},
    "cool_roof": {"label": "+0.15 roof albedo", "relative_cost": 1.8},
    "blue_green": {"label": "Blue-green corridor", "relative_cost": 3.5},
    "combined": {"label": "Combined portfolio", "relative_cost": 6.5},
}

_initialized = False
_last_context: dict[str, Any] | None = None


def initialize_earth_engine() -> None:
    global _initialized
    if _initialized:
        return

    project = os.getenv("GEE_PROJECT") or None
    service_account = os.getenv("GEE_SERVICE_ACCOUNT")
    private_key_file = os.getenv("GEE_PRIVATE_KEY_FILE")
    private_key_json = os.getenv("GEE_PRIVATE_KEY_JSON")

    try:
        if service_account and (private_key_file or private_key_json):
            credentials = ee.ServiceAccountCredentials(
                service_account,
                key_file=private_key_file or None,
                key_data=private_key_json or None,
            )
            ee.Initialize(credentials, project=project)
        else:
            ee.Initialize(project=project)
    except Exception as exc:
        raise RuntimeError(
            "Google Earth Engine initialization failed. Confirm that credentials are "
            "authorized, GEE_PROJECT is registered for Earth Engine, and Google APIs "
            f"are reachable. Details: {exc}"
        ) from exc

    _initialized = True


def list_areas() -> list[dict[str, Any]]:
    return [{"id": key, **value} for key, value in AOI_PRESETS.items()]


def analyze_mumbai(start: str, end: str) -> dict[str, Any]:
    return analyze_area("mumbai", start, end)


def analyze_area(area: str, start: str, end: str) -> dict[str, Any]:
    area_key = area.lower().strip()
    if area_key not in AOI_PRESETS:
        raise ValueError(f"Unknown area '{area}'. Use one of: {', '.join(AOI_PRESETS)}")
    initialize_earth_engine()
    area_config = AOI_PRESETS[area_key]
    bbox = area_config["bbox"]
    start_date = _parse_date(start)
    end_date = _parse_date(end)
    if end_date <= start_date:
        raise ValueError("end date must be after start date")

    aoi = ee.Geometry.Rectangle(bbox)
    image_bundle = build_analysis_image(aoi, start, end)
    samples = sample_driver_table(image_bundle["drivers"], aoi)
    model_result = train_lst_model(samples)
    scenario_images = build_scenarios(image_bundle["image"], model_result.sensitivities)
    all_layers = image_bundle["image"].addBands(scenario_images)

    stats = zonal_stats(all_layers, aoi)
    scenarios = scenario_summary(stats)
    optimal_strategy = select_optimal_scenario(scenarios)
    top_zones = top_intervention_zones(all_layers, aoi, area_config["name"])
    tile_urls = build_tile_urls(all_layers)

    global _last_context
    _last_context = {
        "start": start,
        "end": end,
        "area_id": area_key,
        "area_name": area_config["name"],
        "aoi": bbox,
        "image": all_layers,
        "tile_urls": tile_urls,
        "stats": stats,
        "top_zones": top_zones,
        "model": model_result,
        "scenarios": scenarios,
        "optimal_strategy": optimal_strategy,
        "data_provenance": image_bundle["data_provenance"],
    }

    return {
        "area": {"id": area_key, "name": area_config["name"], "state": area_config["state"]},
        "aoi": bbox,
        "period": {"start": start, "end": end},
        "data_provenance": image_bundle["data_provenance"],
        "stats": stats,
        "tiles": tile_urls,
        "feature_importance": model_result.feature_importance,
        "grouped_importance": model_result.grouped_importance,
        "model": {
            "rows_used": model_result.rows_used,
            "r2": model_result.r2,
            "mae": model_result.mae,
            "rmse": model_result.rmse,
        },
        "scenarios": scenarios,
        "optimal_strategy": optimal_strategy,
        "top_zones": top_zones,
        "recommendations": build_recommendations(stats, model_result.grouped_importance),
    }


def build_analysis_image(aoi: ee.Geometry, start: str, end: str) -> dict[str, ee.Image]:
    landsat = (
        ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
        .merge(ee.ImageCollection("LANDSAT/LC09/C02/T1_L2"))
        .filterBounds(aoi)
        .filterDate(start, end)
        .filter(ee.Filter.lt("CLOUD_COVER", 45))
        .map(_mask_landsat_l2)
        .map(_add_landsat_indices)
    )

    composite = landsat.median().clip(aoi)
    worldcover = (
        ee.ImageCollection("ESA/WorldCover/v200")
        .first()
        .select("Map")
        .clip(aoi)
        .rename("landcover")
    )
    water = worldcover.eq(80).rename("water")
    tree_grass = worldcover.eq(10).Or(worldcover.eq(30)).rename("green_cover")

    era5_collection = ee.ImageCollection("ECMWF/ERA5/DAILY").filterBounds(aoi)
    era5_period = era5_collection.filterDate(start, end)
    era5_count = int(era5_period.size().getInfo())
    if era5_count:
        era5 = era5_period.mean().clip(aoi)
        meteorology_period = f"{start} to {end}"
        meteorology_mode = "period mean"
    else:
        start_month = _parse_date(start).month
        end_month = _parse_date(end).month
        if start_month <= end_month:
            month_filter = ee.Filter.calendarRange(start_month, end_month, "month")
        else:
            month_filter = ee.Filter.Or(
                ee.Filter.calendarRange(start_month, 12, "month"),
                ee.Filter.calendarRange(1, end_month, "month"),
            )
        era5 = (
            era5_collection.filterDate("2015-01-01", "2020-01-01")
            .filter(month_filter)
            .mean()
            .clip(aoi)
        )
        meteorology_period = "2015-2019 same-season climatology"
        meteorology_mode = "climatology fallback"
    air_c = era5.select("mean_2m_air_temperature").subtract(273.15).rename("air_temperature")
    dew_c = era5.select("dewpoint_2m_temperature").subtract(273.15).rename("dewpoint")
    u = era5.select("u_component_of_wind_10m")
    v = era5.select("v_component_of_wind_10m")
    wind = u.pow(2).add(v.pow(2)).sqrt().rename("wind_speed")
    humidity_proxy = dew_c.subtract(air_c).multiply(-1).rename("dewpoint_depression")
    # Magnus approximation: RH = 100 * es(Td) / es(T).
    vapor_dew = dew_c.multiply(17.625).divide(dew_c.add(243.04)).exp()
    vapor_air = air_c.multiply(17.625).divide(air_c.add(243.04)).exp()
    relative_humidity = vapor_dew.divide(vapor_air).multiply(100).clamp(0, 100).rename(
        "relative_humidity"
    )

    ndvi = composite.select("NDVI")
    ndbi = composite.select("NDBI")
    lst = composite.select("LST")
    built_up = ndbi.unitScale(-0.2, 0.5).clamp(0, 1).rename("built_up")
    ndvi_norm = ndvi.unitScale(-0.2, 0.8).clamp(0, 1)
    vegetation_deficit = ee.Image(1).subtract(ndvi_norm).rename("vegetation_deficit")
    lst_norm = lst.unitScale(28, 46).clamp(0, 1)
    ndbi_norm = ndbi.unitScale(-0.25, 0.55).clamp(0, 1)
    heat_risk = (
        lst_norm.multiply(0.50)
        .add(ndbi_norm.multiply(0.30))
        .add(vegetation_deficit.multiply(0.20))
        .rename("heat_risk")
    )
    priority = (
        lst_norm.multiply(0.45)
        .add(ndbi_norm.multiply(0.35))
        .add(vegetation_deficit.multiply(0.20))
        .rename("priority")
    )
    hotspots = heat_risk.gt(0.72).rename("hotspots")

    image = (
        lst.addBands(ndvi)
        .addBands(ndbi)
        .addBands(built_up)
        .addBands(vegetation_deficit)
        .addBands(heat_risk)
        .addBands(priority)
        .addBands(hotspots)
        .addBands(air_c)
        .addBands(dew_c)
        .addBands(humidity_proxy)
        .addBands(relative_humidity)
        .addBands(wind)
        .addBands(water)
        .addBands(tree_grass)
        .clip(aoi)
    )

    drivers = image.select(
        [
            "LST",
            "NDVI",
            "NDBI",
            "built_up",
            "vegetation_deficit",
            "air_temperature",
            "relative_humidity",
            "wind_speed",
        ]
    )
    return {
        "image": image,
        "drivers": drivers,
        "data_provenance": {
            "landsat": "LANDSAT/LC08/C02/T1_L2 + LANDSAT/LC09/C02/T1_L2",
            "land_cover": "ESA/WorldCover/v200",
            "meteorology": "ECMWF/ERA5/DAILY",
            "meteorology_period": meteorology_period,
            "meteorology_mode": meteorology_mode,
        },
    }


def build_scenarios(image: ee.Image, sensitivities: dict[str, float]) -> ee.Image:
    """Build bounded intervention effects using ML sensitivity and energy-balance priors."""
    ndvi_gain = image.select("vegetation_deficit").multiply(0.20).rename("ndvi_gain")
    greening_reduction = ndvi_gain.multiply(sensitivities["ndvi_cooling_per_0_1"] * 10).rename(
        "scenario_greening_reduction"
    ).clamp(0, 3)

    # A +0.15 albedo intervention lowers absorbed shortwave energy on built surfaces.
    albedo_gain = image.select("built_up").multiply(0.15).rename("albedo_gain")
    cool_roof_reduction = albedo_gain.divide(0.15).multiply(1.0).add(0.5).clamp(0, 1.5).rename(
        "scenario_cool_roof_reduction"
    )

    water_influence = image.select("water").focalMax(750, "circle", "meters")
    water_priority = water_influence.add(0.25).multiply(image.select("priority")).clamp(0, 1).rename(
        "scenario_blue_green_priority"
    )
    blue_green_reduction = water_priority.multiply(1.25).add(
        image.select("vegetation_deficit").multiply(0.25)
    ).clamp(0, 1.75).rename("scenario_blue_green_reduction")

    synergy = greening_reduction.min(cool_roof_reduction).multiply(0.12)
    combined = (
        greening_reduction.add(cool_roof_reduction).add(blue_green_reduction).add(synergy)
        .clamp(0, 5)
        .rename("cooling_reduction")
    )
    scenario_lst = image.select("LST").subtract(combined).rename("scenario_combined_lst")
    return (
        ndvi_gain.addBands(albedo_gain)
        .addBands(greening_reduction)
        .addBands(cool_roof_reduction)
        .addBands(water_priority)
        .addBands(blue_green_reduction)
        .addBands(combined)
        .addBands(scenario_lst)
    )


def sample_driver_table(image: ee.Image, aoi: ee.Geometry) -> list[dict[str, Any]]:
    feature_collection = image.sample(
        region=aoi,
        scale=SCALE,
        numPixels=MAX_SAMPLE_POINTS,
        seed=42,
        geometries=False,
        tileScale=4,
    )
    rows = feature_collection.getInfo().get("features", [])
    return [row.get("properties", {}) for row in rows]


def zonal_stats(image: ee.Image, aoi: ee.Geometry) -> dict[str, Any]:
    reducer = ee.Reducer.mean().combine(ee.Reducer.minMax(), sharedInputs=True).combine(
        ee.Reducer.percentile([75, 90]), sharedInputs=True
    )
    raw = image.select([
        "LST",
        "NDVI",
        "NDBI",
        "relative_humidity",
        "wind_speed",
        "heat_risk",
        "priority",
        "scenario_greening_reduction",
        "scenario_cool_roof_reduction",
        "scenario_blue_green_reduction",
        "cooling_reduction",
    ]).reduceRegion(
        reducer=reducer,
        geometry=aoi,
        scale=SCALE,
        maxPixels=1_000_000_000,
        tileScale=4,
    )
    values = raw.getInfo()
    hotspot_area = (
        image.select("hotspots")
        .multiply(ee.Image.pixelArea())
        .divide(1_000_000)
        .reduceRegion(ee.Reducer.sum(), aoi, SCALE, maxPixels=1_000_000_000, tileScale=4)
        .getInfo()
        .get("hotspots", 0)
    )
    return {
        "mean_lst": _round(values.get("LST_mean")),
        "max_lst": _round(values.get("LST_max")),
        "p90_lst": _round(values.get("LST_p90")),
        "mean_ndvi": _round(values.get("NDVI_mean"), 3),
        "mean_ndbi": _round(values.get("NDBI_mean"), 3),
        "mean_relative_humidity": _round(values.get("relative_humidity_mean"), 1),
        "mean_wind_speed": _round(values.get("wind_speed_mean"), 2),
        "mean_heat_risk": _round(values.get("heat_risk_mean"), 3),
        "mean_priority": _round(values.get("priority_mean"), 3),
        "estimated_avg_reduction": _round(values.get("cooling_reduction_mean")),
        "greening_avg_reduction": _round(values.get("scenario_greening_reduction_mean")),
        "cool_roof_avg_reduction": _round(values.get("scenario_cool_roof_reduction_mean")),
        "blue_green_avg_reduction": _round(values.get("scenario_blue_green_reduction_mean")),
        "hotspot_area_sq_km": _round(hotspot_area),
    }


def top_intervention_zones(image: ee.Image, aoi: ee.Geometry, area_name: str) -> list[dict[str, Any]]:
    grid = aoi.coveringGrid(proj=ee.Projection("EPSG:4326").atScale(1000), scale=1000)
    zone_image = image.select([
        "LST",
        "NDVI",
        "NDBI",
        "priority",
        "scenario_greening_reduction",
        "scenario_cool_roof_reduction",
        "scenario_blue_green_reduction",
        "cooling_reduction",
    ])
    reduced = zone_image.reduceRegions(
        collection=grid,
        reducer=ee.Reducer.mean(),
        scale=SCALE,
        tileScale=4,
    )
    sorted_zones = reduced.sort("priority", False).limit(10)
    features = sorted_zones.getInfo().get("features", [])
    zones: list[dict[str, Any]] = []
    for index, feature in enumerate(features, start=1):
        props = feature.get("properties", {})
        centroid = _feature_centroid(feature.get("geometry", {}))
        zones.append(
            {
                "rank": index,
                "zone": f"{area_name} Grid {index}",
                "lat": _round(centroid[1], 5),
                "lon": _round(centroid[0], 5),
                "lst": _round(props.get("LST")),
                "ndvi": _round(props.get("NDVI"), 3),
                "ndbi": _round(props.get("NDBI"), 3),
                "priority": _round(props.get("priority"), 3),
                "estimated_reduction": _round(props.get("cooling_reduction")),
                "greening_reduction": _round(props.get("scenario_greening_reduction")),
                "cool_roof_reduction": _round(props.get("scenario_cool_roof_reduction")),
                "blue_green_reduction": _round(props.get("scenario_blue_green_reduction")),
                "recommendation": _zone_recommendation(props),
            }
        )
    return zones


def build_tile_urls(image: ee.Image) -> dict[str, str]:
    mapping = {
        "lst": "LST",
        "heat_risk": "heat_risk",
        "priority": "priority",
        "cooling_reduction": "cooling_reduction",
        "hotspots": "hotspots",
        "ndvi": "NDVI",
        "ndbi": "NDBI",
        "greening_reduction": "scenario_greening_reduction",
        "cool_roof_reduction": "scenario_cool_roof_reduction",
        "blue_green_reduction": "scenario_blue_green_reduction",
    }
    urls: dict[str, str] = {}
    for layer, band in mapping.items():
        map_id = image.select(band).getMapId(LAYER_VIS[layer])
        urls[layer] = map_id["tile_fetcher"].url_format
    return urls


def get_tile_layer(layer: str) -> dict[str, str]:
    if _last_context is None:
        analyze_area("mumbai", "2024-03-01", "2024-05-31")
    assert _last_context is not None
    tile_urls = _last_context["tile_urls"]
    if layer not in tile_urls:
        raise KeyError(f"Unknown layer: {layer}")
    return {"layer": layer, "url": tile_urls[layer]}


def build_report() -> str:
    if _last_context is None:
        analyze_area("mumbai", "2024-03-01", "2024-05-31")
    assert _last_context is not None
    stats = _last_context["stats"]
    model = _last_context["model"]
    zones = _last_context["top_zones"]
    scenarios = _last_context["scenarios"]
    optimal = _last_context["optimal_strategy"]
    lines = [
        f"# CoolGrid Urban - {_last_context['area_name']} Heat Decision Brief",
        "",
        "## Executive Decision",
        f"The optimized strategy is **{optimal['label']}**, with an estimated mean reduction of **{optimal.get('mean_reduction_c', 0)} C** across modeled intervention surfaces.",
        f"For cooling delivered per relative cost unit, prioritize **{optimal.get('best_value_label', optimal['label'])}**.",
        "",
        "## Analysis Scope",
        f"Analysis period: {_last_context['start']} to {_last_context['end']}",
        f"Selected area: {_last_context['area_name']}",
        f"AOI bounding box: {_last_context['aoi']}",
        f"Meteorology: {_last_context.get('data_provenance', {}).get('meteorology_period', 'ECMWF/ERA5/DAILY')}",
        "",
        "## Key Statistics",
        f"- Mean LST: {stats['mean_lst']} C",
        f"- P90 LST: {stats['p90_lst']} C",
        f"- Maximum LST: {stats['max_lst']} C",
        f"- Mean heat risk score: {stats['mean_heat_risk']}",
        f"- Hotspot area: {stats['hotspot_area_sq_km']} sq km",
        f"- Estimated average combined cooling: {stats['estimated_avg_reduction']} C",
        "",
        "## Validated AIML Model",
        f"- RandomForest sampled rows: {model.rows_used}",
        f"- Validation R2: {model.r2 if model.r2 is not None else 'not enough held-out rows'}",
        f"- Validation MAE: {model.mae if model.mae is not None else 'not enough held-out rows'} C",
        f"- Validation RMSE: {model.rmse if model.rmse is not None else 'not enough held-out rows'} C",
        f"- Driver groups: {model.grouped_importance}",
        "",
        "## Physics-Informed Scenario Evaluation",
        "",
    ]
    for scenario in scenarios:
        lines.append(
            f"- {scenario['label']}: mean reduction {scenario['mean_reduction_c']} C; "
            f"effectiveness score {scenario['effectiveness_score']}"
        )
    lines.extend([
        f"- Optimized portfolio: {optimal['label']} ({optimal['reason']})",
        "",
        "## Top Intervention Zones",
    ])
    for zone in zones:
        lines.append(
            f"{zone['rank']}. {zone['zone']} ({zone['lat']}, {zone['lon']}): "
            f"priority {zone['priority']}, expected reduction {zone['estimated_reduction']} C, "
            f"{zone['recommendation']}"
        )
    lines.extend(
        [
            "",
            "## Recommended Strategy",
            "Prioritize dense built-up hotspots with low vegetation for street trees, shaded corridors, cool roofs, and blue-green links to existing water bodies.",
        ]
    )
    return "\n".join(lines)


def scenario_summary(stats: dict[str, Any]) -> list[dict[str, Any]]:
    reductions = {
        "greening": stats.get("greening_avg_reduction", 0.0),
        "cool_roof": stats.get("cool_roof_avg_reduction", 0.0),
        "blue_green": stats.get("blue_green_avg_reduction", 0.0),
        "combined": stats.get("estimated_avg_reduction", 0.0),
    }
    scenarios = []
    for key, reduction in reductions.items():
        meta = SCENARIO_META[key]
        reduction_value = float(reduction or 0)
        scenarios.append(
            {
                "key": key,
                "label": meta["label"],
                "mean_reduction_c": round(reduction_value, 2),
                "relative_cost": meta["relative_cost"],
                "effectiveness_score": round(reduction_value / meta["relative_cost"], 3),
            }
        )
    return scenarios


def select_optimal_scenario(scenarios: list[dict[str, Any]]) -> dict[str, Any]:
    if not scenarios:
        return {"key": "combined", "label": "Combined portfolio", "reason": "No scenario statistics available"}
    best_value = max(scenarios, key=lambda item: item["mean_reduction_c"])
    best_efficiency = max(scenarios, key=lambda item: item["effectiveness_score"])
    return {
        "key": best_value["key"],
        "label": best_value["label"],
        "mean_reduction_c": best_value["mean_reduction_c"],
        "best_value_key": best_efficiency["key"],
        "best_value_label": best_efficiency["label"],
        "reason": (
            f"{best_value['label']} maximizes cooling; {best_efficiency['label']} "
            "offers the strongest cooling per relative cost unit."
        ),
    }


def build_recommendations(stats: dict[str, Any], grouped: dict[str, float]) -> list[str]:
    recommendations = [
        "Target the top priority grids first: they combine high LST, high built-up intensity, and vegetation deficit.",
        "Use +20% vegetation interventions on corridors where NDVI is lowest and pedestrian exposure is high.",
        "Deploy cool roof coating and high-albedo surfaces in dense built-up clusters before the next pre-monsoon season.",
        "Protect and connect water-adjacent blue-green corridors to improve local cooling continuity.",
    ]
    if grouped.get("vegetation", 0) > grouped.get("built_up", 0):
        recommendations.insert(0, "Vegetation is the strongest modeled cooling driver; prioritize canopy expansion and pocket parks.")
    if stats.get("hotspot_area_sq_km", 0) > 10:
        recommendations.append("Create ward-level heat action micro-plans for the hotspot area flagged by the heat risk layer.")
    return recommendations


def _mask_landsat_l2(image: ee.Image) -> ee.Image:
    qa = image.select("QA_PIXEL")
    cloud = qa.bitwiseAnd(1 << 3).eq(0)
    cloud_shadow = qa.bitwiseAnd(1 << 4).eq(0)
    cirrus = qa.bitwiseAnd(1 << 2).eq(0)
    return image.updateMask(cloud_shadow.And(cloud).And(cirrus))


def _add_landsat_indices(image: ee.Image) -> ee.Image:
    red = image.select("SR_B4").multiply(0.0000275).add(-0.2)
    nir = image.select("SR_B5").multiply(0.0000275).add(-0.2)
    swir1 = image.select("SR_B6").multiply(0.0000275).add(-0.2)
    ndvi = nir.subtract(red).divide(nir.add(red)).rename("NDVI")
    ndbi = swir1.subtract(nir).divide(swir1.add(nir)).rename("NDBI")
    lst = image.select("ST_B10").multiply(0.00341802).add(149.0).subtract(273.15).rename("LST")
    return image.addBands([ndvi, ndbi, lst])


def _zone_recommendation(props: dict[str, Any]) -> str:
    ndvi = props.get("NDVI") or 0
    ndbi = props.get("NDBI") or 0
    if ndbi > 0.2 and ndvi < 0.2:
        return "Cool roofs plus street-tree corridor"
    if ndvi < 0.25:
        return "Vegetation infill and shaded public spaces"
    return "Blue-green corridor and surface cooling"


def _feature_centroid(geometry: dict[str, Any]) -> list[float]:
    coordinates = geometry.get("coordinates", [])
    points: list[list[float]] = []
    if geometry.get("type") == "Polygon" and coordinates:
        points = coordinates[0]
    elif geometry.get("type") == "MultiPolygon" and coordinates:
        points = coordinates[0][0]
    if not points:
        return [0.0, 0.0]
    lon = sum(point[0] for point in points) / len(points)
    lat = sum(point[1] for point in points) / len(points)
    return [lon, lat]


def _parse_date(value: str) -> dt.date:
    return dt.date.fromisoformat(value)


def _round(value: Any, digits: int = 2) -> float:
    if value is None:
        return 0.0
    return round(float(value), digits)
