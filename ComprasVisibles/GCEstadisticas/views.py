from django.shortcuts import render
from django.core import serializers
from .models import Entity, EntityType, PurchaseCategory, Requisition, Supplier, Proposal, Awarded
from .services import *
from django.db.models import Sum, Count
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from dateutil.relativedelta import relativedelta
from django.utils import timezone
import json
import datetime
import pytz
from django.views.generic.edit import FormView
from .forms import CustomContactForm
from django.core.urlresolvers import reverse

app_name = 'visualizaciones'

def index(request):
    opciones_pagina = {
        'Cantidad gastada por día (sumarización para todas las entidades)':app_name+':entidad_pagos_index',
        'Comparativo de gastos entre entidades':app_name+':entidad_comparativo',
        'Comparativo de gastos por municipio':app_name+':municipio_index',
        'Comparativo de gastos por modalidad':app_name+':modalidad_index',
        'Comparativo de gastos por categoria':app_name+':categoria_index',
        'Vista por Entidad':app_name+':entidad_index'
    }
    return render(request, 'GCEstadisticas/index.html', {'opciones':sorted(opciones_pagina.items())})

def date_converter(year_start=None,month_start=None, day_start=None):
    tz = pytz.timezone('America/Guatemala')
    if (year_start is None):
        try:
            curr_date = timezone.localtime(timezone.now()).replace(tzinfo=pytz.timezone('America/Guatemala')) + relativedelta(days=-1)
            result_date = date_converter(curr_date.year, curr_date.month, curr_date.day)
            return result_date
        except Exception as e:
            e.args = ("date convertion error",)
            raise
    else:
        try:
            result_date = tz.localize(datetime.datetime(year=int(year_start),month=int(month_start),day=int(day_start)))
            return result_date
        except Exception as e:
            e.args = ("date convertion error",)
            raise
    

def entidad_pagos_index(request):
    end_date = date_converter()
    start_date = end_date + relativedelta(months=-1)
    return render(request, 'GCEstadisticas/entidad_pagos.html', {'start_date':start_date.strftime("%Y-%m-%d"), 'end_date':end_date.strftime("%Y-%m-%d")})

def entidad_pagos_summary(request,year_start,month_start,day_start,year_end,month_end,day_end):
    try:
        start_date = date_converter(year_start, month_start, day_start)
        end_date = date_converter(year_end, month_end, day_end) + relativedelta(seconds=86399)
        s_data = summarized_ammount_by_day(start_date, end_date)
    except Exception:
        raise Http404
    return HttpResponse(json.dumps(s_data, cls=DjangoJSONEncoder))

def entidad_pagos_list(request, year_start, month_start, day_start, entity_id=None, supplier_id=None):
    try:
        start_date = date_converter(year_start, month_start, day_start)
        end_date = start_date + relativedelta(seconds=86399)
        s_data = purchase_list(start_date=start_date, final_date=end_date, entity_id=entity_id, supplier_id=supplier_id)
        entity_name = None
        if (entity_id is not None):
            entity_name = Entity.objects.filter(id=entity_id).first().name
        if (supplier_id is not None):
            entity_name = "Compras en las que se adjudico a: "+Supplier.objects.filter(id=supplier_id).first().name
    except Exception:
        raise Http404
    return render(request, 'GCEstadisticas/entidad_pagos_list.html', {'start_date':start_date.strftime("%Y-%m-%d"), 'requisitions':s_data, 'entity_name':entity_name})

def entidad_comparativo(request,year_start="",month_start="",day_start="",year_end="",month_end="",day_end=""):
    if (year_start == ""):
        end_date = date_converter()
        start_date = end_date + relativedelta(months=-1)
    else:
        end_date = date_converter(year_end, month_end, day_end)
        start_date = date_converter(year_start, month_start, day_start)
    return render(request, 'GCEstadisticas/entidad_comparativo.html', {'start_date':start_date.strftime("%Y-%m-%d"), 'end_date':end_date.strftime("%Y-%m-%d")})

def entidad_comparativo_summary(request,year_start,month_start,day_start,year_end,month_end,day_end):
    try:
        start_date = date_converter(year_start, month_start, day_start)
        end_date = date_converter(year_end, month_end, day_end) + relativedelta(seconds=86399)
        s_data = entity_summarized_data(start_date, end_date)
    except Exception:
        raise Http404
    return HttpResponse(json.dumps(list(s_data.values()), cls=DjangoJSONEncoder))

def municipio_index(request):
    end_date = date_converter()
    start_date = end_date + relativedelta(months=-1)
    e_list = entity_list(get_cities=True)
    return render(request, 'GCEstadisticas/municipios.html', {'start_date':start_date.strftime("%Y-%m-%d"), 'end_date':end_date.strftime("%Y-%m-%d"), 'entity_list':e_list[0], 'cities_list':e_list[1]})

def municipio_summary(request,year_start,month_start,day_start,year_end,month_end,day_end):
    try:
        start_date = date_converter(year_start, month_start, day_start)
        end_date = date_converter(year_end, month_end, day_end) + relativedelta(seconds=86399)
        s_data = muni_summarized_data(start_date, end_date)
    except Exception:
        raise Http404
    return HttpResponse(json.dumps(list(s_data.values()), cls=DjangoJSONEncoder))

def modalidad_index(request):
    end_date = date_converter()
    start_date = end_date + relativedelta(months=-1)
    return render(request, 'GCEstadisticas/modalidad.html', {'start_date':start_date.strftime("%Y-%m-%d"), 'end_date':end_date.strftime("%Y-%m-%d")})

def modalidad_summary(request,year_start,month_start,day_start,year_end,month_end,day_end):
    try:
        start_date = date_converter(year_start, month_start, day_start)
        end_date = date_converter(year_end, month_end, day_end) + relativedelta(seconds=86399)
        s_data = entity_modality(start_date, end_date)
    except Exception:
        raise Http404
    return HttpResponse(json.dumps(list(s_data), cls=DjangoJSONEncoder))

def categoria_index(request):
    end_date = date_converter()
    start_date = end_date + relativedelta(months=-1)
    return render(request, 'GCEstadisticas/categoria.html', {'start_date':start_date.strftime("%Y-%m-%d"), 'end_date':end_date.strftime("%Y-%m-%d")})

def categoria_summary(request,year_start,month_start,day_start,year_end,month_end,day_end):
    try:
        start_date = date_converter(year_start, month_start, day_start)
        end_date = date_converter(year_end, month_end, day_end) + relativedelta(seconds=86399)
        s_data = category_summary(start_date, end_date)
    except Exception:
        raise Http404
    return HttpResponse(json.dumps(s_data, cls=DjangoJSONEncoder))

def entidad_index(request):
    s_data = entity_list()
    return render(request, 'GCEstadisticas/entidades.html', {'entidades':sorted(s_data.items())})

def entidad_item(request,entity_id, year_start="",month_start="",day_start="",year_end="",month_end="",day_end=""):
    if (year_start == ""):
        end_date = date_converter()
        start_date = end_date + relativedelta(months=-1)
    else:
        start_date = date_converter(year_start, month_start, day_start)
        end_date = date_converter(year_end, month_end, day_end) + relativedelta(seconds=86399)
    entity = get_object_or_404(Entity, pk=entity_id)
    return render(request, 'GCEstadisticas/entidad.html', {'entidad':entity, 'start_date':start_date.strftime("%Y-%m-%d"), 'end_date':end_date.strftime("%Y-%m-%d")})

def entidad_suppliers(request, entity_id, year_start, month_start, day_start, year_end, month_end, day_end):
    try:
        start_date = date_converter(year_start, month_start, day_start)
        end_date = date_converter(year_end, month_end, day_end) + relativedelta(seconds=86399)
        s_data = suppliers_by_entity(start_date, end_date,entity_id)
    except Exception:
        raise Http404
    return HttpResponse(json.dumps(list(s_data), cls=DjangoJSONEncoder))

def entidad_categories(request, entity_id, year_start, month_start, day_start, year_end, month_end, day_end):
    try:
        start_date = date_converter(year_start, month_start, day_start)
        end_date = date_converter(year_end, month_end, day_end) + relativedelta(seconds=86399)
        s_data = entity_category_summary(start_date, end_date, entity_id)
    except Exception:
        raise Http404
    return HttpResponse(json.dumps(list(s_data), cls=DjangoJSONEncoder))

def entidad_modalities(request, entity_id, year_start, month_start, day_start, year_end, month_end, day_end):
    try:
        start_date = date_converter(year_start, month_start, day_start)
        end_date = date_converter(year_end, month_end, day_end) + relativedelta(seconds=86399)
        s_data = entity_modality_summary(start_date, end_date, entity_id=entity_id)
    except Exception:
        raise Http404
    return HttpResponse(json.dumps(list(s_data), cls=DjangoJSONEncoder))

def entidad_expense_day(request, entity_id, year_start,month_start,day_start,year_end,month_end,day_end):
    try:
        start_date = date_converter(year_start, month_start, day_start)
        end_date = date_converter(year_end, month_end, day_end) + relativedelta(seconds=86399)
        s_data = summarized_ammount_by_day(start_date, end_date, entity_id=entity_id)
    except Exception:
        raise Http404
    return HttpResponse(json.dumps(s_data, cls=DjangoJSONEncoder))

def proveedor_item(request,supplier_id, year_start="",month_start="",day_start="",year_end="",month_end="",day_end=""):
    if (year_start == ""):
        end_date = date_converter()
        start_date = end_date + relativedelta(months=-1)
    else:
        start_date = date_converter(year_start, month_start, day_start)    
        end_date = date_converter(year_end, month_end, day_end) + relativedelta(seconds=86399)
    supplier = get_object_or_404(Supplier, pk=supplier_id)
    return render(request, 'GCEstadisticas/proveedor.html', {'supplier':supplier, 'start_date':start_date.strftime("%Y-%m-%d"), 'end_date':end_date.strftime("%Y-%m-%d")})
    
def proveedor_entities(request,supplier_id, year_start,month_start,day_start,year_end,month_end,day_end):
    try:
        start_date = date_converter(year_start, month_start, day_start)    
        end_date = date_converter(year_end, month_end, day_end) + relativedelta(seconds=86399)
        s_data = supplier_entities_summary(start_date, end_date, supplier_id)
    except Exception:
        raise Http404
    return HttpResponse(json.dumps(list(s_data.values()), cls=DjangoJSONEncoder))
    
def proveedor_pagos_by_day(request,supplier_id, year_start,month_start,day_start,year_end,month_end,day_end):
    try:
        start_date = date_converter(year_start, month_start, day_start)
        end_date = date_converter(year_end, month_end, day_end) + relativedelta(seconds=86399)
        s_data = summarized_ammount_by_day(start_date, end_date, supplier_id=supplier_id)
    except Exception:
        raise Http404
    return HttpResponse(json.dumps(s_data, cls=DjangoJSONEncoder))

def proveedor_modalities(request, supplier_id, year_start, month_start, day_start, year_end, month_end, day_end):
    start_date = date_converter(year_start, month_start, day_start)    
    end_date = date_converter(year_end, month_end, day_end) + relativedelta(seconds=86399)
    s_data = entity_modality_summary(start_date, end_date, supplier_id=supplier_id)
    return HttpResponse(json.dumps(list(s_data), cls=DjangoJSONEncoder))

def proveedor_categories(request, supplier_id, year_start, month_start, day_start, year_end, month_end, day_end):
    start_date = date_converter(year_start, month_start, day_start)    
    end_date = date_converter(year_end, month_end, day_end) + relativedelta(seconds=86399)
    s_data = supplier_category_summary(start_date, end_date, supplier_id)
    return HttpResponse(json.dumps(list(s_data), cls=DjangoJSONEncoder))

class CustomContactFormView(FormView):
    form_class = CustomContactForm
    template_name = 'contact_form/contact_form.html'
 
    def form_valid(self, form):
        form.save()
        return super(CustomContactFormView, self).form_valid(form)
 
    def get_form_kwargs(self):
        # ContactForm instances require instantiation with an
        # HttpRequest.
        kwargs = super(CustomContactFormView, self).get_form_kwargs()
        kwargs.update({'request': self.request})
        return kwargs
 
    def get_success_url(self):
        # This is in a method instead of the success_url attribute
        # because doing it as an attribute would involve a
        # module-level call to reverse(), creating a circular
        # dependency between the URLConf (which imports this module)
        # and this module (which would need to access the URLConf to
        # make the reverse() call).
        return reverse(app_name+':contact_form_sent')
