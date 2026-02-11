import django_tables2 as tables
from .models import FieldSurvey, FieldSample, FilterSample, SubCoreSample, FieldCrew, \
    EnvMeasure, EnvMeasureType
from django_tables2.utils import A
from django.utils.html import format_html
from django.urls import reverse


class EnvMeasurementLinkColumn(tables.Column):
    """Custom column to render environmental measurement count as a link"""
    def render(self, record):
        # Handle FieldSample, FilterSample, and FieldSurvey records
        if hasattr(record, 'sample_global_id'):
            # This is a FieldSample record
            survey = record.survey_global_id
            count = survey.env_measurements.count()
            url = reverse('view_envmeasure') + f'?survey_global_id={survey.survey_global_id}'
        elif hasattr(record, 'field_sample'):
            # This is a FilterSample or SubCoreSample record
            survey = record.field_sample.survey_global_id
            count = survey.env_measurements.count()
            url = reverse('view_envmeasure') + f'?survey_global_id={survey.survey_global_id}'
        else:
            # This is a FieldSurvey record
            count = record.env_measurements.count()
            url = reverse('view_envmeasure') + f'?survey_global_id={record.survey_global_id}'
        return format_html('<a href="{}">{}</a>', url, count)


class FieldSurveyTable(tables.Table):
    _selected_action = tables.CheckBoxColumn(accessor='pk',
                                             attrs={'td': {'class': 'action-checkbox'},
                                                    'input': {'class': 'action-select'},
                                                    'th__input': {'id': 'action-toggle'},
                                                    'th': {'class': 'action-checkbox-column'}},
                                             orderable=False)
    # project_code = tables.TemplateColumn('<data-toggle="tooltip" title="{{ record.project_ids.all|join:", " }}">{{ record.project_ids.all|join:", "|truncatewords:5 }}', verbose_name='Projects')
    project_code = tables.Column(accessor='project_code', 
                                 verbose_name='Project Code')
    env_measurements = EnvMeasurementLinkColumn(verbose_name='Env Measurements',
                                                orderable=False,
                                                empty_values=())
    site_name = tables.Column(accessor='site_id.general_location_name')
    created_datetime = tables.DateTimeColumn(format='M d, Y h:i a')
    created_by = tables.Column(accessor='created_by.email')
    edit = tables.LinkColumn(viewname='update_fieldsurvey', args=[A('pk')], text='Edit')

    class Meta:
        model = FieldSurvey
        fields = ('_selected_action', 'created_datetime', 
                  'project_code', 
                  'site_name', 
                  'env_measurements',
                  'created_by', )
        order_by = ('-created_datetime', )  # use dash for descending order


class FieldCrewTable(tables.Table):
    _selected_action = tables.CheckBoxColumn(accessor='pk',
                                             attrs={'td': {'class': 'action-checkbox'},
                                                    'input': {'class': 'action-select'},
                                                    'th__input': {'id': 'action-toggle'},
                                                    'th': {'class': 'action-checkbox-column'}},
                                             orderable=False)
    # formatting for date column
    survey_datetime = tables.DateTimeColumn(accessor='survey_global_id.created_datetime', format='M d, Y h:i a', verbose_name='Survey DateTime')
    created_datetime = tables.DateTimeColumn(format='M d, Y h:i a')
    modified_datetime = tables.DateTimeColumn(format='M d, Y h:i a')
    created_by = tables.Column(accessor='created_by.email')
    edit = tables.LinkColumn(viewname='update_fieldcrew', args=[A('pk')], text='Edit')

    class Meta:
        model = FieldCrew
        fields = ('_selected_action', 'crew_global_id', 'created_datetime', 'crew_fname', 'crew_lname',
                  'survey_global_id', 'created_datetime', 'modified_datetime', 'created_by', )
        order_by = ('-created_datetime', )  # use dash for descending order


class EnvMeasureTypeTable(tables.Table):
    _selected_action = tables.CheckBoxColumn(accessor='pk',
                                             attrs={'td': {'class': 'action-checkbox'},
                                                    'input': {'class': 'action-select'},
                                                    'th__input': {'id': 'action-toggle'},
                                                    'th': {'class': 'action-checkbox-column'}},
                                             orderable=False)
    created_datetime = tables.DateTimeColumn(format='M d, Y h:i a')
    modified_datetime = tables.DateTimeColumn(format='M d, Y h:i a')
    created_by = tables.Column(accessor='created_by.email')

    class Meta:
        model = EnvMeasureType
        fields = ('_selected_action', 'env_measure_type_code', 'env_measure_type_unit', 
                  'env_measure_type_name', 'created_datetime', 'modified_datetime' )
        order_by = ('env_measure_type_code', )


class EnvMeasureTable(tables.Table):
    _selected_action = tables.CheckBoxColumn(accessor='pk',
                                             attrs={'td': {'class': 'action-checkbox'},
                                                    'input': {'class': 'action-select'},
                                                    'th__input': {'id': 'action-toggle'},
                                                    'th': {'class': 'action-checkbox-column'}},
                                             orderable=False)
    # formatting for date column
    # created_datetime = tables.DateTimeColumn(format='M d, Y h:i a')
    # modified_datetime = tables.DateTimeColumn(format='M d, Y h:i a')
    created_by = tables.Column(accessor='created_by.email')
    env_measure_name = tables.Column(accessor='env_measure_type.env_measure_type_name', verbose_name='Measure Type Name')
    env_measure_type_unit = tables.Column(accessor='env_measure_type.env_measure_type_unit', verbose_name='Measure Type Code')
    site_name = tables.Column(accessor='survey_global_id.site_name',
                              verbose_name='Site Name')
    edit = tables.LinkColumn(viewname='update_envmeasure', args=[A('pk')], text='Edit')

    class Meta:
        model = EnvMeasure
        fields = ('_selected_action', 'env_measure_datetime', 
                  'env_measure_value', 'env_measure_type_unit', 'env_measure_name', 
                  'site_name',
                  'env_instrument', 
                  'created_by', )
        order_by = ('-env_measure_datetime', ) # use dash for descending order


class FieldSampleTable(tables.Table):
    _selected_action = tables.CheckBoxColumn(accessor='pk',
                                             attrs={'td': {'class': 'action-checkbox'},
                                                    'input': {'class': 'action-select'},
                                                    'th__input': {'id': 'action-toggle'},
                                                    'th': {'class': 'action-checkbox-column'}},
                                             orderable=False)
    field_sample_barcode = tables.Column(accessor='field_sample_barcode_id',
                                         verbose_name='Field Barcode')
    env_measurements = EnvMeasurementLinkColumn(verbose_name='Env Measurements',
                                                orderable=False,
                                                empty_values=())
    survey_datetime = tables.DateTimeColumn(accessor='survey_global_id.survey_datetime', 
                                            format='M d, Y g:i a', 
                                            verbose_name='Survey DateTime')
    is_extracted = tables.Column(accessor='is_extracted', 
                                 verbose_name='Extracted')
    project_ids = tables.ManyToManyColumn(accessor='survey_global_id.project_ids', 
                                          verbose_name='Project',
                                          transform=lambda project: project.project_label)
    site_name = tables.Column(accessor='survey_global_id.site_name')
    gps_lat = tables.TemplateColumn('{{ record.survey_global_id.lat|floatformat:4 }}', verbose_name='Latitude')
    gps_lon = tables.TemplateColumn('{{ record.survey_global_id.lon|floatformat:4 }}', verbose_name='Longitude')
    gps_alt = tables.TemplateColumn('{{ record.survey_global_id.gps_alt|floatformat:4 }}')
    # formatting for date column
    created_datetime = tables.DateTimeColumn(format='M d, Y h:i a')
    modified_datetime = tables.DateTimeColumn(format='M d, Y h:i a')
    created_by = tables.Column(accessor='created_by.email')
    edit = tables.LinkColumn(viewname='update_fieldsample', args=[A('pk')], text='Edit')

    class Meta:
        model = FieldSample
        fields = ('_selected_action', 'field_sample_barcode', 
                  'env_measurements', 
                  'survey_datetime',
                  'is_extracted',
                  'project_ids',
                  'site_name',
                  'gps_lat', 'gps_lon',
                  'gps_alt',
                  'created_by', )
        order_by = ('-created_datetime', )  # use dash for descending order


class FilterSampleTable(tables.Table):
    _selected_action = tables.CheckBoxColumn(accessor='pk',
                                             attrs={'td': {'class': 'action-checkbox'},
                                                    'input': {'class': 'action-select'},
                                                    'th__input': {'id': 'action-toggle'},
                                                    'th': {'class': 'action-checkbox-column'}},
                                             orderable=False)
    field_sample_barcode = tables.Column(accessor='field_sample.field_sample_barcode_id',
                                         verbose_name='Field Barcode')
    env_measurements = EnvMeasurementLinkColumn(verbose_name='Env Measurements',
                                                orderable=False,
                                                empty_values=())
    filter_datetime = tables.DateTimeColumn(format='M d, Y g:i a', 
                                            verbose_name='Filter DateTime')
    filter_sample_label = tables.Column(verbose_name='Filter Label')
    filter_method = tables.Column(verbose_name='Filter Method')
    filter_vol = tables.TemplateColumn('{{ record.filter_vol|floatformat:2 }}', verbose_name='Volume Filtered')
    filter_type = tables.Column(verbose_name='Filter Type')
    filter_pore = tables.TemplateColumn('{{ record.filter_pore|floatformat:2 }}', verbose_name='Pore Size')
    is_extracted = tables.Column(accessor='field_sample.is_extracted', 
                                 verbose_name='Extracted')
    project_ids = tables.ManyToManyColumn(accessor='field_sample.survey_global_id.project_ids', 
                                          verbose_name='Project',
                                          transform=lambda project: project.project_label)
    site_name = tables.Column(accessor='field_sample.survey_global_id.site_name',
                              verbose_name='Site Name')
    survey_datetime = tables.DateTimeColumn(accessor='field_sample.survey_global_id.survey_datetime', 
                                            format='M d, Y g:i a', 
                                            verbose_name='Survey DateTime')
    created_datetime = tables.DateTimeColumn(format='M d, Y h:i a')
    created_by = tables.Column(accessor='created_by.email')
    edit = tables.LinkColumn(viewname='update_filtersample', args=[A('field_sample__pk')], text='Edit')

    class Meta:
        model = FilterSample
        fields = ('_selected_action', 'field_sample_barcode',
                  'env_measurements',
                  'survey_datetime',
                  'site_name',
                  'filter_method',
                  'filter_vol',
                  'filter_type',
                  'filter_pore',
                  'is_extracted',
                  'project_ids',
                  'created_by', )
        order_by = ('-created_datetime', )  # use dash for descending order


class SubCoreSampleTable(tables.Table):
    _selected_action = tables.CheckBoxColumn(accessor='pk',
                                             attrs={'td': {'class': 'action-checkbox'},
                                                    'input': {'class': 'action-select'},
                                                    'th__input': {'id': 'action-toggle'},
                                                    'th': {'class': 'action-checkbox-column'}},
                                             orderable=False)
    field_sample_barcode = tables.Column(accessor='field_sample.field_sample_barcode.sample_barcode_id', verbose_name='Field Barcode')
    survey_datetime = tables.DateTimeColumn(accessor='field_sample.survey_global_id.created_datetime', format='M d, Y h:i a', verbose_name='Survey DateTime')
    is_extracted = tables.Column(accessor='field_sample.is_extracted', verbose_name='Extracted')
    subcore_fname = tables.Column(verbose_name='SubCorer First Name')
    subcore_lname = tables.Column(verbose_name='SubCorer Last Name')
    subcore_sample_label = tables.Column(verbose_name='SubCore Label')
    subcore_datetime_start = tables.DateTimeColumn(format='M d, Y h:i a', verbose_name='SubCore Start')
    subcore_datetime_end = tables.DateTimeColumn(format='M d, Y h:i a', verbose_name='SubCore End')
    subcore_protocol = tables.Column(accessor='subcore_protocol.sop_title', verbose_name='Protocol')
    subcore_method = tables.Column(verbose_name='SubCore Method')
    subcore_number = tables.Column(verbose_name='Num SubCores')
    subcore_length = tables.TemplateColumn('{{ record.subcore_length|floatformat:2 }}', verbose_name='SubCore Length')
    subcore_diameter = tables.TemplateColumn('{{ record.subcore_diameter|floatformat:2 }}', verbose_name='SubCore Diameter')
    subcore_clayer = tables.Column(verbose_name='SubCore Consistency Layer')
    subcore_notes = tables.TemplateColumn('<data-toggle="tooltip" title="{{ record.subcore_notes }}">{{ record.subcore_notes|truncatewords:5 }}', verbose_name='SubCore Notes')
    project_ids = tables.ManyToManyColumn(accessor='field_sample.survey_global_id.project_ids.project_label', verbose_name='Project')
    supervisor = tables.Column(accessor='field_sample.survey_global_id.supervisor.email', verbose_name='Supervisor')
    username = tables.Column(accessor='field_sample.survey_global_id.username.email', verbose_name='Username')
    site_id = tables.Column(accessor='field_sample.survey_global_id.site_id.site_id')
    site_name = tables.Column(accessor='field_sample.survey_global_id.site_name')
    survey_complete = tables.Column(accessor='field_sample.survey_global_id.survey_complete')
    qa_editor = tables.Column(accessor='field_sample.survey_global_id.qa_editor.email')
    qa_datetime = tables.DateTimeColumn(accessor='field_sample.survey_global_id.qa_datetime', format='M d, Y h:i a')
    gps_lat = tables.TemplateColumn('{{ record.field_sample.survey_global_id.surveglobal_id.lat|floatformat:4 }}', verbose_name='Latitude')
    gps_lon = tables.TemplateColumn('{{ record.field_sample.survey_global_id.lon|floatformat:4 }}', verbose_name='Longitude')
    gps_alt = tables.TemplateColumn('{{ record.field_sample.survey_global_id.gps_alt|floatformat:4 }}')
    gps_horacc = tables.TemplateColumn('{{ record.field_sample.survey_global_id.gps_horacc|floatformat:4 }}')
    gps_vertacc = tables.TemplateColumn('{{ record.field_sample.survey_global_id.gps_vertacc|floatformat:4 }}')
    sample_global_id = tables.Column(accessor='field_sample.sample_global_id', verbose_name='Sample Global ID')
    survey_global_id = tables.Column(accessor='field_sample.survey_global_id.pk', verbose_name='Collection Global ID')
    survey_global_id = tables.Column(accessor='field_sample.survey_global_id.survey_global_id.pk', verbose_name='Survey Global ID')
    # formatting for date column
    created_datetime = tables.DateTimeColumn(format='M d, Y h:i a')
    modified_datetime = tables.DateTimeColumn(format='M d, Y h:i a')
    created_by = tables.Column(accessor='created_by.email')
    edit = tables.LinkColumn(viewname='update_subcoresample', args=[A('pk')], text='Edit')

    class Meta:
        model = SubCoreSample
        fields = ('_selected_action', 'field_sample_barcode', 'core_label', 'created_datetime', 'is_extracted',
                  'subcore_fname', 'subcore_lname', 'subcore_sample_label', 'core_control', 'subcore_datetime_start', 'subcore_datetime_end',
                  'subcore_protocol',
                  'subcore_method', 'subcore_number', 'subcore_length', 'subcore_diameter', 'subcore_clayer', 'subcore_notes',
                  'core_notes', 'core_datetime_start', 'project_ids', 'supervisor', 'username',
                  'site_id', 'site_name',
                  'survey_complete', 'qa_editor', 'qa_datetime',
                  'gps_lat', 'gps_lon',
                  'gps_alt', 'gps_horacc', 'gps_vertacc',
                  'sample_global_id', 'survey_global_id', 'survey_global_id',
                  'created_datetime', 'modified_datetime', 'created_by', )
        order_by = ('-created_datetime', )  # use dash for descending order
