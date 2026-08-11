from django import forms


class LoginForm(forms.Form):
    username = forms.CharField(label="Nome", required=True)
    password = forms.CharField(label="Senha", required=True, widget=forms.PasswordInput)


class FichaFiltroForm(forms.Form):
    f_nomeFicha = forms.CharField(label="Receita", required=False)
    f_cliente = forms.CharField(label="Cliente", required=False)
    f_autor = forms.CharField(label="Autor", required=False)
