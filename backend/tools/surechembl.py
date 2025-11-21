import httpx
import json
import asyncio
import os
import urllib.parse
from typing import List, Dict, Optional, Any
from utils.cache import cache_manager
from config import settings
import logging

logger = logging.getLogger(__name__)

SURECHEMBL_BASE_URL = "https://www.surechembl.org/api"

async def _poll_search_results(client: httpx.AsyncClient, job_id: str, max_retries: int = 10) -> Dict:
    """
    Helper to poll for search results
    """
    for _ in range(max_retries):
        status_resp = await client.get(f"{SURECHEMBL_BASE_URL}/search/{job_id}/status")
        status_resp.raise_for_status()
        status = status_resp.json().get("status")
        
        if status == "COMPLETE":
            results_resp = await client.get(f"{SURECHEMBL_BASE_URL}/search/{job_id}/results?page=0&itemsPerPage={settings.SURECHEMBL_PAGE_SIZE}")
            results_resp.raise_for_status()
            return results_resp.json()
        
        elif status in ["FAILED", "ERROR"]:
            raise Exception(f"Search job failed with status: {status}")
            
        await asyncio.sleep(2)
        
    raise Exception("Search timed out")

async def search_patents_tool(query: str) -> str:
    """
    Search patents by text/keywords using SureChEMBL API.
    Useful for finding industrial applications or prior art.
    """
    cache_key = f"surechembl:patents:v2:{query}"
    cached = cache_manager.get(cache_key)
    if cached:
        return cached

    try:
        async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT) as client:
            submit_url = f"{SURECHEMBL_BASE_URL}/search/content"
            params = {
                "query": query,
                "page": 0,
                "itemsPerPage": settings.SURECHEMBL_PAGE_SIZE
            }
            
            response = await client.post(submit_url, params=params)
            response.raise_for_status()
            
            job_id = response.json().get("string") # Based on Swagger typical response for "hash"
            
            if not job_id:
                 job_id = response.json().get("hash") or response.json().get("id")

            data = await _poll_search_results(client, job_id)
            
            hits = data.get("results", [])
            formatted = []
            
            for hit in hits:
                formatted.append({
                    "patent_id": hit.get("id"),
                    "title": hit.get("title", {}).get("english", "No Title"),
                    "publication_date": hit.get("publicationDate"),
                    "url": f"https://www.surechembl.org/document/{hit.get('id')}"
                })

            result_str = json.dumps(formatted, indent=2)
            cache_manager.set(cache_key, result_str, ttl=settings.CACHE_TTL_PATENTS)
            return result_str

    except Exception as e:
        return json.dumps({"error": f"SureChEMBL search failed: {str(e)}"})

async def search_similar_structures_tool(smiles: str, threshold: float = 0.7) -> str:
    """
    Find structurally similar chemicals in patent database.
    """
    cache_key = f"surechembl:similarity:v2:{smiles}:{threshold}"
    cached = cache_manager.get(cache_key)
    if cached:
        return cached

    try:
        async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT) as client:
            submit_url = f"{SURECHEMBL_BASE_URL}/search/structure"
            payload = {
                "struct": smiles,
                "structSearchType": "SIMILARITY",
                "maxResults": 10,
                "options": str(threshold)
            }
            
            response = await client.post(submit_url, json=payload)
            response.raise_for_status()
            job_id = response.json().get("string")
            
            data = await _poll_search_results(client, job_id)
            
            hits = data.get("results", [])
            formatted = []
            
            for hit in hits:
                formatted.append({
                    "surechembl_id": hit.get("id"),
                    "similarity": hit.get("similarity"),
                    "num_patents": hit.get("numDocs", 0)
                })

            result_str = json.dumps(formatted, indent=2)
            cache_manager.set(cache_key, result_str, ttl=settings.CACHE_TTL_STRUCTURES)
            return result_str

    except Exception as e:
        return json.dumps({"error": f"Similarity search failed: {str(e)}"})

async def get_chemical_frequency_tool(compound_name: str) -> str:
    """
    Get frequency of a chemical across patent database.
    """
    cache_key = f"surechembl:frequency:v2:{compound_name}"
    cached = cache_manager.get(cache_key)
    if cached:
        return cached

    try:
        async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT) as client:
            submit_url = f"{SURECHEMBL_BASE_URL}/search/content"
            params = {
                "query": f'"{compound_name}"',
                "page": 0,
                "itemsPerPage": 1
            }
            
            response = await client.post(submit_url, params=params)
            response.raise_for_status()
            job_id = response.json().get("string")
            
            data = await _poll_search_results(client, job_id)
            
            total_hits = data.get("totalRecords", 0)
            
            status = "Novel/Rare"
            if total_hits > 100: status = "Known"
            if total_hits > 1000: status = "Common/Commodity"
            if total_hits > 10000: status = "Heavily Patented"
            
            result = {
                "compound": compound_name,
                "patent_count": total_hits,
                "status": status,
                "source": "SureChEMBL"
            }
            
            result_str = json.dumps(result, indent=2)
            cache_manager.set(cache_key, result_str, ttl=settings.CACHE_TTL_PATENTS)
            return result_str

    except Exception as e:
        return json.dumps({"error": f"Frequency check failed: {str(e)}"})


async def get_chemical_by_name(chemical_name: str) -> str:
    """
    Get basic chemical information by name from SureChEMBL.
    Returns SMILES, InChI, InChI Key, molecular weight, and patent frequency.
    
    NOTE: Name search returns limited properties. Use get_chemical_by_id() 
    for comprehensive drug-likeness data.
    
    Endpoint: /api/chemical/name/{name}
    """
    cache_key = f"surechembl:chem_name:{chemical_name}"
    cached = cache_manager.get(cache_key)
    if cached:
        return cached
    
    try:
        async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT) as client:
            url = f"{SURECHEMBL_BASE_URL}/chemical/name/{urllib.parse.quote(chemical_name)}"
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") != "OK" or not data.get("data"):
                return json.dumps({"error": f"Chemical '{chemical_name}' not found in SureChEMBL"})
            
            chem = data["data"][0]
            
            result = {
                "surechembl_id": chem.get("chemical_id"),
                "name": chem.get("name"),
                "smiles": chem.get("smiles"),
                "inchi": chem.get("inchi"),
                "inchikey": chem.get("inchi_key"),
                "molecular_weight": chem.get("mol_weight"),
                "global_frequency": chem.get("global_frequency"),
                "is_element": chem.get("is_element") == 1,
                "note": "Use get_chemical_by_id() for comprehensive drug-likeness properties"
            }
            
            result_str = json.dumps(result, indent=2)
            cache_manager.set(cache_key, result_str, ttl=None)  # Permanent cache
            return result_str
            
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return json.dumps({"error": f"Chemical '{chemical_name}' not found (404)"})
        return json.dumps({"error": f"SureChEMBL API error: {e.response.status_code}"})
    except Exception as e:
        return json.dumps({"error": f"Chemical lookup failed: {str(e)}"})


async def get_chemical_by_id(surechembl_id: str) -> str:
    """
    Get comprehensive chemical information by SureChEMBL ID.
    Returns full molecular properties including drug-likeness metrics.
    
    Endpoint: /api/chemical/id/{id}
    """
    cache_key = f"surechembl:chem_id:{surechembl_id}"
    cached = cache_manager.get(cache_key)
    if cached:
        return cached
    
    try:
        async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT) as client:
            url = f"{SURECHEMBL_BASE_URL}/chemical/id/{surechembl_id}"
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") != "OK" or not data.get("data"):
                return json.dumps({"error": f"SureChEMBL ID '{surechembl_id}' not found"})
            
            chem = data["data"][0]
            
            result = {
                # Core Identifiers
                "surechembl_id": chem.get("chemical_id"),
                "name": chem.get("name"),
                "smiles": chem.get("smiles"),
                "inchi": chem.get("inchi"),
                "inchikey": chem.get("inchi_key"),
                "molecular_formula": chem.get("mol_formula"),
                "molecular_weight": chem.get("mol_weight"),
                
                # Patent Frequency
                "global_frequency": chem.get("global_frequency"),
                
                # Physical/Chemical Properties
                "logp": chem.get("log_p"),
                "polar_surface_area": chem.get("psa"),  # PSA (TPSA)
                "heavy_atoms": chem.get("heavy_atoms"),
                
                # Hydrogen Bonding
                "h_bond_donors": chem.get("hbd"),  # HBD not donor_count
                "h_bond_acceptors": chem.get("hba"),  # HBA not accept_count
                
                # Structural Features
                "rotatable_bonds": chem.get("rtb"),  # RTB not rotatable_bond_count
                "aromatic_rings": chem.get("aromatic_rings"),
                
                # Drug-likeness Assessments
                "num_ro5_violations": chem.get("num_ro5_violations"),  # Lipinski's Rule of 5
                "ro3_pass": chem.get("ro3_pass") == 1,  # Rule of 3 (fragment-like)
                "qed_weighted": chem.get("qed_weighted"),  # Quantitative Estimate of Drug-likeness
                
                # Flags
                "is_organic": chem.get("organic") == 1,
                "is_element": chem.get("is_element") == 1
            }
            
            result_str = json.dumps(result, indent=2)
            cache_manager.set(cache_key, result_str, ttl=None)
            return result_str
            
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": f"SureChEMBL API error: {e.response.status_code}"})
    except Exception as e:
        return json.dumps({"error": f"Chemical lookup failed: {str(e)}"})


async def get_patent_document_content(patent_id: str) -> str:
    """
    Get full patent document content including title, abstract, and description.
    
    Endpoint: /api/document/{docid}/contents
    
    Args:
        patent_id: Patent ID (e.g., "WO-2020096695-A1", "EP-0008067-B1")
    """
    cache_key = f"surechembl:doc:{patent_id}"
    cached = cache_manager.get(cache_key)
    if cached:
        return cached
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:  # Longer timeout for document content
            url = f"{SURECHEMBL_BASE_URL}/document/{patent_id}/contents"
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            
            if not data.get("data"):
                return json.dumps({"error": f"Patent '{patent_id}' not found"})
            
            doc_data = data["data"]["contents"]["patentDocument"]
            biblio = doc_data.get("bibliographicData", {})
            
            # Extract title (English if available)
            titles = biblio.get("technicalData", {}).get("inventionTitles", [])
            title = next((t["title"] for t in titles if t.get("lang") == "EN"), "No title")
            
            # Extract abstract (English if available)
            abstracts = doc_data.get("abstracts", [])
            abstract = ""
            for ab in abstracts:
                if ab.get("lang") == "EN":
                    abstract = ab.get("section", {}).get("content", "")
                    break
            
            # Extract description (English if available) - truncate to avoid huge responses
            descriptions = doc_data.get("descriptions", [])
            description = ""
            for desc in descriptions:
                if desc.get("lang") == "EN":
                    full_desc = desc.get("section", {}).get("content", "")
                    description = full_desc[:1000] + ("..." if len(full_desc) > 1000 else "")
                    break
            
            result = {
                "patent_id": data["data"]["doc_id"],
                "title": title,
                "abstract": abstract,
                "description_excerpt": description,
                "publication_date": biblio.get("publicationReference", [{}])[0].get("date"),
                "url": f"https://www.surechembl.org/document/{patent_id}"
            }
            
            result_str = json.dumps(result, indent=2)
            cache_manager.set(cache_key, result_str, ttl=None)
            return result_str
            
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return json.dumps({"error": f"Patent '{patent_id}' not found (404)"})
        return json.dumps({"error": f"SureChEMBL API error: {e.response.status_code}"})
    except Exception as e:
        logger.error(f"Patent content fetch error: {e}")
        return json.dumps({"error": f"Patent content fetch failed: {str(e)}"})


async def get_patent_family_members(patent_id: str) -> str:
    """
    Get all family members of a patent (related patents across different jurisdictions).
    
    Endpoint: /api/document/{docid}/family/members
    
    Args:
        patent_id: Patent ID (e.g., "EP-0008067-B1")
    """
    cache_key = f"surechembl:family:{patent_id}"
    cached = cache_manager.get(cache_key)
    if cached:
        return cached
    
    try:
        async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT) as client:
            url = f"{SURECHEMBL_BASE_URL}/document/{patent_id}/family/members"
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            
            if not data.get("data"):
                return json.dumps({"error": f"Patent family for '{patent_id}' not found"})
            
            # Extract family members
            family_data = data["data"].get(patent_id, {})
            members = family_data.get("members", [])
            
            # Get just the patent IDs
            member_ids = []
            for member in members:
                member_ids.extend(member.keys())
            
            result = {
                "patent_id": patent_id,
                "family_size": len(member_ids),
                "family_members": member_ids[:50],  # Limit to 50 to avoid huge responses
                "note": f"Showing {min(50, len(member_ids))} of {len(member_ids)} family members"
            }
            
            result_str = json.dumps(result, indent=2)
            cache_manager.set(cache_key, result_str, ttl=None)
            return result_str
            
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return json.dumps({"error": f"Patent '{patent_id}' not found (404)"})
        return json.dumps({"error": f"SureChEMBL API error: {e.response.status_code}"})
    except Exception as e:
        return json.dumps({"error": f"Patent family lookup failed: {str(e)}"})


async def get_chemical_image_url(smiles: str, width: int = 300, height: int = 300) -> dict:
    """
    Generate and fetch a chemical structure image from SMILES notation.
    
    For multimodal models: Returns base64 encoded image that can be directly
    passed to the LLM in HumanMessage content.
    
    Endpoint: /api/service/chemical/image
    
    Args:
        smiles: SMILES notation of the chemical structure
        width: Image width in pixels (default: 300)
        height: Image height in pixels (default: 300)
    
    Returns:
        Dict with base64 encoded PNG image for multimodal LLM consumption:
        {
            "type": "image",
            "smiles": "CCO",
            "image_base64": "iVBORw0KGgo...",
            "image_url_format": "data:image/png;base64,{image_base64}",
            "width": 300,
            "height": 300
        }
    """
    import base64
    
    try:
        encoded_smiles = urllib.parse.quote(smiles, safe='')
        
        image_url = f"{SURECHEMBL_BASE_URL}/service/chemical/image?height={height}&width={width}&structure={encoded_smiles}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(image_url)
            response.raise_for_status()
            
            # Convert to base64
            image_bytes = response.content
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
            result = {
                "type": "image",
                "smiles": smiles,
                "image_base64": image_base64,
                "image_url_format": f"data:image/png;base64,{image_base64}",
                "width": width,
                "height": height,
                "note": "Image is base64 encoded and ready for multimodal LLM. Use 'image_url_format' in HumanMessage content."
            }
            
            return result
        
    except httpx.HTTPStatusError as e:
        return {"error": f"SureChEMBL API error ({e.response.status_code}): Failed to fetch image for SMILES '{smiles}'"}
    except Exception as e:
        return {"error": f"Image generation failed: {str(e)}"}
