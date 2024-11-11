"""
Custom template filters for the dashboard.

This module provides template filters used in the dashboard templates
to calculate and display various risk-related metrics.
"""

from django import template
from django.db.models import Avg

register = template.Library()

@register.filter
def high_risk_count(assets):
    """Count assets with high risk level (>= 7)."""
    return sum(1 for asset in assets if asset.get_risk_level() >= 7)

@register.filter
def avg_risk_score(assets):
    """Calculate average risk score across assets."""
    if not assets:
        return 0
    return sum(asset.get_risk_level() for asset in assets) / len(assets)

@register.filter
def format_risk_level(value):
    """Format risk level with appropriate color class."""
    if value >= 7:
        return 'danger'
    elif value >= 4:
        return 'warning'
    return 'success'

@register.filter
def barrier_effectiveness_class(score):
    """Get Bootstrap class for barrier effectiveness score."""
    if score >= 7:
        return 'success'
    elif score >= 4:
        return 'warning'
    return 'danger'

@register.filter
def trend_direction_class(direction):
    """Get Bootstrap class for trend direction."""
    if direction == 'up':
        return 'success'
    elif direction == 'down':
        return 'danger'
    return 'secondary'

@register.filter
def percentage_format(value):
    """Format percentage value with sign."""
    if value > 0:
        return f'+{value:.1f}%'
    return f'{value:.1f}%'

@register.filter
def risk_matrix_cell_class(likelihood, impact):
    """Get Bootstrap class for risk matrix cell."""
    risk_level = likelihood * impact
    if risk_level >= 15:  # High risk
        return 'bg-danger'
    elif risk_level >= 8:  # Medium-high risk
        return 'bg-warning'
    elif risk_level >= 4:  # Medium risk
        return 'bg-info'
    return 'bg-success'  # Low risk

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary using a key."""
    if not dictionary:
        return None
    return dictionary.get(str(key))

@register.filter
def format_date(date):
    """Format date in a consistent way."""
    if not date:
        return ''
    return date.strftime('%d %b %Y')
