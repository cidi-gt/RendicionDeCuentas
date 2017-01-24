from django.conf.urls import url
from . import views
from django.contrib.flatpages import views as fpviews
from .views import CustomContactFormView
from django.views.generic import TemplateView

app_name = views.app_name
urlpatterns = [
    #contact form
    url(r'contact/$', CustomContactFormView.as_view(), name='contact_form'),
    url(r'^contact/sent/$', TemplateView.as_view(template_name='contact_form/contact_form_sent.html'), name='contact_form_sent'),
    #index
    url(r'^$', views.index, name='index'),
    #supplier pages and queries
    url(r'proveedor/(?P<supplier_id>[0-9]{1,5})/$', views.proveedor_item, name='proveedor_item'),
    url(r'proveedor/(?P<supplier_id>[0-9]{1,5})/(?P<year_start>[0-9]{4})-(?P<month_start>[0-9]{2})-(?P<day_start>[0-9]{2})/(?P<year_end>[0-9]{4})-(?P<month_end>[0-9]{2})-(?P<day_end>[0-9]{2})/$', views.proveedor_item, name='proveedor_item'),
    url(r'proveedor/(?P<supplier_id>[0-9]{1,5})/(?P<year_start>[0-9]{4})-(?P<month_start>[0-9]{2})-(?P<day_start>[0-9]{2})/(?P<year_end>[0-9]{4})-(?P<month_end>[0-9]{2})-(?P<day_end>[0-9]{2})/entidad/$', views.proveedor_entities, name='proveedor_entities'),
    url(r'proveedor/(?P<supplier_id>[0-9]{1,5})/(?P<year_start>[0-9]{4})-(?P<month_start>[0-9]{2})-(?P<day_start>[0-9]{2})/(?P<year_end>[0-9]{4})-(?P<month_end>[0-9]{2})-(?P<day_end>[0-9]{2})/day/$', views.proveedor_pagos_by_day, name='proveedor_pagos_by_day'),
    url(r'proveedor/(?P<supplier_id>[0-9]{1,5})/(?P<year_start>[0-9]{4})-(?P<month_start>[0-9]{2})-(?P<day_start>[0-9]{2})/(?P<year_end>[0-9]{4})-(?P<month_end>[0-9]{2})-(?P<day_end>[0-9]{2})/mod/$', views.proveedor_modalities, name='proveedor_modalities'),
    url(r'proveedor/(?P<supplier_id>[0-9]{1,5})/(?P<year_start>[0-9]{4})-(?P<month_start>[0-9]{2})-(?P<day_start>[0-9]{2})/(?P<year_end>[0-9]{4})-(?P<month_end>[0-9]{2})-(?P<day_end>[0-9]{2})/cat/$', views.proveedor_categories, name='proveedor_categories'),
    #entity pages and queries
    url(r'entidad/$', views.entidad_index, name='entidad_index'),
    url(r'entidad/(?P<entity_id>[0-9]{1,5})/$', views.entidad_item, name='entidad_item'),
    url(r'entidad/(?P<entity_id>[0-9]{1,5})/(?P<year_start>[0-9]{4})-(?P<month_start>[0-9]{2})-(?P<day_start>[0-9]{2})/(?P<year_end>[0-9]{4})-(?P<month_end>[0-9]{2})-(?P<day_end>[0-9]{2})/$', views.entidad_item, name='entidad_item'),
    url(r'entidad/(?P<entity_id>[0-9]{1,5})/(?P<year_start>[0-9]{4})-(?P<month_start>[0-9]{2})-(?P<day_start>[0-9]{2})/(?P<year_end>[0-9]{4})-(?P<month_end>[0-9]{2})-(?P<day_end>[0-9]{2})/prove/$', views.entidad_suppliers, name='entidad_suppliers'),
    url(r'entidad/(?P<entity_id>[0-9]{1,5})/(?P<year_start>[0-9]{4})-(?P<month_start>[0-9]{2})-(?P<day_start>[0-9]{2})/(?P<year_end>[0-9]{4})-(?P<month_end>[0-9]{2})-(?P<day_end>[0-9]{2})/cat/$', views.entidad_categories, name='entidad_categories'),
    url(r'entidad/(?P<entity_id>[0-9]{1,5})/(?P<year_start>[0-9]{4})-(?P<month_start>[0-9]{2})-(?P<day_start>[0-9]{2})/(?P<year_end>[0-9]{4})-(?P<month_end>[0-9]{2})-(?P<day_end>[0-9]{2})/mod/$', views.entidad_modalities, name='entidad_modalities'),
    url(r'entidad/(?P<entity_id>[0-9]{1,5})/(?P<year_start>[0-9]{4})-(?P<month_start>[0-9]{2})-(?P<day_start>[0-9]{2})/(?P<year_end>[0-9]{4})-(?P<month_end>[0-9]{2})-(?P<day_end>[0-9]{2})/day/$', views.entidad_expense_day, name='entidad_expense_day'),
    #payments mande by entities, and queries
    url(r'entidad/pagos/$', views.entidad_pagos_index, name='entidad_pagos_index'),
    url(r'entidad/pagos/(?P<year_start>[0-9]{4})-(?P<month_start>[0-9]{2})-(?P<day_start>[0-9]{2})/$', views.entidad_pagos_list, name='entidad_pagos_list'),
    url(r'entidad/pagos/(?P<entity_id>[0-9]{1,5})/(?P<year_start>[0-9]{4})-(?P<month_start>[0-9]{2})-(?P<day_start>[0-9]{2})/$', views.entidad_pagos_list, name='entidad_pagos_list'),
    url(r'entidad/pagos/proveedor/(?P<supplier_id>[0-9]{1,5})/(?P<year_start>[0-9]{4})-(?P<month_start>[0-9]{2})-(?P<day_start>[0-9]{2})/$', views.entidad_pagos_list, name='entidad_pagos_list'),
    #url(r'entidad/pagos/(?P<year_start>[0-9]{4})-(?P<month_start>[0-9]{2})-(?P<day_start>[0-9]{2})/(?P<year_end>[0-9]{4})-(?P<month_end>[0-9]{2})-(?P<day_end>[0-9]{2})/(?P<order_field>entity__name|modality|purchasing_unit|end_date|t_ammount)/(?P<order_direction>asc|desc)/$', views.entidad_pagos_list, name='entidad_pagos_list'),
    url(r'entidad/pagos/(?P<year_start>[0-9]{4})-(?P<month_start>[0-9]{2})-(?P<day_start>[0-9]{2})/(?P<year_end>[0-9]{4})-(?P<month_end>[0-9]{2})-(?P<day_end>[0-9]{2})/$', views.entidad_pagos_summary, name='entidad_pagos_summary'),
    #all entitis together, and queries
    url(r'entidad/comparativo/json/(?P<year_start>[0-9]{4})-(?P<month_start>[0-9]{2})-(?P<day_start>[0-9]{2})/(?P<year_end>[0-9]{4})-(?P<month_end>[0-9]{2})-(?P<day_end>[0-9]{2})/$', views.entidad_comparativo_summary, name='entidad_comparativo_summary'),
    url(r'entidad/comparativo/$', views.entidad_comparativo, name='entidad_comparativo'),
    url(r'entidad/comparativo/(?P<year_start>[0-9]{4})-(?P<month_start>[0-9]{2})-(?P<day_start>[0-9]{2})/(?P<year_end>[0-9]{4})-(?P<month_end>[0-9]{2})-(?P<day_end>[0-9]{2})/$', views.entidad_comparativo, name='entidad_comparativo'),
    #map and queries
    url(r'municipalidades/$', views.municipio_index, name='municipio_index'),
    url(r'municipalidades/(?P<year_start>[0-9]{4})-(?P<month_start>[0-9]{2})-(?P<day_start>[0-9]{2})/(?P<year_end>[0-9]{4})-(?P<month_end>[0-9]{2})-(?P<day_end>[0-9]{2})/$', views.municipio_summary, name='municipio_summary'),
    #modality and queries
    url(r'modalidad/$', views.modalidad_index, name='modalidad_index'),
    url(r'modalidad/(?P<year_start>[0-9]{4})-(?P<month_start>[0-9]{2})-(?P<day_start>[0-9]{2})/(?P<year_end>[0-9]{4})-(?P<month_end>[0-9]{2})-(?P<day_end>[0-9]{2})/$', views.modalidad_summary, name='modalidad_summary'),
    #category and queries
    url(r'categoria/$', views.categoria_index, name='categoria_index'),
    url(r'categoria/(?P<year_start>[0-9]{4})-(?P<month_start>[0-9]{2})-(?P<day_start>[0-9]{2})/(?P<year_end>[0-9]{4})-(?P<month_end>[0-9]{2})-(?P<day_end>[0-9]{2})/$', views.categoria_summary, name='categoria_summary'),    
]
