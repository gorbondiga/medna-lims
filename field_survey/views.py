import csv

from django.db import transaction
from django.db.models import F, Count, Func, Value, CharField, Q
from django.db.models.functions import TruncMonth
from django.core.serializers import serialize
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic.edit import CreateView, UpdateView
import json
from django_filters import rest_framework as filters
from django_tables2.views import SingleTableMixin
from django_filters.views import FilterView
from rest_framework import generics
from rest_framework import viewsets
from utility.charts import return_queryset_lists, return_zeros_lists, return_merged_zeros_lists
from utility.views import export_context, CreatePopupMixin, UpdatePopupMixin
from utility.serializers import CharSerializerExportMixin
from utility.enumerations import CollectionTypes
from sample_label.models import SampleMaterial
import field_survey.filters as fieldsurvey_filters
import field_survey.serializers as fieldsurvey_serializers
from .models import FieldSurvey, FieldCrew, EnvMeasureType, EnvMeasure, \
    FieldSample, FilterSample, SubCoreSample
from .resources import FieldSurveyAdminResource, FieldSampleAdminResource
from .tables import FieldSurveyTable, FieldCrewTable, EnvMeasureTable, EnvMeasureTypeTable, \
    FieldSampleTable, FilterSampleTable, SubCoreSampleTable
from .forms import FieldSurveyForm, FieldCrewForm, EnvMeasureForm, \
    FieldSampleForm, FilterSampleForm, SubCoreSampleForm
from django.conf import settings
from import_export.formats.base_formats import CSV, XLS, XLSX
from import_export.forms import ImportForm


# Create your views here.
########################################
# FRONTEND REQUESTS                    #
########################################
@permission_required('field_survey.view_fieldsurvey', 
                     login_url='dashboard_login')
@login_required(login_url='dashboard_login')
def get_field_survey_geom(request):
    # https://simpleisbetterthancomplex.com/tutorial/2020/01/19/how-to-use-chart-js-with-django.html
    # https://www.paulox.net/2020/12/08/maps-with-django-part-1-geodjango-spatialite-and-leaflet/
    # https://leafletjs.com/examples/geojson/
    # https://stackoverflow.com/questions/52025577/how-to-remove-certain-fields-when-doing-serialization-to-a-django-model
    # project = get_object_or_404(Project, pk=pk)
    # We can't use serialize('geojson', ...) directly on FieldSurvey since geom is not a model field.
    # Instead, serialize FieldSite and join FieldSurvey data in properties.
    qs = FieldSurvey.objects.select_related('site_id').prefetch_related('project_ids')
    features = []
    for survey in qs:
        geom = survey.site_id.geom if survey.site_id and survey.site_id.geom else None
        geometry = geom.geojson if geom else None  # geometry as string
        projects = list(survey.project_ids.values_list('pk', flat=True))
        properties = {
            "survey_global_id": str(survey.survey_global_id),
            "created_datetime": survey.created_datetime.isoformat() if survey.created_datetime else None,
            "site_id": survey.site_id.pk if survey.site_id else None,
            "project_ids": projects,
        }
        feature = {
            "type": "Feature",
            "geometry": json.loads(geometry) if geometry else None,
            "properties": properties
        }
        features.append(feature)
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    return JsonResponse(geojson)


def get_project_survey_geom(request, pk):
    # https://simpleisbetterthancomplex.com/tutorial/2020/01/19/how-to-use-chart-js-with-django.html
    # https://www.paulox.net/2020/12/08/maps-with-django-part-1-geodjango-spatialite-and-leaflet/
    # https://leafletjs.com/examples/geojson/
    # https://stackoverflow.com/questions/52025577/how-to-remove-certain-fields-when-doing-serialization-to-a-django-model
    # project = get_object_or_404(Project, pk=pk)
    qs = FieldSurvey.objects.only('survey_global_id', 'geom', 'site_id', 'project_ids').prefetch_related('project_ids', 'site_id').filter(project_ids=pk)
    qs_json = serialize('geojson', qs, fields=('survey_global_id', 'geom', 'created_datetime', 'site_id', 'project_ids'))
    return JsonResponse(json.loads(qs_json))


@login_required(login_url='dashboard_login')
def get_survey_count_chart(request):
    # https://simpleisbetterthancomplex.com/tutorial/2020/01/19/how-to-use-chart-js-with-django.html
    # https://stackoverflow.com/questions/38570258/how-to-get-django-queryset-results-with-formatted-datetime-field
    # https://stackoverflow.com/questions/52354104/django-query-set-for-counting-records-each-month
    # labels, data = return_queryset_lists(FieldSurvey.objects.annotate(survey_date=TruncMonth('created_datetime')).values('survey_date').order_by('survey_date').annotate(data=Count('pk')).annotate(label=Func(F('created_datetime'), Value('MM/YYYY'), function='to_char', output_field=CharField())))
    labels, data = return_queryset_lists(FieldSurvey.objects.annotate(survey_date=TruncMonth('created_datetime')).values('survey_date').annotate(data=Count('pk')).order_by('survey_date').annotate(label=Func(F('survey_date'), Value('MM/YYYY'), function='to_char', output_field=CharField())))
    labels, data = return_zeros_lists(labels, data)
    return JsonResponse(data={'labels': labels, 'data': data, })


@login_required(login_url='dashboard_login')
def get_survey_system_count_chart(request):
    # https://simpleisbetterthancomplex.com/tutorial/2020/01/19/how-to-use-chart-js-with-django.html
    # https://stackoverflow.com/questions/31933239/using-annotate-or-extra-to-add-field-of-foreignkey-to-queryset-equivalent-of/31933276#31933276
    labels, data = return_queryset_lists(FieldSurvey.objects.exclude(Q(site_id__system__system_label__exact='') | Q(site_id__system__system_label__isnull=True)).annotate(label=F('site_id__system__system_label')).values('label').annotate(data=Count('pk')).order_by('-label'))
    # labels = ['Other' if x == '' else x for x in labels]
    return JsonResponse(data={'labels': labels, 'data': data, })


@login_required(login_url='dashboard_login')
def get_survey_site_count_chart(request):
    # https://simpleisbetterthancomplex.com/tutorial/2020/01/19/how-to-use-chart-js-with-django.html
    labels, data = return_queryset_lists(FieldSurvey.objects.exclude(Q(site_id__site_id__exact='') | Q(site_id__site_id__isnull=True)).annotate(label=F('site_id__site_id')).values('label').annotate(data=Count('pk')).order_by('-label'))
    # labels = ['eLP_O01' if x == '' else x for x in labels]
    return JsonResponse(data={'labels': labels, 'data': data, })


@login_required(login_url='dashboard_login')
def get_field_sample_count_chart(request):
    # https://simpleisbetterthancomplex.com/tutorial/2020/01/19/how-to-use-chart-js-with-django.html
    # https://stackoverflow.com/questions/38570258/how-to-get-django-queryset-results-with-formatted-datetime-field
    # https://stackoverflow.com/questions/52354104/django-query-set-for-counting-records-each-month
    filter_labels, filter_data = return_queryset_lists(FilterSample.objects.annotate(filter_date=TruncMonth('filter_datetime')).values('filter_date').annotate(data=Count('pk')).annotate(label=Func(F('filter_datetime'), Value('MM/YYYY'), function='to_char', output_field=CharField())))
    subcore_labels, subcore_data = return_queryset_lists(SubCoreSample.objects.annotate(subcore_date=TruncMonth('subcore_datetime_start')).values('subcore_date').annotate(data=Count('pk')).annotate(label=Func(F('subcore_datetime_start'), Value('MM/YYYY'), function='to_char', output_field=CharField())))
    fieldsample_labels, fieldsample_data = return_queryset_lists(FieldSample.objects.annotate(label=F('is_extracted')).values('label').annotate(data=Count('pk')).order_by('-label'))
    labels, data_array, = return_merged_zeros_lists([filter_labels, subcore_labels], [filter_data, subcore_data])
    print(data_array)
    return JsonResponse(data={
        'fieldsample_labels': fieldsample_labels,
        'fieldsample_data': fieldsample_data,
        'count_labels': labels,
        'filter_data': data_array[0],
        'subcore_data': data_array[1],
    })


@login_required(login_url='dashboard_login')
def get_filter_type_count_chart(request):
    # https://simpleisbetterthancomplex.com/tutorial/2020/01/19/how-to-use-chart-js-with-django.html
    # https://stackoverflow.com/questions/31933239/using-annotate-or-extra-to-add-field-of-foreignkey-to-queryset-equivalent-of/31933276#31933276
    labels, data = return_queryset_lists(FilterSample.objects.exclude(Q(filter_type__exact='') | Q(filter_type__isnull=True)).annotate(label=F('filter_type')).values('label').annotate(data=Count('pk')).order_by('-label'))
    # labels = ['other' if x == '' else x for x in labels]
    return JsonResponse(data={'labels': labels, 'data': data, })


@login_required(login_url='dashboard_login')
def get_filter_system_count_chart(request):
    # https://simpleisbetterthancomplex.com/tutorial/2020/01/19/how-to-use-chart-js-with-django.html
    # https://stackoverflow.com/questions/31933239/using-annotate-or-extra-to-add-field-of-foreignkey-to-queryset-equivalent-of/31933276#31933276
    labels, data = return_queryset_lists(FilterSample.objects.exclude(Q(field_sample__field_sample_barcode__site_id__system__system_label__exact='') | Q(field_sample__field_sample_barcode__site_id__system__system_label__isnull=True)).annotate(label=F('field_sample__field_sample_barcode__site_id__system__system_label')).values('label').annotate(data=Count('pk')).order_by('-label'))
    # labels = ['Other' if x == '' else x for x in labels]
    return JsonResponse(data={'labels': labels, 'data': data, })


@login_required(login_url='dashboard_login')
def get_filter_site_count_chart(request):
    # https://simpleisbetterthancomplex.com/tutorial/2020/01/19/how-to-use-chart-js-with-django.html
    # https://stackoverflow.com/questions/31933239/using-annotate-or-extra-to-add-field-of-foreignkey-to-queryset-equivalent-of/31933276#31933276
    labels, data = return_queryset_lists(FilterSample.objects.exclude(Q(field_sample__field_sample_barcode__site_id__site_id__exact='') | Q(field_sample__field_sample_barcode__site_id__site_id__isnull=True)).annotate(label=F('field_sample__field_sample_barcode__site_id__site_id')).values('label').annotate(data=Count('pk')).order_by('-label'))
    # labels = ['Other' if x == '' else x for x in labels]
    return JsonResponse(data={'labels': labels, 'data': data, })


########################################
# FRONTEND VIEWS                       #
########################################
class FieldSurveyFilterView(LoginRequiredMixin, PermissionRequiredMixin, 
                            CharSerializerExportMixin, SingleTableMixin, 
                            FilterView):
    # permissions - https://stackoverflow.com/questions/9469590/check-permission-inside-a-template-in-django
    # View site filter view with REST serializer and django-tables2
    # export_formats = ['csv','xlsx'] # set in user_sites in default
    model = FieldSurvey
    table_class = FieldSurveyTable
    template_name = 'home/django-material-dashboard/model-filter-list-fieldsurvey.html'
    permission_required = ('field_survey.view_fieldsurvey', )
    export_name = 'fieldsurvey_' + str(timezone.now().replace(microsecond=0).isoformat())
    serializer_class = fieldsurvey_serializers.FieldSurveyTableSerializer
    filter_backends = [filters.DjangoFilterBackend]
    export_formats = settings.EXPORT_FORMATS

    def get_context_data(self, **kwargs):
        # Return the view context data.
        context = super().get_context_data(**kwargs)
        context['segment'] = 'view_fieldsurvey'
        context['page_title'] = 'Field Survey'
        context['export_formats'] = self.export_formats
        context = {**context, **export_context(self.request, self.export_formats)}
        return context

    def handle_no_permission(self):
        if self.raise_exception:
            raise PermissionDenied(self.get_permission_denied_message())
        return redirect('main/model-perms-required.html')


class FieldSurveyCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    # LoginRequiredMixin prevents users who aren’t logged in from accessing the form.
    # If you omit that, you’ll need to handle unauthorized users in form_valid().
    permission_required = 'field_survey.add_fieldsurvey'
    model = FieldSurvey
    form_class = FieldSurveyForm
    # fields = ['site_id', 'sample_material', 'sample_type', 'sample_year', 'purpose', 'req_sample_label_num']
    template_name = 'home/django-material-dashboard/model-add-fieldsurvey.html'

    def get_context_data(self, **kwargs):
        # Return the view context data.
        context = super().get_context_data(**kwargs)
        context['segment'] = 'add_fieldsurvey'
        context['page_title'] = 'Field Survey'
        return context

    # Sending user object to the form, to verify which fields to display
    def get_form_kwargs(self):
        kwargs = super(FieldSurveyCreateView, self).get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.created_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('view_fieldsurvey')

    def handle_no_permission(self):
        if self.raise_exception:
            raise PermissionDenied(self.get_permission_denied_message())
        return redirect('main/model-perms-required.html')


class FieldSurveyImportView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    View for importing FieldSurvey data from CSV/Excel files
    Uses django-import-export's ImportForm for better handling
    """
    permission_required = 'field_survey.add_fieldsurvey'
    template_name = 'home/django-material-dashboard/model-import-fieldsurvey.html'
    resource_class = FieldSurveyAdminResource
    formats = [CSV, XLS, XLSX]
    
    def get(self, request):
        """Display the import form"""
        form = ImportForm(self.formats)
        context = {
            'segment': 'import_fieldsurvey',
            'page_title': 'Import Field Survey',
            'form': form,
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle file upload and import"""
        form = ImportForm(self.formats, request.POST, request.FILES)
        
        if not form.is_valid():
            messages.error(request, 'Invalid form submission.')
            context = {
                'segment': 'import_fieldsurvey',
                'page_title': 'Import Field Survey',
                'form': form,
            }
            return render(request, self.template_name, context)
        
        resource = self.resource_class()
        
        # Get the uploaded file and format
        import_file = form.cleaned_data['import_file']
        input_format_index = int(form.cleaned_data['input_format'] or 0)
        input_format = self.formats[input_format_index]()
        
        try:
            # Read and parse the file using the selected format
            data = import_file.read()
            if isinstance(input_format, CSV):
                data = data.decode('utf-8')
            
            dataset = input_format.create_dataset(data)
            
            # Dry run to check for errors
            result = resource.import_data(dataset, dry_run=True, raise_errors=False)
            
            if result.has_errors():
                error_messages = []
                for row_errors in result.row_errors():
                    row_num = row_errors[0]
                    errors = row_errors[1]
                    for error in errors:
                        error_messages.append(f"Row {row_num}: {error.error}")
                
                # Show first 5 errors
                messages.error(request, 'Import validation failed with errors:')
                for msg in error_messages[:5]:
                    messages.error(request, msg)
                
                if len(error_messages) > 5:
                    messages.warning(request, f'... and {len(error_messages) - 5} more errors')
                
                context = {
                    'segment': 'import_fieldsurvey',
                    'page_title': 'Import Field Survey',
                    'form': form,
                }
                return render(request, self.template_name, context)
            
            # If no errors, perform the actual import
            result = resource.import_data(dataset, dry_run=False, raise_errors=True)
            
            # Show success message with statistics
            success_msg = f'Successfully imported {result.totals["new"]} new records'
            if result.totals["update"] > 0:
                success_msg += f', updated {result.totals["update"]} records'
            if result.totals["skip"] > 0:
                success_msg += f', skipped {result.totals["skip"]} records'
            
            messages.success(request, success_msg)
            return redirect('view_fieldsurvey')
            
        except Exception as e:
            messages.error(request, f'Import failed: {str(e)}')
            context = {
                'segment': 'import_fieldsurvey',
                'page_title': 'Import Field Survey',
                'form': form,
            }
            return render(request, self.template_name, context)
    
    def handle_no_permission(self):
        if self.raise_exception:
            raise PermissionDenied(self.get_permission_denied_message())
        return redirect('main/model-perms-required.html')


class FieldSurveyUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = FieldSurvey
    form_class = FieldSurveyForm
    login_url = '/dashboard/login/'
    redirect_field_name = 'next'
    template_name = 'home/django-material-dashboard/model-update-fieldsurvey.html'
    permission_required = ('field_survey.update_fieldsurvey', 'field_survey.view_fieldsurvey', )

    def get_context_data(self, **kwargs):
        # Return the view context data.
        context = super().get_context_data(**kwargs)
        context['segment'] = 'update_fieldsurvey'
        context['page_title'] = 'Field Survey'
        return context

    def handle_no_permission(self):
        if self.raise_exception:
            raise PermissionDenied(self.get_permission_denied_message())
        return redirect('main/model-perms-required.html')

    def get_success_url(self):
        # after successfully filling out and submitting a form,
        # show the user the detail view of the label
        return reverse('view_fieldsurvey')


class FieldSurveyPopupCreateView(CreatePopupMixin, LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    # LoginRequiredMixin prevents users who aren’t logged in from accessing the form.
    # If you omit that, you’ll need to handle unauthorized users in form_valid().
    permission_required = 'field_survey.add_fieldsurvey'
    model = FieldSurvey
    form_class = FieldSurveyForm
    # fields = ['site_id', 'sample_material', 'sample_type', 'sample_year', 'purpose', 'req_sample_label_num']
    template_name = 'home/django-material-dashboard/model-add-popup-fieldsurvey.html'

    def get_context_data(self, **kwargs):
        # Return the view context data.
        context = super().get_context_data(**kwargs)
        context['segment'] = 'add_fieldsurvey'
        context['page_title'] = 'Field Survey'
        return context

    # Sending user object to the form, to verify which fields to display
    def get_form_kwargs(self):
        kwargs = super(FieldSurveyPopupCreateView, self).get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.created_by = self.request.user
        return super().form_valid(form)

    def handle_no_permission(self):
        if self.raise_exception:
            raise PermissionDenied(self.get_permission_denied_message())
        return redirect('main/model-perms-required.html')


class FieldSurveyPopupUpdateView(UpdatePopupMixin, LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = FieldSurvey
    form_class = FieldSurveyForm
    login_url = '/dashboard/login/'
    redirect_field_name = 'next'
    template_name = 'home/django-material-dashboard/model-update-popup-fieldsurvey.html'
    permission_required = ('field_survey.update_fieldsurvey', 'field_survey.view_fieldsurvey', )

    def get_context_data(self, **kwargs):
        # Return the view context data.
        context = super().get_context_data(**kwargs)
        context['segment'] = 'update_fieldsurvey'
        context['page_title'] = 'Field Survey'
        return context

    def handle_no_permission(self):
        if self.raise_exception:
            raise PermissionDenied(self.get_permission_denied_message())
        return redirect('main/model-perms-required.html')


class EnvMeasureTypeFilterView(LoginRequiredMixin, 
                               PermissionRequiredMixin, 
                               CharSerializerExportMixin, 
                               SingleTableMixin, 
                               FilterView):
    """
    View to display all available Environmental Measurement Types in the database
    """
    model = EnvMeasureType
    table_class = EnvMeasureTypeTable
    template_name = 'home/django-material-dashboard/model-filter-list.html'
    permission_required = ('field_survey.view_envmeasuretype', )
    export_name = 'envmeastype_' + str(timezone.now().replace(microsecond=0).isoformat())
    serializer_class = fieldsurvey_serializers.EnvMeasureTypeSerializer
    filter_backends = [filters.DjangoFilterBackend]
    export_formats = settings.EXPORT_FORMATS
    # Disable DataTables pagination for this view
    table_pagination = False

    def get_context_data(self, **kwargs):
        # Return the view context data.
        context = super().get_context_data(**kwargs)
        context['segment'] = 'view_envmeasuretype'
        context['page_title'] = 'Environmental Measurement Types'
        context['export_formats'] = self.export_formats
        context['disable_datatables'] = True  # Flag to disable DataTables in template
        context = {**context, **export_context(self.request, self.export_formats)}
        return context

    def handle_no_permission(self):
        if self.raise_exception:
            raise PermissionDenied(self.get_permission_denied_message())
        return redirect('main/model-perms-required.html')


class EnvMeasureFilterView(LoginRequiredMixin, PermissionRequiredMixin, CharSerializerExportMixin, SingleTableMixin, FilterView):
    # permissions - https://stackoverflow.com/questions/9469590/check-permission-inside-a-template-in-django
    # View site filter view with REST serializer and django-tables2
    # export_formats = ['csv','xlsx'] # set in user_sites in default
    model = EnvMeasure
    table_class = EnvMeasureTable
    template_name = 'home/django-material-dashboard/model-filter-list.html'
    permission_required = ('field_survey.view_envmeasure', )
    export_name = 'envmeas_' + str(timezone.now().replace(microsecond=0).isoformat())
    serializer_class = fieldsurvey_serializers.EnvMeasureSerializer
    filter_backends = [filters.DjangoFilterBackend]
    export_formats = settings.EXPORT_FORMATS

    def get_context_data(self, **kwargs):
        # Return the view context data.
        context = super().get_context_data(**kwargs)
        context['segment'] = 'view_envmeasure'
        context['page_title'] = 'Environmental Measurement'
        context['export_formats'] = self.export_formats
        context = {**context, **export_context(self.request, self.export_formats)}
        return context

    def handle_no_permission(self):
        if self.raise_exception:
            raise PermissionDenied(self.get_permission_denied_message())
        return redirect('main/model-perms-required.html')


class EnvMeasureCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    # LoginRequiredMixin prevents users who aren't logged in from accessing the form.
    # If you omit that, you'll need to handle unauthorized users in form_valid().
    permission_required = 'field_survey.add_envmeasure'
    model = EnvMeasure
    form_class = EnvMeasureForm
    template_name = 'home/django-material-dashboard/model-add.html'

    def get_context_data(self, **kwargs):
        # Return the view context data.
        context = super().get_context_data(**kwargs)
        context['segment'] = 'add_envmeasure'
        context['page_title'] = 'Environmental Measurement'
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.created_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('view_envmeasure')

    def handle_no_permission(self):
        if self.raise_exception:
            raise PermissionDenied(self.get_permission_denied_message())
        return redirect('main/model-perms-required.html')


class EnvMeasureUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = EnvMeasure
    form_class = EnvMeasureForm
    login_url = '/dashboard/login/'
    redirect_field_name = 'next'
    template_name = 'home/django-material-dashboard/model-update.html'
    permission_required = ('field_survey.update_envmeasure', 'field_survey.view_envmeasure', )

    def get_context_data(self, **kwargs):
        # Return the view context data.
        context = super().get_context_data(**kwargs)
        context['segment'] = 'update_envmeasure'
        context['page_title'] = 'Environmental Measurement'
        return context

    def handle_no_permission(self):
        if self.raise_exception:
            raise PermissionDenied(self.get_permission_denied_message())
        return redirect('main/model-perms-required.html')

    def get_success_url(self):
        # after successfully filling out and submitting a form,
        # show the user the detail view of the label
        return reverse('view_envmeasure')


class FieldCrewFilterView(LoginRequiredMixin, PermissionRequiredMixin, CharSerializerExportMixin, SingleTableMixin, FilterView):
    # permissions - https://stackoverflow.com/questions/9469590/check-permission-inside-a-template-in-django
    # View site filter view with REST serializer and django-tables2
    # export_formats = ['csv','xlsx'] # set in user_sites in default
    model = FieldCrew
    table_class = FieldCrewTable
    template_name = 'home/django-material-dashboard/model-filter-list.html'
    permission_required = ('field_survey.view_fieldcrew', )
    export_name = 'fieldcrew_' + str(timezone.now().replace(microsecond=0).isoformat())
    serializer_class = fieldsurvey_serializers.FieldCrewSerializer
    filter_backends = [filters.DjangoFilterBackend]
    export_formats = settings.EXPORT_FORMATS

    def get_context_data(self, **kwargs):
        # Return the view context data.
        context = super().get_context_data(**kwargs)
        context['segment'] = 'view_fieldcrew'
        context['page_title'] = 'Field Crew'
        context['export_formats'] = self.export_formats
        context = {**context, **export_context(self.request, self.export_formats)}
        return context

    def handle_no_permission(self):
        if self.raise_exception:
            raise PermissionDenied(self.get_permission_denied_message())
        return redirect('main/model-perms-required.html')


class FieldCrewCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    # LoginRequiredMixin prevents users who aren’t logged in from accessing the form.
    # If you omit that, you’ll need to handle unauthorized users in form_valid().
    permission_required = 'field_survey.add_fieldcrew'
    model = FieldCrew
    form_class = FieldCrewForm
    template_name = 'home/django-material-dashboard/model-add.html'

    def get_context_data(self, **kwargs):
        # Return the view context data.
        context = super().get_context_data(**kwargs)
        context['segment'] = 'add_fieldcrew'
        context['page_title'] = 'Field Crew'
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.created_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('view_fieldcrew')

    def handle_no_permission(self):
        if self.raise_exception:
            raise PermissionDenied(self.get_permission_denied_message())
        return redirect('main/model-perms-required.html')


class FieldCrewUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = FieldCrew
    form_class = FieldCrewForm
    login_url = '/dashboard/login/'
    redirect_field_name = 'next'
    template_name = 'home/django-material-dashboard/model-update.html'
    permission_required = ('field_survey.update_fieldcrew', 'field_survey.view_fieldcrew', )

    def get_context_data(self, **kwargs):
        # Return the view context data.
        context = super().get_context_data(**kwargs)
        context['segment'] = 'update_fieldcrew'
        context['page_title'] = 'Field Crew'
        return context

    def handle_no_permission(self):
        if self.raise_exception:
            raise PermissionDenied(self.get_permission_denied_message())
        return redirect('main/model-perms-required.html')

    def get_success_url(self):
        # after successfully filling out and submitting a form,
        # show the user the detail view of the label
        return reverse('view_fieldcrew')


class FieldSampleFilterView(LoginRequiredMixin, 
                            PermissionRequiredMixin, 
                            CharSerializerExportMixin, 
                            SingleTableMixin, 
                            FilterView):
    # View site filter view with REST serializer and django-tables2
    # export_formats = ['csv','xlsx'] # set in user_sites in default
    model = FieldSample
    table_class = FieldSampleTable
    filterset_class = fieldsurvey_filters.FieldSampleFilter
    template_name = 'home/django-material-dashboard/model-filter-list.html'
    permission_required = ('field_survey.view_fieldsample', )
    export_name = 'fieldsample_' + str(timezone.now().replace(microsecond=0).isoformat())
    # serializer_class = fieldsurvey_serializers.FieldSampleTableSerializer
    filter_backends = [filters.DjangoFilterBackend]
    export_formats = settings.EXPORT_FORMATS

    def get_context_data(self, **kwargs):
        # Return the view context data.
        context = super().get_context_data(**kwargs)
        context['segment'] = 'view_fieldsample'
        context['page_title'] = 'Field Sample'
        context['export_formats'] = self.export_formats
        context = {**context, **export_context(self.request, self.export_formats)}
        return context

    def handle_no_permission(self):
        if self.raise_exception:
            raise PermissionDenied(self.get_permission_denied_message())
        return redirect('main/model-perms-required.html')


class FieldSampleCreateView(LoginRequiredMixin, 
                            PermissionRequiredMixin, 
                            CreateView):
    # LoginRequiredMixin prevents users who aren’t logged in from accessing the form.
    # If you omit that, you’ll need to handle unauthorized users in form_valid().
    permission_required = 'field_survey.add_fieldsample'
    model = FieldSample
    form_class = FieldSampleForm
    # fields = ['site_id', 'sample_material', 'sample_type', 'sample_year', 'purpose', 'req_sample_label_num']
    template_name = 'home/django-material-dashboard/model-add-fieldsurvey.html'

    def get_context_data(self, **kwargs):
        # Return the view context data.
        context = super().get_context_data(**kwargs)
        context['segment'] = 'add_fieldsample'
        context['page_title'] = 'Field Sample'
        return context

    # Sending user object to the form, to verify which fields to display
    def get_form_kwargs(self):
        kwargs = super(FieldSampleCreateView, self).get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.created_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('view_fieldsample')

    def handle_no_permission(self):
        if self.raise_exception:
            raise PermissionDenied(self.get_permission_denied_message())
        return redirect('main/model-perms-required.html')
    

class FieldSampleUpdateView(LoginRequiredMixin, 
                            PermissionRequiredMixin, 
                            UpdateView):
    model = FieldSample
    form_class = FieldSampleForm
    login_url = '/dashboard/login/'
    redirect_field_name = 'next'
    template_name = 'home/django-material-dashboard/model-update-fieldsurvey.html'
    permission_required = ('field_survey.update_fieldsample', 'field_survey.view_fieldsample', )

    def get_context_data(self, **kwargs):
        # Return the view context data.
        context = super().get_context_data(**kwargs)
        context['segment'] = 'update_fieldsample'
        context['page_title'] = 'Field Sample'
        return context

    def handle_no_permission(self):
        if self.raise_exception:
            raise PermissionDenied(self.get_permission_denied_message())
        return redirect('main/model-perms-required.html')

    def get_success_url(self):
        # after successfully filling out and submitting a form,
        # show the user the detail view of the label
        return reverse('view_fieldsample')
    

class FieldSampleImportView(LoginRequiredMixin, 
                            PermissionRequiredMixin, 
                            View):
    """
    View for importing FieldSample data from CSV/Excel files with automatic creation
    of FieldSurvey, Projects, EnvMeasures, and related objects
    """
    permission_required = 'field_survey.add_fieldsample'
    template_name = 'home/django-material-dashboard/model-import-fieldsurvey.html'
    formats = [CSV, XLS, XLSX]
    
    def get(self, request):
        """Display the import form"""
        print("GET request received for FieldSample import")
        form = ImportForm(self.formats)
        context = {
            'segment': 'import_fieldsample',
            'page_title': 'Import Field Sample',
            'form': form,
        }
        print(f"Rendering template: {self.template_name}")
        print(f"Context: {context}")
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle file upload and import with automatic creation of related objects"""
        form = ImportForm(self.formats, request.POST, request.FILES)
        
        if not form.is_valid():
            messages.error(request, f'Invalid form submission. Errors: {form.errors}')
            context = {
                'segment': 'import_fieldsample',
                'page_title': 'Import Field Sample',
                'form': form,
            }
            return render(request, self.template_name, context)
        
        # Get the uploaded file and format
        import_file = form.cleaned_data['import_file']
        input_format_index = int(form.cleaned_data['input_format'] or 0)
        input_format = self.formats[input_format_index]()
        
        try:
            # Read and parse the file using the selected format
            data = import_file.read()
            if isinstance(input_format, CSV):
                data = data.decode('utf-8')
            
            dataset = input_format.create_dataset(data)
            
            # Process each row and create related objects
            from field_site.models import FieldSite
            from sample_label.models import SampleBarcode, SampleType
            from utility.models import Project
            from users.models import CustomUser
            
            created_count = 0
            updated_count = 0
            error_messages = []
            
            for row_num, row in enumerate(dataset.dict, start=1):
                try:
                    with transaction.atomic():
                        # 1. Get or create FieldSite
                        site_id_str = row.get('site_id')
                        if site_id_str:
                            field_site = FieldSite.objects.filter(site_id=site_id_str).first()
                            if not field_site:
                                error_messages.append(f"Row {row_num}: FieldSite '{site_id_str}' not found")
                                continue
                        else:
                            error_messages.append(f"Row {row_num}: Missing site_id")
                            continue
                        
                        # 2. Get users
                        username_email = row.get('username')
                        supervisor_email = row.get('supervisor')
                        survey_datetime = row.get('survey_datetime')
                        
                        username = CustomUser.objects.filter(email=username_email).first() if username_email else request.user
                        supervisor = CustomUser.objects.filter(email=supervisor_email).first() if supervisor_email else None
                        
                        # 3. Create FieldSurvey
                        field_survey = FieldSurvey.objects.create(
                            site_id=field_site,
                            username=username or request.user,
                            supervisor=supervisor,
                            survey_datetime=survey_datetime or timezone.now(),
                            created_by=request.user
                        )
                        
                        # 4. Add projects to survey
                        project_codes = row.get('project_codes', '')
                        if project_codes:
                            for proj_code in project_codes.split(';'):
                                proj_code = proj_code.strip()
                                if proj_code:
                                    project = Project.objects.filter(project_code=proj_code).first()
                                    if project:
                                        field_survey.project_ids.add(project)
                                    else:
                                        error_messages.append(f"Row {row_num}: Project '{proj_code}' not found")
                        
                        # 5. Create EnvMeasure records
                        env_measures = {
                            'env_measure_temp': 'temp',
                            'env_measure_salinity': 'salinity', 
                            'env_measure_ph': 'ph',
                            'env_measure_turbidity': 'turbidity',
                            'env_measure_do': 'do'
                        }
                        
                        for col_name, measure_code in env_measures.items():
                            value = row.get(col_name)
                            if value:
                                env_type = EnvMeasureType.objects.filter(env_measure_type_code=measure_code).first()
                                if env_type:
                                    EnvMeasure.objects.create(
                                        survey_global_id=field_survey,
                                        env_measure_type=env_type,
                                        env_measure_value=str(value),
                                        created_by=request.user
                                    )
                        
                        # 6. Get or create SampleBarcode
                        barcode_id = row.get('field_sample_barcode')
                        if barcode_id:
                            sample_barcode, _ = SampleBarcode.objects.get_or_create(
                                sample_barcode_id=barcode_id,
                                defaults={
                                    'site_id': field_site,
                                    'sample_year': timezone.now().year,
                                    'purpose': 'Import',
                                    'created_by': request.user
                                }
                            )
                        else:
                            error_messages.append(f"Row {row_num}: Missing field_sample_barcode")
                            continue
                        
                        # 7. Get SampleType
                        sample_type_text = row.get('sample_type')
                        sample_type = SampleType.objects.filter(sample_type_label=sample_type_text).first()
                        if not sample_type and sample_type_text:
                            sample_type = SampleType.objects.filter(sample_type_code=sample_type_text).first()
                        if not sample_type:
                            error_messages.append(f"Row {row_num}: SampleType '{sample_type_text}' not found")
                            continue
                        
                        # 8. Create FieldSample
                        field_sample, created = FieldSample.objects.get_or_create(
                            field_sample_barcode=sample_barcode,
                            defaults={
                                'survey_global_id': field_survey,
                                'sample_type': sample_type,
                                'sampling_method': row.get('sampling_method', ''),
                                'is_extracted': row.get('is_extracted', 'no'),
                                'created_by': request.user
                            }
                        )
                        
                        if created:
                            created_count += 1
                        else:
                            updated_count += 1
                            
                except Exception as e:
                    import traceback
                    error_messages.append(f"Row {row_num}: {str(e)}")
                    error_messages.append(f"  Traceback: {traceback.format_exc()}")
            
            # Show results
            if error_messages:
                messages.warning(request, f'Import completed with {len(error_messages)} errors')
                for msg in error_messages[:5]:
                    messages.error(request, msg)
                if len(error_messages) > 5:
                    messages.warning(request, f'... and {len(error_messages) - 5} more errors')
            
            if created_count > 0 or updated_count > 0:
                success_msg = f'Successfully imported {created_count} new records'
                if updated_count > 0:
                    success_msg += f', updated {updated_count} records'
                messages.success(request, success_msg)
                return redirect('view_fieldsample')
            else:
                messages.error(request, 'No records were imported')
                context = {
                    'segment': 'import_fieldsample',
                    'page_title': 'Import Field Sample',
                    'form': form,
                }
                return render(request, self.template_name, context)
            
        except Exception as e:
            messages.error(request, f'Import failed: {str(e)}')
            context = {
                'segment': 'import_fieldsample',
                'page_title': 'Import Field Sample',
                'form': form,
            }
            return render(request, self.template_name, context)
    
    def handle_no_permission(self):
        if self.raise_exception:
            raise PermissionDenied(self.get_permission_denied_message())
        return redirect('main/model-perms-required.html')


# NOTE: Removed duplicate incomplete filter sample import methods (lines ~971-1215) 
# that were overriding the field sample import. These duplicate get() and post() methods
# were inside FieldSampleImportView class and Python was using the last definition.
# TODO: Create separate FilterSampleImportView class if filter sample import is needed


class FilterSampleFilterView(LoginRequiredMixin, 
                            PermissionRequiredMixin, 
                            CharSerializerExportMixin, 
                            SingleTableMixin, 
                            FilterView):
    """View for displaying and filtering FilterSample records"""
    model = FilterSample
    table_class = FilterSampleTable
    filterset_class = fieldsurvey_filters.FilterSampleFilter
    template_name = 'home/django-material-dashboard/model-filter-list.html'
    permission_required = ('field_survey.view_filtersample', )
    export_name = 'filtersample_' + str(timezone.now().replace(microsecond=0).isoformat())
    serializer_class = fieldsurvey_serializers.FilterSampleSerializer
    filter_backends = [filters.DjangoFilterBackend]
    export_formats = settings.EXPORT_FORMATS

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['segment'] = 'view_filtersample'
        context['page_title'] = 'Filter Sample'
        context['export_formats'] = self.export_formats
        context = {**context, **export_context(self.request, self.export_formats)}
        return context

    def handle_no_permission(self):
        if self.raise_exception:
            raise PermissionDenied(self.get_permission_denied_message())
        return redirect('main/model-perms-required.html')


class FilterSampleImportView(LoginRequiredMixin, 
                             PermissionRequiredMixin, 
                             View):
    """
    View for importing FilterSample data from CSV/Excel files with automatic creation
    of FieldSample and related objects
    """
    permission_required = 'field_survey.add_filtersample'
    template_name = 'home/django-material-dashboard/model-import-fieldsurvey.html'
    formats = [CSV, XLS, XLSX]
    
    def get(self, request):
        """Display the import form"""
        form = ImportForm(self.formats)
        context = {
            'segment': 'import_filtersample',
            'page_title': 'Import Filter Sample',
            'form': form,
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle file upload and import with automatic creation of related objects"""
        form = ImportForm(self.formats, request.POST, request.FILES)
        
        if not form.is_valid():
            messages.error(request, f'Invalid form submission. Errors: {form.errors}')
            context = {
                'segment': 'import_filtersample',
                'page_title': 'Import Filter Sample',
                'form': form,
            }
            return render(request, self.template_name, context)
        
        # Get the uploaded file and format
        import_file = form.cleaned_data['import_file']
        input_format_index = int(form.cleaned_data['input_format'] or 0)
        input_format = self.formats[input_format_index]()
        
        try:
            # Read and parse the file
            data = import_file.read()
            if isinstance(input_format, CSV):
                data = data.decode('utf-8')
            
            dataset = input_format.create_dataset(data)
            
            # Process each row
            from field_site.models import FieldSite
            from sample_label.models import SampleBarcode, SampleType
            from utility.models import Project
            from users.models import CustomUser
            
            created_count = 0
            updated_count = 0
            error_messages = []
            skipped_count = 0
            
            for row_num, row in enumerate(dataset.dict, start=1):
                try:
                    with transaction.atomic():
                        # Normalize all column names to lowercase for case-insensitive access
                        row = {k.lower() if k else k: v for k, v in row.items()}
                        
                        # Skip rows that don't have minimum required data
                        # Required: barcode, site, date
                        required_fields = ['barcode', 'site', 'date']
                        missing_required = [f for f in required_fields 
                                          if not row.get(f) or not str(row.get(f)).strip()]
                        
                        if missing_required:
                            # This is an incomplete row, skip it
                            print(f"Skipping row {row_num}: Missing required fields {missing_required}")
                            skipped_count += 1
                            continue
                        
                        # Helper function to parse date
                        from datetime import datetime as dt
                        
                        def parse_datetime(date_str, time_str):
                            """Parse date and time strings into datetime object"""
                            if not date_str or not time_str:
                                return None
                            try:
                                # Date format: 2025-08-21
                                date_obj = dt.strptime(str(date_str).strip(), '%Y-%m-%d').date()
                                # Time format: 01:10:00 PM or 13:10:00
                                time_str = str(time_str).strip()
                                try:
                                    time_obj = dt.strptime(time_str, '%I:%M:%S %p').time()
                                except ValueError:
                                    time_obj = dt.strptime(time_str, '%H:%M:%S').time()
                                # Combine date and time
                                combined_dt = dt.combine(date_obj, time_obj)
                                return timezone.make_aware(combined_dt)
                            except (ValueError, AttributeError) as e:
                                return None
                        
                        # Get site - try multiple site id and site name
                        site_txt_str = row.get('site')
                        if site_txt_str and str(site_txt_str).strip():
                            # Try to find by site_id OR general_location_name using Q objects
                            field_site = FieldSite.objects.filter(
                                Q(site_id=site_txt_str) | Q(general_location_name=site_txt_str)
                            ).first()
                            if not field_site:
                                error_messages.append(
                                    f"Row {row_num}: FieldSite '{site_txt_str}' not found \
                                        (tried site_id and general_location_name)")
                                continue
                        else:
                            # Better error message: show which fields have data
                            non_empty = {k: v for k, v in row.items() if v and str(v).strip()}
                            error_messages.append(
                                f"Row {row_num}: Missing or empty 'site' column. \
                                    Non-empty fields: {list(non_empty.keys())}")
                            continue
                        
                        # Parse survey datetime from Date and StartTime columns
                        # Note: Time format in CSV seems to be split into time and AM/PM
                        date_str = row.get('date')
                        start_time_str = row.get('starttime')
                        end_time_str = row.get('endtime')
                        
                        # Survey datetime from Date and StartTime columns
                        survey_datetime = parse_datetime(date_str, start_time_str) or timezone.now()
                        
                        # Sample datetime from Date column
                        sample_datetime = parse_datetime(date_str, start_time_str) or timezone.now()
                        
                        # Create or get FieldSurvey - use get_or_create to avoid duplicates
                        # Multiple samples from the same site/date should share the same survey
                        field_survey, survey_created = FieldSurvey.objects.get_or_create(
                                        site_id=field_site,
                                        survey_datetime=survey_datetime,
                                        defaults={
                                            'survey_complete': True if end_time_str else False,
                                            'created_by': request.user
                                        }
                                    )
                        
                        # Add projects
                        project_txt = row.get('project', '')
                        if project_txt:
                            project = Project.objects \
                                .filter(Q(project_code=project_txt) | 
                                        Q(project_label=project_txt)) \
                                .first()
                            if project:
                                field_survey.project_ids.add(project)
                        
                                                # Get SampleType (default to water sample)
                        
                        sample_type_text = row.get('sampletype')
                        sample_type = SampleType.objects \
                            .filter(Q(sample_type_code=sample_type_text) |
                                    Q(sample_type_label=sample_type_text)) \
                            .first()
                        if not sample_type:
                            error_messages.append(f"Row {row_num}: SampleType '{sample_type_text}' not found")
                            continue
                                                        
                        # Get or create SampleBarcode from 'barcode' column or 'field_sample_barcode'
                        barcode_id = row.get('barcode')
                        if barcode_id:
                            sample_barcode, _ = SampleBarcode.objects.get_or_create(
                                sample_barcode_id=str(barcode_id).strip(),
                                defaults={
                                    'sample_type': sample_type,
                                    'sample_year': timezone.now().year,
                                    'created_by': request.user
                                }
                            )
                        else:
                            error_messages.append(f"Row {row_num}: Missing Barcode")
                            continue
                        
                        # Get sample code from 'sample' column or 'sample_code'
                        sample_code = row.get('sample') or row.get('sample code')

                        # Create FieldSample
                        field_sample, created = FieldSample.objects.get_or_create(
                            field_sample_barcode=sample_barcode,
                            defaults={
                                'sample_code': sample_code,
                                'sample_datetime': sample_datetime,
                                'survey_global_id': field_survey,
                                'sample_type': sample_type,
                                'is_extracted': row.get('is_extracted', 'no'),
                                'created_by': request.user
                            }
                        )
                        
                        # Create FilterSample
                        filter_sample, created = FilterSample.objects.get_or_create(
                            field_sample=field_sample,
                            defaults={
                                'filter_vol': row.get('filtered (ml)') or row.get('filteredvolume'),
                                'filter_type': row.get('filtertype') or row.get('filtertype', ''),
                                'filter_pore': row.get('filterpore'),
                                'filter_size': row.get('filtersize'),
                                'filter_saturation': str(row.get('filtersaturation',
                                                                 row.get('saturation')))
                                                    .strip().lower() == 'true',
                                'filter_notes': row.get('comment'),
                                'created_by': request.user
                            }
                        )
                        
                        # Create Environmental Measurements ONLY if this is a new survey
                        # or if this row has different environmental data than what's stored
                        if survey_created:
                            # This is a new survey, create all environmental measurements
                            from field_survey.models import EnvMeasure
                            
                            # Retrieve all existing EnvMeasureTypes from database
                            all_env_types = EnvMeasureType.objects.all()
                            
                            # Match CSV columns to EnvMeasureType codes/names
                            env_mappings = []
                            for env_type in all_env_types:
                                # Try to match column name with env_measure_type_code first, then env_measure_type_name
                                # Also try with underscores replaced by spaces and vice versa for flexibility
                                code_lower = env_type.env_measure_type_code.lower()
                                name_lower = env_type.env_measure_type_name.lower()
                                
                                # Try multiple variations to match CSV columns - use 'in' check instead of or chain
                                column_value = None
                                if code_lower in row:
                                    column_value = row[code_lower]
                                elif name_lower in row:
                                    column_value = row[name_lower]
                                elif name_lower.replace(' ', '_') in row:
                                    column_value = row[name_lower.replace(' ', '_')]
                                elif name_lower.replace('_', ' ') in row:
                                    column_value = row[name_lower.replace('_', ' ')]
                                elif name_lower.replace('_', '').replace(' ', '') in row:
                                    column_value = row[name_lower.replace('_', '').replace(' ', '')]
                                
                                if (column_value and 
                                    str(column_value).strip() 
                                    not in ['', 'NA', 'na', 'N/A', 'None']):
                                    env_mappings.append((env_type, column_value))
                            
                            # Create environmental measurements for matched columns
                            for env_type, measure_value in env_mappings:
                                # Create EnvMeasure (only for new surveys)
                                env_measure = EnvMeasure.objects.create(
                                    survey_global_id=field_survey,
                                    env_measure_type=env_type,
                                    env_measure_value=str(measure_value).strip(),
                                    created_by=request.user
                                )
                        else:
                            print(f"Debug: Survey already exists, skipping EnvMeasure creation for row {row_num}")


                        if created:
                            created_count += 1
                        else:
                            updated_count += 1
                            
                except Exception as e:
                    import traceback
                    error_messages.append(f"Row {row_num}: {str(e)}")
                    error_messages.append(f"  Traceback: {traceback.format_exc()}")
            
            # Show results
            if error_messages:
                messages.warning(request, f'Import completed with {len(error_messages)} errors')
                for msg in error_messages[:5]:
                    messages.error(request, msg)
                if len(error_messages) > 5:
                    messages.warning(request, f'... and {len(error_messages) - 5} more errors')
            
            if skipped_count > 0:
                messages.info(request, f'Skipped {skipped_count} incomplete rows')
            
            if created_count > 0 or updated_count > 0:
                success_msg = f'Successfully imported {created_count} new records'
                if updated_count > 0:
                    success_msg += f', updated {updated_count} records'
                if skipped_count > 0:
                    success_msg += f' (skipped {skipped_count} incomplete rows)'
                messages.success(request, success_msg)
                return redirect('view_filtersample')
            else:
                if skipped_count > 0:
                    messages.warning(request, f'No records were imported (skipped {skipped_count} incomplete rows)')
                else:
                    messages.error(request, 'No records were imported')
                context = {
                    'segment': 'import_filtersample',
                    'page_title': 'Import Filter Sample',
                    'form': form,
                }
                return render(request, self.template_name, context)
            
        except Exception as e:
            messages.error(request, f'Import failed: {str(e)}')
            context = {
                'segment': 'import_filtersample',
                'page_title': 'Import Filter Sample',
                'form': form,
            }
            return render(request, self.template_name, context)
    
    def handle_no_permission(self):
        if self.raise_exception:
            raise PermissionDenied(self.get_permission_denied_message())
        return redirect('main/model-perms-required.html')


class FilterSampleUpdateView(LoginRequiredMixin, 
                             PermissionRequiredMixin, 
                             UpdateView):
    """Class-based view for updating FilterSample records"""
    model = FilterSample
    form_class = FilterSampleForm
    login_url = '/dashboard/login/'
    redirect_field_name = 'next'
    template_name = 'home/django-material-dashboard/model-update.html'
    permission_required = ('field_survey.update_filtersample', 'field_survey.view_filtersample', )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['segment'] = 'update_filtersample'
        context['page_title'] = 'Filter Sample'
        return context

    def handle_no_permission(self):
        if self.raise_exception:
            raise PermissionDenied(self.get_permission_denied_message())
        return redirect('main/model-perms-required.html')

    def get_success_url(self):
        return reverse('view_filtersample')


@login_required
@permission_required('field_survey.add_fieldsample', login_url='/dashboard/login/')
@transaction.atomic
def filter_sample_create_view(request):
    # TODO change to class based view to enable popups
    # https://simpleisbetterthancomplex.com/tutorial/2016/07/22/how-to-extend-django-user-model.html
    # https://gist.github.com/vitorfs/cbe877156ba538a20c53c9a1cea29277
    if request.method == 'POST':
        fieldsample_form = FieldSampleForm(request.POST, sample_material=SampleMaterial.objects.get(sample_material_code='w'))
        filtersample_form = FilterSampleForm(request.POST)
        if fieldsample_form.is_valid() and filtersample_form.is_valid():
            fieldsample = fieldsample_form.save(commit=False)
            fieldsample.created_by = request.user
            fieldsample = fieldsample_form.save()
            fieldsample.refresh_from_db()  # This will load the FieldSample created by the Signal
            filtersample_form = FilterSampleForm(request.POST, instance=fieldsample.filter_sample)  # Reload the filtersample form with the fieldsample instance
            filtersample_form.full_clean()  # Manually clean the form this time. It is implicitly called by "is_valid()" method
            filtersample = filtersample_form.save(commit=False)
            filtersample.created_by = request.user
            filtersample.save()  # Gracefully save the form
            return redirect('view_filtersample')
    else:
        fieldsample_form = FieldSampleForm(sample_material=SampleMaterial.objects.get(sample_material_code='w'))
        filtersample_form = FilterSampleForm()
    return render(request, 'home/django-material-dashboard/model-add-related.html', {
        'parent_form': fieldsample_form,
        'child_form': filtersample_form,
        'segment': 'add_filtersample',
        'page_title': 'Filter Sample'
    })


@login_required
@permission_required('field_survey.update_fieldsample', login_url='/dashboard/login/')
@transaction.atomic
def filter_sample_update_view(request, pk):
    # TODO change to class based view to enable popups
    # https://simpleisbetterthancomplex.com/tutorial/2016/07/22/how-to-extend-django-user-model.html
    # https://gist.github.com/vitorfs/cbe877156ba538a20c53c9a1cea29277
    fieldsample = get_object_or_404(FieldSample, pk=pk)
    if request.method == 'POST':
        fieldsample_form = FieldSampleForm(request.POST, instance=fieldsample, pk=pk)
        filtersample_form = FilterSampleForm(request.POST, instance=fieldsample.filter_sample)
        if fieldsample_form.is_valid() and filtersample_form.is_valid():
            fieldsample_form.save()
            filtersample_form.save()
            messages.success(request, _('Your filtersample was successfully updated.'))
            return redirect('view_filtersample')
        else:
            messages.error(request, _('Please correct the error below.'))
    else:
        fieldsample_form = FieldSampleForm(instance=fieldsample, pk=pk)
        filtersample_form = FilterSampleForm(instance=fieldsample.filter_sample)
    return render(request, 'home/django-material-dashboard/model-update-related.html', {
        'parent_form': fieldsample_form,
        'child_form': filtersample_form,
        'segment': 'update_filtersample',
        'page_title': 'Filter Sample'
    })


class SubCoreSampleFilterView(LoginRequiredMixin, PermissionRequiredMixin, CharSerializerExportMixin, SingleTableMixin, FilterView):
    # permissions - https://stackoverflow.com/questions/9469590/check-permission-inside-a-template-in-django
    # View site filter view with REST serializer and django-tables2
    # export_formats = ['csv','xlsx'] # set in user_sites in default
    model = SubCoreSample
    table_class = SubCoreSampleTable
    template_name = 'home/django-material-dashboard/model-filter-list.html'
    permission_required = ('field_survey.view_fieldsurvey', 'field_survey.view_fieldcrew',
                           'field_survey.view_envmeasure', 'field_survey.view_fieldsample',
                           'field_survey.view_subcoresample', )
    export_name = 'subcoresample_' + str(timezone.now().replace(microsecond=0).isoformat())
    serializer_class = fieldsurvey_serializers.SubCoreSampleTableSerializer
    filter_backends = [filters.DjangoFilterBackend]
    export_formats = settings.EXPORT_FORMATS

    def get_context_data(self, **kwargs):
        # Return the view context data.
        context = super().get_context_data(**kwargs)
        context['segment'] = 'view_subcoresample'
        context['page_title'] = 'SubCore Sample'
        context['export_formats'] = self.export_formats
        context = {**context, **export_context(self.request, self.export_formats)}
        return context

    def handle_no_permission(self):
        if self.raise_exception:
            raise PermissionDenied(self.get_permission_denied_message())
        return redirect('main/model-perms-required.html')


@login_required
@permission_required('field_survey.add_fieldsample', login_url='/dashboard/login/')
@transaction.atomic
def subcore_sample_create_view(request):
    # TODO change to class based view to enable popups
    # https://simpleisbetterthancomplex.com/tutorial/2016/07/22/how-to-extend-django-user-model.html
    # https://gist.github.com/vitorfs/cbe877156ba538a20c53c9a1cea29277
    if request.method == 'POST':
        fieldsample_form = FieldSampleForm(request.POST, sample_material=SampleMaterial.objects.get(sample_material_code='s'))
        subcore_form = SubCoreSampleForm(request.POST)
        if fieldsample_form.is_valid() and subcore_form.is_valid():
            fieldsample = fieldsample_form.save(commit=False)
            fieldsample.created_by = request.user
            fieldsample = fieldsample_form.save()
            fieldsample.refresh_from_db()  # This will load the FieldSample created by the Signal
            subcore_form = SubCoreSampleForm(request.POST, instance=fieldsample.subcore_sample)  # Reload the subcore form with the fieldsample instance
            subcore_form.full_clean()  # Manually clean the form this time. It is implicitly called by "is_valid()" method
            subcoresample = subcore_form.save(commit=False)
            subcoresample.created_by = request.user
            subcoresample.save()  # Gracefully save the form
            return redirect('view_subcoresample')
    else:
        fieldsample_form = FieldSampleForm(sample_material=SampleMaterial.objects.get(sample_material_code='s'))
        subcore_form = SubCoreSampleForm()
    return render(request, 'home/django-material-dashboard/model-add-related.html', {
        'parent_form': fieldsample_form,
        'child_form': subcore_form,
        'segment': 'add_subcoresample',
        'page_title': 'SubCore Sample'
    })


@login_required
@permission_required('field_survey.update_fieldsample', login_url='/dashboard/login/')
@transaction.atomic
def subcore_sample_update_view(request, pk):
    # TODO change to class based view to enable popups
    # https://simpleisbetterthancomplex.com/tutorial/2016/07/22/how-to-extend-django-user-model.html
    # https://gist.github.com/vitorfs/cbe877156ba538a20c53c9a1cea29277
    fieldsample = get_object_or_404(FieldSample, pk=pk)
    if request.method == 'POST':
        fieldsample_form = FieldSampleForm(request.POST, instance=fieldsample, pk=pk)
        subcore_form = SubCoreSampleForm(request.POST, instance=fieldsample.subcore_sample)
        if fieldsample_form.is_valid() and subcore_form.is_valid():
            fieldsample_form.save()
            subcore_form.save()
            messages.success(request, _('Your subcore was successfully updated.'))
            return redirect('view_subcoresample')
        else:
            messages.error(request, _('Please correct the error below.'))
    else:
        fieldsample_form = FieldSampleForm(instance=fieldsample, pk=pk)
        subcore_form = SubCoreSampleForm(instance=fieldsample.subcore_sample)
    return render(request, 'home/django-material-dashboard/model-update-related.html', {
        'parent_form': fieldsample_form,
        'child_form': subcore_form,
        'segment': 'update_subcoresample',
        'page_title': 'SubCore Sample'
    })


########################################
# SERIALIZERS VIEWS                    #
########################################
class GeoFieldSurveyViewSet(viewsets.ModelViewSet):
    serializer_class = fieldsurvey_serializers.GeoFieldSurveySerializer
    # https://stackoverflow.com/questions/39669553/django-rest-framework-setting-up-prefetching-for-nested-serializers
    # https://www.django-rest-framework.org/api-guide/relations/
    queryset = FieldSurvey.objects.prefetch_related('created_by', 'project_ids', 'site_id', 'username', 'supervisor', 'qa_editor', )
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = fieldsurvey_filters.GeoFieldSurveySerializerFilter
    swagger_tags = ['field survey']


class FieldCrewViewSet(viewsets.ModelViewSet):
    serializer_class = fieldsurvey_serializers.FieldCrewSerializer
    # https://stackoverflow.com/questions/39669553/django-rest-framework-setting-up-prefetching-for-nested-serializers
    # https://www.django-rest-framework.org/api-guide/relations/
    # https://www.django-rest-framework.org/api-guide/relations/#writable-nested-serializers
    queryset = FieldCrew.objects.prefetch_related('created_by', 'survey_global_id', )
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = fieldsurvey_filters.FieldCrewSerializerFilter
    swagger_tags = ['field survey']


class EnvMeasureTypeViewSet(viewsets.ModelViewSet):
    serializer_class = fieldsurvey_serializers.EnvMeasureTypeSerializer
    queryset = EnvMeasureType.objects.prefetch_related('created_by', )
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = fieldsurvey_filters.EnvMeasureTypeSerializerFilter
    swagger_tags = ['field survey']


class EnvMeasureViewSet(viewsets.ModelViewSet):
    serializer_class = fieldsurvey_serializers.EnvMeasureSerializer
    queryset = EnvMeasure.objects.prefetch_related('created_by', 'survey_global_id', 'env_measure_type', )
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = fieldsurvey_filters.EnvMeasureSerializerFilter
    swagger_tags = ['field survey']


class FieldSampleViewSet(viewsets.ModelViewSet):
    serializer_class = fieldsurvey_serializers.FieldSampleSerializer
    queryset = FieldSample.objects.prefetch_related('created_by', 'survey_global_id', 'sample_material', 'field_sample_barcode', )
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = fieldsurvey_filters.FieldSampleSerializerFilter
    swagger_tags = ['field survey']


class FilterSampleViewSet(viewsets.ModelViewSet):
    serializer_class = fieldsurvey_serializers.FilterSampleSerializer
    queryset = FilterSample.objects.prefetch_related('created_by', 'field_sample')
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = fieldsurvey_filters.FilterSampleSerializerFilter
    swagger_tags = ['field survey']


class SubCoreSampleViewSet(viewsets.ModelViewSet):
    serializer_class = fieldsurvey_serializers.SubCoreSampleSerializer
    queryset = SubCoreSample.objects.prefetch_related('created_by', 'field_sample')
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = fieldsurvey_filters.SubCoreSampleSerializerFilter
    swagger_tags = ['field survey']


########################################
# NESTED SERIALIZER VIEWS              #
########################################
class FieldSurveyEnvsNestedViewSet(viewsets.ModelViewSet):
    serializer_class = fieldsurvey_serializers.FieldSurveyEnvsNestedSerializer
    # https://stackoverflow.com/questions/39669553/django-rest-framework-setting-up-prefetching-for-nested-serializers
    # https://www.django-rest-framework.org/api-guide/relations/
    # queryset = FieldSurvey.objects.prefetch_related('created_by', 'project_ids', 'site_id', 'username', 'supervisor', 'qa_editor', )
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = fieldsurvey_filters.FieldSurveyEnvsNestedSerializerFilter
    swagger_tags = ['field survey']

    def get_queryset(self):
        queryset = FieldSurvey.objects.all()
        return self.get_serializer_class().setup_eager_loading(queryset)


class FieldSurveyFiltersNestedViewSet(viewsets.ModelViewSet):
    serializer_class = fieldsurvey_serializers.FieldSurveyFiltersNestedSerializer
    # https://stackoverflow.com/questions/39669553/django-rest-framework-setting-up-prefetching-for-nested-serializers
    # https://www.django-rest-framework.org/api-guide/relations/
    # queryset = FieldSurvey.objects.prefetch_related('created_by', 'project_ids', 'site_id', 'username', 'supervisor', 'qa_editor', )
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = fieldsurvey_filters.FieldSurveyFiltersNestedSerializerFilter
    swagger_tags = ['field survey']

    def get_queryset(self):
        queryset = FieldSurvey.objects.all()
        return self.get_serializer_class().setup_eager_loading(queryset)


class FieldSurveySubCoresNestedViewSet(viewsets.ModelViewSet):
    serializer_class = fieldsurvey_serializers.FieldSurveySubCoresNestedSerializer
    # https://stackoverflow.com/questions/39669553/django-rest-framework-setting-up-prefetching-for-nested-serializers
    # https://www.django-rest-framework.org/api-guide/relations/
    # queryset = FieldSurvey.objects.prefetch_related('created_by', 'project_ids', 'site_id', 'username', 'supervisor', 'qa_editor', )
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = fieldsurvey_filters.FieldSurveySubCoresNestedSerializerFilter
    swagger_tags = ['field survey']

    def get_queryset(self):
        queryset = FieldSurvey.objects.all()
        return self.get_serializer_class().setup_eager_loading(queryset)
