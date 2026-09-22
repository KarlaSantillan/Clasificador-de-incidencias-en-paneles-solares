from django.urls import path

from . import views

app_name = 'predictor'

urlpatterns = [
    path('', views.home, name='home'),
    path('analizar/', views.analyze, name='analyze'),
    path('modelo/', views.model_info, name='model_info'),
    path(
        'modelo/graficos/<slug:image_key>.png',
        views.model_result_image,
        name='model_result_image',
    ),
]
