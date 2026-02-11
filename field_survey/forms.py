# users/forms.py
# from django import forms
from django.urls import reverse_lazy
from django.contrib.gis import forms
from django.db.models import Exists, OuterRef
from leaflet.forms.widgets import LeafletWidget
from utility.widgets import CustomRadioSelect, CustomSelect2, CustomSelect2Multiple, \
    CustomAdminDateWidget, CustomAdminSplitDateTime, AddAnotherWidgetWrapper
from utility.models import Project, StandardOperatingProcedure
from utility.enumerations import YesNo, CollectionTypes, ControlTypes, \
    FilterLocations, FilterMethods, FilterTypes, SubSedimentMethods, TurbidTypes, PrecipTypes, WindSpeeds, CloudCovers, \
    EnvoMaterials, MeasureModes, EnvInstruments, SopTypes
from sample_label.models import SampleBarcode, SampleMaterial
from users.models import CustomUser
from field_site.models import FieldSite
from .models import FieldSurvey, EnvMeasure, FieldCrew, \
    FieldSample, FilterSample, SubCoreSample, EnvMeasureType


class FieldSurveyAllowEditLeaflet(LeafletWidget):
    geometry_field_class = 'allowEditLeaflet'
    template_name = 'leaflet/widget-add-fieldsite.html'


class FieldSurveyForm(forms.ModelForm):
    username = forms.ModelChoiceField(
        required=True,
        queryset=CustomUser.objects.all(),
        help_text='The user conducting the field survey.',
        widget=CustomSelect2(
            attrs={
                'class': 'form-control',
            }
        )
    )
    project_ids = forms.ModelMultipleChoiceField(
        required=True,
        label='Projects',
        queryset=Project.objects.all(),
        widget=CustomSelect2Multiple(
            attrs={
                'class': 'form-control',
            }
        )
    )
    supervisor = forms.ModelChoiceField(
        required=True,
        queryset=CustomUser.objects.all(),
        widget=CustomSelect2(
            attrs={
                'class': 'form-control',
            }
        )
    )
    recorder_fname = forms.CharField(
        required=True,
        label='Recorder First Name',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
            }
        )
    )
    recorder_lname = forms.CharField(
        required=True,
        label='Recorder Last Name',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
            }
        )
    )
    site_id = forms.ModelChoiceField(
        required=False,
        label='Site ID',
        help_text='If unknown or not available in drop-down, select eOT_O01 (Other).',
        queryset=FieldSite.objects.all(),
        widget=CustomSelect2(
            attrs={
                'class': 'form-control',
            }
        )
    )
    env_measure_mode = forms.ChoiceField(
        required=True,
        label='Measurement Mode',
        choices=MeasureModes.choices,
        widget=CustomRadioSelect(
            attrs={
                'class': 'form-check-input',
            }
        )
    )
    survey_complete = forms.ChoiceField(
        required=True,
        label='Is this survey complete?',
        choices=YesNo.choices,
        widget=CustomRadioSelect(
            attrs={
                'class': 'form-check-input',
            }
        )
    )
    gps_alt = forms.DecimalField(
        required=False,
        label='GPS Altitude in meters (m)',
        widget=forms.NumberInput(
            attrs={
                'class': 'form-control',
            }
        )
    )

    class Meta:
        model = FieldSurvey
        fields = ['username', 'project_ids', 'supervisor', 
                  'recorder_fname', 'recorder_lname',
                  'site_id',
                  'env_measure_mode',
                  'survey_complete', 'gps_alt',
                  ]
        widgets = {}

    def __init__(self, *args, **kwargs):
        _user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if _user:
            self.fields['username'].initial = _user


class FieldCrewForm(forms.ModelForm):
    survey_global_id = forms.ModelChoiceField(
        required=True,
        queryset=FieldSurvey.objects.none(),
    )
    crew_fname = forms.CharField(
        required=True,
        label='Crew First Name',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
            }
        )
    )
    crew_lname = forms.CharField(
        required=True,
        label='Crew Last Name',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
            }
        )
    )

    class Meta:
        model = FieldCrew
        fields = ['survey_global_id', 'crew_fname', 'crew_lname', ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['survey_global_id'].widget = (AddAnotherWidgetWrapper(CustomSelect2(attrs={'class': 'form-control', }), reverse_lazy('add_popup_fieldsurvey')))
        self.fields['survey_global_id'].queryset = FieldSurvey.objects.all().order_by('-created_datetime')


class EnvMeasureForm(forms.ModelForm):
    survey_global_id = forms.ModelChoiceField(
        required=True,
        queryset=FieldSurvey.objects.none(),
    )
    env_measure_depth = forms.DecimalField(
        label='Environmental Measurement Depth (m)',
        required=True,
        help_text='Depth in meters (m) environmental conditions were measured at.',
        widget=forms.NumberInput(
            attrs={
                'class': 'form-control',
            }
        )
    )
    env_instrument = forms.MultipleChoiceField(
        required=False,
        label='Environmental Measurement Instruments',
        choices=EnvInstruments.choices,
        help_text='Were instruments used to measure environmental conditions at this depth? Select all that apply.',
        widget=CustomSelect2Multiple(
            attrs={
                'class': 'form-control',
            }
        )
    )
    env_measurement_type = forms.ModelMultipleChoiceField(
        required=False,
        label='Environmental Measurements Taken',
        queryset=EnvMeasureType.objects.all(),
        help_text='Select all measurements taken.',
        widget=CustomSelect2Multiple(
            attrs={
                'class': 'form-control',
            }
        )
    )

    class Meta:
        model = EnvMeasure
        fields = ['survey_global_id', 'env_instrument', 'env_measure_type', 'env_measure_notes', ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['survey_global_id'].widget = (AddAnotherWidgetWrapper(CustomSelect2(attrs={'class': 'form-control', }), reverse_lazy('add_popup_fieldsurvey')))
        self.fields['survey_global_id'].queryset = FieldSurvey.objects.all().order_by('-created_datetime')

 
class FieldSampleForm(forms.ModelForm):
    # https://stackoverflow.com/questions/14831327/in-a-django-queryset-how-to-filter-for-not-exists-in-a-many-to-one-relationsh
    # Only show options where fk does not exist
    survey_global_id = forms.ModelChoiceField(
        required=True,
        queryset=FieldSurvey.objects.none(),
        widget=CustomSelect2(
            attrs={
                'class': 'form-control',
            }
        )
    )
    field_sample_barcode = forms.ModelChoiceField(
        required=True,
        label='Sample Barcode',
        queryset=SampleBarcode.objects.none(),
        widget=CustomSelect2(
            attrs={
                'class': 'form-control',
            }
        )
    )
    sample_material = forms.ModelChoiceField(
        required=True,
        disabled=True,
        label='Sample Material',
        queryset=SampleMaterial.objects.all(),
        widget=forms.Select(
            attrs={
                'class': 'form-control',
                'readonly': True
            }
        )
    )
    is_extracted = forms.ChoiceField(
        required=True,
        label='Was this sample extracted?',
        choices=YesNo.choices,
        widget=CustomRadioSelect(
            attrs={
                'class': 'form-check-input',
            }
        )
    )

    class Meta:
        model = FieldSample
        fields = ['survey_global_id', 'field_sample_barcode', 'sample_material', 'is_extracted', ]

    def __init__(self, *args, **kwargs):
        _sample_material = kwargs.pop('sample_material', None)
        _pk = kwargs.pop('pk', None)
        _user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if _sample_material:
            self.fields['sample_material'].initial = _sample_material
        if _pk:
            self.fields['field_sample_barcode'].queryset = SampleBarcode.objects.all().order_by('-created_datetime')
            self.fields['survey_global_id'].queryset = FieldSurvey.objects.all().order_by('-created_datetime')
        else:
            self.fields['field_sample_barcode'].queryset = SampleBarcode.objects.filter(~Exists(FieldSample.objects.filter(field_sample_barcode=OuterRef('pk'))))


class FilterSampleForm(forms.ModelForm):
    filter_location = forms.ChoiceField(
        required=True,
        label='Filtration Location',
        choices=FilterLocations.choices,
        help_text='Was the water filtered in the field, or in the lab?',
        widget=CustomSelect2(
            attrs={
                'class': 'form-control',
            }
        )
    )
    is_prefilter = forms.ChoiceField(
        required=True,
        choices=YesNo.choices,
        label='Prefilter',
        help_text='Is this a coarse pre-filter? A pre-filter is a coarse nitex filter that proceeds filtering with a '
                  'finer filter.',
        widget=CustomRadioSelect(
            attrs={
                'class': 'form-check-input',
            }
        )
    )
    filter_fname = forms.CharField(
        required=True,
        label='Filterer First Name',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
            }
        )
    )
    filter_lname = forms.CharField(
        required=True,
        label='Filterer Last Name',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
            }
        )
    )
    filter_sample_label = forms.CharField(
        required=True,
        label='Filter Label',
        help_text='The label written on the sample.',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
            }
        )
    )
    filter_datetime = forms.SplitDateTimeField(
        required=True,
        label='Filtration DateTime',
        widget=CustomAdminSplitDateTime()
    )
    filter_protocol = forms.ModelChoiceField(
        required=True,
        label='Filter Protocol',
        help_text='A literature reference, electronic resource or a standard operating procedure (SOP) '
                  'that describes the field sample collection method.',
        queryset=StandardOperatingProcedure.objects.filter(sop_type=SopTypes.FIELDCOLLECTION).order_by('-created_datetime'),
        widget=CustomSelect2(
            attrs={
                'class': 'form-control',
            }
        )
    )
    filter_method = forms.ChoiceField(
        required=True,
        label='Filtration Method',
        choices=FilterMethods.choices,
        widget=CustomSelect2(
            attrs={
                'class': 'form-control',
            }
        )
    )
    filter_method_other = forms.CharField(
        required=False,
        label='Other Filtration Method',
        help_text='If filtration method was other, please specify the other filter method.',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
            }
        )
    )
    filter_vol = forms.DecimalField(
        required=True,
        label='Water Volume Filtered in milliliters (mL)',
        widget=forms.NumberInput(
            attrs={
                'class': 'form-control',
            }
        )
    )
    filter_type = forms.ChoiceField(
        required=True,
        label='Filter Type',
        choices=FilterTypes.choices,
        help_text='The type of filter used.',
        widget=CustomSelect2(
            attrs={
                'class': 'form-control',
            }
        )
    )
    filter_type_other = forms.CharField(
        required=False,
        label='Other Filter Type',
        help_text='If filter type was other, please specify the other filter type.',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
            }
        )
    )
    filter_pore = forms.DecimalField(
        required=True,
        label='Filter Pore Size in microns (μm)',
        help_text='Typically, Nitex are 80 μm, Glass Fiber Filter (GF/F) are 0.7 μm, Supor are 0.2 μm, '
                  'and Cellulose Nitrate (CN) are 0.7 μm.',
        widget=forms.NumberInput(
            attrs={
                'class': 'form-control',
            }
        )
    )
    filter_size = forms.DecimalField(
        required=True,
        label='Filter Size in milimeters (mm)',
        help_text='Typically, Nitex, Glass Fiber Filter (GF/F), Supor, and Cellulose Nitrate (CN) are 47 mm.',
        widget=forms.NumberInput(
            attrs={
                'class': 'form-control',
            }
        )
    )
    filter_notes = forms.CharField(
        required=False,
        label='Filter Notes',
        widget=forms.Textarea(
            attrs={
                'class': 'form-control',
            }
        )
    )

    class Meta:
        model = FilterSample
        fields = ['filter_location', 'is_prefilter', 'filter_fname', 'filter_lname', 'filter_sample_label',
                  'filter_datetime', 'filter_protocol', 'filter_method', 'filter_method_other',
                  'filter_vol', 'filter_type', 'filter_type_other', 'filter_pore', 'filter_size', 'filter_notes', ]


class SubCoreSampleForm(forms.ModelForm):
    subcore_fname = forms.CharField(
        label='SubCorer First Name',
        required=True,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
            }
        )
    )
    subcore_lname = forms.CharField(
        required=True,
        label='SubCorer Last Name',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
            }
        )
    )
    subcore_sample_label = forms.CharField(
        required=True,
        label='SubCore Label',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
            }
        )
    )
    subcore_protocol = forms.ModelChoiceField(
        required=True,
        label='SubCore Protocol',
        help_text='A literature reference, electronic resource or a standard operating procedure (SOP) '
                  'that describes the field sample collection method.',
        queryset=StandardOperatingProcedure.objects.filter(sop_type=SopTypes.FIELDCOLLECTION).order_by('-created_datetime'),
        widget=CustomSelect2(
            attrs={
                'class': 'form-control',
            }
        )
    )
    subcore_method = forms.ChoiceField(
        required=True,
        label='SubCoring Method',
        choices=SubSedimentMethods.choices,
        widget=CustomSelect2(
            attrs={
                'class': 'form-control',
            }
        )
    )
    subcore_method_other = forms.CharField(
        required=False,
        label='Other SubCoring Method',
        help_text='If subcore method was other, please specify the other subcore method.',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
            }
        )
    )
    subcore_datetime_start = forms.SplitDateTimeField(
        required=True,
        widget=CustomAdminSplitDateTime()
    )
    subcore_datetime_end = forms.SplitDateTimeField(
        required=True,
        widget=CustomAdminSplitDateTime()
    )
    subcore_number = forms.IntegerField(
        required=True,
        label='Total SubCores',
        help_text='Total number of subcores taken, e.g., 60.',
        widget=forms.NumberInput(
            attrs={
                'class': 'form-control',
            }
        )
    )
    subcore_length = forms.DecimalField(
        required=True,
        label='SubCore Length (cm)',
        help_text='Length or thickness of each subcore in centimeters (cm).',
        widget=forms.NumberInput(
            attrs={
                'class': 'form-control',
            }
        )
    )
    subcore_diameter = forms.DecimalField(
        required=True,
        label='SubCore Diameter (cm)',
        help_text='Diameter of each subcore in centimeters (cm).',
        widget=forms.NumberInput(
            attrs={
                'class': 'form-control',
            }
        )
    )
    subcore_clayer = forms.IntegerField(
        required=True,
        label='SubCore Consistency Layer',
        help_text='The layer where sediment is consistently stratified by horizon, usually below the upper and '
                  'inconsistent organic soil horizon/layer.',
        widget=forms.NumberInput(
            attrs={
                'class': 'form-control',
            }
        )
    )
    subcore_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                'class': 'form-control',
            }
        )
    )

    class Meta:
        model = SubCoreSample
        fields = ['subcore_fname', 'subcore_lname', 'subcore_sample_label', 'subcore_protocol',
                  'subcore_method', 'subcore_method_other',
                  'subcore_datetime_start', 'subcore_datetime_end',
                  'subcore_number', 'subcore_length', 'subcore_diameter', 'subcore_clayer',
                  'subcore_notes', ]
