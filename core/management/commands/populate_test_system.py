# Populate test system with sample data
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from core.models.geo_models import Country, Continent
from core.models.asset_models import (
    Asset, AssetType, AssetLink,
    AssetVulnerabilityQuestion, AssetCriticalityQuestion,
    AssetVulnerabilityAnswer, AssetCriticalityAnswer
)
from core.models.risk_models import (
    RiskType, RiskSubtype, Scenario, ScenarioQuestion,
    QuestionChoice, AssetScenarioAnswer, RiskScenarioAssessment,
    BaselineThreatAssessment, FinalRiskMatrix
)
from core.models.barrier_models import (
    Barrier, BarrierCategory, BarrierEffectivenessScore,
    BarrierQuestion, BarrierQuestionAnswer, BarrierIssueReport
)


class Command(BaseCommand):
    help = 'Populate complete test system with interconnected data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting system population...')
        
        # Create test admin user
        User = get_user_model()
        admin_user, _ = User.objects.get_or_create(
            username='admin',
            email='admin@example.com',
            is_staff=True,
            is_superuser=True
        )
        admin_user.set_password('adminpass')
        admin_user.save()

        # 2. Create Risk Types and Scenarios
        risk_types = self.create_risk_types()

        # 3. Create Asset Types and Questions
        asset_types = self.create_asset_components()

        # 4. Create Barriers
        barriers = self.create_barriers()

        # 5. Create Test Assets
        assets = self.create_test_assets()

        # 6. Create Asset Links
        self.create_asset_links()

        # 7. Create Barrier Issues
        self.create_barrier_issues(admin_user)

        # 8. Create Baseline Threats
        self.create_baseline_threats()

        # 9. Create Barrier Effectiveness Scores
        self.create_barrier_effectiveness(barriers, risk_types)

        # 10. Create Risk Scenario Assessments
        self.create_risk_assessments(assets, risk_types, barriers)

        self.stdout.write(self.style.SUCCESS('Successfully populated test system'))

    def create_risk_types(self):
        """Create risk types, subtypes, and scenarios with questions"""
        # 1. Terrorism Risk Type
        terrorism, _ = RiskType.objects.get_or_create(
            name='Terrorism',
            defaults={'description': 'Risks related to terrorist activities'}
        )

        # Create terrorism subtypes
        terrorism_attack, _ = RiskSubtype.objects.get_or_create(
            name='Physical Attack',
            risk_type=terrorism,
            defaults={'description': 'Direct physical attacks on facilities'}
        )
        terrorism_vehicle, _ = RiskSubtype.objects.get_or_create(
            name='Vehicle Attack',
            risk_type=terrorism,
            defaults={'description': 'Vehicle-based attacks on facilities'}
        )

        # 2. Crime Risk Type
        crime, _ = RiskType.objects.get_or_create(
            name='Crime',
            defaults={'description': 'Criminal activities against assets'}
        )

        # Create crime subtypes
        robbery, _ = RiskSubtype.objects.get_or_create(
            name='Robbery',
            risk_type=crime,
            defaults={'description': 'Theft with force or threat'}
        )
        burglary, _ = RiskSubtype.objects.get_or_create(
            name='Burglary',
            risk_type=crime,
            defaults={'description': 'Breaking and entering'}
        )

        # 3. Activism Risk Type
        activism, _ = RiskType.objects.get_or_create(
            name='Activism',
            defaults={'description': 'Activist activities against company'}
        )

        # Create activism subtypes
        protest, _ = RiskSubtype.objects.get_or_create(
            name='Protest',
            risk_type=activism,
            defaults={'description': 'Organized protests at facilities'}
        )
        trespass, _ = RiskSubtype.objects.get_or_create(
            name='Trespass',
            risk_type=activism,
            defaults={'description': 'Unauthorized entry by activists'}
        )

        # 4. Cyber Risk Type
        cyber, _ = RiskType.objects.get_or_create(
            name='Cyber',
            defaults={'description': 'Cyber security risks'}
        )

        # Create cyber subtypes
        network_breach, _ = RiskSubtype.objects.get_or_create(
            name='Network Breach',
            risk_type=cyber,
            defaults={'description': 'Unauthorized access to network systems'}
        )
        data_theft, _ = RiskSubtype.objects.get_or_create(
            name='Data Theft',
            risk_type=cyber,
            defaults={'description': 'Theft of sensitive data'}
        )

        # Create scenarios for each subtype
        self.create_scenario(terrorism_attack, 'Facility Attack', 'Direct attack on facility')
        self.create_scenario(terrorism_vehicle, 'Vehicle Attack', 'Vehicle-based attack')
        self.create_scenario(robbery, 'Armed Robbery', 'Armed robbery attempt')
        self.create_scenario(burglary, 'Night Break-in', 'Breaking and entering after hours')
        self.create_scenario(protest, 'Mass Protest', 'Large protest at facility')
        self.create_scenario(trespass, 'Activist Break-in', 'Activists attempting entry')
        self.create_scenario(network_breach, 'Network Intrusion', 'Unauthorized network access')
        self.create_scenario(data_theft, 'Data Breach', 'Theft of sensitive data')

        self.stdout.write('Created risk types and scenarios')
        return [terrorism, crime, activism, cyber]

    def create_scenario(self, subtype, name, description):
        """Helper method to create a scenario with standard questions"""
        scenario = Scenario.objects.create(
            name=name,
            description=description
        )
        scenario.risk_subtypes.add(subtype)

        # Create standard questions for each scenario
        likelihood_q = ScenarioQuestion.objects.create(
            scenario=scenario,
            text=f'How likely is a {name.lower()}?',
            question_type='LIKELIHOOD',
            weight=1.0
        )
        for choice in [
            ('Very Unlikely', 1), ('Unlikely', 3), ('Possible', 5),
            ('Likely', 7), ('Very Likely', 9)
        ]:
            QuestionChoice.objects.create(
                question=likelihood_q,
                text=choice[0],
                score=choice[1]
            )

        impact_q = ScenarioQuestion.objects.create(
            scenario=scenario,
            text=f'What would be the impact of a {name.lower()}?',
            question_type='IMPACT',
            weight=1.0
        )
        for choice in [
            ('Minimal', 1), ('Minor', 3), ('Moderate', 5),
            ('Major', 7), ('Severe', 9)
        ]:
            QuestionChoice.objects.create(
                question=impact_q,
                text=choice[0],
                score=choice[1]
            )

        return scenario

    def create_asset_components(self):
        """Create asset types and assessment questions"""
        # Asset Types
        office_type, _ = AssetType.objects.get_or_create(
            name='Office Building',
            defaults={'description': 'Corporate office facilities'}
        )

        datacenter_type, _ = AssetType.objects.get_or_create(
            name='Data Center',
            defaults={'description': 'IT infrastructure facilities'}
        )

        # Create Criticality Questions
        crit_q1 = AssetCriticalityQuestion.objects.create(
            question_text='What is the operational importance of this asset?',
            choice1='Critical to operations', score1=10,
            choice2='Very important', score2=8,
            choice3='Important', score3=6,
            choice4='Somewhat important', score4=4,
            choice5='Not critical', score5=2
        )

        crit_q2 = AssetCriticalityQuestion.objects.create(
            question_text='What is the potential impact on business continuity?',
            choice1='Severe disruption', score1=10,
            choice2='Major disruption', score2=8,
            choice3='Moderate disruption', score3=6,
            choice4='Minor disruption', score4=4,
            choice5='Minimal disruption', score5=2
        )

        # Create Vulnerability Questions for each risk type
        for risk_type in RiskType.objects.all():
            AssetVulnerabilityQuestion.objects.create(
                question_text=f'How vulnerable is this asset to {risk_type.name.lower()} risks?',
                choice1='Highly vulnerable', score1=10,
                choice2='Moderately vulnerable', score2=7,
                choice3='Limited vulnerability', score3=5,
                choice4='Well protected', score4=3,
                choice5='Highly protected', score5=1,
                risk_type=risk_type
            )

        self.stdout.write('Created asset components')
        return [office_type, datacenter_type]

    def create_barriers(self):
        """Create barriers and their characteristics"""
        # Categories
        physical_cat, _ = BarrierCategory.objects.get_or_create(
            name='Physical Security',
            defaults={'description': 'Physical security measures'}
        )

        cyber_cat, _ = BarrierCategory.objects.get_or_create(
            name='Cyber Security',
            defaults={'description': 'Cyber security measures', 'is_shareable': True}
        )

        # Get risk types and subtypes
        terrorism = RiskType.objects.get(name='Terrorism')
        crime = RiskType.objects.get(name='Crime')
        activism = RiskType.objects.get(name='Activism')
        cyber = RiskType.objects.get(name='Cyber')

        # Create Physical Barriers with multiple risk type/subtype associations
        perimeter_fence = Barrier.objects.create(
            name='Perimeter Fence',
            description='Main perimeter security fence',
            category=physical_cat
        )
        # Fence affects multiple risk types
        perimeter_fence.risk_types.add(terrorism, crime, activism)
        # And specific subtypes
        perimeter_fence.risk_subtypes.add(
            RiskSubtype.objects.get(name='Vehicle Attack'),
            RiskSubtype.objects.get(name='Trespass')
        )

        access_control = Barrier.objects.create(
            name='Access Control System',
            description='Electronic access control system',
            category=physical_cat
        )
        # Access control affects both physical and cyber risks
        access_control.risk_types.add(crime, cyber)
        access_control.risk_subtypes.add(
            RiskSubtype.objects.get(name='Burglary'),
            RiskSubtype.objects.get(name='Data Theft')
        )

        # Create Cyber Barriers
        firewall = Barrier.objects.create(
            name='Enterprise Firewall',
            description='Network security system',
            category=cyber_cat
        )
        # Firewall primarily affects cyber risks
        firewall.risk_types.add(cyber)
        firewall.risk_subtypes.add(
            RiskSubtype.objects.get(name='Network Breach'),
            RiskSubtype.objects.get(name='Data Theft')
        )

        # Create Barrier Questions for each barrier
        self.create_barrier_questions(perimeter_fence)
        self.create_barrier_questions(access_control)
        self.create_barrier_questions(firewall)

        # Add barriers to scenarios
        for scenario in Scenario.objects.all():
            if scenario.name in ['Facility Attack', 'Vehicle Attack', 'Mass Protest']:
                scenario.barriers.add(perimeter_fence)
            if scenario.name in ['Armed Robbery', 'Night Break-in', 'Data Breach']:
                scenario.barriers.add(access_control)
            if scenario.name in ['Network Intrusion', 'Data Breach']:
                scenario.barriers.add(firewall)

        self.stdout.write('Created barriers with multiple risk type/subtype associations')
        return [perimeter_fence, access_control, firewall]

    def create_barrier_questions(self, barrier):
        """Helper method to create standard barrier questions"""
        # Create questions for each associated risk type and subtype
        for risk_type in barrier.risk_types.all():
            question = BarrierQuestion.objects.create(
                barrier=barrier,
                question_text=f'How effective is {barrier.name} against {risk_type.name} risks?',
                answer_choices={
                    'answers': [
                        {'choice': 'Highly effective', 'impact': 10, 'description': 'Maximum effectiveness'},
                        {'choice': 'Moderately effective', 'impact': 7, 'description': 'Good effectiveness'},
                        {'choice': 'Limited effectiveness', 'impact': 4, 'description': 'Some effectiveness'}
                    ]
                }
            )
            # Add risk type after creation
            question.risk_types.add(risk_type)

        for subtype in barrier.risk_subtypes.all():
            question = BarrierQuestion.objects.create(
                barrier=barrier,
                question_text=f'How effective is {barrier.name} specifically against {subtype.name}?',
                answer_choices={
                    'answers': [
                        {'choice': 'Highly effective', 'impact': 10, 'description': 'Maximum effectiveness'},
                        {'choice': 'Moderately effective', 'impact': 7, 'description': 'Good effectiveness'},
                        {'choice': 'Limited effectiveness', 'impact': 4, 'description': 'Some effectiveness'}
                    ]
                }
            )
            # Add risk type and subtype after creation
            question.risk_types.add(subtype.risk_type)
            question.risk_subtypes.add(subtype)

    def create_test_assets(self):
        """Create test assets with answers to all questions"""
        office_type = AssetType.objects.get(name='Office Building')
        datacenter_type = AssetType.objects.get(name='Data Center')
        country = Country.objects.get(name='United States of America')
        
        # Create main office
        main_office = Asset.objects.create(
            name='Main Office',
            description='Corporate headquarters',
            latitude=38.8977,
            longitude=-77.0365,
            asset_type=office_type,
            country=country,
            criticality_score=8,
            vulnerability_score=6
        )

        # Create data center
        data_center = Asset.objects.create(
            name='Primary Data Center',
            description='Main data center facility',
            latitude=39.0438,
            longitude=-77.4874,
            asset_type=datacenter_type,
            country=country,
            criticality_score=9,
            vulnerability_score=5
        )

        # Create answers for each asset
        for asset in [main_office, data_center]:
            # Criticality Answers
            for question in AssetCriticalityQuestion.objects.all():
                AssetCriticalityAnswer.objects.create(
                    asset=asset,
                    question=question,
                    selected_choice=question.choice2,  # Use 'Very important' choice
                    selected_score=question.score2
                )

            # Vulnerability Answers
            for question in AssetVulnerabilityQuestion.objects.all():
                AssetVulnerabilityAnswer.objects.create(
                    asset=asset,
                    question=question,
                    selected_choice=question.choice3,  # Use 'Limited vulnerability' choice
                    selected_score=question.score3
                )

            # Add scenarios and barriers
            for scenario in Scenario.objects.all():
                asset.scenarios.add(scenario)
            for barrier in Barrier.objects.all():
                asset.barriers.add(barrier)

                # Create barrier question answers
                for question in barrier.questions.all():
                    # Get the first answer choice
                    answer_choice = question.answer_choices['answers'][0]
                    BarrierQuestionAnswer.objects.create(
                        question=question,
                        asset=asset,
                        selected_choice=answer_choice['choice'],
                        impact=answer_choice['impact']
                    )

        self.stdout.write('Created test assets with all answers')
        return [main_office, data_center]

    def create_asset_links(self):
        """Create asset links with shared risks and barriers"""
        main_office = Asset.objects.get(name='Main Office')
        data_center = Asset.objects.get(name='Primary Data Center')
        
        # Get barriers
        perimeter_fence = Barrier.objects.get(name='Perimeter Fence')
        access_control = Barrier.objects.get(name='Access Control System')
        firewall = Barrier.objects.get(name='Enterprise Firewall')
        
        # Get risk types
        terrorism = RiskType.objects.get(name='Terrorism')
        crime = RiskType.objects.get(name='Crime')
        cyber = RiskType.objects.get(name='Cyber')

        # Physical security complex
        physical_link = AssetLink.objects.create(
            name='Security Complex'
        )
        physical_link.assets.add(main_office, data_center)
        physical_link.shared_risks.add(terrorism, crime)
        physical_link.shared_barriers.add(perimeter_fence, access_control)

        # IT infrastructure link
        it_link = AssetLink.objects.create(
            name='IT Infrastructure'
        )
        it_link.assets.add(main_office, data_center)
        it_link.shared_risks.add(cyber)
        it_link.shared_barriers.add(firewall, access_control)

        self.stdout.write('Created asset links')

    def create_barrier_issues(self, admin_user):
        """Create sample barrier issues"""
        perimeter_fence = Barrier.objects.get(name='Perimeter Fence')
        access_control = Barrier.objects.get(name='Access Control System')
        firewall = Barrier.objects.get(name='Enterprise Firewall')
        main_office = Asset.objects.get(name='Main Office')
        data_center = Asset.objects.get(name='Primary Data Center')

        # Physical barrier issues
        fence_issue = BarrierIssueReport.objects.create(
            barrier=perimeter_fence,
            reported_by=admin_user,
            description='Damage to perimeter fence section A3',
            status='OPEN',
            impact_rating='SUBSTANTIAL'
        )
        fence_issue.affected_assets.add(main_office, data_center)

        access_issue = BarrierIssueReport.objects.create(
            barrier=access_control,
            reported_by=admin_user,
            description='Card reader malfunction at main entrance',
            status='IN_PROGRESS',
            impact_rating='MINIMAL'
        )
        access_issue.affected_assets.add(main_office)

        # Cyber barrier issue
        firewall_issue = BarrierIssueReport.objects.create(
            barrier=firewall,
            reported_by=admin_user,
            description='Firewall configuration issue detected',
            status='IN_PROGRESS',
            impact_rating='MINIMAL'
        )
        firewall_issue.affected_assets.add(main_office, data_center)

        self.stdout.write('Created barrier issues')

    def create_baseline_threats(self):
        """Create baseline threat assessments"""
        country = Country.objects.get(name='United States of America')
        today = timezone.now().date()
        
        # Create BTAs for each risk type
        for risk_type in RiskType.objects.all():
            BaselineThreatAssessment.objects.create(
                risk_type=risk_type,
                country=country,
                baseline_score=5,  # Default middle score
                date_assessed=today,
                impact_on_assets=True,
                notes=f'Current {risk_type.name.lower()} threat assessment'
            )

        self.stdout.write('Created baseline threat assessments')

    def create_barrier_effectiveness(self, barriers, risk_types):
        """Create barrier effectiveness scores"""
        for barrier in barriers:
            # Create effectiveness scores for directly associated risk types
            for risk_type in barrier.risk_types.all():
                BarrierEffectivenessScore.objects.create(
                    barrier=barrier,
                    risk_type=risk_type,
                    preventive_capability=8,
                    detection_capability=7,
                    response_capability=7,
                    reliability=8,
                    coverage=8
                )
            
            # Create effectiveness scores for risk types of associated subtypes
            for subtype in barrier.risk_subtypes.all():
                BarrierEffectivenessScore.objects.create(
                    barrier=barrier,
                    risk_type=subtype.risk_type,
                    risk_subtype=subtype,
                    preventive_capability=9,  # Higher for specific subtypes
                    detection_capability=8,
                    response_capability=8,
                    reliability=9,
                    coverage=9
                )

        self.stdout.write('Created barrier effectiveness scores')

    def create_risk_assessments(self, assets, risk_types, barriers):
        """Create risk scenario assessments"""
        for asset in assets:
            for scenario in asset.scenarios.all():
                # Create answers for scenario questions
                for question in scenario.questions.all():
                    choice = question.choices.order_by('?').first()  # Random choice
                    AssetScenarioAnswer.objects.create(
                        asset=asset,
                        scenario=scenario,
                        question=question,
                        selected_choice=choice
                    )

                # Create risk assessment
                assessment = RiskScenarioAssessment.objects.create(
                    asset=asset,
                    scenario=scenario,
                    likelihood_score=7,
                    impact_score=8,
                    vulnerability_score=6,
                    residual_risk_score=7,
                    barrier_effectiveness={str(barrier.id): 0.8 for barrier in scenario.barriers.all()}
                )

                # Generate risk matrices
                FinalRiskMatrix.generate_matrices(asset)

        self.stdout.write('Created risk scenario assessments and matrices')
 