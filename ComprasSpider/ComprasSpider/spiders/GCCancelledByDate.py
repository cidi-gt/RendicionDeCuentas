# This package will contain the spiders of your Scrapy project
#
# Please refer to the documentation for information on how to create and manage
# your spiders.


import scrapy
import logging
from scrapy.http import FormRequest
import re
from urllib.parse import urlparse, parse_qs
from GCEstadisticas.models import Requisition, Proposal, Awarded
from datetime import datetime
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from babel.dates import format_date
import pytz
from scrapy.spidermiddlewares.httperror import HttpError


#to call:  
#$lname="logname";sdate="01.febrero.2016";edate="29.febrero.2016";c_type="0";scrapy crawl GCCancelledByDate -a fecha_ini=$sdate -a fecha_fin=$edate -a c_type=$c_type --logfile=crawls/logs/$lname.txt -s JOBDIR=crawls


class GCCancelledByDate(scrapy.Spider):
    name = 'GCCancelledByDate'
    limit_per_page = 0 #qty of nogs per page to scrap, 0 for no limit
    limit_of_pages = 0 #qty of pages to scrap, 0 for no limit
    pagesScrapped = 1 #var to hold number of page being scraped
    controlPage = None #hold of response in the first request (needed as the site relies on ajax calls)
    start_urls=['http://guatecompras.gt/concursos/consultaConAvanz.aspx']
    formdata={ #post variables that are filled with js
        'MasterGC$ContentBlockHolder$scriptManager':'MasterGC$ContentBlockHolder$UPConsultar|MasterGC$ContentBlockHolder$btnBuscar',
        '__EVENTTARGET':'',
        '__EVENTARGUMENT':'',
        '__LASTFOCUS':'',
        #'__VIEWSTATEGENERATOR':'784013A1',
        'MasterGC$ContentBlockHolder$DDLPreTipoEnt':'-1',
        'MasterGC$ContentBlockHolder$DDLTipoEntidad':'-1',
        'MasterGC$ContentBlockHolder$ddlEntidad':'-1',
        'MasterGC$ContentBlockHolder$hdnSelEnti':'-1',
        'MasterGC$ContentBlockHolder$ddlUC':'-1',
        'MasterGC$ContentBlockHolder$hdnSelUni':'-1',
        'MasterGC$ContentBlockHolder$ddlCat':'-1',
        'MasterGC$ContentBlockHolder$DdlModalidad':'-1',
        'MasterGC$ContentBlockHolder$DDLTipoConcurso':'-1',
        'MasterGC$ContentBlockHolder$DdlRecepOferta':'-1',
        #'MasterGC$ContentBlockHolder$txtHoy':'07.dic.2016', 
        'MasterGC$ContentBlockHolder$txtFechaIni':'',
        'MasterGC$ContentBlockHolder$txtFechaFin':'',
        'MasterGC$ContentBlockHolder$txtNOG':'',
        'MasterGC$ContentBlockHolder$TextBoxNOG':'',
        'MasterGC$ContentBlockHolder$txtTexto':'',
        'MasterGC$ContentBlockHolder$IEEnterSolv':'',
        '__ASYNCPOST':'true',
        'MasterGC$ContentBlockHolder$btnBuscar.x':'0',
        'MasterGC$ContentBlockHolder$btnBuscar.y':'0',
        'MasterGC$ContentBlockHolder$btnBuscar':''
    }

    def __init__(self, fecha_ini='', fecha_fin=''):
        if (fecha_ini.strip() == '') and (fecha_fin.strip() == ''):
            tz = pytz.timezone('America/Guatemala')
            yesterday = timezone.localtime(timezone.now()).replace(tzinfo=pytz.timezone('America/Guatemala')) + relativedelta(days=-1)
            fecha_ini = format_date(yesterday, "dd.LLLL.YYYY", locale='es_GT')
            fecha_fin = format_date(yesterday, "dd.LLLL.YYYY", locale='es_GT')
        self.formdata['MasterGC$ContentBlockHolder$txtFechaIni'] = fecha_ini
        self.formdata['MasterGC$ContentBlockHolder$txtFechaFin'] = fecha_fin
        self.start_date = fecha_ini
        self.end_date = fecha_fin
        #as there are more than one cancel types, it uses the variable c_type to tell the scraper which one to do, starting on 0
        self.c_type = 0
        self.cancel_types = []
        self.cancel_type_data = {}
        self.cancel_type_data['viewstate'] = '/wEPDwUJODgyMTI1NDY4DxYEHgpTb3J0Q29sdW1uBRFGRUNIQV9QVUJMSUNBQ0lPTh4KU29ydEFzY2VuZAUEREVTQxYCZg9kFgICAw9kFgICCQ9kFgICAQ9kFhwCBA9kFgJmD2QWAgIBDxAPFgYeDURhdGFUZXh0RmllbGQFBk5PTUJSRR4ORGF0YVZhbHVlRmllbGQFDFRJUE9fRU5USURBRB4LXyFEYXRhQm91bmRnZBAVBA9TZWN0b3IgUMO6YmxpY28eRmlkZWljb21pc29zIHkgb3RyYXMgZW50aWRhZGVzHk9yZ2FuaXphY2lvbmVzIEludGVybmFjaW9uYWxlcyQtLS0gVG9kb3MgbG9zIHRpcG9zIGRlIGVudGlkYWRlcyAtLS0VBAExATIBMwItMRQrAwRnZ2dnFgECA2QCBQ9kFgJmD2QWAgIBDxBkEBUBJi0tLSBUb2RvIGxvcyBzdWJ0aXBvcyBkZSBlbnRpZGFkZXMgLS0tFQECLTEUKwMBZxYBZmQCBg9kFgJmD2QWAgIBDxBkEBUBGy0tLSBUb2RhcyBsYXMgZW50aWRhZGVzIC0tLRUBAi0xFCsDAWcWAWZkAggPZBYCZg9kFgICAQ8QZBAVARotLS0gVG9kYXMgbGFzIHVuaWRhZGVzIC0tLRUBAi0xFCsDAWcWAWZkAgkPEA8WBh8CBQ5ub21icmVfbWVkaWFubx8DBRJjYXRlZ29yaWFfY29uY3Vyc28fBGdkEBUPFEFsaW1lbnRvcyB5IHNlbWlsbGFzIUNvbXB1dGFjacOzbiB5IHRlbGVjb211bmljYWNpb25lcyFDb25zdHJ1Y2Npw7NuIHkgbWF0ZXJpYWxlcyBhZmluZXMhRWxlY3RyaWNpZGFkIHkgYWlyZSBhY29uZGljaW9uYWRvKUxpbXBpZXphLCBmdW1pZ2FjacOzbiB5IGFydMOtY3Vsb3MgYWZpbmVzH011ZWJsZXMgeSBtb2JpbGlhcmlvIGRlIG9maWNpbmEkUGFwZWxlcsOtYSB5IGFydMOtY3Vsb3MgZGUgbGlicmVyw61hHlB1YmxpY2lkYWQsIGNhbXBhw7FhcyB5IHZhbGxhcx1TYWx1ZCBlIGluc3Vtb3MgaG9zcGl0YWxhcmlvcxVTZWd1cmlkYWQgeSBhcm1hbWVudG8mU2VndXJvcywgZmlhbnphcyB5IHNlcnZpY2lvcyBiYW5jYXJpb3MYVGV4dGlsZXMsIHJvcGEgeSBjYWx6YWRvJFRyYW5zcG9ydGUsIHJlcHVlc3RvcyB5IGNvbWJ1c3RpYmxlcyFPdHJvcyB0aXBvcyBkZSBiaWVuZXMgbyBzZXJ2aWNpb3MdLS0tIFRvZGFzIGxhcyBjYXRlZ29yw61hcyAtLS0VDwExATIBMwE0ATUBNgE3ATgBOQIxMAIxMQIxMgIxMwIxNAItMRQrAw9nZ2dnZ2dnZ2dnZ2dnZ2cWAQIOZAIKDxAPFgYfAgUGbm9tYnJlHwMFCU1vZGFsaWRhZB8EZ2QQFREsQmllbmVzIHkgU3VtaW5pc3Ryb3MgSW1wb3J0YWRvcyAoQXJ0LiA1IExDRSk0Q29tcHJhIERpcmVjdGEgY29uIE9mZXJ0YSBFbGVjdHLDs25pY2EgKEFydC4gNDMgTENFKTRDb21wcmEgRGlyZWN0YSBwb3IgYXVzZW5jaWEgZGUgb2ZlcnRhcyAoQXJ0LiAzMiBMQ0UpHkNvbnRyYXRvIEFiaWVydG8gKEFydC4gNDYgTENFKTFDb252ZW5pb3MgeSBUcmF0YWRvcyBJbnRlcm5hY2lvbmFsZXMgKEFydC4gMSBMQ0UpGUNvdGl6YWNpw7NuIChBcnQuIDM4IExDRSkXRG9uYWNpb25lcyAoQXJ0LiAxIExDRSkiTGljaXRhY2nDs24gUMO6YmxpY2EgKEFydC4gMTcgTENFKTROZWdvY2lhY2lvbmVzIGVudHJlIEVudGlkYWRlcyBQw7pibGljYXMgKEFydC4gMiBMQ0UpO1ByZWNhbGlmaWNhY2nDs24gZGUgUHJveWVjdG9zIEFQUCAoQXJ0LiA2MCBEZWNyZXRvIDE2LTIwMTApSFByb2NlZGltaWVudG8gUmVndWxhZG8gcG9yIGVsIEFydC4gNTRCaXMgIChTdWJhc3RhIEVsZWN0csOzbmljYSBJbnZlcnNhKUlQcm9jZWRpbWllbnRvIFJlZ3VsYWRvIHBvciBlbCBBcnTDrWN1bG8gNTQgQmlzIChGYXNlIGRlIFByZWNhbGlmaWNhY2nDs24pRlByb2NlZGltaWVudG9zIFJlZ3VsYWRvcyBwb3IgZWwgYXJ0w61jdWxvIDQ0IExDRSAoQ2Fzb3MgZGUgRXhjZXBjacOzbikwUHJvY2VkaW1pZW50b3MgcmVndWxhZG9zIHBvciBlbCBhcnTDrWN1bG8gNTQgTENFHlN1YmFzdGEgUMO6YmxpY2EgKEFydC4gODkgTENFKStWaW5jdWxhY2lvbmVzIEFjdWVyZG8gTWluaXN0ZXJpYWwgNjUtMjAxMSBBHS0tLSBUb2RhcyBsYXMgTW9kYWxpZGFkZXMgLS0tFRECMjMBMQEyATUCMTUBMwIyNQE0AjI3AjE5AjMxAjI5ATYBNwIxNwIyMQItMRQrAxFnZ2dnZ2dnZ2dnZ2dnZ2dnZxYBAhBkAgwPZBYCAgEPZBYCAgMPEGRkFgBkAg0PZBYCAgEPZBYCAgEPEGRkFgBkAg4PEA8WBh8CBQtkZXNjcmlwY2lvbh8DBQ10aXBvX2NvbmN1cnNvHwRnZBAVBAhQw7pibGljbwtSZXN0cmluZ2lkbwlWaW5jdWxhZG8XLS0tIFRvZG9zIGxvcyB0aXBvcyAtLS0VBAExATIBMwItMRQrAwRnZ2dnZGQCDw8QZGQWAWZkAhAPZBYCAgEPZBYCAgEPEGRkFgFmZAIRDxAPFgYfAgUGbm9tYnJlHwMFEGVzdGF0dXNfY29uY3Vyc28fBGdkEBUJB1ZpZ2VudGUORW4gZXZhbHVhY2nDs24UVGVybWluYWRvIGFkanVkaWNhZG8SRmluYWxpemFkbyBhbnVsYWRvE0ZpbmFsaXphZG8gZGVzaWVydG8SVGVybWluYWRvIFJlbWF0YWRvF1Rlcm1pbmFkbyBQcmVjYWxpZmljYWRvClN1YmFzdGFuZG8ZLS0tIFRvZG9zIGxvcyBlc3RhdHVzIC0tLRUJATEBMgEzATQBNQIxMgIxMwIxNAItMRQrAwlnZ2dnZ2dnZ2cWAQIDZAISD2QWAmYPZBYGAgEPEA8WAh8EZ2QQFQYPRGUgcHVibGljYWNpw7NuHEzDrW1pdGUgcGFyYSByZWNpYmlyIG9mZXJ0YXMNRGUgYW51bGFjacOzbhhGZWNoYSBkZSBSZWdpc3RybyBkZSBTRUkORmVjaGEgZGUgUHVqYXMeLS0tIEVsaWphIHVuIHRpcG8gZGUgZmVjaGEgLS0tFQYBMQEyATQBNgE3Ai0xFCsDBmdnZ2dnZxYBAgJkAgcPDxYCHgdFbmFibGVkZ2RkAgsPDxYCHwVnZGQCGg9kFgJmD2QWBAIBD2QWAmYPZBYCZg9kFgJmDw8WAh4HVmlzaWJsZWhkZAIDDzwrAAsAZBgBBR5fX0NvbnRyb2xzUmVxdWlyZVBvc3RCYWNrS2V5X18WAQUlTWFzdGVyR0MkQ29udGVudEJsb2NrSG9sZGVyJGJ0bkJ1c2NhctnmoVPBp37SFff94aiHQze8P4c5'
        self.cancel_type_data['ddlEstatus'] = '4'
        self.cancel_type_data['ddlTipoFecha'] =  '4'
        self.cancel_types.append(self.cancel_type_data)
        self.cancel_type_data = {}
        self.cancel_type_data['viewstate'] = '/wEPDwUJODgyMTI1NDY4DxYEHgpTb3J0Q29sdW1uBRFGRUNIQV9QVUJMSUNBQ0lPTh4KU29ydEFzY2VuZAUEREVTQxYCZg9kFgICAw9kFgICCQ9kFgICAQ9kFhwCBA9kFgJmD2QWAgIBDxAPFgYeDURhdGFUZXh0RmllbGQFBk5PTUJSRR4ORGF0YVZhbHVlRmllbGQFDFRJUE9fRU5USURBRB4LXyFEYXRhQm91bmRnZBAVBA9TZWN0b3IgUMO6YmxpY28eRmlkZWljb21pc29zIHkgb3RyYXMgZW50aWRhZGVzHk9yZ2FuaXphY2lvbmVzIEludGVybmFjaW9uYWxlcyQtLS0gVG9kb3MgbG9zIHRpcG9zIGRlIGVudGlkYWRlcyAtLS0VBAExATIBMwItMRQrAwRnZ2dnFgECA2QCBQ9kFgJmD2QWAgIBDxBkEBUBJi0tLSBUb2RvIGxvcyBzdWJ0aXBvcyBkZSBlbnRpZGFkZXMgLS0tFQECLTEUKwMBZxYBZmQCBg9kFgJmD2QWAgIBDxBkEBUBGy0tLSBUb2RhcyBsYXMgZW50aWRhZGVzIC0tLRUBAi0xFCsDAWcWAWZkAggPZBYCZg9kFgICAQ8QZBAVARotLS0gVG9kYXMgbGFzIHVuaWRhZGVzIC0tLRUBAi0xFCsDAWcWAWZkAgkPEA8WBh8CBQ5ub21icmVfbWVkaWFubx8DBRJjYXRlZ29yaWFfY29uY3Vyc28fBGdkEBUPFEFsaW1lbnRvcyB5IHNlbWlsbGFzIUNvbXB1dGFjacOzbiB5IHRlbGVjb211bmljYWNpb25lcyFDb25zdHJ1Y2Npw7NuIHkgbWF0ZXJpYWxlcyBhZmluZXMhRWxlY3RyaWNpZGFkIHkgYWlyZSBhY29uZGljaW9uYWRvKUxpbXBpZXphLCBmdW1pZ2FjacOzbiB5IGFydMOtY3Vsb3MgYWZpbmVzH011ZWJsZXMgeSBtb2JpbGlhcmlvIGRlIG9maWNpbmEkUGFwZWxlcsOtYSB5IGFydMOtY3Vsb3MgZGUgbGlicmVyw61hHlB1YmxpY2lkYWQsIGNhbXBhw7FhcyB5IHZhbGxhcx1TYWx1ZCBlIGluc3Vtb3MgaG9zcGl0YWxhcmlvcxVTZWd1cmlkYWQgeSBhcm1hbWVudG8mU2VndXJvcywgZmlhbnphcyB5IHNlcnZpY2lvcyBiYW5jYXJpb3MYVGV4dGlsZXMsIHJvcGEgeSBjYWx6YWRvJFRyYW5zcG9ydGUsIHJlcHVlc3RvcyB5IGNvbWJ1c3RpYmxlcyFPdHJvcyB0aXBvcyBkZSBiaWVuZXMgbyBzZXJ2aWNpb3MdLS0tIFRvZGFzIGxhcyBjYXRlZ29yw61hcyAtLS0VDwExATIBMwE0ATUBNgE3ATgBOQIxMAIxMQIxMgIxMwIxNAItMRQrAw9nZ2dnZ2dnZ2dnZ2dnZ2cWAQIOZAIKDxAPFgYfAgUGbm9tYnJlHwMFCU1vZGFsaWRhZB8EZ2QQFREsQmllbmVzIHkgU3VtaW5pc3Ryb3MgSW1wb3J0YWRvcyAoQXJ0LiA1IExDRSk0Q29tcHJhIERpcmVjdGEgY29uIE9mZXJ0YSBFbGVjdHLDs25pY2EgKEFydC4gNDMgTENFKTRDb21wcmEgRGlyZWN0YSBwb3IgYXVzZW5jaWEgZGUgb2ZlcnRhcyAoQXJ0LiAzMiBMQ0UpHkNvbnRyYXRvIEFiaWVydG8gKEFydC4gNDYgTENFKTFDb252ZW5pb3MgeSBUcmF0YWRvcyBJbnRlcm5hY2lvbmFsZXMgKEFydC4gMSBMQ0UpGUNvdGl6YWNpw7NuIChBcnQuIDM4IExDRSkXRG9uYWNpb25lcyAoQXJ0LiAxIExDRSkiTGljaXRhY2nDs24gUMO6YmxpY2EgKEFydC4gMTcgTENFKTROZWdvY2lhY2lvbmVzIGVudHJlIEVudGlkYWRlcyBQw7pibGljYXMgKEFydC4gMiBMQ0UpO1ByZWNhbGlmaWNhY2nDs24gZGUgUHJveWVjdG9zIEFQUCAoQXJ0LiA2MCBEZWNyZXRvIDE2LTIwMTApSFByb2NlZGltaWVudG8gUmVndWxhZG8gcG9yIGVsIEFydC4gNTRCaXMgIChTdWJhc3RhIEVsZWN0csOzbmljYSBJbnZlcnNhKUlQcm9jZWRpbWllbnRvIFJlZ3VsYWRvIHBvciBlbCBBcnTDrWN1bG8gNTQgQmlzIChGYXNlIGRlIFByZWNhbGlmaWNhY2nDs24pRlByb2NlZGltaWVudG9zIFJlZ3VsYWRvcyBwb3IgZWwgYXJ0w61jdWxvIDQ0IExDRSAoQ2Fzb3MgZGUgRXhjZXBjacOzbikwUHJvY2VkaW1pZW50b3MgcmVndWxhZG9zIHBvciBlbCBhcnTDrWN1bG8gNTQgTENFHlN1YmFzdGEgUMO6YmxpY2EgKEFydC4gODkgTENFKStWaW5jdWxhY2lvbmVzIEFjdWVyZG8gTWluaXN0ZXJpYWwgNjUtMjAxMSBBHS0tLSBUb2RhcyBsYXMgTW9kYWxpZGFkZXMgLS0tFRECMjMBMQEyATUCMTUBMwIyNQE0AjI3AjE5AjMxAjI5ATYBNwIxNwIyMQItMRQrAxFnZ2dnZ2dnZ2dnZ2dnZ2dnZxYBAhBkAgwPZBYCAgEPZBYCAgMPEGRkFgBkAg0PZBYCAgEPZBYCAgEPEGRkFgBkAg4PEA8WBh8CBQtkZXNjcmlwY2lvbh8DBQ10aXBvX2NvbmN1cnNvHwRnZBAVBAhQw7pibGljbwtSZXN0cmluZ2lkbwlWaW5jdWxhZG8XLS0tIFRvZG9zIGxvcyB0aXBvcyAtLS0VBAExATIBMwItMRQrAwRnZ2dnZGQCDw8QZGQWAWZkAhAPZBYCAgEPZBYCAgEPEGRkFgFmZAIRDxAPFgYfAgUGbm9tYnJlHwMFEGVzdGF0dXNfY29uY3Vyc28fBGdkEBUJB1ZpZ2VudGUORW4gZXZhbHVhY2nDs24UVGVybWluYWRvIGFkanVkaWNhZG8SRmluYWxpemFkbyBhbnVsYWRvE0ZpbmFsaXphZG8gZGVzaWVydG8SVGVybWluYWRvIFJlbWF0YWRvF1Rlcm1pbmFkbyBQcmVjYWxpZmljYWRvClN1YmFzdGFuZG8ZLS0tIFRvZG9zIGxvcyBlc3RhdHVzIC0tLRUJATEBMgEzATQBNQIxMgIxMwIxNAItMRQrAwlnZ2dnZ2dnZ2cWAQIEZAISD2QWAmYPZBYGAgEPEA8WAh8EZ2QQFQYPRGUgcHVibGljYWNpw7NuHEzDrW1pdGUgcGFyYSByZWNpYmlyIG9mZXJ0YXMVRGUgZGVjbGFyYWRvIGRlc2llcnRvGEZlY2hhIGRlIFJlZ2lzdHJvIGRlIFNFSQ5GZWNoYSBkZSBQdWphcx4tLS0gRWxpamEgdW4gdGlwbyBkZSBmZWNoYSAtLS0VBgExATIBNAE2ATcCLTEUKwMGZ2dnZ2dnFgECAmQCBw8PFgIeB0VuYWJsZWRnZGQCCw8PFgIfBWdkZAIaD2QWAmYPZBYEAgEPZBYCZg9kFgJmD2QWAmYPDxYCHgdWaXNpYmxlaGRkAgMPPCsACwBkGAEFHl9fQ29udHJvbHNSZXF1aXJlUG9zdEJhY2tLZXlfXxYBBSVNYXN0ZXJHQyRDb250ZW50QmxvY2tIb2xkZXIkYnRuQnVzY2FyEGugIOUEcx0CRenYL6oVrhgRAgQ='
        self.cancel_type_data['ddlEstatus'] = '5'
        self.cancel_type_data['ddlTipoFecha'] = '4'
        self.cancel_types.append(self.cancel_type_data)
        self.logger.info('[ComprasVisibles]---------%r-%r---------'%(fecha_ini, fecha_fin))
        self.curr_date =  format_date(timezone.now(), "YYYYLLdd", locale='es_GT')

    def parse(self, response):
        self.controlPage = response
        print("FIRST PARSE USER AGENT %r"%response.request.headers['User-Agent'])
        #clearing variables so every new type has clean variables
        self.formdata['MasterGC$ContentBlockHolder$btnBuscar.x'] = '0'
        self.formdata['MasterGC$ContentBlockHolder$btnBuscar.y'] = '0'
        self.formdata['MasterGC$ContentBlockHolder$btnBuscar'] = ''
        self.formdata['__EVENTTARGET'] = ''
        self.formdata['MasterGC$ContentBlockHolder$scriptManager'] = 'MasterGC$ContentBlockHolder$UPConsultar|MasterGC$ContentBlockHolder$btnBuscar'
        #uses c_type to know which cancel type to use
        if (self.c_type < len(self.cancel_types)):
            print("process ctype %r"%self.c_type)
            self.formdata['__VIEWSTATE'] = self.cancel_types[self.c_type]['viewstate']
            self.formdata['MasterGC$ContentBlockHolder$ddlEstatus'] = self.cancel_types[self.c_type]['ddlEstatus']
            self.formdata['MasterGC$ContentBlockHolder$ddlTipoFecha'] = self.cancel_types[self.c_type]['ddlTipoFecha']
            next_page = FormRequest.from_response(
                self.controlPage,
                formname='aspnetForm',
                formid='aspnetForm',
                formdata=self.formdata,
                callback=self.process_search,
                dont_filter=True
            )
            yield next_page

    def process_search_again(self, failure):
        #sometimes the scraper loses the sequence in the paginator (server returns a 411 error), 
        #when that occurs, then the same request will be sent again, 
        #until it can be fullfilled or it is manually aborted.
        if (failure.check(HttpError)):
            self.logger.info('[ComprasVisibles] HTTPERROR se intetara scrapear de nuevo')
            next_page_request = FormRequest.from_response(
                self.controlPage,
                formname='aspnetForm',
                formid='aspnetForm',
                formdata=self.formdata,
                callback=self.process_search,
                priority=10,
                errback=self.process_search_again,
                dont_filter=True
            )
            yield next_page_request

    def process_search(self, response):
        self.logger.info('[ComprasVisibles] starting page %r'%self.pagesScrapped)
        #print("PROCESS PAGE USER AGENT %r"%response.request.headers['User-Agent'])
        #extract pagination variables, so it can yield next page
        nextPag = response.xpath('//tr[@class="TablaPagineo"]/td/span[2]/following::a[1]/@href').extract()
        if (nextPag):
            nextPag = nextPag.pop()
            nextPost = re.search('\'.*?\'', nextPag)
            if nextPost:
                nextPost = re.sub("'","",nextPost.group(0),count=2)
                self.formdata.pop('MasterGC$ContentBlockHolder$btnBuscar',None)
                self.formdata.pop('MasterGC$ContentBlockHolder$btnBuscar.x',None)
                self.formdata.pop('MasterGC$ContentBlockHolder$btnBuscar.y',None)
                self.formdata['__EVENTTARGET'] = nextPost
                self.formdata['__VIEWSTATE'] = re.search(b"__VIEWSTATE\|(.*?)\|", response.body, re.MULTILINE).group(1)
                self.formdata['MasterGC$ContentBlockHolder$scriptManager'] = 'MasterGC$ContentBlockHolder$UPResultado|'+nextPost
                if (((self.limit_of_pages > 0) and (self.pagesScrapped < self.limit_of_pages)) or ((self.limit_of_pages == 0))):
                    next_page_request = FormRequest.from_response(
                        self.controlPage,
                        formname='aspnetForm',
                        formid='aspnetForm',
                        formdata=self.formdata,
                        callback=self.process_search,
                        priority=10,
                        errback=self.process_search_again,
                        dont_filter=True
                    )
                    yield next_page_request
            else:
                self.logger.info('[ComprasVisibles] no se encontraron mas paginas(nextPost vacio). la ultima scrapeada fue %r, '%self.pagesScrapped)
        else:
            self.logger.info('[ComprasVisibles] no se encontraron mas paginas(nextPage vacio). la ultima scrapeada fue %r, '%self.pagesScrapped)
            #try to scrap the next cancel type (parse method will check if there is another cancel type)
            self.c_type += 1
            url='http://guatecompras.gt/concursos/consultaConAvanz.aspx'
            yield scrapy.Request(url=url, callback=self.parse, priority=1, dont_filter=True)
        #extract nogs in the page (limited by nogCount)
        nogCount = 0
        nogs = response.xpath('//tr[@class="TablaFilaMix1"] | //tr[@class="TablaFilaMix2"]')
        if not nogs:
            self.logger.error('[ComprasVisibles] ERROR: no se encontraro NOGs en la pagina %r'%response.url)
        for sel in nogs:
            nog = sel.xpath('td[1]/div/span[1]/text()').extract()
            self.logger.info('[ComprasVisibles] searching nog %r'%nog[0])
            search_nog = Requisition.objects.filter(nog=nog[0])
            for s_nog in search_nog:
                self.logger.info('[ComprasVisibles] deleting nog %r'%s_nog)
                for prop in Proposal.objects.filter(requisition=s_nog):
                    prop.delete()
                for aw in Awarded.objects.filter(requisition=s_nog):
                    aw.delete()
                #log nog id,end_date, and then delete it
                with open('cancelled_nogs.txt', 'a') as f:
                    f.write('SpiderCancelDate: '+self.curr_date+';  Nog end_date: '+format_date(s_nog.end_date, "YYYYLLdd", locale='es_GT')+'; Nog#: '+s_nog.nog+'\n')
                s_nog.delete()
            nogCount = nogCount + 1
            if ((self.limit_per_page > 0) and (self.limit_per_page <= nogCount)):
                break
        self.pagesScrapped = self.pagesScrapped+1


