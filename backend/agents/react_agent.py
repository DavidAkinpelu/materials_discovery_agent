import json
import asyncio
import logging
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain.tools import tool
from typing import Dict, List
from datetime import datetime
from config import settings

from tools.exa_search import exa_search_tool
from tools.materials_project import execute_mp_search
from tools.pubchem import execute_pubchem_search
from tools.materials_project import get_mp_statistics
from tools.surechembl import (
    search_patents_tool,
    search_similar_structures_tool,
    get_chemical_frequency_tool,
    get_chemical_by_name,
    get_chemical_by_id,
    get_patent_document_content,
    get_patent_family_members,
    get_chemical_image_url
)
from prompts import REACT_AGENT_SYSTEM_PROMPT
from models.tool_schemas import (
    WebSearchInput,
    MaterialsProjectSearchInput,
    FieldStatsInput,
    PubChemSearchInput,
    PatentSearchInput,
    SimilarStructuresInput,
    ChemicalFrequencyInput,
    ChemicalByNameInput,
    ChemicalByIdInput,
    PatentDocumentInput,
    PatentFamilyInput,
    ChemicalImageInput
)

logger = logging.getLogger(__name__)

llm = ChatOpenAI(
    model=settings.MODEL_NAME,
    api_key=settings.OPENAI_API_KEY,
    temperature=settings.MODEL_TEMPERATURE
)

@tool(args_schema=WebSearchInput)
async def web_search(
    query: str,
    num_results: int = 5,
    type: str = "auto",
    include_domains: List[str] = None,
    exclude_domains: List[str] = None,
    start_published_date: str = None,
    end_published_date: str = None
) -> str:
    """Search the web for general information, concepts, prices, or validation.
    
    Args:
        query: Search query string
        num_results: Number of results (1-100, default 5)
        type: Search type - 'keyword' (Google-like), 'neural' (semantic), or 'auto' (intelligent mix)
        include_domains: List of domains to include (e.g., ['arxiv.org', 'nature.com'])
        exclude_domains: List of domains to exclude
        start_published_date: Start date for content (ISO 8601 format: '2023-01-01T00:00:00.000Z')
        end_published_date: End date for content (ISO 8601 format)
    
    Returns:
        JSON string with search results including titles, URLs, snippets, and metadata
    """
    search_kwargs = {'num_results': num_results, 'type': type}
    if include_domains:
        search_kwargs['include_domains'] = include_domains
    if exclude_domains:
        search_kwargs['exclude_domains'] = exclude_domains
    if start_published_date:
        search_kwargs['start_published_date'] = start_published_date
    if end_published_date:
        search_kwargs['end_published_date'] = end_published_date
    
    result = await exa_search_tool(query, **search_kwargs)
    return result if isinstance(result, str) else json.dumps(result, indent=2)

@tool(args_schema=MaterialsProjectSearchInput)
async def search_materials_project(
    criteria: str,
    fields: List[str] = None,
    limit: int = 20,
    include_gnome: bool = True
) -> str:
    """Search Materials Project database for inorganic materials with computed properties.
    
    The Materials Project contains 170k+ experimentally known materials plus 380k+ from Google's
    GNoME dataset (predicted stable materials). Use tuple syntax [min, max] for numeric ranges.
    
    Args:
        criteria: JSON string with search criteria using tuples [min, max] for ranges
        fields: List of fields to return (default: ["material_id", "formula_pretty", "band_gap", "density", "formation_energy"])
        limit: Maximum number of results (default: 20)
        include_gnome: Include GNoME dataset materials (default: true)
    
    Returns:
        JSON string with matching materials and their properties
    
    Examples:
        1. Stable Li-Fe-O battery materials:
           criteria='{"elements": ["Li", "Fe", "O"], "energy_above_hull": [0, 0.05]}'
        
        2. Wide bandgap semiconductors:
           criteria='{"band_gap": [3.0, 5.0], "is_gap_direct": true}'
        
        3. Hard ceramic materials:
           criteria='{"k_vrh": [300, 500], "elements": ["B", "C", "N", "O"]}'
           fields=["material_id", "formula_pretty", "k_vrh", "g_vrh", "density"]
        
        4. Magnetic materials:
           criteria='{"total_magnetization": [1.0, 10.0], "magnetic_ordering": "FM"}'
           fields=["material_id", "formula_pretty", "total_magnetization", "magnetic_ordering"]
    """
    try:
        search_criteria = json.loads(criteria)
        
        if fields is None:
            fields = ["material_id", "formula_pretty", "band_gap", "density", "formation_energy"]
        
        search_criteria["include_gnome"] = include_gnome
        
        params = {
            "criteria": search_criteria,
            "fields": fields,
            "limit": limit
        }
        
        results = await execute_mp_search(params)
        return json.dumps(results, indent=2)
    except json.JSONDecodeError as e:
        return json.dumps({"error": f"Invalid JSON in criteria: {str(e)}"})
    except Exception as e:
        return json.dumps({"error": f"Search failed: {str(e)}"})

@tool(args_schema=FieldStatsInput)
async def get_field_stats(field: str) -> str:
    """Get statistical distribution of a Materials Project field to understand typical values."""
    result = await get_mp_statistics(field)
    return result if isinstance(result, str) else json.dumps(result, indent=2)

@tool(args_schema=PubChemSearchInput)
async def search_pubchem(
    compound: str,
    search_type: str = "name",
    include_synonyms: bool = False
) -> str:
    """Search PubChem for organic compounds, polymers, and molecular properties.
    
    PubChem contains 110M+ compounds with computed properties including:
    - Molecular identifiers (SMILES, InChI, InChIKey)
    - Drug-likeness descriptors (XLogP, TPSA, H-bond counts)
    - Structural features (stereocenters, rotatable bonds)
    - 3D conformer data (volume, RMSD)
    
    Args:
        compound: Identifier (name, CID, formula, SMILES, or InChIKey)
        search_type: Type of identifier - "name", "cid", "formula", "smiles", or "inchikey"
        include_synonyms: Include list of alternative names (default: false)
    
    Returns:
        JSON string with comprehensive compound data
    
    Examples:
        1. By name:
           compound="aspirin", search_type="name"
        
        2. By CID:
           compound="2244", search_type="cid"
        
        3. By SMILES with synonyms:
           compound="CCO", search_type="smiles", include_synonyms=true
        
        4. By formula (finds all isomers):
           compound="C9H8O4", search_type="formula"
    """
    query = {
        "compound": compound,
        "type": search_type,
        "include_synonyms": include_synonyms
    }
    result = await execute_pubchem_search(query)
    return json.dumps(result, indent=2)

@tool(args_schema=PatentSearchInput)
async def search_patents(query: str) -> str:
    """Search SureChEMBL patent database for materials and applications."""
    result = await search_patents_tool(query)
    return result if isinstance(result, str) else json.dumps(result, indent=2)

@tool(args_schema=SimilarStructuresInput)
async def search_similar_structures(smiles: str, threshold: float = 0.7) -> str:
    """Find structurally similar chemicals in patents using SMILES notation."""
    result = await search_similar_structures_tool(smiles, threshold)
    return result if isinstance(result, str) else json.dumps(result, indent=2)

@tool(args_schema=ChemicalFrequencyInput)
async def get_chemical_frequency(compound_name: str) -> str:
    """Get frequency statistics for a chemical across the patent database."""
    result = await get_chemical_frequency_tool(compound_name)
    return result if isinstance(result, str) else json.dumps(result, indent=2)

@tool(args_schema=ChemicalByNameInput)
async def lookup_chemical_by_name(chemical_name: str) -> str:
    """Look up chemical by name in SureChEMBL to get SMILES, InChI, and basic properties.
    
    Returns: SureChEMBL ID, SMILES, InChI, molecular weight, patent frequency.
    Note: For comprehensive drug-likeness data, use lookup_chemical_by_id() with the returned ID.
    """
    result = await get_chemical_by_name(chemical_name)
    return result if isinstance(result, str) else json.dumps(result, indent=2)

@tool(args_schema=ChemicalByIdInput)
async def lookup_chemical_by_id(surechembl_id: str) -> str:
    """Get comprehensive chemical data by SureChEMBL ID.
    
    Returns full molecular properties including:
    - SMILES, InChI, molecular formula, molecular weight
    - LogP, polar surface area, heavy atoms
    - H-bond donors/acceptors, rotatable bonds, aromatic rings
    - Drug-likeness: QED score, Lipinski violations, Rule of 3 compliance
    - Patent frequency and organic/element flags
    """
    result = await get_chemical_by_id(surechembl_id)
    return result if isinstance(result, str) else json.dumps(result, indent=2)

@tool(args_schema=PatentDocumentInput)
async def get_patent_content(patent_id: str) -> str:
    """Get full patent document content including title, abstract, and description.
    
    Use this to read patent text for detailed invention analysis.
    Patent ID format: {COUNTRY}-{NUMBER}-{KIND}, e.g., "WO-2020096695-A1"
    """
    result = await get_patent_document_content(patent_id)
    return result if isinstance(result, str) else json.dumps(result, indent=2)

@tool(args_schema=PatentFamilyInput)
async def get_patent_family(patent_id: str) -> str:
    """Get all family members of a patent across different jurisdictions.
    
    Use this to assess global IP coverage for an invention.
    Shows same invention filed in multiple countries (up to 50 members).
    """
    result = await get_patent_family_members(patent_id)
    return result if isinstance(result, str) else json.dumps(result, indent=2)

@tool(args_schema=ChemicalImageInput)
async def visualize_chemical_structure(smiles: str, width: int = 300, height: int = 300) -> dict:
    """Fetch chemical structure image from SMILES notation for multimodal analysis.
    
    Returns base64 encoded PNG image that can be directly viewed by multimodal models.
    Use this to visually analyze:
    - Molecular structure and connectivity
    - Stereochemistry (chiral centers, E/Z isomers)
    - Ring systems (aromatic, aliphatic)
    - Functional groups
    - Spatial arrangement
    
    The returned image can be passed to the LLM using HumanMessage with image_url content.
    
    Args:
        smiles: SMILES notation (e.g., "CCO" for ethanol, "c1ccccc1" for benzene)
        width: Image width in pixels (50-1000, default: 300)
        height: Image height in pixels (50-1000, default: 300)
    
    Returns:
        Dict with base64 encoded image ready for multimodal LLM
    
    Example: "CCO" → Returns base64 PNG of ethanol structure
    """
    result = await get_chemical_image_url(smiles, width, height)
    return result

def create_materials_agent(checkpointer=None, store=None):
    """
    Create a ReAct agent for materials discovery using LangGraph
    
    Args:
        checkpointer: Short-term memory for conversation history (SQLite)
        store: Long-term memory for persistent user information (SQLite)
    """
    
    system_prompt_text = REACT_AGENT_SYSTEM_PROMPT.format(
        current_datetime=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    
    tools = [
        web_search,
        search_materials_project,
        get_field_stats,
        search_pubchem,
        search_patents,
        search_similar_structures,
        get_chemical_frequency,
        lookup_chemical_by_name,
        lookup_chemical_by_id,
        get_patent_content,
        get_patent_family,
        visualize_chemical_structure
    ]
    
    
    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=system_prompt_text,
        checkpointer=checkpointer,
        store=store
    )
    
    logger.info("LangGraph ReAct agent created successfully with memory support and system prompt")
    return agent

