from django.db import models

class Document(models.Model):
    RENT_ROLL = "rent_roll"
    FLYER = "flyer"
    DOC_TYPES = [(RENT_ROLL, "Rent Roll"), (FLYER, "Flyer")]


    file = models.FileField(upload_to="uploads/")
    doc_type = models.CharField(max_length=20, choices=DOC_TYPES)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    pages = models.IntegerField(default=0)


class Section(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="sections")
    page = models.IntegerField()
    title = models.CharField(max_length=255, blank=True)
    text = models.TextField(blank=True)
    bbox_x0 = models.FloatField(default=0)
    bbox_y0 = models.FloatField(default=0)
    bbox_x1 = models.FloatField(default=0)
    bbox_y1 = models.FloatField(default=0)


class Property(models.Model):
    name = models.CharField(max_length=255, blank=True)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=128, blank=True)
    state = models.CharField(max_length=64, blank=True)
    zipcode = models.CharField(max_length=20, blank=True)
    year_built = models.CharField(max_length=32, blank=True)
    sqft = models.IntegerField(null=True, blank=True)
    unit_count = models.IntegerField(null=True, blank=True)
    cap_rate = models.FloatField(null=True, blank=True)
    source_document = models.ForeignKey(Document, on_delete=models.SET_NULL, null=True, related_name="properties")

class Unit(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="units")
    unit_number = models.CharField(max_length=64, blank=True)
    unit_type = models.CharField(max_length=64, blank=True)
    beds = models.CharField(max_length=16, blank=True)
    baths = models.CharField(max_length=16, blank=True)
    sqft = models.IntegerField(null=True, blank=True)
    rent = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=64, blank=True)
    lease_start = models.CharField(max_length=64, blank=True)
    lease_end = models.CharField(max_length=64, blank=True)


class FieldCitation(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="citations")
    model_name = models.CharField(max_length=64) # e.g., "Property" or "Unit"
    record_id = models.IntegerField() # pk of the record
    field_name = models.CharField(max_length=64)
    page = models.IntegerField()
    x0 = models.FloatField()
    y0 = models.FloatField()
    x1 = models.FloatField()
    y1 = models.FloatField()
    snippet = models.CharField(max_length=500, blank=True)