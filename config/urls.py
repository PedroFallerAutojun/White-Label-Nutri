from django.contrib import admin
from django.urls import path

from apps.fichas import views

urlpatterns = [
    path("admin/", admin.site.urls),
    # Nomes de rota preservados do sistema original
    path("", views.login_user, name="loginUser"),
    path("loginUser", views.login_user, name="loginUser"),
    path("logoutUser", views.logout_user, name="logoutUser"),
    path("listaFichas", views.lista_fichas, name="listaFichas"),
]
