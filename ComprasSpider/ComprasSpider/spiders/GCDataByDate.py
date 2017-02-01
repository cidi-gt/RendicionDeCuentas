#exec op1: $scrapy crawl GCDataByDate -a fecha_ini=13.junio.2016 -a fecha_fin=13.junio.2016
#exec op2: $pdate="03.agosto.2016"; scrapy crawl GCDataByDate -a fecha_ini=$pdate -a fecha_fin=$pdate --logfile=$pdate.txt
#exec op3: $lname="201608-01-07";sdate="01.agosto.2016";edate="07.agosto.2016";scrapy crawl GCDataByDate -a fecha_ini=$sdate -a fecha_fin=$edate --logfile=crawls/logs/$lname.txt -s JOBDIR=crawls
#exec op4 (solo nogs): $scrapy crawl GCDataByDate -a nogs=2086980,2086981
#exec op5 (solo nogs con log): $lname="nogs_sin_awarded";sdate="";edate="";nogs="2086980,2086981";scrapy crawl GCDataByDate -a fecha_ini=$sdate -a fecha_fin=$edate -a nogs=$nogs --logfile=crawls/logs/$lname.txt -s JOBDIR=crawls


import scrapy
import logging
from scrapy.http import FormRequest
import re
from decimal import Decimal
from urllib.parse import urlparse, parse_qs
from GCEstadisticas.models import Entity, EntityType, PurchaseCategory, Requisition, Supplier, Proposal, Awarded
from datetime import datetime
from django.utils import timezone
from babel.dates import format_date
import pytz
from dateutil.relativedelta import relativedelta
from scrapy.spidermiddlewares.httperror import HttpError


class GCDataByDate(scrapy.Spider):
    name = 'GCDataByDate'
    limit_per_page = 0 #qty of nogs per page to scrap, 0 for no limit
    limit_of_pages = 0 #qty of pages to scrap, 0 for no limit
    pagesScrapped = 1 #var to hold number of page being scraped
    controlPage = None #hold of response in the first request (needed as the site relies on ajax calls)
    skip_repetead = False
    nogs_processed = 0
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

    def start_requests(self):
        if (self.start_date != '') and (self.end_date != ''):
            url='http://guatecompras.gt/concursos/consultaConAvanz.aspx'
            yield scrapy.Request(url=url, callback=self.parse, priority=1, dont_filter=True)
        for nog in self.nogs:
            self.qty_nogs = len(self.nogs)
            if (nog.strip() != ''):
                url='http://guatecompras.gt/concursos/consultaDetalleCon.aspx?nog='+nog.strip()+'&o=4'
                yield scrapy.Request(url=url, callback=self.parse_nog, priority=1, dont_filter=True)
        for entity in self.entities:
            if (entity.strip() != ''):
                url='http://guatecompras.gt/Compradores/consultaDetEnt.aspx?iEnt='+entity.strip()+'&iUnt=0&iTipo=1'
                yield scrapy.Request(url=url, callback=self.parse_entity, priority=1, dont_filter=True)


    def __init__(self, fecha_ini='', fecha_fin='', skip='0', nogs='', entities=''):
        if (fecha_ini.strip() == '') and (fecha_fin.strip() == ''):
            tz = pytz.timezone('America/Guatemala')
            yesterday = timezone.localtime(timezone.now()).replace(tzinfo=pytz.timezone('America/Guatemala')) + relativedelta(days=-1)
            fecha_ini = format_date(yesterday, "dd.LLLL.YYYY", locale='es_GT')
            fecha_fin = format_date(yesterday, "dd.LLLL.YYYY", locale='es_GT')
        self.formdata['MasterGC$ContentBlockHolder$txtFechaIni'] = fecha_ini
        self.formdata['MasterGC$ContentBlockHolder$txtFechaFin'] = fecha_fin
        self.start_date = fecha_ini
        self.end_date = fecha_fin
        self.nogs = nogs.split(",")
        self.entities = entities.split(",")
        if (skip=='1'):
            self.skip_repetead = True
        self.logger.info('[ComprasVisibles]---------%r-%r---------'%(fecha_ini, fecha_fin))

    def parse(self, response):
        self.controlPage = response
        print("FIRST PARSE USER AGENT %r"%response.request.headers['User-Agent'])
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
        self.logger.info('[ComprasVisibles] starting page %r'%self.pagesScrapped)
        #print("PROCESS PAGE USER AGENT %r"%response.request.headers['User-Agent'])
        #print("MORE DATA %r %r %r"%(response.headers,response.meta,response.url))
        #extract qty of nogs and ammount and write it on the log file
        if (self.pagesScrapped == 1):
            self.qty_nogs = int(response.xpath('(//td[@class="EtiquetaFormMoradoDetalle"]/a/text())[1]').extract()[0].replace(',',''))
            t_ammount = Decimal(response.xpath('(//td[@class="EtiquetaFormMoradoDetalle"]/a/text())[2]').extract()[0].replace(',',''))
            self.logger.info('[ComprasVisibles] QTY of nogs: %r. Total ammount for the search: %r'%(self.qty_nogs, t_ammount))
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
        #extract nogs in the page (limited by nogCount)
        nogCount = 0
        nogs = response.xpath('//tr[@class="TablaFilaMix1"] | //tr[@class="TablaFilaMix2"]')
        if not nogs:
            self.logger.error('[ComprasVisibles] ERROR: no se encontraro NOGs en la pagina %r'%response.url)
        for sel in nogs:
            nog = sel.xpath('td[1]/div/span[1]/text()').extract()
            if(self.skip_repetead):
                search_nog = Requisition.objects.filter(nog=nog[0])
                if (search_nog.count()>0):
                    self.logger.info('[ComprasVisibles] skipping nog page %r'%nog[0])
                    self.nogs_processed += 1
                    print("processing nog %r of %r"%(self.nogs_processed, self.qty_nogs))
                    continue
            url = sel.xpath('td[2]/div/div/a/@href').extract()
            #call to scrap the nog
            yield scrapy.Request(url=response.urljoin(url[0]), callback=self.parse_nog, priority=1, dont_filter=True)
            nogCount = nogCount + 1
            if ((self.limit_per_page > 0) and (self.limit_per_page <= nogCount)):
                break
        self.pagesScrapped = self.pagesScrapped+1

    def parse_nog(self, response):
        self.logger.info('[ComprasVisibles] parsing nog page %r'%response.url)
        #print("USER AGENT %r"%response.request.headers['User-Agent'])
        #labels for values that will be saved, and then itemInfo will recieve the value of labelToItem as key
        self.nogs_processed += 1
        print("processing nog %r of %r"%(self.nogs_processed, self.qty_nogs))
        labelToItem = {
            'disposable':'disposable', 
            'NOG:':'nog',
            'Entidad:':'entidad', 
            'Estatus:':'estado', 
            'Modalidad:':'modalidad', 
            'Tipo de concurso:':'tipoConc', 
            'Tipo de entidad:':'entidadTipo', 
            'Unidad compradora:':'unidadCompradora', 
            u'Categor\xeda:':'categoria',
            u'Categor\xedas:':'categorias',  
            u'Descripci\xf3n:':'descripcion', 
            u'Fecha de publicaci\xf3n:':'fechaPub', 
            u'Fecha de presentaci\xf3n de ofertas:':'fechaPresentacionOfertas', 
            u'Fecha de cierre de recepci\xf3n de ofertas:':'fechaCierreRecepcion', 
            u'Recepci\xf3n de ofertas:':'tipoRecepcion', 
            u'Fecha de finalizaci\xf3n:':'fechaFin',
        }
        itemInfo = {}
        #labels for links that will be stored, and then itemInfo will recieve the value of labelGetLink as key
        labelGetLink = {
            'disposeLink':'disposeLink', 
            'Entidad:':'entidadLink', 
            'Unidad compradora:':'unidadCompradoraLink'
        }
        #this are the items that are in the table containing main nog info
        info_items = response.xpath('//div[@id="MasterGC_ContentBlockHolder_upNog"]/table/tr/td/table[@class="TablaForm2"]/tr/td[@class="TablaForm3"]/table[@class="TablaForm3"]/tr')
        if not info_items:
            self.logger.error('[ComprasVisibles] ERROR: no se encontro informacion del NOG en la pagina %r'%response.url)
        for nogInfo in info_items:
            rowItem = nogInfo.xpath('td[1]/text() | td[1]/span/text()').extract()
            if rowItem:
                rowLabel = rowItem.pop()
                #if the rowItem is on the list of items to store, then store the extracted data on itemInfo
                label = labelToItem.get(rowLabel,'disposable')
                itemInfo[label] = nogInfo.xpath('td[2]/span/text() | td[2]/span/a/text()').extract()
                #get the category objects to make the relation
                if (label == 'categoria'):
                    item_category = [PurchaseCategory.objects.get_or_create(name=itemInfo['categoria'][0])[0]]
                elif (label == 'categorias'):
                    item_category = []
                    for item in itemInfo['categorias']:
                        item = re.compile("[0-9]+\. ").split(item)[1].strip()
                        item_category.append(PurchaseCategory.objects.get_or_create(name=item)[0])
                #check if the data being extracted is an URL
                url = nogInfo.xpath('td[2]/span/a/@href').extract()
                if (url):
                    url = response.urljoin(url.pop())
                    #check if the link is supposed to be stored
                    label = labelGetLink.get(rowLabel,'disposeLink')
                    itemInfo[label] = url
                    #if we got the 'entidad' check if exists and get the 'entidad' info if not.
                    if (label == 'entidadLink'):
                        parsed_url = urlparse(url)
                        url_params = parse_qs(parsed_url.query)
                        if ('iEnt' in url_params):
                            entity = int(url_params['iEnt'][0])
                            try:
                                nog_entity = Entity.objects.get(id=entity)
                            except Exception:
                                #save minimum data so the nog can be processed even if the info is not complete, and then complete with the yield
                                #get type from url_params
                                if ('iTipo' in url_params):
                                    entity_type_id = int(url_params['iTipo'][0])
                                    entity_type_obj = EntityType.objects.get(id=entity_type_id)
                                    if not entity_type_obj:
                                        self.logger.error('[ComprasVisibles] ERROR: el entity type no existe  %r'%response.url)
                                #get the name from link text.
                                default_argument = {
                                    'name':itemInfo['entidad'][0]
                                }
                                nog_entity = Entity.objects.get_or_create(
                                    id = entity,
                                    entity_type = entity_type_obj,
                                    defaults = default_argument
                                )
                                #finally call the scrapper to finish the entity info
                                yield scrapy.Request(url=url, callback=self.parse_entity, priority=2)
        #prepare dates convertion to something that python understands when passed to the model.
        #it has been done converting spanish to month_num, since it was easer than change the locale
        #of the script
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
            'diciembre':'12',
            'a.m.':'am',
            'p.m.':'pm',
            'a. m.':'am',
            'p. m.':'pm'
        }
        tz = pytz.timezone('America/Guatemala')
        for key in date_convertion_map:
            itemInfo['fechaPub'][0] = itemInfo['fechaPub'][0].replace(key, date_convertion_map[key])
            if ('fechaPresentacionOfertas' in itemInfo.keys()):
                itemInfo['fechaPresentacionOfertas'][0] = itemInfo['fechaPresentacionOfertas'][0].replace(key, date_convertion_map[key])
            if ('fechaCierreRecepcion' in itemInfo.keys()):
                itemInfo['fechaCierreRecepcion'][0] = itemInfo['fechaCierreRecepcion'][0].replace(key, date_convertion_map[key])
            if ('fechaFin' in itemInfo.keys()):
                itemInfo['fechaFin'][0] = itemInfo['fechaFin'][0].replace(key, date_convertion_map[key])
            #start_date and end_date of the spider are used when there is no 'fechaFin', and if start_date == end_date, then use that as fechaFin
            self.start_date = self.start_date.replace(key, date_convertion_map[key])
            self.end_date = self.end_date.replace(key, date_convertion_map[key])
        try:
            itemInfo['fechaCierreRecepcion'][0] = tz.localize(datetime.strptime(itemInfo['fechaCierreRecepcion'][0], '%d.%m.%Y Hora:%I:%M:%S %p'))
        except Exception:
            if (not('fechaCierreRecepcion' in itemInfo.keys())):
                #use fechaFin instead of fechaCierraRecepcion. probably an inverse auction
                itemInfo['fechaCierreRecepcion'] = [tz.localize(datetime.strptime(itemInfo['fechaFin'][0], '%d.%m.%Y Hora:%I:%M:%S %p'))]
            else:
                itemInfo['fechaCierreRecepcion'][0] = tz.localize(datetime.strptime(itemInfo['fechaCierreRecepcion'][0], '%d.%m.%Y'))
        #save nog info
        if (not('tipoRecepcion' in itemInfo.keys())):
            itemInfo['tipoRecepcion'] = 'N/A'
        default_argument = {
            'entity': Entity.objects.get(id=entity),
            'state': itemInfo['estado'][0],
            'modality': (itemInfo['modalidad'][0][:98]+'..') if len(itemInfo['modalidad'][0])>98 else itemInfo['modalidad'][0],
            'competition_type': (itemInfo['tipoConc'][0][:68]+'..') if len(itemInfo['tipoConc'][0])>68 else itemInfo['tipoConc'][0],
            'purchasing_unit': (itemInfo['unidadCompradora'][0][:123]+'..') if len(itemInfo['unidadCompradora'][0][:123])>123 else itemInfo['unidadCompradora'][0][:123],
            'description': itemInfo['descripcion'][0],
            'publication_date': tz.localize(datetime.strptime(itemInfo['fechaPub'][0], '%d.%m.%Y Hora:%I:%M:%S %p')),
            'close_date': itemInfo['fechaCierreRecepcion'][0],
            'reception_type': (itemInfo['tipoRecepcion'][0][:123]+'..') if len(itemInfo['tipoRecepcion'][0])>123 else itemInfo['tipoRecepcion'][0]
        }
        if ('fechaPresentacionOfertas' in itemInfo.keys()):
            default_argument['presentation_date'] = tz.localize(datetime.strptime(itemInfo['fechaPresentacionOfertas'][0], '%d.%m.%Y Hora:%I:%M:%S %p'))
        if ('fechaFin' in itemInfo.keys()):
            default_argument['end_date'] = tz.localize(datetime.strptime(itemInfo['fechaFin'][0], '%d.%m.%Y Hora:%I:%M:%S %p'))
        else:
            #Sometiems nogs don't have end_date, in these cases if possible, use the spider start_date as nog end_date.  It is possible when start_date==end_date
            if(self.start_date == self.end_date):
                default_argument['end_date'] = tz.localize(datetime.strptime(self.start_date, '%d.%m.%Y'))
            else:
                self.logger.error('[ComprasVisibles] ERROR: el nog no tiene fecha de adjudicacion y no se puede determinar a traves de las fechas del spider %r'%itemInfo['nog'][0])
        nog = Requisition.objects.update_or_create(
            nog = itemInfo['nog'][0],
            defaults = default_argument
        )[0]
        try:
            nog.categories.clear()
            for item in item_category:
                nog.categories.add(item)
        except Exception as e:
            self.logger.error('[ComprasVisibles] ERROR: error al hacer la relacion nog-categoria %r'%str(e))
        #delete proposals and awarded if exists (this is in case the nog is being loaded again, to load again the data)
        for prop in Proposal.objects.filter(requisition=nog):
            prop.delete()
        for aw in Awarded.objects.filter(requisition=nog):
            aw.delete()
        #get info from 'oferentes'
        for oferente in response.xpath('//table[@id="MasterGC_ContentBlockHolder_GV_Oferentes"]/tr[@class="TablaFila1Norm"] | //table[@id="MasterGC_ContentBlockHolder_GV_Oferentes"]/tr[@class="TablaFila2Norm"]'):
            oferente_nit = oferente.xpath('td[1]/text()').extract()[0].strip()
            oferente_nit = (oferente_nit[:20]) if len(oferente_nit)>20 else oferente_nit
            oferente_name_results = oferente.xpath('td[2]/a/text() | td[2]/text() | td[2]/span/text()').extract()
            oferente_name = ""
            for on in oferente_name_results:
                if (on.strip() != ""):
                    oferente_name = on.strip()
            oferente_name = (oferente_name[:125]) if len(oferente_name)>125 else oferente_name
            oferta_monto = Decimal(re.sub(r'[^\d.]','',oferente.xpath('td[4]/text()').extract()[0].strip()))
            oferente_url = oferente.xpath('td[2]/a/@href').extract()
            #if it has lprv, meaning that is correctly registered in GC
            if (oferente_url):
                oferente_url = response.urljoin(oferente_url.pop())
                parsed_url = urlparse(oferente_url)
                url_params = parse_qs(parsed_url.query)
                if ('lprv' in url_params):
                    oferente_lprv = int(url_params['lprv'][0])
                    default_argument = {
                        'nit': oferente_nit,
                        'name': oferente_name
                    }
                    supplier_oferta = Supplier.objects.get_or_create(
                        lprv=oferente_lprv, 
                        defaults = default_argument
                    )[0]
                    #some suppliers loaded have blank name, if this find them, it will fix them
                    if (supplier_oferta.name.strip() == ''):
                        supplier_oferta.name = oferente_name
                        supplier_oferta.save()
                    #prepare data to save proposal info
                    default_argument = {
                        'ammount': oferta_monto
                    }
                    proposal = Proposal.objects.get_or_create(
                        supplier = supplier_oferta,
                        requisition = nog,
                        defaults = default_argument
                    )
                    #if it was "get" instead of create,  add the two ammounts and update (in some nogs there are more than one line per supplier)
                    if(not proposal[1]):
                        proposal[0].ammount += oferta_monto
                        proposal[0].save()
            else:
                #this means that it does not have lprv, it is an foreign supplier and there is no
                #info about it in GC
                supplier_oferta = Supplier.objects.get_or_create(
                    nit = oferente_nit,
                    name = oferente_name
                )[0]
                default_argument = {
                    'ammount':oferta_monto                        
                }
                proposal = Proposal.objects.get_or_create(
                    supplier = supplier_oferta,
                    requisition = nog,
                    defaults = default_argument
                )
                #if it was "get" instead of create,  add the two ammounts and update (in some nogs there are more than one line per supplier)
                if(not proposal[1]):
                    proposal[0].ammount += oferta_monto
                    proposal[0].save()

        #get info from 'adjudicados'
        for adjudicado in response.xpath('//table[@id="MasterGC_ContentBlockHolder_dgProveedores"]/tr[@class="TablaFilaMix1"] | //table[@id="MasterGC_ContentBlockHolder_dgProveedores"]/tr[@class="TablaFilaMix2"]'):
            adjudicado_nit = adjudicado.xpath('td[1]/text()').extract()[0].strip()
            adjudicado_nit = (adjudicado_nit[:20]) if len(adjudicado_nit)>20 else adjudicado_nit
            adjudicado_name = adjudicado.xpath('td[2]/span/a/text() | td[2]/span/text()').extract()[0].strip()
            adjudicado_name = (adjudicado_name[:125]) if len(adjudicado_name)>125 else adjudicado_name
            adjudicado_monto = Decimal(re.sub(r'[^\d.]','', adjudicado.xpath('td[4]/text()').extract()[0].strip()))
            adjudicado_url = adjudicado.xpath('td[2]/span/a/@href').extract()
            if (adjudicado_url):
                adjudicado_url = response.urljoin(adjudicado_url.pop())
                parsed_url = urlparse(adjudicado_url)
                url_params = parse_qs(parsed_url.query)
                if ('lprv' in url_params):
                    adjudicado_lprv = int(url_params['lprv'][0])
                    default_argument = {
                        'nit': adjudicado_nit, 
                        'name': adjudicado_name                        
                    }
                    supplier_adjudicado = Supplier.objects.get_or_create(
                        lprv = adjudicado_lprv, 
                        defaults = default_argument
                    )[0]
                    #some suppliers loaded have blank name, if this find them, it will fix them
                    if (supplier_adjudicado.name.strip() == ''):
                        supplier_adjudicado.name = adjudicado_name
                        supplier_adjudicado.save()
                    #prepare data to save awarded info
                    default_argument = {
                        'ammount':adjudicado_monto                        
                    }
                    awarded = Awarded.objects.get_or_create(
                        supplier = supplier_adjudicado,
                        requisition = nog,
                        defaults = default_argument
                    )
                    #if it was "get" instead of create,  add the two ammounts and update (in some nogs there are more than one line per supplier)
                    if(not awarded[1]):
                        awarded[0].ammount += adjudicado_monto
                        awarded[0].save()
            else:
                #this means that it does not have lprv, it is an foreign supplier and there is no
                #info about it in GC
                supplier_adjudicado = Supplier.objects.get_or_create(
                    nit = adjudicado_nit,
                    name = adjudicado_name
                )[0]
                default_argument = {
                    'ammount':adjudicado_monto                        
                }
                awarded = Awarded.objects.get_or_create(
                    supplier = supplier_adjudicado,
                    requisition = nog,
                    defaults = default_argument
                )
                #if it was "get" instead of create,  add the two ammounts and update (in some nogs there are more than one line per supplier)
                if(not awarded[1]):
                    awarded[0].ammount += adjudicado_monto
                    awarded[0].save()

    def parse_entity(self, response):
        self.logger.info('[ComprasVisibles] parsing entity page %r'%response.url)
        #labels for values that you want to save, and then itemInfo will recieve the value of labelToItem as key
        label_to_item = {
            'disposable':'disposable', 
            'Entidad:':'entidad',
            'Tipo:':'type',
            'NIT:':'nit', 
            'Departamento:':'departamento', 
            'Municipio:':'municipio', 
        }
        item_info = {}
        #this are the items that are in the table containing entity info
        info_items = response.xpath('//div[@id="MasterGC_ContentBlockHolder_up_datos_actuales_unidad_gral"]/table/tr/td/table[@class="TablaForm2"]/tr/td[@class="TablaForm3"]/table[@class="TablaForm3"]/tr')
        if not info_items:
            self.logger.error('[ComprasVisibles] ERROR: no se encontro informacion de la entidad en la pagina %r'%response.url)        
        for entity_info in info_items:
            row_item = entity_info.xpath('td[1]/text() | td[1]/span/text()').extract()
            if row_item:
                row_label = row_item.pop()
                #if item is supposed to be saved (on latel_to_item), then store it on item_info
                item_info[label_to_item.get(row_label,'disposable')] = entity_info.xpath('td[2]/span/text() | td[2]/span/a/text() | td[2]/text()').extract()
                #get the entityType from URL and save it to item_info
                parsed_url = urlparse(response.url)
                url_params = parse_qs(parsed_url.query)
                if ('iTipo' in url_params):
                    item_info['entity_type_id'] = int(url_params['iTipo'][0])
                if ('iEnt' in url_params):
                    item_info['entity_id'] = int(url_params['iEnt'][0])
        #assign dummy value if it does not have nit
        if (('nit' not in item_info.keys()) or (item_info['nit'][0] == '')):
            item_info['nit'] = ['SN'+str(item_info['entity_id'])]
        #if entity type not in url (for example if the entity is being scraped directly and not by link in nog page) get it from page
        #check if assigned entity type is 1, since it is the dummy entity type that is being used forming the entity url and does not really exists
        if ('entity_type_id' not in item_info.keys() or (item_info['entity_type_id'] == 1)):
            eType = EntityType.objects.get(name=item_info['type'][0].strip())
        else:
            eType = EntityType.objects.get(id=item_info['entity_type_id'])
        if not eType:
            self.logger.error('[ComprasVisibles] ERROR: el entity type no existe  %r'%response.url)
        default_argument = {
            'name': item_info['entidad'][0].strip(),
            'nit': item_info['nit'][0].strip(),
            'department': item_info['departamento'][0].strip(),
            'city': item_info['municipio'][0].strip()
        }
        entity = Entity.objects.update_or_create(
            id = item_info['entity_id'],
            entity_type = eType,
            defaults = default_argument
        )
        print("se guardo la info complementaria de: %r - %r - %r"%(item_info['entity_id'],item_info['entidad'][0],item_info['nit'][0]))

