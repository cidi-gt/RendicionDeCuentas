import decimal
import json
from GCEstadisticas.models import Requisition, Entity, Awarded, Supplier
from django.db.models import Count,Sum
from django.db.models.expressions import RawSQL
from django.db import connection
from django.core import serializers


def entity_summarized_data(start_date, final_date):
    kwargs = {}
    kwargs['t_suppliers_awarded'] = RawSQL("""
        SELECT
            COUNT("supplier_awarded"."supplier_id")
        FROM
            (
                SELECT DISTINCT "GCEstadisticas_supplier"."id" as "supplier_id"
                FROM "GCEstadisticas_requisition"
                LEFT OUTER JOIN  "GCEstadisticas_awarded" 
                    ON ("GCEstadisticas_requisition"."id" = "GCEstadisticas_awarded"."requisition_id")
                LEFT OUTER JOIN "GCEstadisticas_supplier"
                    ON ("GCEstadisticas_awarded"."supplier_id" = "GCEstadisticas_supplier"."id")
                WHERE (
                    "GCEstadisticas_requisition"."entity_id" = "GCEstadisticas_entity"."id" AND
                    "GCEstadisticas_requisition"."end_date" >= %s AND
                    "GCEstadisticas_requisition"."end_date" <= %s
                )
            ) "supplier_awarded"
            """,[start_date, final_date])
    kwargs['t_nogs'] = RawSQL("""
        SELECT 
            COUNT("GCEstadisticas_requisition"."id") AS "t_nogs" 
        FROM "GCEstadisticas_requisition" 
        WHERE ( 
            "GCEstadisticas_requisition"."entity_id" = "GCEstadisticas_entity"."id" AND
            "GCEstadisticas_requisition"."end_date" >= %s AND
            "GCEstadisticas_requisition"."end_date" <= %s
        )
        """,[start_date, final_date])
    kwargs['t_ammount'] = RawSQL("""
        SELECT
            SUM("GCEstadisticas_awarded"."ammount")
        FROM
            "GCEstadisticas_awarded"
        WHERE
            "GCEstadisticas_awarded"."requisition_id" IN (
                SELECT
                    "GCEstadisticas_requisition"."id"
                FROM "GCEstadisticas_requisition"
                WHERE ( 
                    "GCEstadisticas_requisition"."entity_id" = "GCEstadisticas_entity"."id" AND
                    "GCEstadisticas_requisition"."end_date" >= %s AND
                    "GCEstadisticas_requisition"."end_date" <= %s
                )
            )
            """,[start_date, final_date])
    all_data = Entity.objects.annotate(**kwargs)
    return all_data

def muni_summarized_data(start_date, final_date):
    #return Entity.objects.filter(entity_type__name__contains="Municipalidades", requisition__end_date__gte=start_date, requisition__end_date__lte=final_date).annotate(t_ammount=Sum('requisition__awarded__ammount'))
    return Entity.objects.filter(requisition__end_date__gte=start_date, requisition__end_date__lte=final_date).annotate(t_ammount=Sum('requisition__awarded__ammount'))
    
    
def summarized_ammount_by_day(start_date, final_date, entity_id=None, supplier_id=None):
    added_where = ''
    if (entity_id):
        added_where = 'AND "GCEstadisticas_requisition"."entity_id" = '+entity_id
    if (supplier_id):
        added_where = 'AND "GCEstadisticas_awarded"."supplier_id" = '+supplier_id
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                date("GCEstadisticas_requisition"."end_date" - interval '6 hours') as day_date,
                SUM("GCEstadisticas_awarded"."ammount") as t_ammount
            FROM "GCEstadisticas_entity"
            INNER JOIN "GCEstadisticas_requisition"
                ON "GCEstadisticas_entity"."id" = "GCEstadisticas_requisition"."entity_id"
            INNER JOIN "GCEstadisticas_awarded"
                ON ("GCEstadisticas_requisition"."id" = "GCEstadisticas_awarded"."requisition_id")
            WHERE(
                "GCEstadisticas_requisition"."end_date" >= %s AND 
                "GCEstadisticas_requisition"."end_date" <= %s
            """+added_where+"""
            )
            GROUP BY 1
            """, [start_date, final_date])
        compiled_data = []
        for e in cursor:
            item_data = {}
            item_data['end_date'] = e[0]
            item_data['t_ammount'] = e[1]
            compiled_data.append(item_data)
    return compiled_data
    
def entity_modality(start_date, final_date):
    summary_data = Entity.objects.raw("""
        SELECT 
            "GCEstadisticas_entity"."id",
            "GCEstadisticas_entity"."name",
            "GCEstadisticas_entity"."entity_type_id",
            "GCEstadisticas_requisition"."modality" as modality,
            Sum("GCEstadisticas_awarded"."ammount") as t_ammount
        FROM 
            "GCEstadisticas_entity"
        INNER JOIN "GCEstadisticas_requisition"
            ON ("GCEstadisticas_entity"."id" = "GCEstadisticas_requisition"."entity_id")
        INNER JOIN "GCEstadisticas_awarded"
            ON ("GCEstadisticas_requisition"."id" = "GCEstadisticas_awarded"."requisition_id")
        WHERE("GCEstadisticas_requisition"."end_date" >= %s and "GCEstadisticas_requisition"."end_date" <= %s)
        GROUP BY 1,4
        """, [start_date, final_date])
    compiled_data = []
    for item in summary_data:
        entity_data = {}
        entity_data['id'] = item.id
        entity_data['name'] = item.name
        entity_data['entity_type_id'] = item.entity_type_id
        entity_data['modality'] = item.modality
        entity_data['t_ammount'] = item.t_ammount
        compiled_data.append(entity_data)
    return compiled_data
    
def category_summary(start_date,final_date):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                "GCEstadisticas_purchasecategory"."id",
                "GCEstadisticas_purchasecategory"."name",
                "GCEstadisticas_entity"."id",
                "GCEstadisticas_entity"."name",
                "GCEstadisticas_entity"."entity_type_id",
                Sum("GCEstadisticas_awarded"."ammount") as t_ammount
            FROM
                "GCEstadisticas_purchasecategory"
            INNER JOIN (
                SELECT
                    "requisition_id",
                    MIN("purchasecategory_id") as "purchasecategory_id"
                FROM 
                    "GCEstadisticas_requisition_categories"
                GROUP BY 1
                HAVING COUNT("requisition_id") = 1 
            ) "GCErc"
                ON "GCEstadisticas_purchasecategory"."id" = "GCErc"."purchasecategory_id"
            INNER JOIN "GCEstadisticas_requisition"
                ON "GCEstadisticas_requisition"."id" = "GCErc"."requisition_id"
            INNER JOIN "GCEstadisticas_entity"
                ON "GCEstadisticas_entity"."id" = "GCEstadisticas_requisition"."entity_id"
            INNER JOIN "GCEstadisticas_awarded"
                ON "GCEstadisticas_awarded"."requisition_id" = "GCEstadisticas_requisition"."id"
            WHERE("GCEstadisticas_requisition"."end_date" >= %s and "GCEstadisticas_requisition"."end_date" <= %s)
            GROUP BY 1,3
            """, [start_date, final_date])
        compiled_data = []
        for e in cursor:
            item_data = {}
            item_data['c_id'] = e[0]
            item_data['category'] = e[1]
            item_data['e_id'] = e[2]
            item_data['entity'] = e[3]
            item_data['entity_type'] = e[4]
            item_data['t_ammount'] = e[5]
            compiled_data.append(item_data)
        cursor.execute("""
                SELECT
                    "GCEstadisticas_entity"."id",
                    "GCEstadisticas_entity"."name",
                    "GCEstadisticas_entity"."entity_type_id",
                    Sum("GCEstadisticas_awarded"."ammount") as t_ammount
                FROM
                    "GCEstadisticas_entity"
                INNER JOIN "GCEstadisticas_requisition"
                    ON "GCEstadisticas_requisition"."entity_id" = "GCEstadisticas_entity"."id"
                INNER JOIN (
                    SELECT
                        "GCEstadisticas_requisition_categories"."requisition_id"
                    FROM 
                        "GCEstadisticas_requisition_categories"
                    GROUP BY 1
                    HAVING COUNT("GCEstadisticas_requisition_categories"."requisition_id") > 1 
                ) "GCErc"
                    ON "GCErc"."requisition_id" = "GCEstadisticas_requisition"."id"
                INNER JOIN "GCEstadisticas_awarded"
                    ON "GCEstadisticas_awarded"."requisition_id" = "GCEstadisticas_requisition"."id"
                WHERE("GCEstadisticas_requisition"."end_date" >=  %s and "GCEstadisticas_requisition"."end_date" <=  %s)
                GROUP BY 1,3
            """, [start_date, final_date])
        for e in cursor:
            item_data = {}
            item_data['c_id'] = 0
            item_data['category'] = "Usada mas de una categoría"
            item_data['e_id'] = e[0]
            item_data['entity'] = e[1]
            item_data['entity_type'] = e[2]
            item_data['t_ammount'] = e[3]
            compiled_data.append(item_data)
    return compiled_data

def entity_list(get_cities=False):
    entities = Entity.objects.all().order_by('name')
    classified_entities = {}
    cities = {}
    for ent in entities:
        if (ent.entity_type.name in classified_entities.keys()):
            classified_entities[ent.entity_type.name].append(ent)
        else:
            classified_entities[ent.entity_type.name] = []
            classified_entities[ent.entity_type.name].append(ent)
        #if we need to get the list of departments and cities, we get it using the same for.
        if (get_cities):
            if (ent.department in cities.keys()):
                cities[ent.department].append(ent.city)
            else:
                cities[ent.department] = []
                cities[ent.department].append(ent.city)
    if (get_cities):
        for dep in cities:
            cities[dep] = list(sorted(set(cities[dep])))
        return [classified_entities, cities]
    else:
        return classified_entities

def suppliers_by_entity(start_date, final_date, entity_id):
    summary_data = Supplier.objects.raw("""
        SELECT q.*
        FROM (
            SELECT 
                "GCEstadisticas_supplier"."id",
                "GCEstadisticas_supplier"."lprv",  
                "GCEstadisticas_supplier"."nit", 
                "GCEstadisticas_supplier"."name", 
                (
                    SELECT
                        SUM("GCEstadisticas_awarded"."ammount") as "t_ammount"
                    FROM
                        "GCEstadisticas_awarded"
                    INNER JOIN "GCEstadisticas_requisition"
                        ON 
                            "GCEstadisticas_awarded"."requisition_id" = "GCEstadisticas_requisition"."id"
                    WHERE (
                        "GCEstadisticas_awarded"."supplier_id" = "GCEstadisticas_supplier"."id" AND
                        "GCEstadisticas_requisition"."entity_id" = %s AND
                        "GCEstadisticas_requisition"."end_date" >= %s AND
                        "GCEstadisticas_requisition"."end_date" <= %s
                    )
                ) as t_ammount,
                (
                    SELECT
                        COUNT("GCEstadisticas_awarded"."id") as "t_awarded"
                    FROM
                        "GCEstadisticas_awarded"
                    INNER JOIN "GCEstadisticas_requisition"
                        ON 
                            "GCEstadisticas_awarded"."requisition_id" = "GCEstadisticas_requisition"."id"
                    WHERE (
                        "GCEstadisticas_awarded"."supplier_id" = "GCEstadisticas_supplier"."id" AND
                        "GCEstadisticas_requisition"."entity_id" = %s AND
                        "GCEstadisticas_requisition"."end_date" >= %s AND
                        "GCEstadisticas_requisition"."end_date" <= %s
                    )
                ) as t_awarded
            FROM "GCEstadisticas_supplier"
        ) q
        """, [entity_id, start_date, final_date, entity_id, start_date, final_date])
    compiled_data = []
    for item in summary_data:
        entity_data = {}
        entity_data['id'] = item.id
        entity_data['lprv'] = item.lprv
        entity_data['nit'] = item.nit
        entity_data['name'] = item.name
        entity_data['t_ammount'] = item.t_ammount
        entity_data['t_awarded'] = item.t_awarded
        compiled_data.append(entity_data)
    return compiled_data

def entity_category_summary(start_date,final_date, entity_id):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                "GCEstadisticas_purchasecategory"."id",
                "GCEstadisticas_purchasecategory"."name",
                "GCEstadisticas_entity"."id",
                "GCEstadisticas_requisition"."purchasing_unit",
                Sum("GCEstadisticas_awarded"."ammount") as t_ammount
            FROM
                "GCEstadisticas_purchasecategory"
            INNER JOIN (
                SELECT
                    "requisition_id",
                    MIN("purchasecategory_id") as "purchasecategory_id"
                FROM 
                    "GCEstadisticas_requisition_categories"
                GROUP BY 1
                HAVING COUNT("requisition_id") = 1 
            ) "GCErc"
                ON "GCEstadisticas_purchasecategory"."id" = "GCErc"."purchasecategory_id"
            INNER JOIN "GCEstadisticas_requisition"
                ON "GCEstadisticas_requisition"."id" = "GCErc"."requisition_id"
            INNER JOIN "GCEstadisticas_entity"
                ON "GCEstadisticas_entity"."id" = "GCEstadisticas_requisition"."entity_id"
            INNER JOIN "GCEstadisticas_awarded"
                ON "GCEstadisticas_awarded"."requisition_id" = "GCEstadisticas_requisition"."id"
            WHERE(
                "GCEstadisticas_requisition"."end_date" >= %s AND 
                "GCEstadisticas_requisition"."end_date" <= %s AND
                "GCEstadisticas_entity"."id" = %s
            )
            GROUP BY 1,3,4
            """, [start_date, final_date, entity_id])
        compiled_data = []
        for e in cursor:
            item_data = {}
            item_data['c_id'] = e[0]
            item_data['category'] = e[1]
            item_data['e_id'] = e[2]
            item_data['unit'] = e[3]
            item_data['t_ammount'] = e[4]
            compiled_data.append(item_data)
        cursor.execute("""
                SELECT
                    "GCEstadisticas_entity"."id",
                    "GCEstadisticas_requisition"."purchasing_unit",
                    Sum("GCEstadisticas_awarded"."ammount") as t_ammount
                FROM
                    "GCEstadisticas_entity"
                INNER JOIN "GCEstadisticas_requisition"
                    ON "GCEstadisticas_requisition"."entity_id" = "GCEstadisticas_entity"."id"
                INNER JOIN (
                    SELECT
                        "GCEstadisticas_requisition_categories"."requisition_id"
                    FROM 
                        "GCEstadisticas_requisition_categories"
                    GROUP BY 1
                    HAVING COUNT("GCEstadisticas_requisition_categories"."requisition_id") > 1 
                ) "GCErc"
                    ON "GCErc"."requisition_id" = "GCEstadisticas_requisition"."id"
                INNER JOIN "GCEstadisticas_awarded"
                    ON "GCEstadisticas_awarded"."requisition_id" = "GCEstadisticas_requisition"."id"
                WHERE(
                    "GCEstadisticas_requisition"."end_date" >=  %s AND 
                    "GCEstadisticas_requisition"."end_date" <=  %s AND
                    "GCEstadisticas_entity"."id" = %s
                )
                GROUP BY 1,2
            """, [start_date, final_date, entity_id])
        for e in cursor:
            item_data = {}
            item_data['c_id'] = 0
            item_data['category'] = "Usada mas de una categoría"
            item_data['e_id'] = e[0]
            item_data['unit'] = e[1]
            item_data['t_ammount'] = e[2]
            compiled_data.append(item_data)
    return compiled_data

def entity_modality_summary(start_date, final_date, entity_id=None, supplier_id=None):
    added_where = ""
    entity_name_alias = "as entity_name"
    supplier_name_alias = "as supplier_name"
    entity_id_alias = "as entity_id"
    supplier_id_alias = "as supplier_id"
    if (entity_id is not None):
        added_where = '"GCEstadisticas_requisition"."entity_id" = ' + entity_id
        supplier_name_alias = "as name"
        supplier_id_alias = "as id"
    if (supplier_id is not None):
        added_where = '"GCEstadisticas_awarded"."supplier_id" = ' + supplier_id
        entity_name_alias = "as name"
        entity_id_alias = "as id"
    summary_data = Entity.objects.raw("""
        SELECT 
            "GCEstadisticas_entity"."id" """+entity_id_alias+""",
            "GCEstadisticas_entity"."name" """+entity_name_alias+""",
            "GCEstadisticas_supplier"."id" """+supplier_id_alias+""",
            "GCEstadisticas_supplier"."name" """+supplier_name_alias+""",
            "GCEstadisticas_requisition"."modality" as modality,
            Sum("GCEstadisticas_awarded"."ammount") as t_ammount
        FROM 
            "GCEstadisticas_entity"
        INNER JOIN "GCEstadisticas_requisition"
            ON ("GCEstadisticas_entity"."id" = "GCEstadisticas_requisition"."entity_id")
        INNER JOIN "GCEstadisticas_awarded"
            ON ("GCEstadisticas_requisition"."id" = "GCEstadisticas_awarded"."requisition_id")
        INNER JOIN "GCEstadisticas_supplier"
            ON ("GCEstadisticas_supplier"."id" = "GCEstadisticas_awarded"."supplier_id")
        WHERE( 
            "GCEstadisticas_requisition"."end_date" >= %s AND 
            "GCEstadisticas_requisition"."end_date" <= %s AND 
            """+added_where+"""
        )
        GROUP BY 1,3,5 
        """, [start_date, final_date])
    compiled_data = []
    for item in summary_data:
        entity_data = {}
        entity_data['id'] = item.id
        entity_data['name'] = item.name
        entity_data['modality'] = item.modality
        entity_data['t_ammount'] = item.t_ammount
        compiled_data.append(entity_data)
    return compiled_data

def purchase_list(start_date, final_date, entity_id=None, supplier_id=None):
    kwargs = {}
    kwargs['end_date__gte'] = start_date
    kwargs['end_date__lte'] = final_date
    if (entity_id is not None):
        kwargs['entity_id'] = entity_id
    if (supplier_id is not None):
        kwargs['awarded__supplier_id'] = supplier_id
    requisitions = Requisition.objects \
                                .filter(**kwargs) \
                                .annotate(t_ammount=Sum('awarded__ammount')) \
                                .select_related('entity')
    return requisitions

def supplier_entities_summary(start_date, final_date, supplier_id):
    return Entity.objects.filter(requisition__awarded__supplier_id = supplier_id, requisition__end_date__gte=start_date, requisition__end_date__lte=final_date).annotate(t_ammount=Sum('requisition__awarded__ammount'), qty_nogs=Count('requisition__awarded__id'))

def supplier_category_summary(start_date,final_date, supplier_id):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                "GCEstadisticas_purchasecategory"."id",
                "GCEstadisticas_purchasecategory"."name",
                "GCEstadisticas_entity"."id",
                "GCEstadisticas_entity"."name",
                "GCEstadisticas_supplier"."id",
                Sum("GCEstadisticas_awarded"."ammount") as t_ammount
            FROM
                "GCEstadisticas_purchasecategory"
            INNER JOIN (
                SELECT
                    "requisition_id",
                    MIN("purchasecategory_id") as "purchasecategory_id"
                FROM 
                    "GCEstadisticas_requisition_categories"
                GROUP BY 1
                HAVING COUNT("requisition_id") = 1 
            ) "GCErc"
                ON "GCEstadisticas_purchasecategory"."id" = "GCErc"."purchasecategory_id"
            INNER JOIN "GCEstadisticas_requisition"
                ON "GCEstadisticas_requisition"."id" = "GCErc"."requisition_id"
            INNER JOIN "GCEstadisticas_entity"
                ON "GCEstadisticas_entity"."id" = "GCEstadisticas_requisition"."entity_id"
            INNER JOIN "GCEstadisticas_awarded"
                ON "GCEstadisticas_awarded"."requisition_id" = "GCEstadisticas_requisition"."id"
            INNER JOIN "GCEstadisticas_supplier"
                ON "GCEstadisticas_supplier"."id" = "GCEstadisticas_awarded"."supplier_id"
            WHERE(
                "GCEstadisticas_requisition"."end_date" >= %s AND 
                "GCEstadisticas_requisition"."end_date" <= %s AND
                "GCEstadisticas_supplier"."id" = %s
            )
            GROUP BY 1,3,5
            """, [start_date, final_date, supplier_id])
        compiled_data = []
        for e in cursor:
            item_data = {}
            item_data['c_id'] = e[0]
            item_data['category'] = e[1]
            item_data['e_id'] = e[2]
            item_data['entity'] = e[3]
            item_data['t_ammount'] = e[5]
            compiled_data.append(item_data)
        cursor.execute("""
            SELECT
                "GCEstadisticas_entity"."id",
                "GCEstadisticas_entity"."name",
                "GCEstadisticas_supplier"."id",
                Sum("GCEstadisticas_awarded"."ammount") as t_ammount
            FROM
                "GCEstadisticas_entity"
            INNER JOIN "GCEstadisticas_requisition"
                ON "GCEstadisticas_requisition"."entity_id" = "GCEstadisticas_entity"."id"
            INNER JOIN (
                SELECT
                    "GCEstadisticas_requisition_categories"."requisition_id"
                FROM 
                    "GCEstadisticas_requisition_categories"
                GROUP BY 1
                HAVING COUNT("GCEstadisticas_requisition_categories"."requisition_id") > 1 
            ) "GCErc"
                ON "GCErc"."requisition_id" = "GCEstadisticas_requisition"."id"
            INNER JOIN "GCEstadisticas_awarded"
                ON "GCEstadisticas_awarded"."requisition_id" = "GCEstadisticas_requisition"."id"
            INNER JOIN "GCEstadisticas_supplier"
                ON "GCEstadisticas_supplier"."id" = "GCEstadisticas_awarded"."supplier_id"
            WHERE(
                "GCEstadisticas_requisition"."end_date" >=  %s AND 
                "GCEstadisticas_requisition"."end_date" <=  %s AND
                "GCEstadisticas_supplier"."id" = %s
            )
            GROUP BY 1,3
            """, [start_date, final_date, supplier_id])
        for e in cursor:
            item_data = {}
            item_data['c_id'] = 0
            item_data['category'] = "Usada mas de una categoría"
            item_data['e_id'] = e[0]
            item_data['entity'] = e[1]
            item_data['t_ammount'] = e[3]
            compiled_data.append(item_data)
    return compiled_data

