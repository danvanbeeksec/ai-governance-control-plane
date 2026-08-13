"""AI Governance Control Plane prototype."""

from .applicability import ControlRecommendationSet, RecommendationError, recommend_controls
from .inventory import (
    InventoryRepository,
    SessionInventoryRepository,
    SQLiteInventoryRepository,
    add_seed_history,
)
from .models import AISystem, Assessment, AssessmentHistoryRecord, DecisionRecord, OwnerRoles
from .intake import AssessmentRequirements, IntakeValidationResult, ProposedInference
from .risk_engine import AssessmentError, evaluate_assessment, evaluate_assessment_record, load_model
from .service import DesignComparison, GovernanceDecisionService

__version__ = "0.5.0"

__all__ = [
    "Assessment",
    "AssessmentHistoryRecord",
    "AssessmentRequirements",
    "AISystem",
    "AssessmentError",
    "ControlRecommendationSet",
    "DecisionRecord",
    "DesignComparison",
    "GovernanceDecisionService",
    "__version__",
    "InventoryRepository",
    "IntakeValidationResult",
    "OwnerRoles",
    "ProposedInference",
    "RecommendationError",
    "SessionInventoryRepository",
    "SQLiteInventoryRepository",
    "add_seed_history",
    "evaluate_assessment",
    "evaluate_assessment_record",
    "load_model",
    "recommend_controls",
]
