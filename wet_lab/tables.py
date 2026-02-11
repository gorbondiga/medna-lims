import django_tables2 as tables
from .models import Extraction, LibraryPrep, Pcr, PooledLibrary, RunPrep, RunResult, FastqFile
from field_survey.models import FieldSample
from django_tables2.utils import A


class ExtractionTable(tables.Table):
    _selected_action = tables.CheckBoxColumn(accessor='pk',
                                             attrs={'td': {'class': 'action-checkbox'},
                                                    'input': {'class': 'action-select'},
                                                    'th__input': {'id': 'action-toggle'},
                                                    'th': {'class': 'action-checkbox-column'}},
                                             orderable=False)
    extraction_barcode = tables.Column(verbose_name='Extraction Barcode')
    extraction_notes = tables.TemplateColumn('<data-toggle="tooltip" title="{{record.extraction_notes}}">{{ record.extraction_notes|truncatewords:5 }}', orderable=False)
    # formatting for date column - https://docs.djangoproject.com/en/4.0/ref/templates/builtins/#std:templatefilter-date
    created_datetime = tables.DateTimeColumn(format='M d, Y h:i a')
    modified_datetime = tables.DateTimeColumn(format='M d, Y h:i a')
    created_by = tables.Column(accessor='created_by.email')
    edit = tables.LinkColumn('update_extraction', text='Update', args=[A('pk')], orderable=False)

    class Meta:
        model = Extraction
        fields = ('_selected_action', 'id', 'extraction_barcode', 'process_location',
                  'extraction_datetime', 'field_sample', 'extraction_control', 'extraction_control_type',
                  'extraction_method', 'extraction_first_name', 'extraction_last_name', 'extraction_volume',
                  'extraction_volume_units', 'quantification_method', 'extraction_concentration',
                  'extraction_concentration_units', 'extraction_notes', 'barcode_slug',
                  'created_by', 'created_datetime', 'modified_datetime', )


class PcrTable(tables.Table):
    _selected_action = tables.CheckBoxColumn(accessor='pk',
                                             attrs={'td': {'class': 'action-checkbox'},
                                                    'input': {'class': 'action-select'},
                                                    'th__input': {'id': 'action-toggle'},
                                                    'th': {'class': 'action-checkbox-column'}},
                                             orderable=False)
    pcr_replicate = tables.TemplateColumn('{{ record.pcr_replicate.pcr_replicate_results.all|join:", " }}', verbose_name='Replicate Results')
    pcr_notes = tables.TemplateColumn('<data-toggle="tooltip" title="{{record.pcr_notes}}">{{ record.pcr_notes|truncatewords:5 }}', orderable=False)
    # formatting for date column
    created_datetime = tables.DateTimeColumn(format='M d, Y h:i a')
    modified_datetime = tables.DateTimeColumn(format='M d, Y h:i a')
    created_by = tables.Column(accessor='created_by.email')
    edit = tables.LinkColumn('update_pcr', text='Update', args=[A('pk')], orderable=False)

    class Meta:
        model = Pcr
        fields = ('_selected_action', 'id', 'pcr_datetime', 'process_location', 'pcr_experiment_name',
                  'pcr_type',
                  'extraction', 'primer_set', 'pcr_first_name', 'pcr_last_name',
                  'pcr_probe', 'pcr_results', 'pcr_results_units', 'pcr_replicate',
                  'pcr_thermal_cond', 'pcr_sop',
                  'pcr_notes', 'pcr_slug', 'created_by', 'created_datetime', 'modified_datetime', )


class LibraryPrepTable(tables.Table):
    _selected_action = tables.CheckBoxColumn(accessor='pk',
                                             attrs={'td': {'class': 'action-checkbox'},
                                                    'input': {'class': 'action-select'},
                                                    'th__input': {'id': 'action-toggle'},
                                                    'th': {'class': 'action-checkbox-column'}},
                                             orderable=False)
    lib_prep_notes = tables.TemplateColumn('<data-toggle="tooltip" title="{{record.lib_prep_notes}}">{{ record.lib_prep_notes|truncatewords:5 }}', orderable=False)
    # formatting for date column
    created_datetime = tables.DateTimeColumn(format='M d, Y h:i a')
    modified_datetime = tables.DateTimeColumn(format='M d, Y h:i a')
    created_by = tables.Column(accessor='created_by.email')
    edit = tables.LinkColumn('update_libraryprep', text='Update', args=[A('pk')], orderable=False)

    class Meta:
        model = LibraryPrep
        fields = ('_selected_action', 'id', 'lib_prep_experiment_name', 'lib_prep_datetime',
                  'process_location', 'extraction', 'amplification_method', 'primer_set', 'size_selection_method',
                  'index_pair', 'index_removal_method', 'quantification_method', 'lib_prep_qubit_results',
                  'lib_prep_qubit_units', 'lib_prep_qpcr_results', 'lib_prep_qpcr_units',
                  'lib_prep_final_concentration', 'lib_prep_final_concentration_units', 'lib_prep_kit',
                  'lib_prep_type', 'lib_prep_layout', 'lib_prep_thermal_cond', 'lib_prep_sop', 'lib_prep_notes', 'lib_prep_slug',
                  'created_by', 'created_datetime', 'modified_datetime', )


class PooledLibraryTable(tables.Table):
    _selected_action = tables.CheckBoxColumn(accessor='pk',
                                             attrs={'td': {'class': 'action-checkbox'},
                                                    'input': {'class': 'action-select'},
                                                    'th__input': {'id': 'action-toggle'},
                                                    'th': {'class': 'action-checkbox-column'}},
                                             orderable=False)
    pooled_lib_notes = tables.TemplateColumn('<data-toggle="tooltip" title="{{record.pooled_lib_notes}}">{{ record.pooled_lib_notes|truncatewords:5 }}', orderable=False)
    # formatting for date column
    created_datetime = tables.DateTimeColumn(format='M d, Y h:i a')
    modified_datetime = tables.DateTimeColumn(format='M d, Y h:i a')
    created_by = tables.Column(accessor='created_by.email')
    edit = tables.LinkColumn('update_pooledlibrary', text='Update', args=[A('pk')], orderable=False)

    class Meta:
        model = PooledLibrary
        fields = ('_selected_action', 'id', 'pooled_lib_label', 'pooled_lib_datetime',
                  'pooled_lib_barcode', 'process_location',
                  'library_prep', 'quantification_method',
                  'pooled_lib_concentration', 'pooled_lib_concentration_units',
                  'pooled_lib_volume', 'pooled_lib_volume_units',
                  'pooled_lib_notes', 'barcode_slug', 'pooled_lib_slug',
                  'created_by', 'created_datetime', 'modified_datetime', )


class RunPrepTable(tables.Table):
    _selected_action = tables.CheckBoxColumn(accessor='pk',
                                             attrs={'td': {'class': 'action-checkbox'},
                                                    'input': {'class': 'action-select'},
                                                    'th__input': {'id': 'action-toggle'},
                                                    'th': {'class': 'action-checkbox-column'}},
                                             orderable=False)
    run_prep_notes = tables.TemplateColumn('<data-toggle="tooltip" title="{{record.run_prep_notes}}">{{ record.run_prep_notes|truncatewords:5 }}', orderable=False)
    # formatting for date column
    created_datetime = tables.DateTimeColumn(format='M d, Y h:i a')
    modified_datetime = tables.DateTimeColumn(format='M d, Y h:i a')
    created_by = tables.Column(accessor='created_by.email')
    edit = tables.LinkColumn('update_runprep', text='Update', args=[A('pk')], orderable=False)

    class Meta:
        model = RunPrep
        fields = ('_selected_action', 'id', 'run_prep_label',
                  'run_prep_datetime', 'process_location', 'pooled_library',
                  'quantification_method', 'run_prep_concentration',
                  'run_prep_concentration_units', 'run_prep_phix_spike_in', 'run_prep_phix_spike_in_units',
                  'run_prep_notes', 'created_by', 'created_datetime', 'modified_datetime', )


class RunResultTable(tables.Table):
    _selected_action = tables.CheckBoxColumn(accessor='pk',
                                             attrs={'td': {'class': 'action-checkbox'},
                                                    'input': {'class': 'action-select'},
                                                    'th__input': {'id': 'action-toggle'},
                                                    'th': {'class': 'action-checkbox-column'}},
                                             orderable=False)
    # formatting for date column
    created_datetime = tables.DateTimeColumn(format='M d, Y h:i a')
    modified_datetime = tables.DateTimeColumn(format='M d, Y h:i a')
    created_by = tables.Column(accessor='created_by.email')
    edit = tables.LinkColumn('update_runresult', text='Update', args=[A('pk')], orderable=False)

    class Meta:
        model = RunResult
        fields = ('_selected_action', 'id', 'run_experiment_name', 'run_id',
                  'run_date', 'process_location', 'run_prep',
                  'run_completion_datetime', 'run_instrument',
                  'created_by', 'created_datetime', 'modified_datetime', )


class FastqFileTable(tables.Table):
    _selected_action = tables.CheckBoxColumn(accessor='pk',
                                             attrs={'td': {'class': 'action-checkbox'},
                                                    'input': {'class': 'action-select'},
                                                    'th__input': {'id': 'action-toggle'},
                                                    'th': {'class': 'action-checkbox-column'}},
                                             orderable=False)
    # formatting for date column
    created_datetime = tables.DateTimeColumn(format='M d, Y h:i a')
    modified_datetime = tables.DateTimeColumn(format='M d, Y h:i a')
    created_by = tables.Column(accessor='created_by.email')
    edit = tables.LinkColumn('update_fastqfile', text='Update', args=[A('pk')], orderable=False)

    class Meta:
        model = FastqFile
        fields = ('_selected_action', 'uuid', 'run_result', 'extraction', 'primer_set', 'fastq_datafile',
                  'submitted_to_insdc', 'insdc_url', 'seq_meth', 'investigation_type', 'created_by', 'created_datetime', 'modified_datetime', )


class MixsWaterTable(tables.Table):
    # MIMARKS-SURVEY - Based on FieldSample model
    _selected_action = tables.CheckBoxColumn(accessor='pk',
                                             attrs={'td': {'class': 'action-checkbox'},
                                                    'input': {'class': 'action-select'},
                                                    'th__input': {'id': 'action-toggle'},
                                                    'th': {'class': 'action-checkbox-column'}},
                                             orderable=False)
    # sample_global_id - field_survey.FieldSample
    sample_id = tables.Column(accessor='sample_global_id', verbose_name='Sample Global ID')
    # barcode_slug - field_survey.FieldSample
    barcode = tables.Column(accessor='barcode_slug', verbose_name='Sample Barcode')
    # mixs_project_name - field_survey.FieldSurvey
    project_name = tables.Column(accessor='survey_global_id.mixs_project_name', verbose_name='Project Name', orderable=False)
    # mixs_lat_lon - field_survey.FieldSurvey
    lat_lon = tables.Column(accessor='survey_global_id.mixs_lat_lon', verbose_name='Geographic Location', orderable=False)
    # mixs_geo_loc_name - field_site.FieldSite
    geo_loc_name = tables.Column(accessor='survey_global_id.site_id.mixs_geo_loc_name', verbose_name='Geographic Location', orderable=False)
    # sample_datetime - field_survey.FieldSample
    collection_date = tables.Column(accessor='sample_datetime', verbose_name='Collection Date')
    # sample_type - sample_label.SampleType
    sample_type = tables.Column(accessor='sample_type.sample_type_label', verbose_name='Sample Type')
    # sampling_method - field_survey.FieldSample
    sampling_method = tables.Column(accessor='sampling_method', verbose_name='Sampling Method', orderable=False)

    class Meta:
        model = FieldSample
        fields = ('_selected_action', 'sample_id', 'barcode', 'project_name', 'lat_lon',
                  'geo_loc_name', 'collection_date',
                  'sample_type', 'sampling_method')


class MixsSedimentTable(tables.Table):
    # MIMARKS-SURVEY - Based on FieldSample model
    _selected_action = tables.CheckBoxColumn(accessor='pk',
                                             attrs={'td': {'class': 'action-checkbox'},
                                                    'input': {'class': 'action-select'},
                                                    'th__input': {'id': 'action-toggle'},
                                                    'th': {'class': 'action-checkbox-column'}},
                                             orderable=False)
    # sample_global_id - field_survey.FieldSample
    sample_id = tables.Column(accessor='sample_global_id', verbose_name='Sample Global ID')
    # barcode_slug - field_survey.FieldSample
    barcode = tables.Column(accessor='barcode_slug', verbose_name='Sample Barcode')
    # mixs_project_name - field_survey.FieldSurvey
    project_name = tables.Column(accessor='survey_global_id.mixs_project_name', verbose_name='Project Name', orderable=False)
    # mixs_lat_lon - field_survey.FieldSurvey
    lat_lon = tables.Column(accessor='survey_global_id.mixs_lat_lon', verbose_name='Geographic Location', orderable=False)
    # mixs_depth - field_survey.SubCoreSample
    depth = tables.Column(accessor='subcore_sample.mixs_depth', verbose_name='Depth', orderable=False)
    # mixs_geo_loc_name - field_site.FieldSite
    geo_loc_name = tables.Column(accessor='survey_global_id.site_id.mixs_geo_loc_name', verbose_name='Geographic Location', orderable=False)
    # sample_datetime - field_survey.FieldSample
    collection_date = tables.Column(accessor='sample_datetime', verbose_name='Collection Date')
    # env_biome - field_site.FieldSite
    env_broad_scale = tables.Column(accessor='survey_global_id.site_id.mixs_env_broad_scale', verbose_name='Envo Broad-Scale', orderable=False)
    # env_feature - field_site.FieldSite
    env_local_scale = tables.Column(accessor='survey_global_id.site_id.mixs_env_local_scale', verbose_name='Envo Local', orderable=False)
    # mixs_env_medium - field_survey.FieldSurvey
    env_medium = tables.Column(accessor='survey_global_id.mixs_env_medium', verbose_name='Envo Medium', orderable=False)
    # sample_type - sample_label.SampleType
    sample_type = tables.Column(accessor='sample_type.sample_type_label', verbose_name='Sample Type')
    # sampling_method - field_survey.FieldSample
    sampling_method = tables.Column(accessor='sampling_method', verbose_name='Sampling Method', orderable=False)
    # mixs_samp_collect_device - field_survey.SubCoreSample
    samp_collect_device = tables.Column(accessor='subcore_sample.mixs_samp_collect_device', verbose_name='Collection Device or Method', orderable=False)
    # mixs_samp_mat_process - field_survey.SubCoreSample
    samp_mat_process = tables.Column(accessor='subcore_sample.mixs_samp_mat_process', verbose_name='Material Processing', orderable=False)
    # mixs_samp_size - field_survey.SubCoreSample
    samp_size = tables.Column(accessor='subcore_sample.mixs_samp_size', verbose_name='Collection Size', orderable=False)
    # mixs_nucl_acid_ext - wet_lab.Extraction (if extraction exists)
    nucl_acid_ext = tables.Column(accessor='extraction.mixs_nucl_acid_ext', verbose_name='Extraction SOP', orderable=False)

    class Meta:
        model = FieldSample
        fields = ('_selected_action', 'sample_id', 'barcode', 'project_name', 'lat_lon', 'depth',
                  'geo_loc_name', 'collection_date', 'env_broad_scale', 'env_local_scale', 'env_medium',
                  'sample_type', 'sampling_method', 'samp_collect_device', 'samp_mat_process', 'samp_size', 
                  'nucl_acid_ext', )
