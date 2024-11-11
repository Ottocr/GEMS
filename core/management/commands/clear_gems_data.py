# File: core/management/commands/clear_gems_data.py

from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth.models import User
from core.models import (
    RiskType, RiskSubtype, Scenario, AssetType, Asset, Barrier,
    BarrierEffectivenessScore, AssetVulnerabilityQuestion, AssetCriticalityQuestion,
    AssetVulnerabilityAnswer, AssetCriticalityAnswer, BaselineThreatAssessment,
    RiskScenarioAssessment, FinalRiskMatrix, BarrierIssueReport, AssetLink,
    Country, Continent
)

class Command(BaseCommand):
    help = 'Clears all GEMS data except users, countries, and continents'

    def add_arguments(self, parser):
        parser.add_argument(
            '--yes-i-am-sure',
            action='store_true',
            dest='confirmed',
            help='Confirms that you want to delete the data',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if not options['confirmed']:
            self.stdout.write(self.style.WARNING('This command will delete all GEMS data except users, countries, and continents.'))
            self.stdout.write(self.style.WARNING('To confirm, run the command with --yes-i-am-sure'))
            return

        self.stdout.write('Starting to clear GEMS data...')

        # Delete data in reverse order of dependencies
        FinalRiskMatrix.objects.all().delete()
        RiskScenarioAssessment.objects.all().delete()
        AssetVulnerabilityAnswer.objects.all().delete()
        AssetCriticalityAnswer.objects.all().delete()
        Asset.objects.all().delete()
        AssetType.objects.all().delete()
        AssetLink.objects.all().delete()
        
        BarrierIssueReport.objects.all().delete()
        BarrierEffectivenessScore.objects.all().delete()
        Barrier.objects.all().delete()
        
        BaselineThreatAssessment.objects.all().delete()
        Scenario.objects.all().delete()
        RiskSubtype.objects.all().delete()
        RiskType.objects.all().delete()
        
        AssetVulnerabilityQuestion.objects.all().delete()
        AssetCriticalityQuestion.objects.all().delete()

        self.stdout.write(self.style.SUCCESS('Successfully cleared GEMS data.'))
        self.stdout.write(self.style.SUCCESS('Users, countries, and continents have been preserved.'))