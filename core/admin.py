from django.contrib import admin
from django import forms
from statistics import mean
from django.utils.html import format_html
from .models.geo_models import Continent, Country
from .models.asset_models import AssetType, Asset, AssetLink, AssetVulnerabilityAnswer, AssetCriticalityAnswer, AssetVulnerabilityQuestion, AssetCriticalityQuestion
from .models.risk_models import RiskType, RiskSubtype, BaselineThreatAssessment, Scenario, RiskScenarioAssessment, FinalRiskMatrix
from .models.barrier_models import Barrier, BarrierQuestion, BarrierEffectivenessScore, BarrierQuestionAnswer, BarrierIssueReport, BarrierCategory
from .models.log_models import RiskLog


admin.site.site_header = "GEMS Admin"
admin.site.site_title = "GEMS Admin Portal"
admin.site.index_title = "Welcome to GEMS Admin Portal"

class CountryInline(admin.TabularInline):
    model = Country
    extra = 1

@admin.register(Continent)
class ContinentAdmin(admin.ModelAdmin):
    list_display = ('name', 'country_count')
    search_fields = ('name',)
    inlines = [CountryInline]

    def country_count(self, obj):
        return obj.countries.count()
    country_count.short_description = 'Number of Countries'

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'continent', 'company_operated')
    list_filter = ('continent', 'company_operated')
    search_fields = ('name', 'code')

class RiskSubtypeInline(admin.TabularInline):
    model = RiskSubtype
    extra = 1

@admin.register(RiskType)
class RiskTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'subtype_count')
    search_fields = ('name',)
    inlines = [RiskSubtypeInline]

    def subtype_count(self, obj):
        return obj.subtypes.count()
    subtype_count.short_description = 'Number of Subtypes'

@admin.register(RiskSubtype)
class RiskSubtypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'risk_type')
    list_filter = ('risk_type',)
    search_fields = ('name', 'risk_type__name')

@admin.register(BaselineThreatAssessment)
class BaselineThreatAssessmentAdmin(admin.ModelAdmin):
    list_display = ('risk_type', 'country', 'baseline_score', 'date_assessed')
    list_filter = ('risk_type', 'country', 'date_assessed')
    search_fields = ('risk_type__name', 'country__name')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Trigger risk matrix generation for affected assets
        assets = Asset.objects.filter(country=obj.country)
        for asset in assets:
            FinalRiskMatrix.generate_matrices(asset)

@admin.register(Scenario)
class ScenarioAdmin(admin.ModelAdmin):
    list_display = ('name', 'risk_subtypes_display')
    filter_horizontal = ('risk_subtypes',)
    search_fields = ('name',)

    def risk_subtypes_display(self, obj):
        return ", ".join([rs.name for rs in obj.risk_subtypes.all()])
    risk_subtypes_display.short_description = 'Risk Subtypes'

class BarrierQuestionInline(admin.TabularInline):
    model = BarrierQuestion
    extra = 1

class BarrierEffectivenessScoreInline(admin.TabularInline):
    model = BarrierEffectivenessScore
    extra = 1

@admin.register(Barrier)
class BarrierAdmin(admin.ModelAdmin):
    list_display = ('name', 'overall_effectiveness_score')
    search_fields = ('name', 'description')

    def overall_effectiveness_score(self, obj):
        # Get related BarrierEffectivenessScore instances
        effectiveness_scores = obj.effectiveness_scores.all()
        
        if effectiveness_scores:
            # Calculate the average score from the related BarrierEffectivenessScore instances
            avg_score = mean([
                round(
                    es.preventive_capability * 0.30 +
                    es.detection_capability * 0.20 +
                    es.response_capability * 0.20 +
                    es.reliability * 0.15 +
                    es.coverage * 0.15
                ) for es in effectiveness_scores
            ])
            return round(avg_score, 2)
        
        return "N/A"

    overall_effectiveness_score.short_description = 'Overall Effectiveness Score'

    inlines = [BarrierQuestionInline, BarrierEffectivenessScoreInline]

class AssetVulnerabilityAnswerInlineForm(forms.ModelForm):
    class Meta:
        model = AssetVulnerabilityAnswer
        fields = ('question', 'selected_choice')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            if self.instance.question:
                self.fields['selected_choice'].widget = forms.Select(choices=self.instance.question.get_choices())
            else:
                self.fields['selected_choice'].widget = forms.Select(choices=[])
        else:
            self.fields['selected_choice'].widget = forms.Select(choices=[])

class AssetVulnerabilityAnswerInline(admin.TabularInline):
    model = AssetVulnerabilityAnswer
    form = AssetVulnerabilityAnswerInlineForm
    extra = 0
    readonly_fields = ('question',)
    fields = ('question', 'selected_choice')

class AssetCriticalityAnswerInlineForm(forms.ModelForm):
    class Meta:
        model = AssetCriticalityAnswer
        fields = ('question', 'selected_choice')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            if self.instance.question:
                self.fields['selected_choice'].widget = forms.Select(choices=self.instance.question.get_choices())
            else:
                self.fields['selected_choice'].widget = forms.Select(choices=[])
        else:
            self.fields['selected_choice'].widget = forms.Select(choices=[])

class AssetCriticalityAnswerInline(admin.TabularInline):
    model = AssetCriticalityAnswer
    form = AssetCriticalityAnswerInlineForm
    extra = 0
    readonly_fields = ('question',)
    fields = ('question', 'selected_choice')

class FinalRiskMatrixInline(admin.TabularInline):
    model = FinalRiskMatrix
    extra = 0
    readonly_fields = ('risk_type', 'residual_risk_score', 'risk_level', 'colored_risk_level', 'sub_risk_details', 'barrier_details')
    fields = ('risk_type', 'residual_risk_score', 'colored_risk_level', 'sub_risk_details', 'barrier_details')
    can_delete = False
    max_num = 0
    
    def colored_risk_level(self, obj):
        colors = {
            'LOW': 'green',
            'MEDIUM': 'orange',
            'HIGH': 'red',
            'CRITICAL': 'purple',
        }
        return format_html(
            '<span style="color: {};">{}</span>',
            colors.get(obj.risk_level, 'black'),
            obj.get_risk_level_display()
        )
    colored_risk_level.short_description = 'Risk Level'

@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ('name', 'asset_type', 'country', 'criticality_score', 'vulnerability_score', 'risk_assessment_count', 'barriers_count')
    list_filter = ('asset_type', 'country')
    search_fields = ('name', 'description')
    filter_horizontal = ('scenarios', 'barriers')
    inlines = [AssetVulnerabilityAnswerInline, AssetCriticalityAnswerInline, FinalRiskMatrixInline]

    def risk_assessment_count(self, obj):
        return obj.risk_scenario_assessments.count()
    risk_assessment_count.short_description = 'Risk Assessments'

    def barriers_count(self, obj):
        return obj.barriers.count()
    barriers_count.short_description = 'Barriers'

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Trigger risk matrix generation
        FinalRiskMatrix.generate_matrices(obj)

@admin.register(RiskScenarioAssessment)
class RiskScenarioAssessmentAdmin(admin.ModelAdmin):
    list_display = ('asset', 'risk_scenario', 'residual_risk_score', 'likelihood_rating', 'barrier_effectiveness_display')
    list_filter = ('asset', 'risk_scenario')
    search_fields = ('asset__name', 'risk_scenario__name')

    def barrier_effectiveness_display(self, obj):
        if obj.barrier_effectiveness:
            return ", ".join([f"{k}: {v}" for k, v in obj.barrier_effectiveness.items()])
        return "N/A"
    barrier_effectiveness_display.short_description = 'Barrier Effectiveness'

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Trigger risk matrix generation
        FinalRiskMatrix.generate_matrices(obj.asset)

@admin.register(FinalRiskMatrix)
class FinalRiskMatrixAdmin(admin.ModelAdmin):
    list_display = ('asset', 'risk_type', 'residual_risk_score', 'risk_level', 'colored_risk_level')
    list_filter = ('asset', 'risk_type', 'risk_level')
    search_fields = ('asset__name', 'risk_type__name')

    def colored_risk_level(self, obj):
        colors = {
            'LOW': 'green',
            'MEDIUM': 'orange',
            'HIGH': 'red',
            'CRITICAL': 'purple',
        }
        return format_html(
            '<span style="color: {};">{}</span>',
            colors.get(obj.risk_level, 'black'),
            obj.get_risk_level_display()
        )
    colored_risk_level.short_description = 'Risk Level'

@admin.register(AssetVulnerabilityQuestion)
class AssetVulnerabilityQuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'risk_type')
    list_filter = ('risk_type',)
    search_fields = ('question_text', 'risk_type__name')

@admin.register(AssetCriticalityQuestion)
class AssetCriticalityQuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text',)
    search_fields = ('question_text',)

@admin.register(BarrierIssueReport)
class BarrierIssueReportAdmin(admin.ModelAdmin):
    list_display = ('barrier', 'status', 'impact_rating', 'reported_by', 'reported_at', 'resolved_at', 'affected_assets_count')
    list_filter = ('status', 'impact_rating', 'barrier')
    search_fields = ('barrier__name', 'description', 'reported_by__username')
    readonly_fields = ('reported_at',)
    filter_horizontal = ('affected_assets',)

    def affected_assets_count(self, obj):
        return obj.affected_assets.count()
    affected_assets_count.short_description = 'Affected Assets'

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Trigger risk matrix generation for affected assets
        for asset in obj.affected_assets.all():
            FinalRiskMatrix.generate_matrices(asset)

@admin.register(RiskLog)
class RiskLogAdmin(admin.ModelAdmin):
    list_display = ('asset', 'risk_type', 'bta_score', 'vulnerability_score', 'criticality_score', 'residual_risk_score', 'timestamp')
    list_filter = ('asset', 'risk_type')
    search_fields = ('asset__name', 'risk_type__name')
    readonly_fields = ('timestamp',)

@admin.register(BarrierCategory)
class BarrierCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(AssetLink)
class AssetLinkAdmin(admin.ModelAdmin):
    list_display = ('name', 'assets_count', 'shared_risks_count', 'shared_barriers_count')
    filter_horizontal = ('assets', 'shared_risks', 'shared_barriers')
    search_fields = ('name',)

    def assets_count(self, obj):
        return obj.assets.count()
    assets_count.short_description = 'Number of Assets'

    def shared_risks_count(self, obj):
        return obj.shared_risks.count()
    shared_risks_count.short_description = 'Number of Shared Risks'

    def shared_barriers_count(self, obj):
        return obj.shared_barriers.count()
    shared_barriers_count.short_description = 'Number of Shared Barriers'

@admin.register(AssetVulnerabilityAnswer)
class AssetVulnerabilityAnswerAdmin(admin.ModelAdmin):
    list_display = ('asset', 'question', 'selected_choice', 'selected_score')
    list_filter = ('asset', 'question__risk_type')
    search_fields = ('asset__name', 'question__question_text')
    readonly_fields = ('asset', 'question', 'selected_score')

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj and obj.question:
            form.base_fields['selected_choice'].widget = forms.Select(choices=obj.question.get_choices())
        else:
            form.base_fields['selected_choice'].widget = forms.Select(choices=[])
        return form

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Trigger risk matrix generation
        FinalRiskMatrix.generate_matrices(obj.asset)

@admin.register(AssetCriticalityAnswer)
class AssetCriticalityAnswerAdmin(admin.ModelAdmin):
    list_display = ('asset', 'question', 'selected_choice', 'selected_score')
    list_filter = ('asset',)
    search_fields = ('asset__name', 'question__question_text')
    readonly_fields = ('asset', 'question', 'selected_score')

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj and obj.question:
            form.base_fields['selected_choice'].widget = forms.Select(choices=obj.question.get_choices())
        else:
            form.base_fields['selected_choice'].widget = forms.Select(choices=[])
        return form

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Trigger risk matrix generation
        FinalRiskMatrix.generate_matrices(obj.asset)

@admin.register(BarrierQuestion)
class BarrierQuestionAdmin(admin.ModelAdmin):
    list_display = ('barrier', 'question_text', 'created_at', 'updated_at')
    search_fields = ('question_text', 'barrier__name')

@admin.register(BarrierQuestionAnswer)
class BarrierQuestionAnswerAdmin(admin.ModelAdmin):
    list_display = ('question', 'asset', 'selected_choice', 'impact', 'created_at')
    list_filter = ('asset', 'question__barrier')
    search_fields = ('question__question_text', 'asset__name', 'selected_choice')
    readonly_fields = ('created_at', 'updated_at')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Trigger risk matrix generation
        FinalRiskMatrix.generate_matrices(obj.asset)

# Register the remaining models
admin.site.register(AssetType)
