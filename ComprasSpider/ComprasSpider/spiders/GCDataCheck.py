# This package will contain the spiders of your Scrapy project
#
# Please refer to the documentation for information on how to create and manage
# your spiders.


import scrapy
import logging
import re
import pytz
from scrapy.http import FormRequest
from decimal import Decimal
from GCEstadisticas.models import Requisition, Awarded
from datetime import datetime
from django.db.models import Count,Sum
from dateutil.relativedelta import relativedelta
from babel.dates import format_date, format_datetime, format_time
from scrapy import signals
from scrapy import Spider



#to call:  
#$lname="BORRAR";sdate="01.febrero.2016";edate="29.febrero.2016";filename="checker";postfix="_check";scrapy crawl GCDataCheck -a fecha_ini=$sdate -a fecha_fin=$edate -a filename=$lname -a postfix=$postfix  --logfile=crawls/logs/$lname.txt -s JOBDIR=crawls


class GCDataCheck(scrapy.Spider):
    name = 'GCDataCheck'
    start_urls=['http://guatecompras.gt/concursos/consultaConAvanz.aspx']
    data_control = {}
    controlPage = None #hold of response in the first request (needed as the site relies on ajax calls)
    formdata={ #post variables that are filled with js
        'MasterGC$ContentBlockHolder$scriptManager':'MasterGC$ContentBlockHolder$UPConsultar|MasterGC$ContentBlockHolder$btnBuscar',
        '__EVENTTARGET':'',
        '__EVENTARGUMENT':'',
        '__LASTFOCUS':'',
        '__VIEWSTATE':'/wEPDwUJODgyMTI1NDY4DxYEHgpTb3J0Q29sdW1uBRFGRUNIQV9QVUJMSUNBQ0lPTh4KU29ydEFzY2VuZAUEREVTQxYCZg9kFgICAw9kFgICCQ9kFgICAQ9kFhwCBA9kFgJmD2QWAgIBDxAPFgYeDURhdGFUZXh0RmllbGQFBk5PTUJSRR4ORGF0YVZhbHVlRmllbGQFDFRJUE9fRU5USURBRB4LXyFEYXRhQm91bmRnZBAVBA9TZWN0b3IgUMO6YmxpY28eRmlkZWljb21pc29zIHkgb3RyYXMgZW50aWRhZGVzHk9yZ2FuaXphY2lvbmVzIEludGVybmFjaW9uYWxlcyQtLS0gVG9kb3MgbG9zIHRpcG9zIGRlIGVudGlkYWRlcyAtLS0VBAExATIBMwItMRQrAwRnZ2dnFgECA2QCBQ9kFgJmD2QWAgIBDxBkEBUBJi0tLSBUb2RvIGxvcyBzdWJ0aXBvcyBkZSBlbnRpZGFkZXMgLS0tFQECLTEUKwMBZxYBZmQCBg9kFgJmD2QWAgIBDxBkEBUBGy0tLSBUb2RhcyBsYXMgZW50aWRhZGVzIC0tLRUBAi0xFCsDAWcWAWZkAggPZBYCZg9kFgICAQ8QZBAVARotLS0gVG9kYXMgbGFzIHVuaWRhZGVzIC0tLRUBAi0xFCsDAWcWAWZkAgkPEA8WBh8CBQ5ub21icmVfbWVkaWFubx8DBRJjYXRlZ29yaWFfY29uY3Vyc28fBGdkEBUPFEFsaW1lbnRvcyB5IHNlbWlsbGFzIUNvbXB1dGFjacOzbiB5IHRlbGVjb211bmljYWNpb25lcyFDb25zdHJ1Y2Npw7NuIHkgbWF0ZXJpYWxlcyBhZmluZXMhRWxlY3RyaWNpZGFkIHkgYWlyZSBhY29uZGljaW9uYWRvKUxpbXBpZXphLCBmdW1pZ2FjacOzbiB5IGFydMOtY3Vsb3MgYWZpbmVzH011ZWJsZXMgeSBtb2JpbGlhcmlvIGRlIG9maWNpbmEkUGFwZWxlcsOtYSB5IGFydMOtY3Vsb3MgZGUgbGlicmVyw61hHlB1YmxpY2lkYWQsIGNhbXBhw7FhcyB5IHZhbGxhcx1TYWx1ZCBlIGluc3Vtb3MgaG9zcGl0YWxhcmlvcxVTZWd1cmlkYWQgeSBhcm1hbWVudG8mU2VndXJvcywgZmlhbnphcyB5IHNlcnZpY2lvcyBiYW5jYXJpb3MYVGV4dGlsZXMsIHJvcGEgeSBjYWx6YWRvJFRyYW5zcG9ydGUsIHJlcHVlc3RvcyB5IGNvbWJ1c3RpYmxlcyFPdHJvcyB0aXBvcyBkZSBiaWVuZXMgbyBzZXJ2aWNpb3MdLS0tIFRvZGFzIGxhcyBjYXRlZ29yw61hcyAtLS0VDwExATIBMwE0ATUBNgE3ATgBOQIxMAIxMQIxMgIxMwIxNAItMRQrAw9nZ2dnZ2dnZ2dnZ2dnZ2cWAQIOZAIKDxAPFgYfAgUGbm9tYnJlHwMFCU1vZGFsaWRhZB8EZ2QQFREsQmllbmVzIHkgU3VtaW5pc3Ryb3MgSW1wb3J0YWRvcyAoQXJ0LiA1IExDRSk0Q29tcHJhIERpcmVjdGEgY29uIE9mZXJ0YSBFbGVjdHLDs25pY2EgKEFydC4gNDMgTENFKTRDb21wcmEgRGlyZWN0YSBwb3IgYXVzZW5jaWEgZGUgb2ZlcnRhcyAoQXJ0LiAzMiBMQ0UpHkNvbnRyYXRvIEFiaWVydG8gKEFydC4gNDYgTENFKTFDb252ZW5pb3MgeSBUcmF0YWRvcyBJbnRlcm5hY2lvbmFsZXMgKEFydC4gMSBMQ0UpGUNvdGl6YWNpw7NuIChBcnQuIDM4IExDRSkXRG9uYWNpb25lcyAoQXJ0LiAxIExDRSkiTGljaXRhY2nDs24gUMO6YmxpY2EgKEFydC4gMTcgTENFKTROZWdvY2lhY2lvbmVzIGVudHJlIEVudGlkYWRlcyBQw7pibGljYXMgKEFydC4gMiBMQ0UpO1ByZWNhbGlmaWNhY2nDs24gZGUgUHJveWVjdG9zIEFQUCAoQXJ0LiA2MCBEZWNyZXRvIDE2LTIwMTApSFByb2NlZGltaWVudG8gUmVndWxhZG8gcG9yIGVsIEFydC4gNTRCaXMgIChTdWJhc3RhIEVsZWN0csOzbmljYSBJbnZlcnNhKUlQcm9jZWRpbWllbnRvIFJlZ3VsYWRvIHBvciBlbCBBcnTDrWN1bG8gNTQgQmlzIChGYXNlIGRlIFByZWNhbGlmaWNhY2nDs24pRlByb2NlZGltaWVudG9zIFJlZ3VsYWRvcyBwb3IgZWwgYXJ0w61jdWxvIDQ0IExDRSAoQ2Fzb3MgZGUgRXhjZXBjacOzbikwUHJvY2VkaW1pZW50b3MgcmVndWxhZG9zIHBvciBlbCBhcnTDrWN1bG8gNTQgTENFHlN1YmFzdGEgUMO6YmxpY2EgKEFydC4gODkgTENFKStWaW5jdWxhY2lvbmVzIEFjdWVyZG8gTWluaXN0ZXJpYWwgNjUtMjAxMSBBHS0tLSBUb2RhcyBsYXMgTW9kYWxpZGFkZXMgLS0tFRECMjMBMQEyATUCMTUBMwIyNQE0AjI3AjE5AjMxAjI5ATYBNwIxNwIyMQItMRQrAxFnZ2dnZ2dnZ2dnZ2dnZ2dnZxYBAhBkAgwPZBYCAgEPZBYCAgMPEGRkFgBkAg0PZBYCAgEPZBYCAgEPEGRkFgBkAg4PEA8WBh8CBQtkZXNjcmlwY2lvbh8DBQ10aXBvX2NvbmN1cnNvHwRnZBAVBAhQw7pibGljbwtSZXN0cmluZ2lkbwlWaW5jdWxhZG8XLS0tIFRvZG9zIGxvcyB0aXBvcyAtLS0VBAExATIBMwItMRQrAwRnZ2dnZGQCDw8QZGQWAWZkAhAPZBYCAgEPZBYCAgEPEGRkFgFmZAIRDxAPFgYfAgUGbm9tYnJlHwMFEGVzdGF0dXNfY29uY3Vyc28fBGdkEBUIB1ZpZ2VudGUORW4gZXZhbHVhY2nDs24UVGVybWluYWRvIGFkanVkaWNhZG8SRmluYWxpemFkbyBhbnVsYWRvE0ZpbmFsaXphZG8gZGVzaWVydG8SVGVybWluYWRvIFJlbWF0YWRvF1Rlcm1pbmFkbyBQcmVjYWxpZmljYWRvGS0tLSBUb2RvcyBsb3MgZXN0YXR1cyAtLS0VCAExATIBMwE0ATUCMTICMTMCLTEUKwMIZ2dnZ2dnZ2cWAQICZAISD2QWAmYPZBYGAgEPEA8WAh8EZ2QQFQQPRGUgcHVibGljYWNpw7NuHEzDrW1pdGUgcGFyYSByZWNpYmlyIG9mZXJ0YXMoRGUgYWRqdWRpY2FjacOzbiAow7psdGltYSBhZGp1ZGljYWNpw7NuKR4tLS0gRWxpamEgdW4gdGlwbyBkZSBmZWNoYSAtLS0VBAExATIBMwItMRQrAwRnZ2dnFgECAmQCBw8PFgIeB0VuYWJsZWRnZGQCCw8PFgIfBWdkZAIaD2QWAmYPZBYEAgEPZBYCZg9kFgJmD2QWAmYPDxYCHgdWaXNpYmxlaGRkAgMPPCsACwBkGAEFHl9fQ29udHJvbHNSZXF1aXJlUG9zdEJhY2tLZXlfXxYBBSVNYXN0ZXJHQyRDb250ZW50QmxvY2tIb2xkZXIkYnRuQnVzY2FyEJdNqWbWw30HnxanT/GaUmC8vjQ=',
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
        'MasterGC$ContentBlockHolder$ddlEstatus':'3', #state 3 is "Terminado Adjudicado", -1 is blank
        'MasterGC$ContentBlockHolder$ddlTipoFecha':'3', #3 es para fecha ultima de adjudicacion (se acompaña de las otras fechas), -1 es blank. hay que ver como queda el state para poder mandarlo correctamente.
        #'MasterGC$ContentBlockHolder$txtHoy':'08.ago.2016', 
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

    def __init__(self, fecha_ini='', fecha_fin='', filename='checker', postfix='_check'):
        self.formdata['MasterGC$ContentBlockHolder$txtFechaIni'] = fecha_ini
        self.formdata['MasterGC$ContentBlockHolder$txtFechaFin'] = fecha_fin
        self.fecha_ini = fecha_ini
        self.fecha_fin = fecha_fin
        self.filename = filename
        self.postfix = postfix
        print("Checking integrity for %r to %r"%(fecha_ini, fecha_fin))
        self.logger.info('[ComprasVisibles] Checking integrity for %r to %r'%(fecha_ini, fecha_fin))

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(GCDataCheck, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.write_differences, signal=signals.spider_closed)
        return spider

    def write_differences(self, spider):
        self.logger.info('[ComprasVisibles] Stats for days with difference')
        for day in self.data_control.keys():
            self.logger.info('%r in GC not in DB: %r'%(day, self.data_control[day]['gc_not_db']))
            self.logger.info('%r in DB not in GC: %r'%(day, self.data_control[day]['db_not_gc']))
            self.logger.info('%r wrong ammount: %r'%(day, self.data_control[day]['wrong_ammount']))

    def parse(self, response):
        self.controlPage = response
        return FormRequest.from_response(
            response,
            formname='aspnetForm',
            formid='aspnetForm',
            formdata=self.formdata,
            callback=self.process_search,
            dont_filter=True
        )

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
        #get the date from the request object so it can be compared to the same range in db
        response_request = str(response.request.body)
        start_date = re.search("MasterGC%24ContentBlockHolder%24txtFechaIni=(.*?)&", response_request).group(1)
        end_date = re.search("MasterGC%24ContentBlockHolder%24txtFechaFin=(.*?)&", response_request).group(1)
        #convert weird GC date formats to somethin that can be used
        date_convertion_map = {
            'enero':'01',
            'febrero':'02',
            'marzo':'03',
            'abril':'04',
            'mayo':'05',
            'junio':'06',
            'julio':'07',
            'agosto':'08',
            'septiembre':'09',
            'octubre':'10',
            'noviembre':'11',
            'diciembre':'12'
        }
        tz = pytz.timezone('America/Guatemala')
        for key in date_convertion_map:
            start_date = start_date.replace(key, date_convertion_map[key])
            end_date = end_date.replace(key, date_convertion_map[key])
        try:
            start_date = tz.localize(datetime.strptime(start_date, '%d.%m.%Y'))
            #add 86399secs to end_date, so it can include the whole day (as the tz.localize uses the time 00:00:00
            end_date = tz.localize(datetime.strptime(end_date, '%d.%m.%Y')) + relativedelta(seconds=86399)
        except Exception:
            self.logger.info('[ComprasVisibles] Error when parsing dates %r %r'%(format_date(start_date, "dd.LLLL.YYYY", locale='es_GT'), format_date(end_date, "dd.LLLL.YYYY", locale='es_GT')))
        #get the info for the same dates from the database
        stored_nogs = Requisition.objects.filter(end_date__gte=start_date, end_date__lte=end_date).aggregate(nog_count=Count('nog'))
        stored_ammount = Awarded.objects.filter(requisition__end_date__gte=start_date,requisition__end_date__lte=end_date).aggregate(t_ammount=Sum('ammount'))
        #extract count of nogs and total ammount in GC
        qty_nogs = int(response.xpath('(//td[@class="EtiquetaFormMoradoDetalle"]/a/text())[1]').extract()[0].replace(',',''))
        t_ammount = Decimal(response.xpath('(//td[@class="EtiquetaFormMoradoDetalle"]/a/text())[2]').extract()[0].replace(',',''))
        #check if data is ok.  if it is just log, else, break the dates and try again (until only one day is being checked)
        if ((qty_nogs == stored_nogs['nog_count']) and (t_ammount == stored_ammount['t_ammount'])): 
            self.logger.info('[ComprasVisibles] %r to %r: is Ok'%(format_date(start_date, "dd.LLLL.YYYY", locale='es_GT'), format_date(end_date, "dd.LLLL.YYYY", locale='es_GT')))
        else:
            delta = end_date - start_date
            if (delta.days == 0):
                #if is the first page of the date scrapped, create info in self.data_control and insert the line in the scheduler so it can be scraped again the same day
                if (format_date(start_date, "dd.LLLL.YYYY", locale='es_GT') not in self.data_control.keys()):
                    self.logger.info('[ComprasVisibles] %r to %r difference(GC - DB): Nogs(%r - %r) and Q(%r - %r)'%(format_date(start_date, "dd.LLLL.YYYY", locale='es_GT'), format_date(end_date, "dd.LLLL.YYYY", locale='es_GT'), qty_nogs, stored_nogs, t_ammount, stored_ammount))
                    with open(self.filename+'_scheduler.txt', 'a') as f:
                        f.write('lname="'+format_date(start_date, "YYYYLLdd", locale='es_GT')+self.postfix+'.txt";sdate="'+format_date(start_date, "dd.LLLL.YYYY", locale='es_GT')+'";edate="'+format_date(start_date, "dd.LLLL.YYYY", locale='es_GT')+'";skip="1";scrapy crawl GCDataByDate -a fecha_ini=$sdate -a fecha_fin=$edate -a skip=$skip --logfile=crawls/logs/$lname.txt -s JOBDIR=crawls\n')
                    #get all nogs in db to compare with the ones in GC (only if the spider is running for 1 day)
                    if (self.fecha_ini == self.fecha_fin):
                        db_not_gc_qs = Requisition.objects.filter(end_date__gte=start_date, end_date__lte=end_date).annotate(t_ammount=Sum('awarded__ammount'))
                        db_not_gc = set(nog.nog for nog in db_not_gc_qs)
                        self.data_control[format_date(start_date, "dd.LLLL.YYYY", locale='es_GT')] = {}
                        self.data_control[format_date(start_date, "dd.LLLL.YYYY", locale='es_GT')]['db_not_gc'] = db_not_gc
                        self.data_control[format_date(start_date, "dd.LLLL.YYYY", locale='es_GT')]['gc_not_db'] = []
                        self.data_control[format_date(start_date, "dd.LLLL.YYYY", locale='es_GT')]['wrong_ammount'] = []
                #yield the next page so the nogs can be processed to find the exact nogs with difference (only if the spider is rnning for 1 day)
                if (self.fecha_ini == self.fecha_fin):
                    nextPag = response.xpath('//tr[@class="TablaPagineo"]/td/span[2]/following::a[1]/@href').extract()
                    if (nextPag):
                        nextPag = nextPag.pop()
                        nextPost = re.search('\'.*?\'', nextPag)
                        if nextPost:
                            nextPost = re.sub("'","",nextPost.group(0),count=2)
                            self.formdata.pop('MasterGC$ContentBlockHolder$btnBuscar',None)
                            self.formdata.pop('MasterGC$ContentBlockHolder$btnBuscar.x',None)
                            self.formdata.pop('MasterGC$ContentBlockHolder$btnBuscar.y',None)
                            self.formdata['MasterGC$ContentBlockHolder$txtFechaIni'] = format_date(start_date, "dd.LLLL.YYYY", locale='es_GT')
                            self.formdata['MasterGC$ContentBlockHolder$txtFechaFin'] = format_date(end_date, "dd.LLLL.YYYY", locale='es_GT')
                            self.formdata['__EVENTTARGET'] = nextPost
                            self.formdata['__VIEWSTATE'] = re.search(b"__VIEWSTATE\|(.*?)\|", response.body, re.MULTILINE).group(1)
                            self.formdata['MasterGC$ContentBlockHolder$scriptManager'] = 'MasterGC$ContentBlockHolder$UPResultado|'+nextPost
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
                            self.logger.info('[ComprasVisibles] no se encontraron mas paginas(nextPost vacio).')
                    else:
                        self.logger.info('[ComprasVisibles] no se encontraron mas paginas(nextPage vacio).')
                    #manage nog info and add the info to the corresponding dictionaries/arrays
                    nogs = response.xpath('//tr[@class="TablaFilaMix1"] | //tr[@class="TablaFilaMix2"]')
                    if not nogs:
                        self.logger.error('[ComprasVisibles] ERROR: no se encontraro NOGs en la pagina %r'%response.url)
                    for sel in nogs:
                        nog = sel.xpath('td[1]/div/span[1]/text()').extract()
                        nog_total = Decimal(sel.xpath('td[4]/text()').extract()[0].replace(',',''))            
                        search_nog = Requisition.objects.filter(nog=nog[0]).annotate(t_ammount=Sum('awarded__ammount'))
                        if (search_nog.count()>0):
                            self.data_control[format_date(start_date, "dd.LLLL.YYYY", locale='es_GT')]['db_not_gc'].discard(search_nog[0].nog)
                            if (search_nog[0].t_ammount != nog_total):
                                self.data_control[format_date(start_date, "dd.LLLL.YYYY", locale='es_GT')]['wrong_ammount'].append(search_nog[0].nog)
                        else:
                            self.data_control[format_date(start_date, "dd.LLLL.YYYY", locale='es_GT')]['gc_not_db'].append(nog[0])
            else:
                #break dates
                self.logger.info('[ComprasVisibles] %r to %r: Breaking dates'%(format_date(start_date, "dd.LLLL.YYYY", locale='es_GT'), format_date(end_date, "dd.LLLL.YYYY", locale='es_GT')))
                #calculate next 2 date ranges
                first_range_days = delta.days // 2
                first_range_end = start_date + relativedelta(days=first_range_days)
                second_range_start = first_range_end + relativedelta(days=1)
                #start_date to first_range_date
                self.formdata['MasterGC$ContentBlockHolder$txtFechaIni'] = format_date(start_date, "dd.LLLL.YYYY", locale='es_GT')
                self.formdata['MasterGC$ContentBlockHolder$txtFechaFin'] = format_date(first_range_end, "dd.LLLL.YYYY", locale='es_GT')
                next_page_request = FormRequest.from_response(
                    self.controlPage,
                    formname='aspnetForm',
                    formid='aspnetForm',
                    formdata=self.formdata,
                    callback=self.process_search,
                    dont_filter=True
                )
                yield next_page_request
                #second_range_start to end_date
                self.formdata['MasterGC$ContentBlockHolder$txtFechaIni'] = format_date(second_range_start, "dd.LLLL.YYYY", locale='es_GT')
                self.formdata['MasterGC$ContentBlockHolder$txtFechaFin'] = format_date(end_date, "dd.LLLL.YYYY", locale='es_GT')
                next_page_request = FormRequest.from_response(
                    self.controlPage,
                    formname='aspnetForm',
                    formid='aspnetForm',
                    formdata=self.formdata,
                    callback=self.process_search,
                    dont_filter=True
                )
                yield next_page_request
                
                
