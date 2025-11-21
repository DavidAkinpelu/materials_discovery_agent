"""Models and schemas for the Materials Discovery Agent."""

from .schemas import ChatRequest, ChatResponse
from .tool_schemas import (
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

__all__ = [
    "ChatRequest",
    "ChatResponse",
    "WebSearchInput",
    "MaterialsProjectSearchInput",
    "FieldStatsInput",
    "PubChemSearchInput",
    "PatentSearchInput",
    "SimilarStructuresInput",
    "ChemicalFrequencyInput",
    "ChemicalByNameInput",
    "ChemicalByIdInput",
    "PatentDocumentInput",
    "PatentFamilyInput",
    "ChemicalImageInput"
]

