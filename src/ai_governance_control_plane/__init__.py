"""AI Governance Control Plane prototype."""

from .applicability import ControlRecommendationSet, RecommendationError, recommend_controls
from .inventory import (
    InventoryRepository,
    SessionInventoryRepository,
    SQLiteInventoryRepository,
    add_seed_history,
)
from .models import AISystem, Assessment, AssessmentHistoryRecord, DecisionRecord, OwnerRoles
from .risk_engine import AssessmentError, evaluate_assessment, evaluate_assessment_record, load_model
from .service import DesignComparison, GovernanceDecisionService

__version__ = "0.3.0"

__all__ = [
    "Assessment",
    "AssessmentHistoryRecord",
    "AISystem",
    "AssessmentError",
    "ControlRecommendationSet",
    "DecisionRecord",
    "DesignComparison",
    "GovernanceDecisionService",
    "__version__",
    "InventoryRepository",
    "OwnerRoles",
    "RecommendationError",
    "SessionInventoryRepository",
    "SQLiteInventoryRepository",
    "add_seed_history",
    "evaluate_assessment",
    "evaluate_assessment_record",
    "load_model",
    "recommend_controls",
]
