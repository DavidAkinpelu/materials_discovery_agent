from mp_api.client import MPRester
import os
from utils.cache import cache_manager
import json
from typing import Dict, List
from config import settings

mp_api_key = os.getenv("MP_API_KEY")

async def get_mp_statistics(field: str) -> str:
    """
    Get statistical distribution of a field to understand typical values and set thresholds.
    
    This helps the agent understand what's "typical", "high", or "low" for a given property
    by sampling ~500 materials and computing percentile distributions.
    
    Args:
        field: The field name to get statistics for (e.g., 'band_gap', 'density', 'k_vrh')
    
    Returns:
        JSON string with statistics including min, max, mean, median, percentiles, and examples
    """
    
    cache_key = f"mp_stats:{field}"
    cached = cache_manager.get(cache_key)
    if cached:
        return cached
    
    try:
        field_criteria_map = {
            "band_gap": {"band_gap": (0, None)},
            "density": {"density": (0, None)},
            "formation_energy": {"formation_energy": (None, 0)},
            "energy_above_hull": {"energy_above_hull": (0, None)},
            "k_vrh": {"k_vrh": (0, None)},
            "g_vrh": {"g_vrh": (0, None)},
            "k_reuss": {"k_reuss": (0, None)},
            "k_voigt": {"k_voigt": (0, None)},
            "g_reuss": {"g_reuss": (0, None)},
            "g_voigt": {"g_voigt": (0, None)},
            "poisson_ratio": {"poisson_ratio": (0, None)},
            "elastic_anisotropy": {"elastic_anisotropy": (0, None)},
            "efermi": {"efermi": (None, None)},
            "e_total": {"e_total": (1, None)},
            "e_electronic": {"e_electronic": (1, None)},
            "e_ionic": {"e_ionic": (0, None)},
            "n": {"n": (1, None)},
            "total_magnetization": {"total_magnetization": (0.1, None)},
            "volume": {"volume": (0, None)},
            "num_sites": {"num_sites": (1, None)},
            "piezoelectric_modulus": {"piezoelectric_modulus": (0, None)},
        }
        
        criteria = field_criteria_map.get(field, {})
        
        with MPRester(mp_api_key) as mpr:
            docs = mpr.materials.summary.search(
                **criteria,
                fields=["material_id", "formula_pretty", field],
                num_chunks=1,
                chunk_size=500
            )
            
            values = []
            examples = []
            
            for doc in docs:
                value = doc
                for part in field.split('.'):
                    value = getattr(value, part, None)
                    if value is None:
                        break
                
                if value is not None and isinstance(value, (int, float)):
                    values.append(float(value))
                    examples.append({
                        "formula": doc.formula_pretty,
                        "material_id": str(doc.material_id),
                        "value": float(value)
                    })
            
            if not values:
                return json.dumps({
                    "error": f"No numerical data found for field '{field}'. Check field name or try a different field.",
                    "suggestion": "Common fields: band_gap, density, formation_energy, k_vrh, g_vrh"
                })
            
            values.sort()
            n = len(values)
            
            stats = {
                "field": field,
                "count": n,
                "min": values[0],
                "max": values[-1],
                "mean": sum(values) / n,
                "median": values[n // 2],
                "percentiles": {
                    "10%": values[int(n * 0.1)],
                    "25%": values[int(n * 0.25)],
                    "50%": values[int(n * 0.5)],
                    "75%": values[int(n * 0.75)],
                    "90%": values[int(n * 0.9)],
                    "95%": values[int(n * 0.95)]
                },
                "interpretation": {
                    "low": f"< {values[int(n * 0.25)]:.3g} (bottom 25%)",
                    "typical": f"{values[int(n * 0.25)]:.3g} - {values[int(n * 0.75)]:.3g} (middle 50%)",
                    "high": f"> {values[int(n * 0.75)]:.3g} (top 25%)",
                    "very_high": f"> {values[int(n * 0.90)]:.3g} (top 10%)"
                },
                "examples": {
                    "low": sorted(examples, key=lambda x: x['value'])[:3],
                    "medium": sorted(examples, key=lambda x: abs(x['value'] - sum(values)/n))[:3],
                    "high": sorted(examples, key=lambda x: x['value'], reverse=True)[:3]
                }
            }
            
            result = json.dumps(stats, indent=2)
            
            cache_manager.set(cache_key, result, ttl=settings.CACHE_TTL_MP_STATS)
            
            return result
            
    except Exception as e:
        return json.dumps({
            "error": f"Failed to get statistics for '{field}': {str(e)}",
            "suggestion": "Verify the field name is correct and corresponds to a numeric property."
        })

async def execute_mp_search(query_params: dict) -> List[dict]:
    """
    Execute a Materials Project search with given parameters
    """
    
    cache_key = f"mp_search:{json.dumps(query_params, sort_keys=True)}"
    cached = cache_manager.get(cache_key)
    if cached:
        return json.loads(cached)
    
    try:
        criteria = query_params.get('criteria', {})
        fields = query_params.get('fields', ['material_id', 'formula_pretty'])
        limit = query_params.get('limit', settings.MP_SEARCH_LIMIT)
        
        with MPRester(mp_api_key) as mpr:
            docs = mpr.materials.summary.search(
                **criteria,
                fields=fields,
                num_chunks=1,
                chunk_size=limit
            )
            
            results = []
            for doc in docs:
                result = {"material_id": str(doc.material_id)}
                
                for field in fields:
                    value = doc
                    for part in field.split('.'):
                        value = getattr(value, part, None)
                        if value is None:
                            break
                    
                    if hasattr(value, '__dict__'):
                        value = str(value)
                    
                    result[field] = value
                
                results.append(result)
            
            cache_manager.set(cache_key, json.dumps(results), ttl=settings.CACHE_TTL_MP_DATA)
            
            return results
            
    except Exception as e:
        return [{"error": str(e)}]
