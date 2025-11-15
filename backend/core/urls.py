from django.urls import path
from .views import UploadView, DocumentDetail, PropertiesList, UnitsList, SearchView, CitationsView, PropertyDetail

urlpatterns = [
    path("upload/", UploadView.as_view()),
    path("documents/<int:pk>/", DocumentDetail.as_view()),
    path("properties/", PropertiesList.as_view()),
    path("properties/<int:pk>/", PropertyDetail.as_view()), 
    path("units/", UnitsList.as_view()),
    path("search/", SearchView.as_view()),
    path("citations/<str:model_name>/<int:record_id>/", CitationsView.as_view()),
]
