"""Pydantic schemas for tool inputs to make parameters explicit for the LLM."""

from pydantic import BaseModel, Field
from typing import Dict, List, Literal, Optional, Any


class WebSearchInput(BaseModel):
    """Input for web search queries using Exa."""
    query: str = Field(
        description="Search query for web results, concepts, prices, or validation"
    )
    num_results: int = Field(
        default=5,
        ge=1,
        le=100,
        description="Number of results to return (max 10 for keyword, 100 for neural)"
    )
    type: Literal["keyword", "neural", "auto"] = Field(
        default="auto",
        description="Search type: 'keyword' (Google-like), 'neural' (embeddings), or 'auto' (intelligent mix)"
    )
    include_domains: Optional[List[str]] = Field(
        default=None,
        description="List of domains to include (e.g., ['arxiv.org', 'nature.com'])"
    )
    exclude_domains: Optional[List[str]] = Field(
        default=None,
        description="List of domains to exclude"
    )
    start_published_date: Optional[str] = Field(
        default=None,
        description="Start date for published content (ISO 8601 format: '2023-01-01T00:00:00.000Z')"
    )
    end_published_date: Optional[str] = Field(
        default=None,
        description="End date for published content (ISO 8601 format)"
    )


class MaterialsProjectSearchInput(BaseModel):
    """Input for Materials Project database search.
    
    The Materials Project API uses tuples [min, max] for numeric ranges.
    For exact values, use a single value (not a tuple).
    """
    criteria: str = Field(
        description="""JSON string with search criteria for inorganic materials.

IMPORTANT: Use tuples [min, max] for numeric ranges, not dict queries.

Common Search Fields:

1. Composition & Structure:
   - elements: List of elements, e.g., ["Li", "Fe", "O"]
   - exclude_elements: List of elements to exclude, e.g., ["Pb", "Cd"]
   - num_elements: Range [min, max] or exact number, e.g., [2, 4] or 3
   - num_sites: [min, max] - Number of atoms in unit cell
   - formula: Formula pattern, e.g., "Fe2O3" or "ABO3" (wildcard)
   - chemsys: Chemical system, e.g., "Li-Fe-O" or list ["Li-Fe-O", "Si-O"]
   - crystal_system: "cubic", "hexagonal", "tetragonal", "orthorhombic", "monoclinic", "triclinic", "trigonal"
   - spacegroup_number: Space group number, e.g., 225 or list [221, 225]
   - spacegroup_symbol: Space group symbol, e.g., "Fm-3m" or list ["Fm-3m", "P63/mmc"]
   - possible_species: List of element+oxidation, e.g., ["Cr2+", "O2-"]

2. Stability & Energy (all in eV/atom unless noted):
   - energy_above_hull: [min, max], e.g., [0, 0.05] for stable materials
   - formation_energy: [min, max], e.g., [-5.0, -1.0] for stable
   - total_energy: [min, max] - Corrected total energy
   - uncorrected_energy: [min, max] - Raw DFT total energy
   - equilibrium_reaction_energy: [min, max] - Equilibrium reaction energy
   - is_stable: true/false - whether on the convex hull

3. Electronic Properties:
   - band_gap: [min, max] in eV, e.g., [1.5, 3.0] for semiconductors
   - is_gap_direct: true/false - direct vs indirect gap
   - is_metal: true/false - metallic character
   - efermi: [min, max] - Fermi energy in eV

4. Mechanical Properties (all in GPa unless noted):
   - k_vrh: [min, max] - Bulk modulus (Voigt-Reuss-Hill average)
   - g_vrh: [min, max] - Shear modulus (Voigt-Reuss-Hill average)
   - k_reuss: [min, max] - Bulk modulus (Reuss bound)
   - k_voigt: [min, max] - Bulk modulus (Voigt bound)
   - g_reuss: [min, max] - Shear modulus (Reuss bound)
   - g_voigt: [min, max] - Shear modulus (Voigt bound)
   - elastic_anisotropy: [min, max] - Elastic anisotropy (dimensionless)
   - poisson_ratio: [min, max] - Poisson's ratio (dimensionless)

5. Physical Properties:
   - density: [min, max] in g/cm³, e.g., [2.0, 4.0]
   - volume: [min, max] in Ų per atom
   - shape_factor: [min, max] - Shape factor (dimensionless)

6. Dielectric & Optical Properties:
   - e_total: [min, max] - Total dielectric constant
   - e_electronic: [min, max] - Electronic component
   - e_ionic: [min, max] - Ionic component
   - n: [min, max] - Refractive index
   - piezoelectric_modulus: [min, max] - Piezoelectric modulus in C/m²

7. Magnetic Properties:
   - total_magnetization: [min, max] in μB - Total magnetization
   - total_magnetization_normalized_formula_units: [min, max] - Per formula unit
   - total_magnetization_normalized_vol: [min, max] - Per volume
   - magnetic_ordering: "FM", "AFM", "FiM", "NM" - Magnetic ordering type
   - num_magnetic_sites: [min, max] - Number of magnetic sites
   - num_unique_magnetic_sites: [min, max] - Number of unique magnetic sites

8. Surface Properties:
   - has_reconstructed: true/false - Has reconstructed surfaces
   - surface_energy_anisotropy: [min, max] - Surface energy anisotropy
   - weighted_surface_energy: [min, max] in J/m² - Weighted surface energy
   - weighted_work_function: [min, max] in eV - Weighted work function

9. Data Availability & Filters:
   - material_ids: Single ID "mp-149" or list ["mp-149", "mp-13"]
   - has_props: List of properties, e.g., ["elasticity", "dielectric", "piezoelectric"]
   - theoretical: true/false - Experimental vs computational
   - deprecated: false - Exclude deprecated entries

Example Queries:

1. Stable lithium battery materials:
   {"elements": ["Li", "Fe", "O"], "num_elements": [2, 4], "energy_above_hull": [0, 0.05]}

2. Wide bandgap semiconductors:
   {"band_gap": [3.0, 5.0], "is_gap_direct": true, "is_stable": true}

3. Hard ceramic materials:
   {"elements": ["B", "C", "N", "O"], "k_vrh": [300, 500], "density": [3.0, 4.0]}

4. High-density metals:
   {"is_metal": true, "density": [10.0, 25.0], "is_stable": true}

5. Transparent conductors:
   {"band_gap": [2.5, 4.0], "n": [1.5, 2.5], "is_stable": true}
"""
    )
    fields: List[str] = Field(
        default=["material_id", "formula_pretty", "band_gap", "density", "formation_energy"],
        description="""Fields to return in results. Common fields:

Core: material_id, formula_pretty, composition, num_elements, num_sites
Energy: formation_energy, energy_above_hull, total_energy, is_stable, equilibrium_reaction_energy
Electronic: band_gap, is_metal, is_gap_direct, efermi
Mechanical: k_vrh, g_vrh, k_reuss, k_voigt, g_reuss, g_voigt, elastic_anisotropy, poisson_ratio
Physical: density, volume, shape_factor
Dielectric: e_total, e_electronic, e_ionic, n, piezoelectric_modulus
Magnetic: total_magnetization, magnetic_ordering, num_magnetic_sites
Surface: surface_energy_anisotropy, weighted_surface_energy, weighted_work_function, has_reconstructed
Structure: crystal_system, spacegroup_number, spacegroup_symbol, symmetry

Note: Use 'num_elements' not 'nelements' (deprecated)
"""
    )
    include_gnome: bool = Field(
        default=True,
        description="Whether to include materials from GNoME dataset (Google's 380k+ new materials)"
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=1000,
        description="Maximum number of results to return"
    )


class FieldStatsInput(BaseModel):
    """Input for getting field statistics from Materials Project."""
    field: str = Field(
        description="""Field name to get statistics for. Common fields:
- band_gap: Electronic band gap (eV)
- density: Material density (g/cm³)
- formation_energy: Formation energy (eV/atom)
- energy_above_hull: Thermodynamic stability (eV/atom)
- bulk_modulus: Bulk modulus (GPa)
- shear_modulus: Shear modulus (GPa)
- efermi: Fermi energy (eV)

Use this to understand typical value ranges before searching.
"""
    )


class PubChemSearchInput(BaseModel):
    """Input for PubChem compound search.
    
    PubChem contains 110M+ compounds with computed properties, bioassay data,
    safety information, and patent references.
    """
    compound: str = Field(
        description="""Compound identifier (format depends on search_type).
        
Examples:
- name: "aspirin", "caffeine", "ethanol"
- cid: "2244", "2519", "702"
- formula: "C9H8O4", "C8H10N4O2", "C2H6O"
- smiles: "CC(=O)Oc1ccccc1C(=O)O", "CCO"
- inchikey: "BSYNRYMUTXBXSQ-UHFFFAOYSA-N"
"""
    )
    search_type: Literal["name", "cid", "formula", "smiles", "inchikey"] = Field(
        default="name",
        description="""Type of search to perform:
        
- name: Common/IUPAC chemical name (most flexible)
- cid: PubChem Compound ID (exact, fastest)
- formula: Molecular formula (finds all isomers)
- smiles: SMILES structure notation (exact structure)
- inchikey: InChI Key (exact, canonical identifier)
"""
    )
    include_synonyms: bool = Field(
        default=False,
        description="Include list of synonyms/alternative names for the compound"
    )


class PatentSearchInput(BaseModel):
    """Input for SureChEMBL patent database search."""
    query: str = Field(
        description="""Query to search for materials and applications in patent database.
        
Tips:
- Use specific chemical names or material types
- Include application context (e.g., "battery", "adhesive", "solar cell")
- Combine terms with AND/OR for better results
- Use quotes for exact phrases

Example: "lithium iron phosphate" AND battery
"""
    )


class SimilarStructuresInput(BaseModel):
    """Input for finding similar chemical structures in patents."""
    smiles: str = Field(
        description="""SMILES notation of the chemical structure to search for similar compounds.
        
SMILES (Simplified Molecular Input Line Entry System) is a text representation of molecular structures.
Example: 'CCO' for ethanol, 'c1ccccc1' for benzene
"""
    )
    threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Similarity threshold between 0.0 (any match) and 1.0 (exact match). Higher = more similar."
    )


class ChemicalFrequencyInput(BaseModel):
    """Input for getting chemical frequency statistics."""
    compound_name: str = Field(
        description="""Name of the chemical to check frequency across patent database.
        
This tells you how often a compound appears in patents:
- High frequency: Well-established, widely used
- Low frequency: Novel, less explored
- Zero frequency: Not found in patents (potentially novel or too new)
"""
    )


class ChemicalByNameInput(BaseModel):
    """Input for getting detailed chemical information by name from SureChEMBL."""
    chemical_name: str = Field(
        description="""Chemical name to look up (e.g., "imidazole", "aspirin", "imatinib").
        
Returns comprehensive information including:
- SMILES, InChI, InChI Key
- Molecular weight
- Patent frequency (how common in patents)
- Drug-likeness properties (Lipinski compliance, logP, H-bond counts)
- Structural features (rings, rotatable bonds)

Example names: "imidazole", "aspirin", "dopamine", "imatinib"
"""
    )


class ChemicalByIdInput(BaseModel):
    """Input for getting chemical information by SureChEMBL ID."""
    surechembl_id: str = Field(
        description="""SureChEMBL chemical ID (numeric string).
        
Example IDs: "897", "3827", "21442"

Returns all molecular properties plus drug-likeness assessment:
- Lipinski compliance (oral bioavailability rule)
- Lead-likeness (drug development potential)
- Bioavailability indicators
"""
    )


class PatentDocumentInput(BaseModel):
    """Input for getting full patent document content."""
    patent_id: str = Field(
        description="""Patent document ID in format: {COUNTRY}-{NUMBER}-{KIND}
        
Examples:
- "WO-2020096695-A1" (WIPO application)
- "EP-0008067-B1" (European Patent)  
- "US-123456-A1" (US Patent Application)

Returns:
- Full title
- Abstract (English)
- Description excerpt (first 1000 chars)
- Publication date
- Direct link to document
"""
    )


class PatentFamilyInput(BaseModel):
    """Input for getting patent family members."""
    patent_id: str = Field(
        description="""Patent ID to find family members for.
        
Format: {COUNTRY}-{NUMBER}-{KIND}
Example: "EP-0008067-B1"

Returns all related patents across different jurisdictions:
- Same invention filed in multiple countries
- Useful to assess global IP coverage
- Shows up to 50 family members
"""
    )


class ChemicalImageInput(BaseModel):
    """Input for generating chemical structure image URL.
    
    For multimodal models: Returns URL to view/analyze chemical structure visually.
    """
    smiles: str = Field(
        description="""SMILES notation to visualize.
        
Examples:
- "CCO" (ethanol)
- "C1CCCCC1" (cyclohexane)
- "c1ccccc1" (benzene)
- "CC(=O)Oc1ccccc1C(=O)O" (aspirin)

Use this when you need to:
- Visually inspect molecular structure
- Verify stereochemistry
- Check ring systems
- Analyze functional groups
"""
    )
    width: int = Field(
        default=300,
        ge=50,
        le=1000,
        description="Image width in pixels (default: 300, range: 50-1000)"
    )
    height: int = Field(
        default=300,
        ge=50,
        le=1000,
        description="Image height in pixels (default: 300, range: 50-1000)"
    )

