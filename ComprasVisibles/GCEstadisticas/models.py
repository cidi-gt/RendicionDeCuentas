from django.db import models

class EntityType(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=75)
    
    def __str__(self):
        return 'EntityType '+self.name


class Entity(models.Model):
    entity_type = models.ForeignKey(EntityType, on_delete=models.PROTECT)
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=125)
    nit = models.CharField(max_length=12)
    department = models.CharField(max_length=50)
    city = models.CharField(max_length=125)

    def __str__(self):
        return 'Entity '+self.name


class PurchaseCategory(models.Model):
    name = models.CharField(max_length=125)
    
    def __str__(self):
        return 'PurchaseCategory '+self.name


class Requisition(models.Model):
    entity = models.ForeignKey(Entity, on_delete=models.PROTECT)
    nog = models.CharField(max_length=16, null=False, unique=True)
    state = models.CharField(max_length=40)
    modality = models.CharField(max_length=100)
    competition_type = models.CharField(max_length=70)
    purchasing_unit = models.CharField(max_length=125)
    categories = models.ManyToManyField(PurchaseCategory)
    description = models.TextField()
    publication_date = models.DateTimeField('fecha de publicación')
    presentation_date = models.DateTimeField('fecha de presentación de ofertas', null=True)
    close_date = models.DateTimeField('Fecha de cierre')
    reception_type = models.CharField(max_length=125)
    end_date = models.DateTimeField('Fecha de finalización')

    def __str__(self):
        return 'Requisition '+self.nog


class Supplier(models.Model):
    lprv = models.IntegerField('id proveedor en guatecompras', null=True)
    nit = models.CharField(max_length=20, null=True)
    name = models.CharField(max_length=125)

    def __str__(self):
        return 'Supplier '+self.nit+' - '+self.name


class Proposal(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    requisition = models.ForeignKey(Requisition, on_delete=models.PROTECT)
    ammount = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return 'Proposal '+self.supplier.__str__()+' - '+self.requisition.__str__()


class Awarded(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    requisition = models.ForeignKey(Requisition, on_delete=models.PROTECT)
    ammount = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return 'Awarded '+self.supplier.__str__()+' - '+self.requisition.__str__()


