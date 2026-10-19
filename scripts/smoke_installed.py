"""Run with python -I from outside the checkout after installing a built wheel."""
from ai_governance_control_plane import GovernanceDecisionService
from ai_governance_control_plane.reporting import review_brief

service = GovernanceDecisionService.from_packaged_resources()
facts = dict(assessment_id='SYNTHETIC-WHEEL-001', system_name='Fictional Wheel Check',
             business_purpose='Summarize public research for human review.', accountable_owner='Fictional Owner',
             autonomy_level='human_supervised', information_sensitivity='public',
             human_review='prior_to_each_meaningful_action', action_authority='generate_only',
             system_access='none', external_reach='none', reversibility='easy', decision_impact='none',
             agent_capabilities=[])
result = service.assess_ai_system(facts)
assert result.decision.final_tier == 'tier_3'
assert result.decision.framework_source.status == 'loaded'
assert service.get_assessment_requirements().input_schema['properties']['system_name']['maxLength'] == 200
assert 'Applicability questions' in review_brief(result)
print('Installed service and Framework passed the synthetic assessment journey')
