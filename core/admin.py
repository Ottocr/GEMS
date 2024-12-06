from django.contrib import admin
from django import forms
from statistics import mean
from django.utils.html import format_html
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from .models.geo_models import Continent, Country
from .models.asset_models import AssetType, Asset, AssetLink, AssetVulnerabilityAnswer, AssetCriticalityAnswer, AssetVulnerabilityQuestion, AssetCriticalityQuestion
from .models.risk_models import (
    RiskType, RiskSubtype, BaselineThreatAssessment, Scenario, RiskScenarioAssessment, 
    FinalRiskMatrix, ScenarioQuestion, QuestionChoice, AssetScenarioAnswer
)
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

class QuestionChoiceInline(admin.TabularInline):
    model = QuestionChoice
    extra = 1
    fields = ('text', 'score', 'description')

class ScenarioQuestionInline(admin.StackedInline):
    model = ScenarioQuestion
    extra = 1
    fields = ('text', 'description', 'question_type', 'weight')
    inlines = [QuestionChoiceInline]

@admin.register(Scenario)
class ScenarioAdmin(admin.ModelAdmin):
    list_display = ('name', 'risk_subtypes_display', 'get_question_count')
    filter_horizontal = ('risk_subtypes', 'barriers')
    search_fields = ('name', 'description')
    inlines = [ScenarioQuestionInline]
    fieldsets = (
        (None, {
            'fields': ('name', 'description')
        }),
        ('Associations', {
            'fields': ('risk_subtypes', 'barriers'),
            'classes': ('collapse',)
        }),
    )

    def risk_subtypes_display(self, obj):
        return ", ".join([rs.name for rs in obj.risk_subtypes.all()])
    risk_subtypes_display.short_description = 'Risk Subtypes'

    def get_question_count(self, obj):
        return obj.questions.count()
    get_question_count.short_description = 'Questions'

@admin.register(ScenarioQuestion)
class ScenarioQuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'scenario', 'question_type', 'weight', 'get_choice_count')
    list_filter = ('scenario', 'question_type')
    search_fields = ('text', 'description', 'scenario__name')
    inlines = [QuestionChoiceInline]
    fieldsets = (
        (None, {
            'fields': ('scenario', 'text', 'description')
        }),
        ('Configuration', {
            'fields': ('question_type', 'weight'),
            'classes': ('collapse',)
        }),
    )

    def get_choice_count(self, obj):
        return obj.choices.count()
    get_choice_count.short_description = 'Choices'

@admin.register(QuestionChoice)
class QuestionChoiceAdmin(admin.ModelAdmin):
    list_display = ('text', 'question', 'score')
    list_filter = ('question__scenario', 'score')
    search_fields = ('text', 'description', 'question__text')

@admin.register(AssetScenarioAnswer)
class AssetScenarioAnswerAdmin(admin.ModelAdmin):
    list_display = ('asset', 'scenario', 'question', 'selected_choice', 'get_score')
    list_filter = ('asset', 'scenario', 'question__question_type')
    search_fields = ('asset__name', 'scenario__name', 'question__text')
    raw_id_fields = ('asset', 'scenario', 'question', 'selected_choice')

    def get_score(self, obj):
        score = obj.selected_choice.score
        color = 'red' if score > 7 else 'orange' if score > 4 else 'green'
        return format_html('<span style="color: {}">{}</span>', color, score)
    get_score.short_description = 'Risk Score'

class BarrierEffectivenessScoreForm(forms.ModelForm):
    class Meta:
        model = BarrierEffectivenessScore
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            if self.instance and hasattr(self.instance, 'barrier') and self.instance.barrier:
                # Get all subtypes from barrier's risk types
                risk_type_subtypes = RiskSubtype.objects.filter(
                    risk_type__in=self.instance.barrier.risk_types.all()
                )
                # Add subtypes directly associated with barrier
                barrier_subtypes = self.instance.barrier.risk_subtypes.all()
                # Combine and remove duplicates
                self.fields['risk_subtype'].queryset = (risk_type_subtypes | barrier_subtypes).distinct()
            else:
                self.fields['risk_subtype'].queryset = RiskSubtype.objects.none()
        except (ObjectDoesNotExist, AttributeError):
            self.fields['risk_subtype'].queryset = RiskSubtype.objects.none()

class BarrierEffectivenessScoreInline(admin.TabularInline):
    model = BarrierEffectivenessScore
    form = BarrierEffectivenessScoreForm
    extra = 1
    fields = ('risk_type', 'risk_subtype', 'preventive_capability', 'detection_capability', 
              'response_capability', 'reliability', 'coverage', 'overall_effectiveness_score')
    readonly_fields = ('overall_effectiveness_score',)

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        formset.form = BarrierEffectivenessScoreForm
        return formset

class BarrierQuestionForm(forms.ModelForm):
    class Meta:
        model = BarrierQuestion
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            if self.instance and hasattr(self.instance, 'barrier') and self.instance.barrier:
                # Get all subtypes from barrier's risk types and directly associated subtypes
                risk_type_subtypes = RiskSubtype.objects.filter(
                    risk_type__in=self.instance.barrier.risk_types.all()
                )
                barrier_subtypes = self.instance.barrier.risk_subtypes.all()
                self.fields['risk_subtypes'].queryset = (risk_type_subtypes | barrier_subtypes).distinct()
            else:
                self.fields['risk_subtypes'].queryset = RiskSubtype.objects.none()
        except (ObjectDoesNotExist, AttributeError):
            self.fields['risk_subtypes'].queryset = RiskSubtype.objects.none()

class BarrierQuestionInline(admin.TabularInline):
    model = BarrierQuestion
    form = BarrierQuestionForm
    extra = 1
    filter_horizontal = ('risk_types', 'risk_subtypes')
    fields = ('question_text', 'risk_types', 'risk_subtypes', 'scenario', 'answer_choices')

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        formset.form = BarrierQuestionForm
        return formset

@admin.register(Barrier)
class BarrierAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'overall_effectiveness_score', 'is_active', 'risk_types_display', 'risk_subtypes_display')
    list_filter = ('category', 'is_active', 'risk_types', 'risk_subtypes')
    search_fields = ('name', 'description')
    filter_horizontal = ('risk_types', 'risk_subtypes')
    inlines = [BarrierEffectivenessScoreInline, BarrierQuestionInline]
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'category', 'is_active')
        }),
        ('Risk Associations', {
            'fields': ('risk_types', 'risk_subtypes'),
            'description': 'A barrier can affect multiple risk types and subtypes simultaneously. For example, a perimeter fence may impact activism, robbery, and terrorism attacks.',
            'classes': ('collapse',)
        }),
        ('Performance', {
            'fields': ('performance_adjustment',),
            'classes': ('collapse',)
        })
    )

    def risk_types_display(self, obj):
        types = obj.risk_types.all()
        if not types:
            return "-"
        return format_html("<br>".join([rt.name for rt in types]))
    risk_types_display.short_description = 'Risk Types'
    risk_types_display.allow_tags = True

    def risk_subtypes_display(self, obj):
        subtypes = obj.risk_subtypes.all()
        if not subtypes:
            return "-"
        # Group subtypes by risk type for better readability
        grouped = {}
        for st in subtypes:
            if st.risk_type.name not in grouped:
                grouped[st.risk_type.name] = []
            grouped[st.risk_type.name].append(st.name)
        
        display = []
        for rt_name, st_names in grouped.items():
            display.append(f"{rt_name}: {', '.join(st_names)}")
        return format_html("<br>".join(display))
    risk_subtypes_display.short_description = 'Risk Subtypes'
    risk_subtypes_display.allow_tags = True

    def overall_effectiveness_score(self, obj):
        effectiveness_scores = obj.effectiveness_scores.all()
        if effectiveness_scores:
            avg_score = mean([score.overall_effectiveness_score for score in effectiveness_scores])
            score = round(avg_score * obj.performance_adjustment, 2)
            # Color code the score
            if score >= 8:
                color = 'green'
            elif score >= 6:
                color = 'orange'
            else:
                color = 'red'
            return format_html('<span style="color: {}">{}</span>', color, score)
        return "N/A"
    overall_effectiveness_score.short_description = 'Overall Effectiveness'

    class Media:
        js = ('core/admin/js/barrier_admin.js',)

@admin.register(BarrierEffectivenessScore)
class BarrierEffectivenessScoreAdmin(admin.ModelAdmin):
    form = BarrierEffectivenessScoreForm
    list_display = ('barrier', 'risk_type', 'risk_subtype', 'overall_effectiveness_score')
    list_filter = ('barrier', 'risk_type', 'risk_subtype')
    search_fields = ('barrier__name', 'risk_type__name', 'risk_subtype__name')
    readonly_fields = ('overall_effectiveness_score',)
    fieldsets = (
        (None, {
            'fields': ('barrier', 'risk_type', 'risk_subtype')
        }),
        ('Capability Scores', {
            'fields': ('preventive_capability', 'detection_capability', 'response_capability', 
                      'reliability', 'coverage', 'overall_effectiveness_score')
        })
    )

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
    list_display = ('asset', 'scenario', 'residual_risk_score', 'likelihood_score', 'impact_score', 'vulnerability_score', 'barrier_effectiveness_display')
    list_filter = ('asset', 'scenario', 'assessment_date')
    search_fields = ('asset__name', 'scenario__name')
    readonly_fields = ('residual_risk_score', 'likelihood_score', 'impact_score', 'vulnerability_score')

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
    form = BarrierQuestionForm
    list_display = ('barrier', 'question_text', 'risk_types_display', 'risk_subtypes_display', 'created_at', 'updated_at')
    list_filter = ('barrier', 'risk_types', 'risk_subtypes')
    search_fields = ('question_text', 'barrier__name')
    filter_horizontal = ('risk_types', 'risk_subtypes')

    def risk_types_display(self, obj):
        return ", ".join([rt.name for rt in obj.risk_types.all()])
    risk_types_display.short_description = 'Risk Types'

    def risk_subtypes_display(self, obj):
        subtypes = obj.risk_subtypes.all()
        if not subtypes:
            return "-"
        grouped = {}
        for st in subtypes:
            if st.risk_type.name not in grouped:
                grouped[st.risk_type.name] = []
            grouped[st.risk_type.name].append(st.name)
        
        display = []
        for rt_name, st_names in grouped.items():
            display.append(f"{rt_name}: {', '.join(st_names)}")
        return format_html("<br>".join(display))
    risk_subtypes_display.short_description = 'Risk Subtypes'
    risk_subtypes_display.allow_tags = True

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

