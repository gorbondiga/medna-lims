# from django.contrib import admin
from django.contrib.gis import admin
# from django_admin_listfilter_dropdown.filters import RelatedDropdownFilter
from .resources import EnvMeasureTypeAdminResource, FieldSurveyAdminResource, \
    FieldCrewAdminResource, EnvMeasureAdminResource, \
    FieldSampleAdminResource, FilterSampleAdminResource, SubCoreSampleAdminResource
from .models import EnvMeasureType, FieldSurvey, FieldCrew, EnvMeasure, \
    FieldSample, FilterSample, SubCoreSample
from import_export.admin import ImportExportActionModelAdmin, ExportActionMixin


try:
    GeoAdminBase = admin.OSMGeoAdmin
except AttributeError:  # Django 5.x+: OSMGeoAdmin removed
    GeoAdminBase = admin.GISModelAdmin


# Register your models here.
class ProjectInline(admin.TabularInline):
    # https://docs.djangoproject.com/en/4.0/ref/contrib/admin/#working-with-many-to-many-intermediary-models
    # https://docs.djangoproject.com/en/4.0/ref/contrib/admin/#working-with-many-to-many-models
    model = FieldSurvey.project_ids.through
    # extra = 1


class FieldSurveyAdmin(ExportActionMixin, GeoAdminBase):
    # below are import_export configs
    # SampleMaterialAdminResource
    resource_class = FieldSurveyAdminResource
    # changes the order of how the tables are displayed and specifies what to display
    list_display = ('survey_global_id', 'username', 'site_id', )
    readonly_fields = ('created_by', 'modified_datetime', 'created_datetime', 'survey_global_id', )
    search_fields = ['survey_global_id', ]
    autocomplete_fields = ['project_ids', 'username', 'supervisor', 'site_id', ]

    def add_view(self, request, extra_content=None):
        # specify the fields that can be viewed in add view
        self.fields = ['survey_global_id', 'username', 'project_ids', 'supervisor',
                       'recorder_fname', 'recorder_lname', 'site_id',
                       'env_measure_mode', 'survey_complete',
                       'gps_alt', ]

        # self.exclude = ('site_prefix', 'site_num','site_id','created_datetime')
        add_fields = request.GET.copy()
        add_fields['created_by'] = request.user
        request.GET = add_fields
        return super(FieldSurveyAdmin, self).add_view(request)

    def change_view(self, request, object_id, extra_content=None):
        # specify what can be changed in admin change view
        self.fields = ['survey_global_id', 'username', 'project_ids', 'supervisor',
                       'recorder_fname', 'recorder_lname', 'site_id',
                       'env_measure_mode', 'survey_complete',
                       'gps_alt',
                       'created_by', 'modified_datetime', 'created_datetime']
        # self.inlines = (ProjectInline,)
        #  self.exclude = ('site_prefix', 'site_num','site_id','created_datetime')
        return super(FieldSurveyAdmin, self).change_view(request, object_id)

admin.site.register(FieldSurvey, FieldSurveyAdmin)


class FieldCrewAdmin(ImportExportActionModelAdmin):
    # below are import_export configs
    # SampleLabelAdminResource
    resource_class = FieldCrewAdminResource
    # changes the order of how the tables are displayed and specifies what to display
    list_display = ('crew_global_id', 'crew_fname', 'crew_lname', 'survey_global_id', )
    readonly_fields = ('created_by', 'modified_datetime', 'created_datetime', 'crew_global_id', )
    search_fields = ['crew_global_id', ]
    autocomplete_fields = ['survey_global_id', ]

    def add_view(self, request, extra_content=None):
        # specify the fields that can be viewed in add view
        self.fields = ['crew_global_id', 'survey_global_id', 'crew_fname', 'crew_lname', ]

        # self.exclude = ('site_prefix', 'site_num','site_id','created_datetime')
        add_fields = request.GET.copy()
        add_fields['created_by'] = request.user
        request.GET = add_fields
        return super(FieldCrewAdmin, self).add_view(request)

    def change_view(self, request, object_id, extra_content=None):
        # specify what can be changed in admin change view
        self.fields = ['crew_global_id', 'survey_global_id', 'crew_fname', 'crew_lname',
                       'created_by', 'modified_datetime', 'created_datetime']
        # self.exclude = ('site_prefix', 'site_num','site_id','created_datetime')
        return super(FieldCrewAdmin, self).change_view(request, object_id)

admin.site.register(FieldCrew, FieldCrewAdmin)


class EnvMeasureTypeAdmin(ImportExportActionModelAdmin):
    # below are import_export configs
    # SampleLabelAdminResource
    resource_class = EnvMeasureTypeAdminResource
    # changes the order of how the tables are displayed and specifies what to display
    list_display = ('env_measure_type_name', 'env_measure_type_code', 'env_measure_type_unit', )
    readonly_fields = ('modified_datetime', 'created_datetime', )
    search_fields = ['env_measure_type_name', 'env_measure_type_code', ]

    def add_view(self, request, extra_content=None):
        self.fields = ['env_measure_type_code', 'env_measure_type_name', 
                       'env_measure_type_unit', 'created_by', ]
        add_fields = request.GET.copy()
        add_fields['created_by'] = request.user
        request.GET = add_fields
        return super(EnvMeasureTypeAdmin, self).add_view(request)

    def change_view(self, request, object_id, extra_content=None):
        # specify what can be changed in admin change view
        self.fields = ['env_measure_type_name', 'env_measure_type_code', 'env_measure_type_unit',
                       'created_by', 'modified_datetime', 'created_datetime']
        return super(EnvMeasureTypeAdmin, self).change_view(request, object_id)
    

admin.site.register(EnvMeasureType, EnvMeasureTypeAdmin)


class EnvMeasureAdmin(ImportExportActionModelAdmin):
    # below are import_export configs
    # SampleLabelAdminResource
    resource_class = EnvMeasureAdminResource
    # changes the order of how the tables are displayed and specifies what to display
    list_display = ('env_global_id', 'env_measure_datetime', 'survey_global_id', )
    readonly_fields = ('created_by', 'modified_datetime', 'created_datetime', 'env_global_id', )
    search_fields = ['env_global_id', ]
    autocomplete_fields = ['survey_global_id', 'env_measure_type', ]

    def add_view(self, request, extra_content=None):
        # specify the fields that can be viewed in add view
        self.fields = ['env_global_id', 'survey_global_id', 'env_measure_datetime', 'env_measure_depth', 'env_instrument',
                       'env_ctd_filename', 'env_ctd_notes', 'env_ysi_filename', 'env_ysi_model', 'env_ysi_sn',
                       'env_ysi_notes', 'env_secchi_depth', 'env_secchi_notes', 'env_niskin_number', 'env_niskin_notes',
                       'env_inst_other', 'env_measure_type', 'env_flow_rate', 'env_water_temp', 'env_salinity',
                       'env_ph_scale', 'env_par1', 'env_par2', 'env_turbidity', 'env_conductivity', 'env_do',
                       'env_pheophytin', 'env_chla', 'env_no3no2', 'env_no2', 'env_nh4', 'env_phosphate',
                       'env_substrate', 'env_lab_datetime', 'env_measure_notes', ]

        # self.exclude = ('site_prefix', 'site_num','site_id','created_datetime')
        add_fields = request.GET.copy()
        add_fields['created_by'] = request.user
        request.GET = add_fields
        return super(EnvMeasureAdmin, self).add_view(request)

    def change_view(self, request, object_id, extra_content=None):
        # specify what can be changed in admin change view
        self.fields = ['env_global_id', 'survey_global_id', 'env_measure_datetime', 'env_measure_depth', 'env_instrument',
                       'env_ctd_filename', 'env_ctd_notes', 'env_ysi_filename', 'env_ysi_model', 'env_ysi_sn',
                       'env_ysi_notes', 'env_secchi_depth', 'env_secchi_notes', 'env_niskin_number', 'env_niskin_notes',
                       'env_inst_other', 'env_measure_type', 'env_flow_rate', 'env_water_temp', 'env_salinity',
                       'env_ph_scale', 'env_par1', 'env_par2', 'env_turbidity', 'env_conductivity', 'env_do',
                       'env_pheophytin', 'env_chla', 'env_no3no2', 'env_no2', 'env_nh4', 'env_phosphate',
                       'env_substrate', 'env_lab_datetime', 'env_measure_notes',
                       'created_by', 'modified_datetime', 'created_datetime']
        # self.exclude = ('site_prefix', 'site_num','site_id','created_datetime')
        return super(EnvMeasureAdmin, self).change_view(request, object_id)

admin.site.register(EnvMeasure, EnvMeasureAdmin)


class FieldSampleAdmin(ImportExportActionModelAdmin):
    # below are import_export configs
    # SampleLabelAdminResource
    resource_class = FieldSampleAdminResource
    # changes the order of how the tables are displayed and specifies what to display
    list_display = ('sample_global_id', 'field_sample_barcode',
                    'is_extracted', 'survey_global_id', )
    readonly_fields = ('modified_datetime', 'created_datetime', 'barcode_slug', 'sample_global_id', )
    search_fields = ['sample_global_id', ]
    autocomplete_fields = ['survey_global_id', 'field_sample_barcode', ]

    def add_view(self, request, extra_content=None):
        # specify the fields that can be viewed in add view
        self.fields = ['sample_global_id', 'survey_global_id', 'field_sample_barcode', 'sample_type',
                       'is_extracted', 'created_by', ]

        # self.exclude = ('site_prefix', 'site_num','site_id','created_datetime')
        add_fields = request.GET.copy()
        add_fields['created_by'] = request.user
        request.GET = add_fields
        return super(FieldSampleAdmin, self).add_view(request)

    def change_view(self, request, object_id, extra_content=None):
        # specify what can be changed in admin change view
        self.fields = ['barcode_slug', 'sample_global_id', 'survey_global_id',
                       'field_sample_barcode', 'sample_type', 'is_extracted',
                       'created_by', 'modified_datetime', 'created_datetime', ]
        # self.exclude = ('site_prefix', 'site_num','site_id','created_datetime')
        return super(FieldSampleAdmin, self).change_view(request, object_id)

admin.site.register(FieldSample, FieldSampleAdmin)


class FilterSampleAdmin(ImportExportActionModelAdmin):
    # below are import_export configs
    resource_class = FilterSampleAdminResource
    # changes the order of how the tables are displayed and specifies what to display
    list_display = ('__str__', 'filter_datetime', 'filter_type', 'filter_method')
    readonly_fields = ('modified_datetime', 'created_datetime', )
    autocomplete_fields = ['field_sample', 'filter_protocol', ]
    search_fields = ['field_sample__sample_global_id', 'field_sample__field_sample_barcode__sample_barcode_id']

    def add_view(self, request, extra_content=None):
        # specify the fields that can be viewed in add view
        self.fields = ['field_sample', 'is_prefilter', 'filter_fname', 'filter_lname',
                       'filter_datetime', 'filter_protocol', 'filter_method', 'filter_method_other',
                       'filter_vol', 'filter_type', 'filter_type_other', 'filter_pore',
                       'filter_size', 'filter_saturation', 'filter_notes',
                       'created_by', ]

        add_fields = request.GET.copy()
        add_fields['created_by'] = request.user
        request.GET = add_fields
        return super(FilterSampleAdmin, self).add_view(request)

    def change_view(self, request, object_id, extra_content=None):
        # specify what can be changed in admin change view
        self.fields = ['field_sample', 'is_prefilter', 'filter_fname', 'filter_lname',
                       'filter_datetime', 'filter_protocol', 'filter_method', 'filter_method_other',
                       'filter_vol', 'filter_type', 'filter_type_other', 'filter_pore',
                       'filter_size', 'filter_saturation', 'filter_notes',
                       'created_by', 'modified_datetime', 'created_datetime', ]
        return super(FilterSampleAdmin, self).change_view(request, object_id)


admin.site.register(FilterSample, FilterSampleAdmin)


class SubCoreSampleAdmin(ImportExportActionModelAdmin):
    # below are import_export configs
    # SampleLabelAdminResource
    resource_class = SubCoreSampleAdminResource
    # changes the order of how the tables are displayed and specifies what to display
    list_display = ('__str__', 'subcore_datetime_start')
    readonly_fields = ('modified_datetime', 'created_datetime', )
    autocomplete_fields = ['field_sample', ]

    def add_view(self, request, extra_content=None):
        # specify the fields that can be viewed in add view
        self.fields = ['field_sample', 'subcore_fname', 'subcore_lname', 'subcore_sample_label',
                       'subcore_protocol',
                       'subcore_method', 'subcore_method_other', 'subcore_datetime_start', 'subcore_datetime_end',
                       'subcore_number', 'subcore_length', 'subcore_diameter', 'subcore_clayer', 'subcore_notes',
                       'created_by', ]

        # self.exclude = ('site_prefix', 'site_num','site_id','created_datetime')
        add_fields = request.GET.copy()
        add_fields['created_by'] = request.user
        request.GET = add_fields
        return super(SubCoreSampleAdmin, self).add_view(request)

    def change_view(self, request, object_id, extra_content=None):
        # specify what can be changed in admin change view
        self.fields = ['field_sample', 'subcore_fname', 'subcore_lname', 'subcore_sample_label',
                       'subcore_protocol',
                       'subcore_method', 'subcore_method_other', 'subcore_datetime_start', 'subcore_datetime_end',
                       'subcore_number', 'subcore_length', 'subcore_diameter', 'subcore_clayer', 'subcore_notes',
                       'created_by', 'modified_datetime', 'created_datetime', ]
        # self.exclude = ('site_prefix', 'site_num','site_id','created_datetime')
        return super(SubCoreSampleAdmin, self).change_view(request, object_id)

    # removes 'delete selected' from drop down menu
    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions
    # below are import_export configs


admin.site.register(SubCoreSample, SubCoreSampleAdmin)
