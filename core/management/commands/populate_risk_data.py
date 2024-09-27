from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import RiskType, RiskSubtype

class Command(BaseCommand):
    help = 'Populates Risk Types and Risk Subtypes for the Risk Management Platform'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write('Setting up risk types and subtypes...')

        # Define risk types and their respective sub-risks
        risk_data = {
            "Crime": [
                "Theft of physical assets",
                "Organized crime infiltration",
                "Armed robbery",
                "Vandalism",
                "Fraud",
                "Counterfeiting",
                "Extortion",
                "Blackmail",
                "Drug trafficking",
                "Kidnapping for ransom"
            ],
            "Civil Unrest": [
                "Protest at company facilities",
                "Riot in surrounding area",
                "Mass looting",
                "Road blockades",
                "Public disorder",
                "Supply chain disruptions due to unrest",
                "Occupation of company assets",
                "Police intervention",
                "Curfews or state of emergency",
                "Sabotage"
            ],
            "Regional Conflict": [
                "Cross-border skirmishes",
                "Territorial disputes",
                "Refugee influx",
                "Military checkpoints",
                "Weapons smuggling",
                "Infrastructure damage from conflict",
                "Use of company assets for war efforts",
                "Local armed militias",
                "Conscription of employees",
                "Border closures"
            ],
            "Terrorism": [
                "Bombing at company asset",
                "Active shooter attack",
                "Chemical or biological attack",
                "Kidnapping of employees",
                "Sabotage of critical infrastructure",
                "Assassination or targeted killings",
                "Bomb threat",
                "Hostage situation",
                "Cyberterrorism",
                "Lone-wolf attacks"
            ],
            "Activism": [
                "Protests outside corporate offices",
                "Social media campaigns",
                "Physical blockade of operations",
                "Sit-ins or occupations",
                "Vandalism or defacement",
                "Sabotage of equipment",
                "Distribution of negative leaflets or materials",
                "Litigation or legal challenges",
                "Direct action protests",
                "Activist shareholder actions"
            ],
            "Cyber": [
                "DDoS attacks",
                "Ransomware attacks",
                "Phishing attacks",
                "Malware injections",
                "Data breaches",
                "Insider threats",
                "Industrial espionage",
                "APT attacks",
                "Social engineering attacks",
                "Website defacement"
            ],
            "Insider": [
                "Insider trading",
                "Embezzlement",
                "Intellectual property theft",
                "Sabotage",
                "Data leaks",
                "Workplace violence",
                "Unauthorized access",
                "Corruption or bribery",
                "Unauthorized sharing of company resources",
                "Collusion with external threats"
            ]
        }

        # Create Risk Types and Risk Subtypes
        for risk_type_name, sub_risks in risk_data.items():
            risk_type, created = RiskType.objects.get_or_create(name=risk_type_name, defaults={
                'description': f'Risks associated with {risk_type_name.lower()}'
            })
            
            for sub_risk_name in sub_risks:
                RiskSubtype.objects.get_or_create(
                    name=sub_risk_name,
                    risk_type=risk_type,
                    defaults={
                        'description': f'{sub_risk_name} within the context of {risk_type_name.lower()}'
                    }
                )

        self.stdout.write(self.style.SUCCESS('Risk types and subtypes setup complete!'))
