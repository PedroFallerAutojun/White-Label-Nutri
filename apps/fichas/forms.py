"""Formulários — portados do original com os mesmos campos, labels e validações."""
from django import forms
from django.db.models.functions import Lower

from apps.fichas.models import Ficha, Ficha_Ingrediente, Ingrediente, Membro, Nutriente, Tabela


def aplicar_classes_bootstrap(form):
    """Adiciona as classes do Bootstrap 5 aos widgets sem repetir em cada campo."""
    for campo in form.fields.values():
        widget = campo.widget
        if isinstance(widget, forms.CheckboxInput):
            widget.attrs.setdefault("class", "form-check-input")
        elif isinstance(widget, forms.Select):
            widget.attrs.setdefault("class", "form-select")
        else:
            widget.attrs.setdefault("class", "form-control")


class LoginForm(forms.Form):
    username = forms.CharField(label="Nome", required=True)
    password = forms.CharField(label="Senha", required=True, widget=forms.PasswordInput)


class FichaFiltroForm(forms.Form):
    f_nomeFicha = forms.CharField(label="Receita", required=False)
    f_cliente = forms.CharField(label="Cliente", required=False)
    f_autor = forms.CharField(label="Autor", required=False)


class FichaFormBase(forms.ModelForm):
    dataCriacao = forms.DateField(
        label="Data de criação",
        widget=forms.DateInput(format="%d/%m/%Y"),
        input_formats=["%d/%m/%Y", "%d-%m-%Y"],
        help_text="Formato: DD/MM/YYYY ou DD-MM-YYYY",
    )

    class Meta:
        model = Ficha
        fields = [
            "autor", "nomeFicha", "cliente", "pesoTotal", "pesoPorcao",
            "pesoAnvisa", "dataCriacao", "medCaseiraPorcao",
        ]
        labels = {
            "autor": "Autor",
            "nomeFicha": "Nome da receita",
            "cliente": "Cliente",
            "pesoTotal": "Peso total (g)",
            "pesoPorcao": "Peso da porção — Cliente (g)",
            "pesoAnvisa": "Peso da porção — Anvisa (g)",
            "medCaseiraPorcao": "Medida caseira da porção",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["autor"].queryset = Membro.objects.all().order_by(Lower("nome"))
        aplicar_classes_bootstrap(self)


class ReceitaForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        aplicar_classes_bootstrap(self)

    class Meta:
        model = Ficha_Ingrediente
        fields = ["pesoBruto", "pesoLiquido", "medidaCaseira", "nomeFantasia"]
        labels = {
            "pesoBruto": "Peso bruto (g)",
            "pesoLiquido": "Peso líquido (g)",
            "medidaCaseira": "Medida caseira",
            "nomeFantasia": "Nome fantasia",
        }


class NutrienteForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        aplicar_classes_bootstrap(self)

    class Meta:
        model = Nutriente
        fields = ["nomeNutri", "qtde", "qtde_Arred", "medida", "qtde_VD"]
        labels = {
            "nomeNutri": "Novo item",
            "qtde": "Quantidade real",
            "qtde_Arred": "Quantidade arredondada",
            "medida": "Medida",
            "qtde_VD": "Quantidade valor diário",
        }


class FormInformacoesComplementares(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        aplicar_classes_bootstrap(self)

    class Meta:
        model = Tabela
        fields = ["informacoesComplementares"]
        labels = {"informacoesComplementares": "Informações complementares"}
        widgets = {"informacoesComplementares": forms.Textarea(attrs={"rows": 3})}


class IngredienteForm(forms.ModelForm):
    dataCriacao = forms.DateField(
        label="Data de criação",
        widget=forms.DateInput(format="%d/%m/%Y"),
        input_formats=["%d/%m/%Y", "%d-%m-%Y"],
        help_text="Formato: DD/MM/YYYY ou DD-MM-YYYY",
    )
    composicao = forms.CharField(
        label="Composição",
        help_text="Formato: leite, açúcar e lactose",
        required=False,
    )

    class Meta:
        model = Ingrediente
        fields = [
            "autorIng", "nomeIng", "composicao", "origemDosDados", "qtdeDoIngrediente",
            "addManualmente", "numRef", "dataCriacao",
            "proteinas", "gordTotais", "acucaresTotais", "carboidratos", "fibras",
            "energiakcal", "energiaKJ", "calcio", "ferro", "magnesio", "fosforo",
            "potassio", "sodio", "zinco", "cobre", "manganes",
            "retinol", "RE", "vitaminaARAE", "vitaminaC", "tiamina",
            "riboflavina", "niancina", "piridoxina", "gordSat", "gordTrans",
            "gordPoli", "gordMono", "colesterol", "acucaresadd", "omega6", "omega3",
            "vitaminaD", "vitaminaE", "vitaminaK", "biotina", "acidoFolico",
            "acidoPantotenico", "vitaminaB12", "cloreto", "cromo", "fluor", "iodo",
            "molibdenio", "selenio", "colina",
        ]
        labels = {
            "autorIng": "Autor",
            "nomeIng": "Ingrediente",
            "origemDosDados": "Fonte / Marca",
            "qtdeDoIngrediente": "Quantidade do ingrediente (g)",
            "addManualmente": "Adicionado manualmente",
            "numRef": "Nº de referência",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["autorIng"].queryset = Membro.objects.all().order_by(Lower("nome"))
        aplicar_classes_bootstrap(self)


class IngredienteFiltroForm(forms.Form):
    f_nomeIng = forms.CharField(label="Nome", required=False)
    f_origemDosDados = forms.CharField(label="Origem", required=False)
    f_autorIng = forms.CharField(label="Autor", required=False)


class UploadForm(forms.Form):
    files = forms.FileField(label="Arquivo TXT (separado por TAB)")
