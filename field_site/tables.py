import django_tables2 as tables
from .models import FieldSite
from django_tables2.utils import A


class FieldSiteTable(tables.Table):
    # or use non geo serializer
    _selected_action = tables.CheckBoxColumn(accessor='pk',
                                             attrs={'td': {'class': 'action-checkbox'},
                                                    'input': {'class': 'action-select'},
                                                    'th__input': {'id': 'action-toggle'},
                                                    'th': {'class': 'action-checkbox-column'}},
                                             orderable=False)
    # same as <a href='{% url 'users:site_detail' site.id %}'> {{ site.site_id }}</a>
    site_id = tables.LinkColumn('detail_fieldsite', args=[A('pk')])
    watershed_type = tables.Column(verbose_name='Watershed')
    # same as <a href="{% url 'users:site_samplelabel_add' site.id %}" class="addlink"> {% translate 'Add' %}</a>
    # add_survey = tables.LinkColumn('add_samplelabelrequestsite', 
    #                               text='Add Label', 
    #                               args=[A('pk')], 
    #                               orderable=False)
    # formatting for date column
    created_datetime = tables.DateTimeColumn(format='M d, Y h:i a')

    class Meta:
        model = FieldSite
        fields = ('_selected_action', 'site_id', 'general_location_name',
                  'watershed_type', 'created_datetime')
