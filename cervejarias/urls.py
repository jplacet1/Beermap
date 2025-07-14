from django.urls import path
from . import views


urlpatterns = [
    path('adicionar/',views.adicionar_cervejaria, name="adicionar_cervejaria"),
    path('cadastro/', views.cadastro, name="cadastro"),
    path('login/', views.logar, name="login"),
    path('', views.home, name="home"),
    path('salvarloc/', views.salvarloc, name='salvarloc'),
    path('editar_cervejaria/<slug:slug>/', views.editar_cervejaria, name='editar_cervejaria'),
    path('<slug:slug>/', views.cervejaria, name='cervejaria'),
]
