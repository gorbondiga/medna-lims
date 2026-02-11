from django import forms
from django_filters import rest_framework as filters
from django_filters.widgets import RangeWidget
from field_site.models import FieldSite
from users.models import CustomUser
from utility.models import Project
from utility.widgets import CustomSelect2Multiple, CustomSelect2
from sample_label.models import SampleBarcode
from .models import FieldSurvey, FieldCrew, EnvMeasureType, EnvMeasure, \
    FieldSample, FilterSample, SubCoreSample


########################################
# FRONTEND - FILTERS                   #
########################################
class GeoFieldSurveyMapFilter(filters.FilterSet):
    pk = filters.CharFilter(field_name='project_ids', lookup_expr='iexact')

    class Meta:
        model = FieldSurvey
        fields = ['project_ids', ]


class FieldSurveyFilter(filters.FilterSet):
    project_ids = filters.ModelMultipleChoiceFilter(field_name='project_ids__project_label', 
                                                    queryset=Project.objects.all(), 
                                                    widget=CustomSelect2Multiple, 
                                                    label='Project')
    site_id = filters.ModelChoiceFilter(field_name='site_id__site_id', 
                                        queryset=FieldSite.objects.all(), 
                                        widget=CustomSelect2, 
                                        label='Site ID')
    username = filters.ModelChoiceFilter(field_name='username__agol_username', 
                                         queryset=CustomUser.objects.all(), 
                                         widget=CustomSelect2, 
                                         label='Username')
    supervisor = filters.ModelChoiceFilter(field_name='supervisor__agol_username', 
                                           queryset=CustomUser.objects.all(), 
                                           widget=CustomSelect2, 
                                           label='Supervisor')
    created_datetime = filters.DateFromToRangeFilter(field_name='created_datetime',
                                                     widget=RangeWidget(attrs={'class': 'form-control', 
                                                                               'type': 'date',
                                                                               'style': 'background-color: white;'}),
                                                     label='Survey DateTime Range')

    class Meta:
        model = FieldSurvey
        fields = ['username', 'supervisor', 'created_datetime', 'site_id', 'project_ids', ]


class FieldCrewFilter(filters.FilterSet):
    survey_global_id = filters.ModelChoiceFilter(field_name='survey_global_id__survey_global_id', 
                                                 queryset=FieldSurvey.objects.all(), 
                                                 widget=CustomSelect2, 
                                                 label='Survey Global ID')
    created_datetime = filters.DateFilter(input_formats=['%Y-%m-%d', '%d-%m-%Y'], 
                                          lookup_expr='icontains', 
                                          widget=forms.SelectDateWidget(attrs={'class': 'form-control', }), 
                                          label='Created DateTime')
    created_by = filters.ModelChoiceFilter(field_name='username__email', 
                                           queryset=CustomUser.objects.all(), 
                                           widget=CustomSelect2, 
                                           label='Created By')

    class Meta:
        model = FieldSurvey
        fields = ['survey_global_id', 'created_datetime', 'created_by', ]


class EnvMeasureFilter(filters.FilterSet):
    survey_global_id = filters.UUIDFilter(field_name='survey_global_id__survey_global_id', 
                                          label='Survey Global ID')
    env_measure_datetime = filters.DateFilter(input_formats=['%Y-%m-%d', '%d-%m-%Y'], 
                                              lookup_expr='icontains', 
                                              widget=forms.SelectDateWidget(
                                                  attrs={'class': 'form-control', }), 
                                              label='Created DateTime')
    created_by = filters.ModelChoiceFilter(field_name='survey_global_id__created_by__email', 
                                           queryset=CustomUser.objects.all(), 
                                           widget=CustomSelect2, label='Created By')
    field_sample_barcode = filters.CharFilter(field_name='survey_global_id__field_samples__field_sample_barcode__sample_barcode_id', 
                                              lookup_expr='iexact', 
                                              label='Sample Barcode')
    project_code = filters.ModelChoiceFilter(field_name='survey_global_id__project_ids__project_code',
                                           queryset=Project.objects.all(),
                                           widget=CustomSelect2,
                                           label='Project Code')

    class Meta:
        model = EnvMeasure
        fields = ['survey_global_id', 'env_measure_datetime', 
                  'created_by', 'field_sample_barcode', 'project_code']


class FieldSampleFilter(filters.FilterSet):
    project_code = filters.ModelMultipleChoiceFilter(field_name='survey_global_id__project_ids', 
                                                    queryset=Project.objects.all(), 
                                                    widget=CustomSelect2Multiple, 
                                                    label='Project Code')
    site_name = filters.ModelChoiceFilter(field_name='survey_global_id__site_id', 
                                        queryset=FieldSite.objects.all(), 
                                        widget=CustomSelect2, 
                                        label='Site Name')
    field_sample_barcode = filters.ModelChoiceFilter(field_name='field_sample_barcode', 
                                                     queryset=FieldSample.objects.all(), 
                                                     widget=CustomSelect2, 
                                                     label='Barcode')
    class Meta:
        model = FieldSample
        fields = []


class FilterSampleFilter(filters.FilterSet):
    project_code = filters.ModelMultipleChoiceFilter(field_name='field_sample__survey_global_id__project_ids', 
                                                    queryset=Project.objects.all(), 
                                                    widget=CustomSelect2Multiple, 
                                                    label='Project Code')
    site_name = filters.ModelChoiceFilter(field_name='field_sample__survey_global_id__site_id__general_location_name', 
                                        queryset=FieldSite.objects.all(), 
                                        widget=CustomSelect2, 
                                        label='Site Name')
    username = filters.ModelChoiceFilter(field_name='field_sample__survey_global_id__username__agol_username', 
                                         queryset=CustomUser.objects.all(), 
                                         widget=CustomSelect2, 
                                         label='Username')
    supervisor = filters.ModelChoiceFilter(field_name='field_sample__survey_global_id__supervisor__agol_username', 
                                           queryset=CustomUser.objects.all(), 
                                           widget=CustomSelect2, 
                                           label='Supervisor')
    filter_datetime = filters.DateFilter(input_formats=['%Y-%m-%d', '%d-%m-%Y'], 
                                         lookup_expr='icontains', 
                                         widget=forms.SelectDateWidget(
                                             attrs={'class': 'form-control', }), 
                                         label='Filter DateTime')
    field_sample_barcode = filters.ModelChoiceFilter(field_name='field_sample__field_sample_barcode__sample_barcode_id', 
                                                     queryset=SampleBarcode.objects.all(), 
                                                     widget=CustomSelect2, 
                                                     label='Barcode')

    class Meta:
        model = FilterSample
        fields = ['username', 'supervisor', 'filter_datetime', 'site_name', 
                  'project_code', 'field_sample_barcode', ]


class SubCoreSampleFilter(filters.FilterSet):
    project_ids = filters.ModelMultipleChoiceFilter(field_name='field_sample__survey_global_id__project_ids__project_label', queryset=Project.objects.all(), widget=CustomSelect2Multiple, label='Project')
    site_id = filters.ModelChoiceFilter(field_name='field_sample__survey_global_id__site_id__site_id', queryset=FieldSite.objects.all(), widget=CustomSelect2, label='Site ID')
    username = filters.ModelChoiceFilter(field_name='field_sample__survey_global_id__username__agol_username', queryset=CustomUser.objects.all(), widget=CustomSelect2, label='Username')
    supervisor = filters.ModelChoiceFilter(field_name='field_sample__survey_global_id__supervisor__agol_username', queryset=CustomUser.objects.all(), widget=CustomSelect2, label='Supervisor')
    subcore_datetime_start = filters.DateFilter(input_formats=['%Y-%m-%d', '%d-%m-%Y'], lookup_expr='icontains', widget=forms.SelectDateWidget(attrs={'class': 'form-control', }), label='SubCore DateTime')
    field_sample_barcode = filters.ModelChoiceFilter(field_name='field_sample__field_sample_barcode__sample_barcode_id', queryset=FieldSample.objects.all(), widget=CustomSelect2, label='Barcode')

    class Meta:
        model = FieldSurvey
        fields = ['username', 'supervisor', 'subcore_datetime_start', 'site_id', 'project_ids', 'field_sample_barcode', ]


########################################
# SERIALIZER FILTERS                   #
########################################
class GeoFieldSurveySerializerFilter(filters.FilterSet):
    created_by = filters.CharFilter(field_name='created_by__email', lookup_expr='iexact')
    project_ids = filters.CharFilter(field_name='project_ids__project_code', lookup_expr='iexact')
    site_id = filters.CharFilter(field_name='site_id__site_id', lookup_expr='iexact')
    username = filters.CharFilter(field_name='username__email', lookup_expr='iexact')
    supervisor = filters.CharFilter(field_name='supervisor__email', lookup_expr='iexact')
    qa_editor = filters.CharFilter(field_name='qa_editor__email', lookup_expr='iexact')
    created_datetime = filters.DateFilter(input_formats=['%m-%d-%Y'], 
                                          lookup_expr='icontains')

    class Meta:
        model = FieldSurvey
        fields = ['created_by', 'project_ids', 'site_id', 'username', 'supervisor']


class FieldCrewSerializerFilter(filters.FilterSet):
    created_by = filters.CharFilter(field_name='created_by__email', lookup_expr='iexact')
    survey_global_id = filters.CharFilter(field_name='survey_global_id__survey_global_id', lookup_expr='iexact')

    class Meta:
        model = FieldCrew
        fields = ['created_by', 'survey_global_id', ]


class EnvMeasureTypeSerializerFilter(filters.FilterSet):
    env_measure_type_code = filters.CharFilter(field_name='env_measure_type_code', lookup_expr='iexact')

    class Meta:
        model = EnvMeasureType
        fields = ['env_measure_type_code']


class EnvMeasureSerializerFilter(filters.FilterSet):
    created_by = filters.CharFilter(field_name='created_by__email', lookup_expr='iexact')
    survey_global_id = filters.CharFilter(field_name='survey_global_id__survey_global_id', lookup_expr='iexact')
    env_measure_type = filters.CharFilter(field_name='env_measure_type__env_measure_type_code', lookup_expr='iexact')

    class Meta:
        model = EnvMeasure
        fields = ['created_by', 'survey_global_id', ]


class FieldSampleSerializerFilter(filters.FilterSet):
    created_by = filters.CharFilter(field_name='created_by__email', lookup_expr='iexact')
    survey_global_id = filters.CharFilter(field_name='survey_global_id__survey_global_id', lookup_expr='iexact')
    sample_material = filters.CharFilter(field_name='sample_material__sample_material_code', lookup_expr='iexact')
    is_extracted = filters.CharFilter(field_name='is_extracted', lookup_expr='iexact')
    barcode_slug = filters.CharFilter(field_name='barcode_slug', lookup_expr='iexact')

    class Meta:
        model = FieldSample
        fields = ['created_by', 'survey_global_id', 'sample_material',
                  'is_extracted', 'barcode_slug']


class FilterSampleSerializerFilter(filters.FilterSet):
    created_by = filters.CharFilter(field_name='created_by__email', lookup_expr='iexact')

    class Meta:
        model = FilterSample
        fields = ['created_by', ]


class SubCoreSampleSerializerFilter(filters.FilterSet):
    created_by = filters.CharFilter(field_name='created_by__email', lookup_expr='iexact')

    class Meta:
        model = SubCoreSample
        fields = ['created_by', 'field_sample', ]


class FilterJoinSerializerFilter(filters.FilterSet):
    field_sample = filters.CharFilter(field_name='field_sample__field_sample_barcode', lookup_expr='iexact')

    class Meta:
        model = SubCoreSample
        fields = ['created_by', 'field_sample', ]


########################################
# SERIALIZERS - NESTED FILTERS         #
########################################
class FieldSurveyEnvsNestedSerializerFilter(filters.FilterSet):
    # project_ids = filters.CharFilter(field_name='project_ids__project_code', lookup_expr='iexact')
    site_id = filters.CharFilter(field_name='site_id__site_id', lookup_expr='iexact')
    username = filters.CharFilter(field_name='username__email', lookup_expr='iexact')
    supervisor = filters.CharFilter(field_name='supervisor__email', lookup_expr='iexact')
    created_datetime = filters.DateFilter(input_formats=['%m-%d-%Y'], lookup_expr='icontains')
    field_sample_barcode = filters.CharFilter(field_name='field_samples__barcode_slug', lookup_expr='iexact')
    env_measure_type = filters.CharFilter(field_name='env_measurements__env_measurement__env_measure_type_code', lookup_expr='iexact')

    class Meta:
        model = FieldSurvey
        fields = ['site_id', 'username', 'supervisor', 'created_datetime']


class FieldSurveyFiltersNestedSerializerFilter(filters.FilterSet):
    # project_ids = filters.CharFilter(field_name='project_ids__project_code', lookup_expr='iexact')
    site_id = filters.CharFilter(field_name='site_id__site_id', lookup_expr='iexact')
    username = filters.CharFilter(field_name='username__email', lookup_expr='iexact')
    supervisor = filters.CharFilter(field_name='supervisor__email', lookup_expr='iexact')
    created_datetime = filters.DateFilter(input_formats=['%m-%d-%Y'], lookup_expr='icontains')
    field_sample_barcode = filters.CharFilter(field_name='field_samples__barcode_slug', lookup_expr='iexact')

    class Meta:
        model = FieldSurvey
        fields = ['site_id', 'username', 'supervisor', 'created_datetime']


class FieldSurveySubCoresNestedSerializerFilter(filters.FilterSet):
    # project_ids = filters.CharFilter(field_name='project_ids__project_code', lookup_expr='iexact')
    site_id = filters.CharFilter(field_name='site_id__site_id', lookup_expr='iexact')
    username = filters.CharFilter(field_name='username__email', lookup_expr='iexact')
    supervisor = filters.CharFilter(field_name='supervisor__email', lookup_expr='iexact')
    created_datetime = filters.DateFilter(input_formats=['%m-%d-%Y'], lookup_expr='icontains')
    field_sample_barcode = filters.CharFilter(field_name='field_samples__barcode_slug', lookup_expr='iexact')

    class Meta:
        model = FieldSurvey
        fields = ['site_id', 'username', 'supervisor', 'created_datetime']
