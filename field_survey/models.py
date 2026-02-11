from django.contrib.gis.db import models
from django.conf import settings
# from django.utils.text import slugify
# from django.db.models import Q
import uuid
from django.utils import timezone
from django.utils.text import slugify
from utility.enumerations import YesNo, MeasureModes, \
    EnvInstruments, \
    FilterLocations, \
    FilterMethods, FilterTypes, SubSedimentMethods, \
    SamplingMethods
from utility.models import DateTimeUserMixin, get_sentinel_user, \
    slug_date_format


class FieldSurvey(DateTimeUserMixin):
    # With RESTRICT, if fund is deleted but system and watershed still exists, it will not cascade delete
    # unless all 3 related fields are gone.
    survey_global_id = models.UUIDField(verbose_name='Survey Global ID', 
                                        primary_key=True, 
                                        editable=False, 
                                        default=uuid.uuid4)
    survey_code = models.CharField('Survey Code',
                                    max_length=255,
                                    unique=True,
                                    blank=True,
                                    null=True)
    survey_datetime = models.DateTimeField('Survey DateTime',
                                           default=timezone.now)
    username = models.ForeignKey(settings.AUTH_USER_MODEL, 
                                 blank=True, 
                                 null=True, 
                                 verbose_name='Username', 
                                 on_delete=models.SET(get_sentinel_user), 
                                 related_name='username')
    # prj_ids
    project_ids = models.ManyToManyField('utility.Project', 
                                         verbose_name='Affiliated Project(s)', 
                                         related_name='project_ids')
    supervisor = models.ForeignKey(settings.AUTH_USER_MODEL, 
                                   blank=True, 
                                   null=True, 
                                   verbose_name='Supervisor', 
                                   on_delete=models.SET(get_sentinel_user), 
                                   related_name='supervisor')
    # recdr_fname
    recorder_fname = models.CharField('Recorder First Name', 
                                      blank=True, 
                                      max_length=255)
    # recdr_lname
    recorder_lname = models.CharField('Recorder Last Name', 
                                      blank=True, 
                                      max_length=255)
    site_id = models.ForeignKey('field_site.FieldSite', 
                                on_delete=models.RESTRICT)
    # by boat or by foot
    env_measure_mode = models.CharField('Collection Mode', 
                                        blank=True, 
                                        max_length=50, 
                                        choices=MeasureModes.choices)
    survey_complete = models.CharField('Survey Complete', 
                                       blank=True, 
                                       max_length=50, 
                                       choices=YesNo.choices)
    gps_alt = models.DecimalField('GPS Altitude (m)', blank=True, null=True, max_digits=22, decimal_places=16)



    @property
    def mixs_project_name(self):
        # mixs_v5
        # Name of the project within which the sequencing was organized
        prjs = self.project_ids.all()
        prjs_list = prjs.values_list('project_label', flat=True)
        return 'Maine-eDNA {project}'.format(project=list(prjs_list))


    @property
    def mixs_lat_lon(self):
        # Use the geom from the linked site_id
        if self.site_id and self.site_id.geom:
            lat_fmt = '{:.4f}'.format(self.site_id.geom.y)
            lon_fmt = '{:.4f}'.format(self.site_id.geom.x)
            return '{lat} {lon}'.format(lat=lat_fmt, lon=lon_fmt)
        return None


    @property
    def lat(self):
        return self.site_id.geom.y if self.site_id and self.site_id.geom else None

    @property
    def lon(self):
        return self.site_id.geom.x if self.site_id and self.site_id.geom else None

    @property
    def geom(self):
        return self.site_id.geom
    
    @property
    def srid(self):
        return self.site_id.geom.srid if self.site_id and self.site_id.geom else None

    @property
    def site_name(self):
        """Returns the general location name from the related FieldSite"""
        return self.site_id.general_location_name if self.site_id else None

    @property
    def site_code(self):
        """Returns the site_id code from the related FieldSite"""
        return self.site_id.site_id if self.site_id else None

    @property
    def country_code(self):
        """Returns the country code from the related FieldSite"""
        return self.site_id.country_code if self.site_id else None
    
    @property
    def project_code(self):
        """Returns all the project code from the related Project(s)"""
        prj = self.project_ids.all()
        return ', '.join([p.project_code for p in prj]) if prj else None

    def __str__(self):
        return str(self.survey_global_id)

    class Meta:
        app_label = 'field_survey'
        verbose_name = 'Field Survey'
        verbose_name_plural = 'Field Surveys'


class FieldCrew(DateTimeUserMixin):
    crew_global_id = models.UUIDField('Crew Global ID', primary_key=True, editable=False, default=uuid.uuid4)
    crew_fname = models.CharField('Crew First Name', blank=True, max_length=255)
    crew_lname = models.CharField('Crew Last Name', blank=True, max_length=255)
    survey_global_id = models.ForeignKey(FieldSurvey, db_column='survey_global_id', related_name='field_crew', on_delete=models.CASCADE)

    @property
    def crew_full_name(self):
        return '{fname} {lname}'.format(fname=self.crew_fname, lname=self.crew_lname)

    def __str__(self):
        return str(self.crew_global_id)

    class Meta:
        app_label = 'field_survey'
        verbose_name = 'Field Crew'
        verbose_name_plural = 'Field Crew'


class EnvMeasureType(DateTimeUserMixin):
    # env_flow, env_water_temp, env_salinity, env_ph, env_par1, env_par2, env_turbidity, env_conductivity,
    # env_do, env_pheophytin, env_chla, env_no3no2, env_no2, env_nh4, env_phosphate, env_substrate,
    # env_labdatetime, env_dnotes
    env_measure_uuid = models.UUIDField(verbose_name='EnvMeasure UUID', 
                                        primary_key=True, 
                                        default=uuid.uuid4)
    env_measure_type_code = models.CharField('Measure Code', unique=True, max_length=255)
    env_measure_type_unit = models.CharField('Measure Unit', max_length=255)
    env_measure_type_name = models.SlugField('Measure Name', max_length=255)

    def __str__(self):
        return '{code}: {name}'.format(code=self.env_measure_type_code, name=self.env_measure_type_name)

    class Meta:
        app_label = 'field_survey'
        verbose_name = 'Env Measure Type'
        verbose_name_plural = 'Env Measure Types'


class EnvMeasure(DateTimeUserMixin):
    env_global_id = models.UUIDField(verbose_name='EnvMeas Global ID', 
                                     primary_key=True, 
                                     editable=False, 
                                     default=uuid.uuid4)
    env_measure_datetime = models.DateTimeField('Measurement DateTime', 
                                                auto_now=True)
    env_instrument = models.TextField('Instruments Used', 
                                      blank=True, 
                                      choices=EnvInstruments.choices)
    # Env measurement type FK and value
    env_measure_type = models.ForeignKey(EnvMeasureType, 
                                        verbose_name='Environmental Measurement(s)', 
                                        related_name='env_measure_types',
                                        on_delete=models.PROTECT)
    env_measure_value = models.CharField('Value', blank=True, max_length=255)
    env_measure_notes = models.TextField('Measurement Notes', blank=True)
    survey_global_id = models.ForeignKey(FieldSurvey, 
                                         db_column='survey_global_id', 
                                         related_name='env_measurements', 
                                         on_delete=models.CASCADE)

    def __str__(self):
        return str(self.env_global_id)

    class Meta:
        app_label = 'field_survey'
        verbose_name = 'Env Measurement'
        verbose_name_plural = 'Env Measurements'
        unique_together = [['survey_global_id', 'env_measure_datetime',
                            'env_measure_type', 'env_measure_value']]


class FieldSample(DateTimeUserMixin):
    # mixs source_mat_id
    sample_global_id = models.UUIDField(verbose_name='Sample Global ID', 
                                        primary_key=True, 
                                        editable=False, 
                                        default=uuid.uuid4)
    sample_code = models.CharField('Sample Code', max_length=255, 
                                   unique=True,
                                   blank=True,
                                   null=True)
    sample_datetime = models.DateTimeField('Sample DateTime',
                                           default=timezone.now)
    field_sample_barcode = models.OneToOneField('sample_label.SampleBarcode', 
                                                related_name='field_sample_barcode', 
                                                on_delete=models.CASCADE)
    survey_global_id = models.ForeignKey(FieldSurvey, 
                                         db_column='survey_global_id', 
                                         related_name='field_samples',
                                        on_delete=models.CASCADE)
    barcode_slug = models.SlugField('Field Sample Barcode Slug', max_length=255)
    is_extracted = models.CharField('Extracted', max_length=3, 
                                    choices=YesNo.choices, 
                                    default=YesNo.NO)
    sampling_method = models.CharField('Sampling Method', max_length=255, 
                                       blank=True,
                                       choices=SamplingMethods.choices)
    sample_type = models.ForeignKey('sample_label.SampleType', 
                                    on_delete=models.RESTRICT)

    def __str__(self):
        return '{barcode}: {gid}'.format(barcode=self.barcode_slug, gid=self.sample_global_id)

    def save(self, *args, **kwargs):
        from sample_label.models import update_barcode_sample_type, get_field_sample_sample_type
        if self.field_sample_barcode:
            # update_barcode_sample_type must come before creating barcode_slug
            # because need to grab old barcode_slug value on updates
            # update barcode to type == Field Sample
            update_barcode_sample_type(self.barcode_slug, self.field_sample_barcode, get_field_sample_sample_type())
            self.barcode_slug = self.field_sample_barcode.barcode_slug
        # all done, time to save changes to the db
        super(FieldSample, self).save(*args, **kwargs)

    class Meta:
        app_label = 'field_survey'
        verbose_name = 'Field Sample'
        verbose_name_plural = 'Field Samples'


class FilterSample(DateTimeUserMixin):
    field_sample = models.OneToOneField(FieldSample, 
                                        primary_key=True, 
                                        related_name='filter_sample', 
                                        on_delete=models.CASCADE)
    is_prefilter = models.CharField('Prefilter', 
                                    blank=True, 
                                    max_length=50, 
                                    choices=YesNo.choices)
    filter_fname = models.CharField('Filterer First Name', blank=True, max_length=255)
    filter_lname = models.CharField('Filterer Last Name', blank=True, max_length=255)
    filter_datetime = models.DateTimeField('Filter DateTime', blank=True, null=True)
    filter_protocol = models.ForeignKey('utility.StandardOperatingProcedure', 
                                        blank=True, null=True, 
                                        verbose_name='Filter Protocol', 
                                        on_delete=models.RESTRICT)
    filter_method = models.CharField('Filter Method', blank=True, 
                                     max_length=50, 
                                     choices=FilterMethods.choices)
    filter_method_other = models.CharField('Other Filter Method', blank=True, max_length=255)
    filter_vol = models.DecimalField('Water Volume Filtered', 
                                     blank=True, 
                                     null=True, 
                                     max_digits=15, 
                                     decimal_places=10)
    filter_type = models.CharField('Filter Type', blank=True, 
                                   max_length=50, 
                                   choices=FilterTypes.choices)
    filter_type_other = models.CharField('Other Filter Type', blank=True, max_length=255)
    filter_pore = models.DecimalField('Filter Pore Size', blank=True, null=True, 
                                      max_digits=15, 
                                      decimal_places=10)
    filter_size = models.DecimalField('Filter Size', blank=True, null=True, 
                                      max_digits=15, 
                                      decimal_places=10)
    filter_saturation = models.BooleanField('Saturation', 
                                            blank=True, 
                                            null=True)
    filter_notes = models.TextField('Filter Notes', blank=True)

    def __str__(self):
        return str(self.field_sample)

    class Meta:
        app_label = 'field_survey'
        verbose_name = 'Filter Sample'
        verbose_name_plural = 'Filter Samples'


class SubCoreSample(DateTimeUserMixin):
    field_sample = models.OneToOneField(FieldSample, primary_key=True, related_name='subcore_sample', on_delete=models.CASCADE)
    subcore_fname = models.CharField('Sub-Corer First Name', blank=True, max_length=255)
    subcore_lname = models.CharField('Sub-Corer Last Name', blank=True, max_length=255)
    subcore_sample_label = models.CharField('Sub-Core Sample Label', blank=True, max_length=255)
    subcore_protocol = models.ForeignKey('utility.StandardOperatingProcedure', blank=True, null=True, verbose_name='Sub-Core Protocol', on_delete=models.RESTRICT)
    # subcore_protocol_other = models.CharField('Other Sub-Core Protocol', blank=True, max_length=255)
    subcore_method = models.CharField('Sub-Core Method', blank=True, max_length=50, choices=SubSedimentMethods.choices)
    subcore_method_other = models.CharField('Other Sub-Core Method', blank=True, max_length=255)
    subcore_datetime_start = models.DateTimeField('Sub-Core DateTime Start', blank=True, null=True)
    subcore_datetime_end = models.DateTimeField('Sub-Core DateTime End', blank=True, null=True)
    subcore_number = models.IntegerField('Number of Sub-Cores', blank=True, null=True)
    subcore_length = models.DecimalField('Sub-Core Length (cm)', blank=True, null=True, max_digits=15, decimal_places=10)
    subcore_diameter = models.DecimalField('Sub-Core Diameter (cm)', blank=True, null=True, max_digits=15, decimal_places=10)
    subcore_clayer = models.IntegerField('Sub-Core Consistency Layer', blank=True, null=True)
    subcore_notes = models.TextField('Sub-Core Notes', blank=True)

    def __str__(self):
        return str(self.field_sample)

    class Meta:
        app_label = 'field_survey'
        verbose_name = 'SubCore Sample'
        verbose_name_plural = 'SubCore Samples'
