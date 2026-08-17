"""Audita o acervo em busca de tabelas nutricionais desatualizadas.

Somente leitura: nada e alterado. Serve para dimensionar o problema e decidir
quais fichas recalcular (o recalculo e sempre uma acao explicita, ficha a ficha —
os valores gravados sao os rotulos ja emitidos, D-007).

    python manage.py auditar_tabelas
    python manage.py auditar_tabelas --limite 0 --detalhar
"""
from django.core.management.base import BaseCommand

from apps.fichas import servicos
from apps.fichas.models import Ficha, Tabela


class Command(BaseCommand):
    help = "Lista fichas cuja tabela nutricional nao corresponde ao calculo atual."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limite",
            type=int,
            default=30,
            help="Quantas fichas listar (0 = todas). Padrão: 30.",
        )
        parser.add_argument(
            "--detalhar",
            action="store_true",
            help="Mostra as diferenças de cada ficha.",
        )
        parser.add_argument(
            "--so-incoerentes",
            action="store_true",
            help="Apenas fichas cujo peso de porção do rótulo não bate com o do cálculo.",
        )

    def handle(self, *args, **opcoes):
        tabelas = {t.pk: t for t in Tabela.objects.all()}
        fichas = Ficha.objects.select_related("autor").order_by("id")

        incoerentes, defasadas, coerentes, sem_tabela = [], [], 0, 0
        for ficha in fichas.iterator():
            tabela = tabelas.get(ficha.pk)
            if tabela is None:
                sem_tabela += 1
                continue
            resultado = servicos.conferir_tabela(ficha, tabela)
            if resultado["porcao_incoerente"]:
                incoerentes.append((ficha, resultado))
            elif resultado["desatualizada"]:
                defasadas.append((ficha, resultado))
            else:
                coerentes += 1

        total = len(incoerentes) + len(defasadas) + coerentes
        self.stdout.write(f"Fichas analisadas: {total}")
        self.stdout.write(
            self.style.SUCCESS(f"  em dia:                        {coerentes}")
        )
        self.stdout.write(
            self.style.ERROR(
                f"  porcao INCOERENTE no rotulo:   {len(incoerentes)}"
                "  <- o rotulo declara um peso e a coluna usa outro"
            )
        )
        self.stdout.write(
            self.style.WARNING(f"  valores defasados:             {len(defasadas)}")
        )
        if sem_tabela:
            self.stdout.write(
                self.style.WARNING(
                    f"  sem tabela (abra e salve a ficha): {sem_tabela}"
                )
            )

        listar = incoerentes if opcoes["so_incoerentes"] else incoerentes + defasadas
        limite = opcoes["limite"]
        if limite:
            listar = listar[:limite]

        if listar:
            self.stdout.write("")
            self.stdout.write("Fichas a revisar:")
        for ficha, resultado in listar:
            marca = "INCOERENTE" if resultado["porcao_incoerente"] else "defasada  "
            self.stdout.write(
                f"  [{marca}] #{ficha.pk:<6} {ficha.nomeFicha[:44]:<44} "
                f"cliente: {ficha.cliente[:18]}"
            )
            if resultado["porcao_incoerente"]:
                self.stdout.write(
                    f"              rotulo declara {resultado['peso_declarado']:g} g, "
                    f"coluna calculada com {resultado['peso_usado']:.4g} g"
                )
            if opcoes["detalhar"]:
                for d in resultado["divergencias"][:8]:
                    self.stdout.write(
                        f"              {d['rotulo']}: {d['gravado']:g} -> "
                        f"{d['esperado']:g} {d['unidade']}"
                    )

        if incoerentes or defasadas:
            self.stdout.write("")
            self.stdout.write(
                "Para corrigir uma ficha, abra o rotulo dela no sistema e use "
                "'Recalcular esta tabela'."
            )
