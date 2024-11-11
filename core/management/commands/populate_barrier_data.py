from django.core.management.base import BaseCommand
from django.db import transaction
from core.models.barrier_models import (
    BarrierCategory, Barrier, BarrierCharacteristic,
    BarrierQuestion
)
from core.models.risk_models import RiskType

class Command(BaseCommand):
    help = 'Populates barrier categories, characteristics, and assessment questions'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write('Setting up barrier data...')

        # Ensure risk types exist
        crime_risk = RiskType.objects.get(name="Crime")
        cyber_risk = RiskType.objects.get(name="Cyber")
        insider_risk = RiskType.objects.get(name="Insider")

        # Physical Security Barriers
        physical_security = BarrierCategory.objects.create(
            name="Physical Security",
            description="Physical barriers and security measures",
            is_shareable=False
        )

        # Fence Characteristics
        fence = Barrier.objects.create(
            name="Perimeter Fence",
            description="Physical barrier around the asset perimeter",
            category=physical_security
        )

        # Fence Height
        BarrierCharacteristic.objects.create(
            name="Height",
            category=physical_security,
            description="Height of the perimeter fence",
            possible_values=[
                {"value": "2m", "label": "2 meters", "score": 3},
                {"value": "3m", "label": "3 meters", "score": 6},
                {"value": "4m", "label": "4 meters", "score": 8},
                {"value": "5m+", "label": "5 meters or higher", "score": 10}
            ],
            weight=0.3
        )

        # Fence Material
        BarrierCharacteristic.objects.create(
            name="Material",
            category=physical_security,
            description="Material of the perimeter fence",
            possible_values=[
                {"value": "chain_link", "label": "Chain Link", "score": 4},
                {"value": "welded_mesh", "label": "Welded Mesh", "score": 6},
                {"value": "palisade", "label": "Palisade", "score": 7},
                {"value": "anti_climb", "label": "Anti-Climb Steel", "score": 9}
            ],
            weight=0.3
        )

        # Fence Condition
        BarrierCharacteristic.objects.create(
            name="Condition",
            category=physical_security,
            description="Current condition of the fence",
            possible_values=[
                {"value": "poor", "label": "Poor - Multiple defects", "score": 2},
                {"value": "fair", "label": "Fair - Some defects", "score": 5},
                {"value": "good", "label": "Good - Minor wear", "score": 8},
                {"value": "excellent", "label": "Excellent - Like new", "score": 10}
            ],
            weight=0.2
        )

        # Fence Questions
        BarrierQuestion.objects.create(
            barrier=fence,
            risk_type=crime_risk,
            question_text="Is the fence equipped with anti-climb features?",
            answer_choices={
                "answers": [
                    {"choice": "Yes, full coverage", "impact": 2, "description": "Anti-climb features along entire perimeter"},
                    {"choice": "Partial coverage", "impact": 1, "description": "Anti-climb features in critical areas only"},
                    {"choice": "No", "impact": -1, "description": "No anti-climb features"}
                ]
            }
        )

        # IT Security Barriers
        it_security = BarrierCategory.objects.create(
            name="IT Security",
            description="Information technology security measures",
            is_shareable=True
        )

        # Firewall
        firewall = Barrier.objects.create(
            name="Enterprise Firewall",
            description="Network security system that monitors and controls incoming and outgoing network traffic",
            category=it_security
        )

        # Firewall Characteristics
        BarrierCharacteristic.objects.create(
            name="Type",
            category=it_security,
            description="Type of firewall implementation",
            possible_values=[
                {"value": "packet_filtering", "label": "Packet Filtering", "score": 5},
                {"value": "stateful", "label": "Stateful Inspection", "score": 7},
                {"value": "application", "label": "Application Layer", "score": 8},
                {"value": "next_gen", "label": "Next-Generation Firewall", "score": 10}
            ],
            weight=0.4
        )

        # Firewall Update Status
        BarrierCharacteristic.objects.create(
            name="Update Status",
            category=it_security,
            description="Current update status of firewall software",
            possible_values=[
                {"value": "outdated", "label": "Outdated (>6 months)", "score": 2},
                {"value": "recent", "label": "Recently Updated (1-6 months)", "score": 6},
                {"value": "current", "label": "Current (Within 1 month)", "score": 8},
                {"value": "latest", "label": "Latest Version", "score": 10}
            ],
            weight=0.3
        )

        # Firewall Questions
        BarrierQuestion.objects.create(
            barrier=firewall,
            risk_type=cyber_risk,
            question_text="Is the firewall configured with IPS/IDS capabilities?",
            answer_choices={
                "answers": [
                    {"choice": "Yes, fully integrated", "impact": 2, "description": "IPS/IDS fully integrated and active"},
                    {"choice": "Partial implementation", "impact": 1, "description": "Basic IPS/IDS features enabled"},
                    {"choice": "No", "impact": -1, "description": "No IPS/IDS capabilities"}
                ]
            }
        )

        # Access Control Barriers
        access_control = BarrierCategory.objects.create(
            name="Access Control",
            description="Physical access control measures",
            is_shareable=False
        )

        # Access Control System
        access_system = Barrier.objects.create(
            name="Electronic Access Control",
            description="Electronic system controlling physical access to facilities",
            category=access_control
        )

        # Access Control Characteristics
        BarrierCharacteristic.objects.create(
            name="Authentication Method",
            category=access_control,
            description="Primary authentication method used",
            possible_values=[
                {"value": "pin", "label": "PIN Only", "score": 4},
                {"value": "card", "label": "Access Card", "score": 6},
                {"value": "biometric", "label": "Biometric", "score": 8},
                {"value": "multi_factor", "label": "Multi-Factor", "score": 10}
            ],
            weight=0.4
        )

        # Access Control Coverage
        BarrierCharacteristic.objects.create(
            name="Coverage",
            category=access_control,
            description="Extent of access control coverage",
            possible_values=[
                {"value": "minimal", "label": "Main Entrance Only", "score": 3},
                {"value": "partial", "label": "Critical Areas", "score": 6},
                {"value": "most", "label": "Most Areas", "score": 8},
                {"value": "complete", "label": "Complete Coverage", "score": 10}
            ],
            weight=0.3
        )

        # Access Control Questions
        BarrierQuestion.objects.create(
            barrier=access_system,
            risk_type=insider_risk,
            question_text="Is there 24/7 monitoring of access control events?",
            answer_choices={
                "answers": [
                    {"choice": "Yes, dedicated team", "impact": 2, "description": "24/7 dedicated security monitoring"},
                    {"choice": "Business hours only", "impact": 1, "description": "Monitoring during business hours"},
                    {"choice": "No active monitoring", "impact": -1, "description": "Events logged but not monitored"}
                ]
            }
        )

        self.stdout.write(self.style.SUCCESS('Successfully populated barrier data'))
