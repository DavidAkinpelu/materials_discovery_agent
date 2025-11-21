import httpx
from utils.cache import cache_manager
import json
from urllib.parse import quote

PUBCHEM_BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"


async def execute_pubchem_search(query_params: dict) -> dict:
    """
    Search PubChem for comprehensive compound data.
    
    Retrieves molecular properties, identifiers, drug-likeness descriptors,
    and optionally synonyms for organic compounds and polymers.
    
    Args:
        query_params: Dict with:
            - 'compound': identifier string
            - 'type': namespace (name/cid/formula/smiles/inchikey)
            - 'include_synonyms': bool (optional, default False)
    
    Returns:
        Dict with compound properties, identifiers, descriptors, and optional synonyms
    """
    
    compound = query_params.get('compound')
    search_type = query_params.get('type', 'name')
    include_synonyms = query_params.get('include_synonyms', False)
    
    if not compound:
        return {"error": "No compound identifier provided"}
    
    cache_key = f"pubchem:{search_type}:{compound}:syn={include_synonyms}"
    cached = cache_manager.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Comprehensive list of properties to retrieve
    properties = [
        # Core Identifiers
        "MolecularFormula",
        "MolecularWeight",
        "CanonicalSMILES",
        "IsomericSMILES",
        "InChI",
        "InChIKey",
        "IUPACName",
        "Title",
        
        # Drug-likeness & ADME Properties
        "XLogP",  # Lipophilicity
        "ExactMass",
        "MonoisotopicMass",
        "TPSA",  # Topological Polar Surface Area
        "Complexity",
        
        # Hydrogen Bonding
        "HBondDonorCount",
        "HBondAcceptorCount",
        
        # Structural Features
        "RotatableBondCount",
        "HeavyAtomCount",
        "AtomStereoCount",
        "DefinedAtomStereoCount",
        "BondStereoCount",
        "DefinedBondStereoCount",
        "CovalentUnitCount",
        
        # Electronic Properties
        "Charge",
        
        # 3D Conformer Properties (if available)
        "Volume3D",
        "ConformerModelRMSD3D",
        "ConformerCount3D"
    ]
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            encoded_compound = quote(compound, safe='')
            properties_str = ",".join(properties)
            
            # Get properties
            url = f"{PUBCHEM_BASE}/compound/{search_type}/{encoded_compound}/property/{properties_str}/JSON"
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            
            if "PropertyTable" not in data or "Properties" not in data["PropertyTable"]:
                return {"error": "No compound data found in PubChem response"}
            
            props = data["PropertyTable"]["Properties"][0]
            
            result = {
                "cid": props.get("CID"),
                "compound_name": props.get("IUPACName") or props.get("Title") or compound,
                "molecular_formula": props.get("MolecularFormula"),
                "molecular_weight": props.get("MolecularWeight"),
                "exact_mass": props.get("ExactMass"),
                "monoisotopic_mass": props.get("MonoisotopicMass"),
                
                "canonical_smiles": props.get("CanonicalSMILES"),
                "isomeric_smiles": props.get("IsomericSMILES"),
                "inchi": props.get("InChI"),
                "inchikey": props.get("InChIKey"),
                
                "xlogp": props.get("XLogP"),
                "tpsa": props.get("TPSA"),
                "complexity": props.get("Complexity"),
                
                "h_bond_donors": props.get("HBondDonorCount"),
                "h_bond_acceptors": props.get("HBondAcceptorCount"),
                
                "rotatable_bonds": props.get("RotatableBondCount"),
                "heavy_atoms": props.get("HeavyAtomCount"),
                "atom_stereo_count": props.get("AtomStereoCount"),
                "defined_atom_stereo_count": props.get("DefinedAtomStereoCount"),
                "bond_stereo_count": props.get("BondStereoCount"),
                "defined_bond_stereo_count": props.get("DefinedBondStereoCount"),
                "covalent_units": props.get("CovalentUnitCount"),
                
                "charge": props.get("Charge"),
                
                "volume_3d": props.get("Volume3D"),
                "conformer_rmsd_3d": props.get("ConformerModelRMSD3D"),
                "conformer_count_3d": props.get("ConformerCount3D")
            }
            
            if include_synonyms:
                try:
                    syn_url = f"{PUBCHEM_BASE}/compound/{search_type}/{encoded_compound}/synonyms/JSON"
                    syn_response = await client.get(syn_url)
                    syn_response.raise_for_status()
                    syn_data = syn_response.json()
                    
                    if "InformationList" in syn_data and "Information" in syn_data["InformationList"]:
                        info = syn_data["InformationList"]["Information"][0]
                        synonyms = info.get("Synonym", [])
                        result["synonyms"] = synonyms[:20]
                        if len(synonyms) > 20:
                            result["total_synonyms"] = len(synonyms)
                except Exception as e:
                    result["synonyms_error"] = f"Could not fetch synonyms: {str(e)}"
            
            result_json = json.dumps(result)
            cache_manager.set(cache_key, result_json, ttl=None)
            
            return result
            
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {"error": f"Compound '{compound}' not found in PubChem (404)"}
        else:
            return {"error": f"PubChem API error: {e.response.status_code} - {e.response.text}"}
    except Exception as e:
        return {"error": f"PubChem search failed: {str(e)}"}

