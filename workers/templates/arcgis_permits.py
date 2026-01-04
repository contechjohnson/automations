"""
ArcGIS Permits Template
=======================
Scrapes building permits from ArcGIS-based permit systems.
Supports 750+ jurisdictions using Accela/Tyler backends.

Config Schema:
{
    "permit_endpoint": "https://gis.example.gov/.../PermitHistory/FeatureServer/0",
    "parcel_endpoint": "https://gis.example.gov/.../Parcels/MapServer/1",  # optional
    "case_types": ["Building Commercial", "Site Development"],
    "min_date": "90_days_ago",  # or ISO date
    "keywords": ["INDUSTRIAL", "WAREHOUSE", "DATA CENTER"],
    "min_lot_size": 5.0  # acres, optional
}
"""

import os
import requests
from datetime import datetime, timedelta
from typing import Optional
from rq import get_current_job


def run(
    config: dict,
    geography: dict,
    job: Optional[object] = None
) -> dict:
    """
    Run the ArcGIS permit scraper.
    
    Args:
        config: Scraper configuration (endpoints, filters)
        geography: Geographic context {state, county, city}
        job: RQ job for progress updates
    
    Returns:
        {records_found, records_new, data: [...]}
    """
    
    def update(message: str, percent: int):
        if job:
            job.meta = {"message": message, "percent": percent}
            job.save_meta()
        print(f"[{percent}%] {message}")
    
    # Validate config
    permit_endpoint = config.get("permit_endpoint")
    if not permit_endpoint:
        raise ValueError("permit_endpoint is required")
    
    update("Fetching permits...", 20)
    
    # Build date filter
    min_date = config.get("min_date", "90_days_ago")
    if min_date == "90_days_ago":
        min_date = (datetime.utcnow() - timedelta(days=90)).strftime("%Y-%m-%d")
    
    # Build WHERE clause
    case_types = config.get("case_types", [])
    where_parts = []
    
    if case_types:
        types_str = ",".join([f"'{t}'" for t in case_types])
        where_parts.append(f"CaseType IN ({types_str})")
    
    where_clause = " AND ".join(where_parts) if where_parts else "1=1"
    
    # Query permit layer
    params = {
        "where": where_clause,
        "outFields": "*",
        "returnGeometry": "true",
        "f": "json"
    }
    
    response = requests.get(f"{permit_endpoint}/query", params=params, timeout=60)
    response.raise_for_status()
    data = response.json()
    
    features = data.get("features", [])
    update(f"Found {len(features)} permits", 40)
    
    # Enrich with parcel data if endpoint provided
    parcel_endpoint = config.get("parcel_endpoint")
    if parcel_endpoint and features:
        update("Enriching with parcel data...", 50)
        features = enrich_with_parcels(features, parcel_endpoint, job)
    
    # Filter by keywords
    keywords = config.get("keywords", [])
    if keywords:
        update("Filtering by keywords...", 70)
        features = filter_by_keywords(features, keywords)
        update(f"{len(features)} match keyword filters", 75)
    
    # Filter by lot size
    min_lot_size = config.get("min_lot_size")
    if min_lot_size:
        features = [f for f in features if f.get("attributes", {}).get("LotSize_Acre", 0) >= min_lot_size]
        update(f"{len(features)} meet lot size minimum", 80)
    
    # Format output
    update("Formatting results...", 90)
    records = []
    for feature in features:
        attrs = feature.get("attributes", {})
        geom = feature.get("geometry", {})
        
        records.append({
            "case_number": attrs.get("CaseNumber") or attrs.get("CASE_NUMBER"),
            "case_type": attrs.get("CaseType") or attrs.get("CASE_TYPE"),
            "application_date": format_date(attrs.get("ApplicationDate") or attrs.get("APPLICATION_DATE")),
            "address": attrs.get("Address") or attrs.get("ADDRESS"),
            "owner_name": attrs.get("OwnerName") or attrs.get("OWNER_NAME"),
            "property_use": attrs.get("PropertyUse") or attrs.get("PROPERTY_USE"),
            "lot_size_acres": attrs.get("LotSize_Acre"),
            "coordinates": {
                "lat": geom.get("y"),
                "lon": geom.get("x")
            } if geom else None,
            "geography": geography,
            "raw_attributes": attrs
        })
    
    update(f"Complete! {len(records)} records", 100)
    
    return {
        "records_found": len(records),
        "records_new": len(records),  # TODO: dedup against previous runs
        "data": records,
        "geography": geography,
        "config_used": {
            "permit_endpoint": permit_endpoint,
            "case_types": case_types,
            "keywords": keywords
        }
    }


def enrich_with_parcels(features: list, parcel_endpoint: str, job: Optional[object] = None) -> list:
    """Enrich permits with parcel data via spatial query."""
    enriched = []
    total = len(features)
    
    for i, feature in enumerate(features):
        geom = feature.get("geometry")
        if not geom:
            enriched.append(feature)
            continue
        
        # Spatial query
        params = {
            "geometry": f"{geom.get('x')},{geom.get('y')}",
            "geometryType": "esriGeometryPoint",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "OwnerName,PropertyUse,LotSize_Acre,Zoning",
            "returnGeometry": "false",
            "f": "json"
        }
        
        try:
            response = requests.get(f"{parcel_endpoint}/query", params=params, timeout=30)
            if response.ok:
                parcel_data = response.json()
                parcels = parcel_data.get("features", [])
                if parcels:
                    parcel_attrs = parcels[0].get("attributes", {})
                    feature["attributes"].update({
                        "OwnerName": parcel_attrs.get("OwnerName"),
                        "PropertyUse": parcel_attrs.get("PropertyUse"),
                        "LotSize_Acre": parcel_attrs.get("LotSize_Acre"),
                        "Zoning": parcel_attrs.get("Zoning")
                    })
        except Exception as e:
            print(f"Parcel enrichment failed for feature {i}: {e}")
        
        enriched.append(feature)
        
        # Progress update every 10%
        if job and i % max(1, total // 10) == 0:
            pct = 50 + int((i / total) * 20)
            job.meta = {"message": f"Enriching {i}/{total} permits...", "percent": pct}
            job.save_meta()
    
    return enriched


def filter_by_keywords(features: list, keywords: list) -> list:
    """Filter features by keywords in property use or description."""
    keywords_upper = [k.upper() for k in keywords]
    
    def matches(feature):
        attrs = feature.get("attributes", {})
        # Check common fields
        for field in ["PropertyUse", "PROPERTY_USE", "Description", "ProjectName", "Notes"]:
            value = attrs.get(field, "")
            if value and any(kw in str(value).upper() for kw in keywords_upper):
                return True
        return False
    
    return [f for f in features if matches(f)]


def format_date(timestamp):
    """Convert ArcGIS timestamp to ISO date."""
    if not timestamp:
        return None
    try:
        # ArcGIS uses milliseconds since epoch
        if isinstance(timestamp, (int, float)):
            return datetime.fromtimestamp(timestamp / 1000).strftime("%Y-%m-%d")
        return str(timestamp)
    except:
        return str(timestamp)
