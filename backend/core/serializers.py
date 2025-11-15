from rest_framework import serializers
from .models import Document, Section, Property, Unit, FieldCitation


class FieldCitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = FieldCitation
        fields = "__all__"


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = "__all__"


class PropertySerializer(serializers.ModelSerializer):
    units = UnitSerializer(many=True, read_only=True)
    class Meta:
        model = Property
        fields = "__all__"


class SectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = "__all__"


class DocumentSerializer(serializers.ModelSerializer):
    sections = SectionSerializer(many=True, read_only=True)
    class Meta:
        model = Document
        fields = ["id", "doc_type", "uploaded_at", "pages", "file", "sections"]