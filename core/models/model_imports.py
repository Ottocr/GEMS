from django.apps import apps
from django.utils.module_loading import import_string

def get_model(app_label, model_name):
    try:
        return apps.get_model(app_label, model_name)
    except:
        return import_string(f"{app_label}.models.{model_name}")

def get_risk_type_model():
    return get_model('core', 'RiskType')

def get_country_model():
    return get_model('core', 'Country')

def get_baseline_threat_assessment_model():
    return get_model('core', 'BaselineThreatAssessment')

def get_final_risk_matrix_model():
    return get_model('core', 'FinalRiskMatrix')

def get_risk_log_model():
    return get_model('core', 'RiskLog')

def get_risk_scenario_assessment_model():
    return get_model('core', 'RiskScenarioAssessment')

def get_barrier_model():
    return get_model('core', 'Barrier')

def get_barrier_issue_report_model():
    return get_model('core', 'BarrierIssueReport')

def get_asset_model():
    return get_model('core', 'Asset')