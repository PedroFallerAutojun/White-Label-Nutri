from django.db import models
import datetime

# Model dos membros da Nutri, usuários do sistema
from django.contrib.auth.models import User
class Membro(models.Model):
  # Relacionamentos:
  usuario = models.OneToOneField(User, on_delete=models.CASCADE, blank=True)  # Ligação com o model User do app Auth (autenticação) que vem por padrão nos setting.py

  # Atributos:
  nome = models.CharField(max_length=120)
  semestre = models.CharField(max_length=6)
  email = models.EmailField(max_length=254)

  # Visualização:
  def __str__(self):
    return self.nome

# Model dos ingredientes
class Ingrediente(models.Model):
  # Relacionamentos:
  autorIng = models.ForeignKey(Membro, on_delete=models.CASCADE)

  # Atributos:
  nomeIng = models.CharField(max_length=120)
  composicao = models.CharField(max_length=250, blank=True, null=True)
  origemDosDados = models.CharField(max_length=120)  # Ex: Tabela IBGE, Taco...
  addManualmente = models.BooleanField(default=True)
  numRef = models.IntegerField(null=True, blank=True, default=0)  # Número de referência na tabela de origem, caso venha por exemplo da tabela IBGE. É opcional
  dataCriacao = models.DateField(null=False, blank=False, default=datetime.date.today)
  qtdeDoIngrediente = models.FloatField(default=100) # Quantidade desse ingrediente que contêm a quantidade de nutrientes descritas. Quando adicionado ingrediente pelo upload ele vale Default que é 100g, já que esse é o padrão da TACO.

  # 1 Proteína
  proteinas = models.FloatField(null=True, blank=True, default=0)
  proteinas_100g = models.FloatField(null=True, blank=True, default=0)
  # 2 Gorduras totais
  gordTotais = models.FloatField(null=True, blank=True, default=0)
  gordTotais_100g = models.FloatField(null=True, blank=True, default=0)
  # 3 Carboidrato
  carboidratos = models.FloatField(null=True, blank=True, default=0)
  carboidratos_100g = models.FloatField(null=True, blank=True, default=0)
  # 4 Fibras
  fibras = models.FloatField(null=True, blank=True, default=0)
  fibras_100g = models.FloatField(null=True, blank=True, default=0)
  # 5 Energia kcal/KJ
  energiakcal = models.FloatField(null=True, blank=True, default=0)
  energiakcal_100g = models.FloatField(null=True, blank=True, default=0)
  energiaKJ = models.FloatField(null=True, blank=True, default=0)
  energiaKJ_100g = models.FloatField(null=True, blank=True, default=0)
  # 6 Cálcio
  calcio = models.FloatField(null=True, blank=True, default=0)
  calcio_100g = models.FloatField(null=True, blank=True, default=0)
  # 7 Ferro
  ferro = models.FloatField(null=True, blank=True, default=0)
  ferro_100g = models.FloatField(null=True, blank=True, default=0)
  # 8 Magnésio
  magnesio = models.FloatField(null=True, blank=True, default=0)
  magnesio_100g = models.FloatField(null=True, blank=True, default=0)
  # 9 Fósforo
  fosforo = models.FloatField(null=True, blank=True, default=0)
  fosforo_100g = models.FloatField(null=True, blank=True, default=0)
  # 10 Potássio
  potassio = models.FloatField(null=True, blank=True, default=0)
  potassio_100g = models.FloatField(null=True, blank=True, default=0)
  # 11 Sódio
  sodio = models.FloatField(null=True, blank=True, default=0)
  sodio_100g = models.FloatField(null=True, blank=True, default=0)
  # 12 Zinco
  zinco = models.FloatField(null=True, blank=True, default=0)
  zinco_100g = models.FloatField(null=True, blank=True, default=0)
  # 13 Cobre
  cobre = models.FloatField(null=True, blank=True, default=0)
  cobre_100g = models.FloatField(null=True, blank=True, default=0)
  # 14 Manganes
  manganes = models.FloatField(null=True, blank=True, default=0)
  manganes_100g = models.FloatField(null=True, blank=True, default=0)
  # 15 Retinol
  retinol = models.FloatField(null=True, blank=True, default=0)
  retinol_100g = models.FloatField(null=True, blank=True, default=0)
  # 16 RE (equivalente de retinol)
  RE = models.FloatField(null=True, blank=True, default=0)
  RE_100g = models.FloatField(null=True, blank=True, default=0)
  # 17 RAE (equivalente de atividade de retinol)
  vitaminaARAE = models.FloatField(null=True, blank=True, default=0)
  vitaminaARAE_100g = models.FloatField(null=True, blank=True, default=0)
  # 18 Vitamina C (ácido ascórbico)
  vitaminaC = models.FloatField(null=True, blank=True, default=0)
  vitaminaC_100g = models.FloatField(null=True, blank=True, default=0)
  # 19 Tiamina (B1)
  tiamina = models.FloatField(null=True, blank=True, default=0)    
  tiamina_100g = models.FloatField(null=True, blank=True, default=0)
  # 20 Riboflavina (B2)
  riboflavina = models.FloatField(null=True, blank=True, default=0)    
  riboflavina_100g = models.FloatField(null=True, blank=True, default=0)
  # 21 Niacina (B3)
  niancina = models.FloatField(null=True, blank=True, default=0)    
  niancina_100g = models.FloatField(null=True, blank=True, default=0)
  # 22 Vitamina Piridoxina (B6)
  piridoxina = models.FloatField(null=True, blank=True, default=0)
  piridoxina_100g = models.FloatField(null=True, blank=True, default=0)
  # 23 Gorduras saturadas
  gordSat = models.FloatField(null=True, blank=True, default=0)
  gordSat_100g = models.FloatField(null=True, blank=True, default=0)
  # 24 Gorduras trans
  gordTrans = models.FloatField(null=True, blank=True, default=0)
  gordTrans_100g = models.FloatField(null=True, blank=True, default=0)
  # 25 Gorduras polinsaturadas
  gordPoli = models.FloatField(null=True, blank=True, default=0)
  gordPoli_100g = models.FloatField(null=True, blank=True, default=0)
  # 26 Gorduras monoinsaturadas
  gordMono = models.FloatField(null=True, blank=True, default=0)
  gordMono_100g = models.FloatField(null=True, blank=True, default=0)
  # 27 Colesterol
  colesterol = models.FloatField(null=True, blank=True, default=0)
  colesterol_100g = models.FloatField(null=True, blank=True, default=0)
  # 28 Açucares adicionais 
  acucaresadd = models.FloatField(null=True, blank=True, default=0)
  acucaresadd_100g = models.FloatField(null=True, blank=True, default=0)
  # 29 Ômega6
  omega6 = models.FloatField(null=True, blank=True, default=0)
  omega6_100g = models.FloatField(null=True, blank=True, default=0)
  # 30 Ômega3
  omega3 = models.FloatField(null=True, blank=True, default=0)
  omega3_100g = models.FloatField(null=True, blank=True, default=0)
  # 31 Vitamina D
  vitaminaD = models.FloatField(null=True, blank=True, default=0)
  vitaminaD_100g = models.FloatField(null=True, blank=True, default=0)
  # 32 Vitamina E
  vitaminaE = models.FloatField(null=True, blank=True, default=0)
  vitaminaE_100g = models.FloatField(null=True, blank=True, default=0)
  # 33 Vitamina K
  vitaminaK = models.FloatField(null=True, blank=True, default=0)
  vitaminaK_100g = models.FloatField(null=True, blank=True, default=0)
  # 34 Biotina
  biotina = models.FloatField(null=True, blank=True, default=0)
  biotina_100g = models.FloatField(null=True, blank=True, default=0)
  # 35 Acido fólico
  acidoFolico = models.FloatField(null=True, blank=True, default=0)
  acidoFolico_100g = models.FloatField(null=True, blank=True, default=0)
  # 36 Acido pantotenico
  acidoPantotenico = models.FloatField(null=True, blank=True, default=0)
  acidoPantotenico_100g = models.FloatField(null=True, blank=True, default=0)
  # 37 Vitamina B12
  vitaminaB12 = models.FloatField(null=True, blank=True, default=0)
  vitaminaB12_100g = models.FloatField(null=True, blank=True, default=0)
  # 38 Cloreto
  cloreto = models.FloatField(null=True, blank=True, default=0)
  cloreto_100g = models.FloatField(null=True, blank=True, default=0)
  # 39 Cromo
  cromo = models.FloatField(null=True, blank=True, default=0)
  cromo_100g = models.FloatField(null=True, blank=True, default=0)
  # 40 Fluor
  fluor = models.FloatField(null=True, blank=True, default=0)
  fluor_100g = models.FloatField(null=True, blank=True, default=0)
  # 41 Iodo
  iodo = models.FloatField(null=True, blank=True, default=0)
  iodo_100g = models.FloatField(null=True, blank=True, default=0)
  # 42 Molibdenio
  molibdenio = models.FloatField(null=True, blank=True, default=0)
  molibdenio_100g = models.FloatField(null=True, blank=True, default=0)
  # 43 Selênio
  selenio = models.FloatField(null=True, blank=True, default=0)
  selenio_100g = models.FloatField(null=True, blank=True, default=0)
  # 44 Colina
  colina = models.FloatField(null=True, blank=True, default=0)
  colina_100g = models.FloatField(null=True, blank=True, default=0)
  # 45 Gorduras totais
  acucaresTotais = models.FloatField(null=True, blank=True, default=0)
  acucaresTotais_100g = models.FloatField(null=True, blank=True, default=0)


  # Visualização:
  def __str__(self):
    return self.nomeIng

# Model das fichas
class Ficha(models.Model):
  # Relacionamentos:
  autor = models.ForeignKey(Membro, on_delete=models.CASCADE)

  # Atributos:
  cliente = models.CharField(max_length=120)
  nomeFicha = models.CharField(max_length=500)
  dataCriacao = models.DateField(null=False, blank=False, default=datetime.date.today)
  finalizada = models.BooleanField(default=False)
  
  # Atributos dependentes da receita:
  pesoLiquidoPreparacao = models.FloatField(null=True, blank=True, default=0)
  pesoTotal = models.FloatField(null=True, blank=True, default=0)
  pesoPorcao = models.FloatField(null=True, blank=True, default=0)
  pesoAnvisa = models.FloatField(null=True, blank=True, default=0)
  numPorcoes = models.IntegerField(null=True, blank=True, default=0)  # Deve arredondar sempre pra baixo. Já que é um Integer ele só pega a parte inteira automaticamente
  medCaseiraPorcao = models.CharField(max_length=120, blank=True, default="medida caseira")

  # Visualização:
  def __str__(self):
    return "Ficha: " + self.nomeFicha

# Model da tabela nutricional com os valores intermediarios e o final arredondado, teriamos o valor arredondado salvo para não precisar calcular o arredondamento toda vez que for usar esse informação no front
class Tabela(models.Model):
  # Relacionamentos:
  origem = models.OneToOneField(Ficha, on_delete=models.CASCADE) #Ficha cujo essa tabela pertence

  # Atributos:
  informacoesComplementares = models.TextField(blank=True)

  # HELP:
  # nutrienteX: Soma de nutrienteX dos ingredientes. Atualiza quando muda a qtde desse nutriente de algum ingrediente da receita muda e alguma view aciona attTabela()
  # nutrienteX_100g: (nutrienteX*100) / pesoTotal. Atualiza quando a variavel de cima ou o pesoTotal muda
  # nutrienteX_Porcao: (nutrienteX_100g*pesoPorcao) / 100. Atualiza quando a variavel de cima ou o pesoPorcao muda
  # nutrienteX_Arred: Atualiza quando a variavel de cima muda
  # nutrienteX_VD: Atualiza quando a variavel de cima muda
  # nutrienteX_Mostrar: Flag que indica se vai para versão final ou não
  # nutrienteX_unidadeMd: Unidade de medida que irá ser mostrada na tabela final

  # 1 Proteína
  proteinas = models.FloatField(null=True, blank=True, default=0)
  proteinas_100g = models.FloatField(null=True, blank=True, default=0)
  proteinas_Porcao = models.FloatField(null=True, blank=True, default=0)
  proteinas_Arred = models.FloatField(null=True, blank=True, default=0)
  proteinas_VD = models.IntegerField(null=True, blank=True, default=0)
  proteinas_Mostrar = models.BooleanField(default=True)
  proteinas_unidadeMd = models.CharField(max_length=5, default="g")

  # 2 Gorduras totais
  gordTotais = models.FloatField(null=True, blank=True, default=0)
  gordTotais_100g = models.FloatField(null=True, blank=True, default=0)
  gordTotais_Porcao = models.FloatField(null=True, blank=True, default=0)
  gordTotais_Arred = models.FloatField(null=True, blank=True, default=0)
  gordTotais_VD = models.IntegerField(null=True, blank=True, default=0)
  gordTotais_Mostrar = models.BooleanField(default=True)
  gordTotais_unidadeMd = models.CharField(max_length=5, default="g")

  # 3 Carboidrato
  carboidratos = models.FloatField(null=True, blank=True, default=0)
  carboidratos_100g = models.FloatField(null=True, blank=True, default=0)
  carboidratos_Porcao = models.FloatField(null=True, blank=True, default=0)
  carboidratos_Arred = models.FloatField(null=True, blank=True, default=0)
  carboidratos_VD = models.IntegerField(null=True, blank=True, default=0)
  carboidratos_Mostrar = models.BooleanField(default=True)
  carboidratos_unidadeMd = models.CharField(max_length=5, default="g")

  # 4 Fibras
  fibras = models.FloatField(null=True, blank=True, default=0)
  fibras_100g = models.FloatField(null=True, blank=True, default=0)
  fibras_Porcao = models.FloatField(null=True, blank=True, default=0)
  fibras_Arred = models.FloatField(null=True, blank=True, default=0)
  fibras_VD = models.IntegerField(null=True, blank=True, default=0)
  fibras_Mostrar = models.BooleanField(default=True)
  fibras_unidadeMd = models.CharField(max_length=5, default="g")

  # 5 Energia kcal/KJ
  energiakcal = models.FloatField(null=True, blank=True, default=0)
  energiakcal_100g = models.FloatField(null=True, blank=True, default=0)
  energiakcal_Porcao = models.FloatField(null=True, blank=True, default=0)
  energiakcal_Arred = models.FloatField(null=True, blank=True, default=0)
  energiakcal_VD = models.IntegerField(null=True, blank=True, default=0)
  energiakcal_Mostrar = models.BooleanField(default=True)
  energiakcal_unidadeMd = models.CharField(max_length=5, default="kcal")

  energiaKJ = models.FloatField(null=True, blank=True, default=0)
  energiaKJ_100g = models.FloatField(null=True, blank=True, default=0)
  energiaKJ_Porcao = models.FloatField(null=True, blank=True, default=0)
  energiaKJ_Arred = models.FloatField(null=True, blank=True, default=0)
  energiaKJ_VD = models.IntegerField(null=True, blank=True, default=0)
  energiaKJ_Mostrar = models.BooleanField(default=True)
  energiaKJ_unidadeMd = models.CharField(max_length=5, default="kJ")

  # 6 Cálcio
  calcio = models.FloatField(null=True, blank=True, default=0)
  calcio_100g = models.FloatField(null=True, blank=True, default=0)
  calcio_Porcao = models.FloatField(null=True, blank=True, default=0)
  calcio_Arred = models.FloatField(null=True, blank=True, default=0)
  calcio_VD = models.IntegerField(null=True, blank=True, default=0)
  calcio_Mostrar = models.BooleanField(default=False)
  calcio_unidadeMd = models.CharField(max_length=5, default="mg")

  # 7 Ferro
  ferro = models.FloatField(null=True, blank=True, default=0)
  ferro_100g = models.FloatField(null=True, blank=True, default=0)
  ferro_Porcao = models.FloatField(null=True, blank=True, default=0)
  ferro_Arred = models.FloatField(null=True, blank=True, default=0)
  ferro_VD = models.IntegerField(null=True, blank=True, default=0)
  ferro_Mostrar = models.BooleanField(default=False)
  ferro_unidadeMd = models.CharField(max_length=5, default="mg")

  # 8 Magnésio
  magnesio = models.FloatField(null=True, blank=True, default=0)
  magnesio_100g = models.FloatField(null=True, blank=True, default=0)
  magnesio_Porcao = models.FloatField(null=True, blank=True, default=0)
  magnesio_Arred = models.FloatField(null=True, blank=True, default=0)
  magnesio_VD = models.IntegerField(null=True, blank=True, default=0)
  magnesio_Mostrar = models.BooleanField(default=False)
  magnesio_unidadeMd = models.CharField(max_length=5, default="mg")

  # 9 Fósforo
  fosforo = models.FloatField(null=True, blank=True, default=0)
  fosforo_100g = models.FloatField(null=True, blank=True, default=0)
  fosforo_Porcao = models.FloatField(null=True, blank=True, default=0)
  fosforo_Arred = models.FloatField(null=True, blank=True, default=0)
  fosforo_VD = models.IntegerField(null=True, blank=True, default=0)
  fosforo_Mostrar = models.BooleanField(default=False)
  fosforo_unidadeMd = models.CharField(max_length=5, default="mg")

  # 10 Potássio
  potassio = models.FloatField(null=True, blank=True, default=0)
  potassio_100g = models.FloatField(null=True, blank=True, default=0)
  potassio_Porcao = models.FloatField(null=True, blank=True, default=0)
  potassio_Arred = models.FloatField(null=True, blank=True, default=0)
  potassio_VD = models.IntegerField(null=True, blank=True, default=0)
  potassio_Mostrar = models.BooleanField(default=False)
  potassio_unidadeMd = models.CharField(max_length=5, default="mg")

  # 11 Sódio
  sodio = models.FloatField(null=True, blank=True, default=0)
  sodio_100g = models.FloatField(null=True, blank=True, default=0)
  sodio_Porcao = models.FloatField(null=True, blank=True, default=0)
  sodio_Arred = models.FloatField(null=True, blank=True, default=0)
  sodio_VD = models.IntegerField(null=True, blank=True, default=0)
  sodio_Mostrar = models.BooleanField(default=True)
  sodio_unidadeMd = models.CharField(max_length=5, default="mg")

  # 12 Zinco
  zinco = models.FloatField(null=True, blank=True, default=0)
  zinco_100g = models.FloatField(null=True, blank=True, default=0)
  zinco_Porcao = models.FloatField(null=True, blank=True, default=0)
  zinco_Arred = models.FloatField(null=True, blank=True, default=0)
  zinco_VD = models.IntegerField(null=True, blank=True, default=0)
  zinco_Mostrar = models.BooleanField(default=False)
  zinco_unidadeMd = models.CharField(max_length=5, default="mg")

  # 13 Cobre
  cobre = models.FloatField(null=True, blank=True, default=0)
  cobre_100g = models.FloatField(null=True, blank=True, default=0)
  cobre_Porcao = models.FloatField(null=True, blank=True, default=0)
  cobre_Arred = models.FloatField(null=True, blank=True, default=0)
  cobre_VD = models.IntegerField(null=True, blank=True, default=0)
  cobre_Mostrar = models.BooleanField(default=False)
  cobre_unidadeMd = models.CharField(max_length=5, default="mg")

  # 14 Manganes
  manganes = models.FloatField(null=True, blank=True, default=0)
  manganes_100g = models.FloatField(null=True, blank=True, default=0)
  manganes_Porcao = models.FloatField(null=True, blank=True, default=0)
  manganes_Arred = models.FloatField(null=True, blank=True, default=0)
  manganes_VD = models.IntegerField(null=True, blank=True, default=0)
  manganes_Mostrar = models.BooleanField(default=False)
  manganes_unidadeMd = models.CharField(max_length=5, default="mg")

  # 15 Retinol
  retinol = models.FloatField(null=True, blank=True, default=0)
  retinol_100g = models.FloatField(null=True, blank=True, default=0)
  retinol_Porcao = models.FloatField(null=True, blank=True, default=0)
  retinol_Arred = models.FloatField(null=True, blank=True, default=0)
  retinol_VD = models.IntegerField(null=True, blank=True, default=0)
  retinol_Mostrar = models.BooleanField(default=False)
  retinol_unidadeMd = models.CharField(max_length=5, default="mg")

  # 16 RE (equivalente de retinol)
  RE = models.FloatField(null=True, blank=True, default=0)
  RE_100g = models.FloatField(null=True, blank=True, default=0)
  RE_Porcao = models.FloatField(null=True, blank=True, default=0)
  RE_Arred = models.FloatField(null=True, blank=True, default=0)
  RE_VD = models.IntegerField(null=True, blank=True, default=0)
  RE_Mostrar = models.BooleanField(default=False)
  RE_unidadeMd = models.CharField(max_length=5, default="mg")

  # 17 RAE (equivalente de atividade de retinol)
  vitaminaARAE = models.FloatField(null=True, blank=True, default=0)
  vitaminaARAE_100g = models.FloatField(null=True, blank=True, default=0)
  vitaminaARAE_Porcao = models.FloatField(null=True, blank=True, default=0)
  vitaminaARAE_Arred = models.FloatField(null=True, blank=True, default=0)
  vitaminaARAE_VD = models.IntegerField(null=True, blank=True, default=0)
  vitaminaARAE_Mostrar = models.BooleanField(default=False)
  vitaminaARAE_unidadeMd = models.CharField(max_length=5, default="mg")

  # 18 Vitamina C (ácido ascórbico)
  vitaminaC = models.FloatField(null=True, blank=True, default=0)
  vitaminaC_100g = models.FloatField(null=True, blank=True, default=0)
  vitaminaC_Porcao = models.FloatField(null=True, blank=True, default=0)
  vitaminaC_Arred = models.FloatField(null=True, blank=True, default=0)
  vitaminaC_VD = models.IntegerField(null=True, blank=True, default=0)
  vitaminaC_Mostrar = models.BooleanField(default=False)
  vitaminaC_unidadeMd = models.CharField(max_length=5, default="mg")

  # 19 Tiamina (B1)
  tiamina = models.FloatField(null=True, blank=True, default=0)
  tiamina_100g = models.FloatField(null=True, blank=True, default=0)
  tiamina_Porcao = models.FloatField(null=True, blank=True, default=0)
  tiamina_Arred = models.FloatField(null=True, blank=True, default=0)
  tiamina_VD = models.IntegerField(null=True, blank=True, default=0)
  tiamina_Mostrar = models.BooleanField(default=False)
  tiamina_unidadeMd = models.CharField(max_length=5, default="mg")
  
  # 20 Riboflavina (B2)
  riboflavina = models.FloatField(null=True, blank=True, default=0)
  riboflavina_100g = models.FloatField(null=True, blank=True, default=0)
  riboflavina_Porcao = models.FloatField(null=True, blank=True, default=0)
  riboflavina_Arred = models.FloatField(null=True, blank=True, default=0)
  riboflavina_VD = models.IntegerField(null=True, blank=True, default=0)
  riboflavina_Mostrar = models.BooleanField(default=False)
  riboflavina_unidadeMd = models.CharField(max_length=5, default="mg")
  
  # 21 Niacina (B3)
  niancina = models.FloatField(null=True, blank=True, default=0)
  niancina_100g = models.FloatField(null=True, blank=True, default=0)
  niancina_Porcao = models.FloatField(null=True, blank=True, default=0)
  niancina_Arred = models.FloatField(null=True, blank=True, default=0)
  niancina_VD = models.IntegerField(null=True, blank=True, default=0)
  niancina_Mostrar = models.BooleanField(default=False)
  niancina_unidadeMd = models.CharField(max_length=5, default="mg")
  
  # 22 Vitamina Piridoxina (B6)
  piridoxina = models.FloatField(null=True, blank=True, default=0)
  piridoxina_100g = models.FloatField(null=True, blank=True, default=0)
  piridoxina_Porcao = models.FloatField(null=True, blank=True, default=0)
  piridoxina_Arred = models.FloatField(null=True, blank=True, default=0)
  piridoxina_VD = models.IntegerField(null=True, blank=True, default=0)
  piridoxina_Mostrar = models.BooleanField(default=False)
  piridoxina_unidadeMd = models.CharField(max_length=5, default="mg")

  # 23 Gorduras saturadas
  gordSat = models.FloatField(null=True, blank=True, default=0)
  gordSat_100g = models.FloatField(null=True, blank=True, default=0)
  gordSat_Porcao = models.FloatField(null=True, blank=True, default=0)
  gordSat_Arred = models.FloatField(null=True, blank=True, default=0)
  gordSat_VD = models.IntegerField(null=True, blank=True, default=0)
  gordSat_Mostrar = models.BooleanField(default=True)
  gordSat_unidadeMd = models.CharField(max_length=5, default="g")

  # 24 Gorduras trans (não tem na planilha, mas é a soma do 18:1t + 18:2t)
  gordTrans = models.FloatField(null=True, blank=True, default=0)
  gordTrans_100g = models.FloatField(null=True, blank=True, default=0)
  gordTrans_Porcao = models.FloatField(null=True, blank=True, default=0)
  gordTrans_Arred = models.FloatField(null=True, blank=True, default=0)
  gordTrans_VD = models.IntegerField(null=True, blank=True, default=0)
  gordTrans_Mostrar = models.BooleanField(default=True)
  gordTrans_unidadeMd = models.CharField(max_length=5, default="g")

  # 25 Gorduras polinsaturadas
  gordPoli = models.FloatField(null=True, blank=True, default=0)
  gordPoli_100g = models.FloatField(null=True, blank=True, default=0)
  gordPoli_Porcao = models.FloatField(null=True, blank=True, default=0)
  gordPoli_Arred = models.FloatField(null=True, blank=True, default=0)
  gordPoli_VD = models.IntegerField(null=True, blank=True, default=0)
  gordPoli_Mostrar = models.BooleanField(default=False)
  gordPoli_unidadeMd = models.CharField(max_length=5, default="g")
  
  # 26 Gorduras monoinsaturadas
  gordMono = models.FloatField(null=True, blank=True, default=0)
  gordMono_100g = models.FloatField(null=True, blank=True, default=0)
  gordMono_Porcao = models.FloatField(null=True, blank=True, default=0)
  gordMono_Arred = models.FloatField(null=True, blank=True, default=0)
  gordMono_VD = models.IntegerField(null=True, blank=True, default=0)
  gordMono_Mostrar = models.BooleanField(default=False)
  gordMono_unidadeMd = models.CharField(max_length=5, default="g")

  # 27 Colesterol
  colesterol = models.FloatField(null=True, blank=True, default=0)
  colesterol_100g = models.FloatField(null=True, blank=True, default=0)
  colesterol_Porcao = models.FloatField(null=True, blank=True, default=0)
  colesterol_Arred = models.FloatField(null=True, blank=True, default=0)
  colesterol_VD = models.IntegerField(null=True, blank=True, default=0)
  colesterol_Mostrar = models.BooleanField(default=False)
  colesterol_unidadeMd = models.CharField(max_length=5, default="mg")

  # 28 Açucares adicionados
  acucaresadd = models.FloatField(null=True, blank=True, default=0)
  acucaresadd_100g = models.FloatField(null=True, blank=True, default=0)
  acucaresadd_Porcao = models.FloatField(null=True, blank=True, default=0)
  acucaresadd_Arred = models.FloatField(null=True, blank=True, default=0)
  acucaresadd_VD = models.IntegerField(null=True, blank=True, default=0)
  acucaresadd_Mostrar = models.BooleanField(default=True)
  acucaresadd_unidadeMd = models.CharField(max_length=5, default="g")

  # 29 Ômega 6
  omega6 = models.FloatField(null=True, blank=True, default=0)
  omega6_100g = models.FloatField(null=True, blank=True, default=0)
  omega6_Porcao = models.FloatField(null=True, blank=True, default=0)
  omega6_Arred = models.FloatField(null=True, blank=True, default=0)
  omega6_VD = models.IntegerField(null=True, blank=True, default=0)
  omega6_Mostrar = models.BooleanField(default=False)
  omega6_unidadeMd = models.CharField(max_length=5, default="g")

  # 30 Ômega 3
  omega3 = models.FloatField(null=True, blank=True, default=0)
  omega3_100g = models.FloatField(null=True, blank=True, default=0)
  omega3_Porcao = models.FloatField(null=True, blank=True, default=0)
  omega3_Arred = models.FloatField(null=True, blank=True, default=0)
  omega3_VD = models.IntegerField(null=True, blank=True, default=0)
  omega3_Mostrar = models.BooleanField(default=False)
  omega3_unidadeMd = models.CharField(max_length=5, default="mg")

  # 31 Vitamina D
  vitaminaD = models.FloatField(null=True, blank=True, default=0)
  vitaminaD_100g = models.FloatField(null=True, blank=True, default=0)
  vitaminaD_Porcao = models.FloatField(null=True, blank=True, default=0)
  vitaminaD_Arred = models.FloatField(null=True, blank=True, default=0)
  vitaminaD_VD = models.IntegerField(null=True, blank=True, default=0)
  vitaminaD_Mostrar = models.BooleanField(default=False)
  vitaminaD_unidadeMd = models.CharField(max_length=5, default="μg")

  # 32 Vitamina E
  vitaminaE = models.FloatField(null=True, blank=True, default=0)
  vitaminaE_100g = models.FloatField(null=True, blank=True, default=0)
  vitaminaE_Porcao = models.FloatField(null=True, blank=True, default=0)
  vitaminaE_Arred = models.FloatField(null=True, blank=True, default=0)
  vitaminaE_VD = models.IntegerField(null=True, blank=True, default=0)
  vitaminaE_Mostrar = models.BooleanField(default=False)
  vitaminaE_unidadeMd = models.CharField(max_length=5, default="mg")

  # 33 Vitamina K
  vitaminaK = models.FloatField(null=True, blank=True, default=0)
  vitaminaK_100g = models.FloatField(null=True, blank=True, default=0)
  vitaminaK_Porcao = models.FloatField(null=True, blank=True, default=0)
  vitaminaK_Arred = models.FloatField(null=True, blank=True, default=0)
  vitaminaK_VD = models.IntegerField(null=True, blank=True, default=0)
  vitaminaK_Mostrar = models.BooleanField(default=False)
  vitaminaK_unidadeMd = models.CharField(max_length=5, default="μg")

  # 34 Biotina
  biotina = models.FloatField(null=True, blank=True, default=0)
  biotina_100g = models.FloatField(null=True, blank=True, default=0)
  biotina_Porcao = models.FloatField(null=True, blank=True, default=0)
  biotina_Arred = models.FloatField(null=True, blank=True, default=0)
  biotina_VD = models.IntegerField(null=True, blank=True, default=0)
  biotina_Mostrar = models.BooleanField(default=False)
  biotina_unidadeMd = models.CharField(max_length=5, default="μg")

  # 35 Acido folico
  acidoFolico = models.FloatField(null=True, blank=True, default=0)
  acidoFolico_100g = models.FloatField(null=True, blank=True, default=0)
  acidoFolico_Porcao = models.FloatField(null=True, blank=True, default=0)
  acidoFolico_Arred = models.FloatField(null=True, blank=True, default=0)
  acidoFolico_VD = models.IntegerField(null=True, blank=True, default=0)
  acidoFolico_Mostrar = models.BooleanField(default=False)
  acidoFolico_unidadeMd = models.CharField(max_length=5, default="μg")

  # 36 Acido pantotenico
  acidoPantotenico = models.FloatField(null=True, blank=True, default=0)
  acidoPantotenico_100g = models.FloatField(null=True, blank=True, default=0)
  acidoPantotenico_Porcao = models.FloatField(null=True, blank=True, default=0)
  acidoPantotenico_Arred = models.FloatField(null=True, blank=True, default=0)
  acidoPantotenico_VD = models.IntegerField(null=True, blank=True, default=0)
  acidoPantotenico_Mostrar = models.BooleanField(default=False)
  acidoPantotenico_unidadeMd = models.CharField(max_length=5, default="mg")

  # 37 Vitamina B12
  vitaminaB12 = models.FloatField(null=True, blank=True, default=0)
  vitaminaB12_100g = models.FloatField(null=True, blank=True, default=0)
  vitaminaB12_Porcao = models.FloatField(null=True, blank=True, default=0)
  vitaminaB12_Arred = models.FloatField(null=True, blank=True, default=0)
  vitaminaB12_VD = models.IntegerField(null=True, blank=True, default=0)
  vitaminaB12_Mostrar = models.BooleanField(default=False)
  vitaminaB12_unidadeMd = models.CharField(max_length=5, default="μg")

  # 38 Cloreto
  cloreto = models.FloatField(null=True, blank=True, default=0)
  cloreto_100g = models.FloatField(null=True, blank=True, default=0)
  cloreto_Porcao = models.FloatField(null=True, blank=True, default=0)
  cloreto_Arred = models.FloatField(null=True, blank=True, default=0)
  cloreto_VD = models.IntegerField(null=True, blank=True, default=0)
  cloreto_Mostrar = models.BooleanField(default=False)
  cloreto_unidadeMd = models.CharField(max_length=5, default="mg")

  # 39 Cromo
  cromo = models.FloatField(null=True, blank=True, default=0)
  cromo_100g = models.FloatField(null=True, blank=True, default=0)
  cromo_Porcao = models.FloatField(null=True, blank=True, default=0)
  cromo_Arred = models.FloatField(null=True, blank=True, default=0)
  cromo_VD = models.IntegerField(null=True, blank=True, default=0)
  cromo_Mostrar = models.BooleanField(default=False)
  cromo_unidadeMd = models.CharField(max_length=5, default="μg")

  # 40 Iodo
  iodo = models.FloatField(null=True, blank=True, default=0)
  iodo_100g = models.FloatField(null=True, blank=True, default=0)
  iodo_Porcao = models.FloatField(null=True, blank=True, default=0)
  iodo_Arred = models.FloatField(null=True, blank=True, default=0)
  iodo_VD = models.IntegerField(null=True, blank=True, default=0)
  iodo_Mostrar = models.BooleanField(default=False)
  iodo_unidadeMd = models.CharField(max_length=5, default="μg")

  # 41 Molibdenio
  molibdenio = models.FloatField(null=True, blank=True, default=0)
  molibdenio_100g = models.FloatField(null=True, blank=True, default=0)
  molibdenio_Porcao = models.FloatField(null=True, blank=True, default=0)
  molibdenio_Arred = models.FloatField(null=True, blank=True, default=0)
  molibdenio_VD = models.IntegerField(null=True, blank=True, default=0)
  molibdenio_Mostrar = models.BooleanField(default=False)
  molibdenio_unidadeMd = models.CharField(max_length=5, default="μg")

  # 42 Selenio
  selenio = models.FloatField(null=True, blank=True, default=0)
  selenio_100g = models.FloatField(null=True, blank=True, default=0)
  selenio_Porcao = models.FloatField(null=True, blank=True, default=0)
  selenio_Arred = models.FloatField(null=True, blank=True, default=0)
  selenio_VD = models.IntegerField(null=True, blank=True, default=0)
  selenio_Mostrar = models.BooleanField(default=False)
  selenio_unidadeMd = models.CharField(max_length=5, default="μg")

  # 43 Colina
  colina = models.FloatField(null=True, blank=True, default=0)
  colina_100g = models.FloatField(null=True, blank=True, default=0)
  colina_Porcao = models.FloatField(null=True, blank=True, default=0)
  colina_Arred = models.FloatField(null=True, blank=True, default=0)
  colina_VD = models.IntegerField(null=True, blank=True, default=0)
  colina_Mostrar = models.BooleanField(default=False)
  colina_unidadeMd = models.CharField(max_length=5, default="mg")


  # 44 Fluor
  fluor = models.FloatField(null=True, blank=True, default=0)
  fluor_100g = models.FloatField(null=True, blank=True, default=0)
  fluor_Porcao = models.FloatField(null=True, blank=True, default=0)
  fluor_Arred = models.FloatField(null=True, blank=True, default=0)
  fluor_VD = models.IntegerField(null=True, blank=True, default=0)
  fluor_Mostrar = models.BooleanField(default=False)
  fluor_unidadeMd = models.CharField(max_length=5, default="mg")

  # 45 Açucares totais
  acucaresTotais = models.FloatField(null=True, blank=True, default=0)
  acucaresTotais_100g = models.FloatField(null=True, blank=True, default=0)
  acucaresTotais_Porcao = models.FloatField(null=True, blank=True, default=0)
  acucaresTotais_Arred = models.FloatField(null=True, blank=True, default=0)
  acucaresTotais_VD = models.IntegerField(null=True, blank=True, default=0)
  acucaresTotais_Mostrar = models.BooleanField(default=True)
  acucaresTotais_unidadeMd = models.CharField(max_length=5, default="g")

  # Visualização:
  def __str__(self):
    return "Tabela nutricional da ficha: " + self.origem.nomeFicha
  
  # Nutrientes altos (implementação da lupa)
  def nutrientes_altos(self, limite_vd=20):
        # Retorna uma lista dos nutrientes em que o produto é alto (%VD >= limite_vd)
        nutrientes = []
        if (self.acucaresadd_100g or 0) >= 15:
            nutrientes.append('acucares')
        if (self.gordSat_100g or 0) >= 6:
            nutrientes.append('gorduras_saturadas')
        if (self.sodio_100g or 0) >= 600:
            nutrientes.append('sodio')
        return nutrientes

# Model dos nutrientes que podem ser adicionados na tabela nutricional que não temos dados sobre a quantidade dele nos ingredientes
class Nutriente(models.Model):
  # Relacionamentos:
  origemTabela = models.ForeignKey(Tabela, on_delete=models.CASCADE)

  # Atributos:
  nomeNutri = models.CharField(max_length=120)
  qtde = models.FloatField()
  qtde_Arred = models.FloatField()
  qtde_VD = models.IntegerField(null=True, blank=True, default=0)
  medida = models.CharField(max_length=20)

  # Visualização:
  def __str__(self):
    return "Nutriente adicional na Tabela da ficha: " + self.origemTabela.origem.nomeFicha

# Model da receita. É uma tabela intermediaria que faz a relação N pra N entre as tabelas Ingrediente e Ficha
class Ficha_Ingrediente(models.Model):
  # Relacionamentos:
  ficha = models.ForeignKey(Ficha, on_delete=models.CASCADE)
  ingrediente = models.ForeignKey(Ingrediente, on_delete=models.CASCADE)

  # Atributos:
  pesoBruto = models.FloatField(null=True, blank=True, default=0)
  pesoLiquido = models.FloatField(null=True, blank=True, default=0)
  medidaCaseira = models.CharField(max_length=30, blank=True)  # Ex: 3 xíc, 1 sachê
  nomeFantasia = models.CharField(max_length=50)

  # Visualização:
  def __str__(self):
    return str(self.pesoLiquido) + " gramas de " + self.ingrediente.nomeIng + " em " + self.ficha.nomeFicha

# Model para armazenar o valor da chave que permite a criação de novos membros no sistema
class Chave(models.Model):
  key = models.CharField(max_length=20)

  def __str__(self):
    return  self.key
