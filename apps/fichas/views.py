"""Views da E1 (fundação): autenticação e listagem de fichas.

Paridade com o original (ver docs/BUSINESS_RULES.md):
- BR-027: abrir a página de login derruba a sessão atual; falha de autenticação
  exibe "Não foi possível fazer login".
- BR-028: filtro de fichas por contains (Receita/Cliente/Autor) e ordenação
  por data de criação decrescente.
As demais telas chegam nas fases E3–E5.
"""
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import redirect, render

from apps.fichas.forms import FichaFiltroForm, LoginForm
from apps.fichas.models import Ficha


def login_user(request):
    logout(request)  # BR-027
    form = LoginForm(request.POST or None)
    if form.is_valid():
        user = authenticate(
            username=form.cleaned_data["username"],
            password=form.cleaned_data["password"],
        )
        if user is not None:
            login(request, user)
            return redirect("listaFichas")
        messages.error(request, "Não foi possível fazer login")
    return render(request, "login.html", {"form": form})


def logout_user(request):
    logout(request)
    return redirect("loginUser")


@login_required
def lista_fichas(request):
    fichas = Ficha.objects.select_related("autor").order_by("-dataCriacao")
    form_filtro = FichaFiltroForm(request.POST or None)
    if form_filtro.is_valid():
        fichas = fichas.filter(
            Q(nomeFicha__contains=form_filtro.cleaned_data["f_nomeFicha"])
            & Q(cliente__contains=form_filtro.cleaned_data["f_cliente"])
            & Q(autor__nome__contains=form_filtro.cleaned_data["f_autor"])
        )
    return render(
        request,
        "fichas_registradas.html",
        {"fichas": fichas, "formFiltro": form_filtro},
    )
