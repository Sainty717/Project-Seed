"""
Anonymization profiles and configuration
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum

from ..core.detector import DataType
from ..core.transformers import (
    FormatPreservingFakeTransformer,
    FPETransformer,
    SeededHMACTransformer,
    HybridTransformer,
    FormatPreservingTransformer
)


class AnonymizationMode(Enum):
    """Supported anonymization modes"""
    FORMAT_PRESERVING_FAKE = "format_preserving_fake"
    FPE = "fpe"
    SEEDED_HMAC = "seeded_hmac"
    HYBRID = "hybrid"


@dataclass
class AnonymizationProfile:
    """Configuration profile for anonymization"""
    
    name: str
    mode: AnonymizationMode
    seed: Optional[str] = None
    columns_to_anonymize: Optional[List[str]] = None
    type_overrides: Dict[str, DataType] = field(default_factory=dict)
    preserve_domain: bool = False  # For emails, preserve domain
    preserve_partial: bool = False  # Keep partial visibility (e.g., Jo** Sm**)
    fully_synthetic: bool = False  # No mapping stored
    referential_integrity: bool = False  # Cross-dataset integrity
    
    def create_transformer(
        self,
        vault=None
    ) -> FormatPreservingTransformer:
        """Create transformer based on profile settings"""
        if self.mode == AnonymizationMode.FORMAT_PRESERVING_FAKE:
            return FormatPreservingFakeTransformer(
                vault=vault if not self.fully_synthetic else None,
                seed=self.seed,
                preserve_domain=self.preserve_domain
            )
        elif self.mode == AnonymizationMode.FPE:
            return FPETransformer(
                vault=vault if not self.fully_synthetic else None,
                seed=self.seed,
                preserve_domain=self.preserve_domain
            )
        elif self.mode == AnonymizationMode.SEEDED_HMAC:
            return SeededHMACTransformer(
                vault=None,  # HMAC is not reversible
                seed=self.seed,
                preserve_domain=self.preserve_domain
            )
        elif self.mode == AnonymizationMode.HYBRID:
            return HybridTransformer(
                vault=vault if not self.fully_synthetic else None,
                seed=self.seed,
                preserve_domain=self.preserve_domain
            )
        else:
            raise ValueError(f"Unknown mode: {self.mode}")


def get_default_profiles() -> Dict[str, AnonymizationProfile]:
    """Get default anonymization profiles"""
    return {
        "default": AnonymizationProfile(
            name="Default",
            mode=AnonymizationMode.HYBRID,
            seed=None
        ),
        "gdpr_compliant": AnonymizationProfile(
            name="GDPR Compliant",
            mode=AnonymizationMode.FPE,
            seed=None,
            fully_synthetic=False  # Store mappings for reversibility
        ),
        "test_data": AnonymizationProfile(
            name="Test Data Generation",
            mode=AnonymizationMode.FORMAT_PRESERVING_FAKE,
            seed="test_seed_123",
            fully_synthetic=True
        ),
        "fast_hash": AnonymizationProfile(
            name="Fast Hash (Non-Reversible)",
            mode=AnonymizationMode.SEEDED_HMAC,
            seed=None
        ),
        "referential_integrity": AnonymizationProfile(
            name="Referential Integrity",
            mode=AnonymizationMode.HYBRID,
            seed="consistent_seed",
            referential_integrity=True
        )
    }

