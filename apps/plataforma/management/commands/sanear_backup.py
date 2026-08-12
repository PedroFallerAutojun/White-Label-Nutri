"""Saneamento do banco restaurado do backup legado (docs/MIGRATION.md, S1–S7).

Idempotente: rodar de novo não muda nada. Use --dry-run para apenas relatar.
Nunca recalcula tabelas existentes (D-007): os valores gravados são os rótulos
já emitidos aos clientes.
"""
from django.conf import settings
from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from apps.fichas.models import Chave, Ficha, Tabela
from apps.plataforma.models import ConfiguracaoInstancia


class Command(BaseCommand):
    help = "Sanea o banco restaurado do backup legado (idempotente)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Apenas relata o que seria feito, sem gravar nada.",
        )
        parser.add_argument(
            "--nome-instancia",
            default="Nutri Jr",
            help="Nome de exibição da instância (default: Nutri Jr).",
        )
        parser.add_argument(
            "--ano-corte",
            type=int,
            default=2024,
            help="Ano de corte dos ingredientes (0 desativa; default: 2024).",
        )
        parser.add_argument(
            "--admin",
            default="admin",
            help="Usuário que recebe o papel de administrador (default: admin).",
        )

    def handle(self, *args, **opcoes):
        simular = opcoes["dry_run"]
        if simular:
            self.stdout.write(self.style.WARNING("MODO SIMULAÇÃO — nada será gravado.\n"))

        with transaction.atomic():
            self._s1_tabelas_faltantes(simular)
            self._s2_grupo_administradores(opcoes["admin"], simular)
            self._s3_datas_suspeitas()
            self._s4_fichas_sem_pesos()
            self._s6_chave(simular)
            self._s7_configuracao(opcoes["nome_instancia"], opcoes["ano_corte"], simular)
            if simular:
                transaction.set_rollback(True)

        self.stdout.write(self.style.SUCCESS("\nSaneamento concluído."))

    # -------------------------------------------------------------- ações

    def _s1_tabelas_faltantes(self, simular):
        orfas = list(Ficha.objects.filter(tabela__isnull=True).order_by("id"))
        if not orfas:
            self.stdout.write("S1 tabelas faltantes: nada a fazer.")
            return
        ids = ", ".join(str(f.pk) for f in orfas)
        self.stdout.write(
            self.style.WARNING(f"S1 criando tabela para {len(orfas)} ficha(s) órfã(s): {ids}")
        )
        if not simular:
            Tabela.objects.bulk_create([Tabela(pk=f.pk, origem=f) for f in orfas])

    def _s2_grupo_administradores(self, username, simular):
        nome_grupo = settings.GRUPO_ADMINISTRADORES
        if simular:
            existe = Group.objects.filter(name=nome_grupo).exists()
            self.stdout.write(
                f"S2 grupo '{nome_grupo}': {'já existe' if existe else 'seria criado'}"
            )
            return
        grupo, criado = Group.objects.get_or_create(name=nome_grupo)
        usuario = User.objects.filter(username=username).first()
        if usuario is None:
            self.stdout.write(
                self.style.WARNING(
                    f"S2 grupo '{nome_grupo}' {'criado' if criado else 'já existia'}; "
                    f"usuário '{username}' não encontrado — atribua o papel manualmente."
                )
            )
            return
        if usuario.groups.filter(name=nome_grupo).exists():
            self.stdout.write(f"S2 '{username}' já é administrador.")
        else:
            usuario.groups.add(grupo)
            self.stdout.write(self.style.WARNING(f"S2 '{username}' virou administrador."))

    def _s3_datas_suspeitas(self):
        suspeitas = Ficha.objects.filter(dataCriacao__year__lt=2019).order_by("dataCriacao")
        if not suspeitas.exists():
            self.stdout.write("S3 datas suspeitas: nenhuma.")
            return
        detalhes = ", ".join(f"#{f.pk} ({f.dataCriacao})" for f in suspeitas[:10])
        self.stdout.write(
            self.style.WARNING(
                f"S3 {suspeitas.count()} ficha(s) com data anterior a 2019 (não alteradas): "
                f"{detalhes}"
            )
        )

    def _s4_fichas_sem_pesos(self):
        """Peso de porção ausente OU zero — a fórmula usa `pesoAnvisa or pesoPorcao`,
        então 0 tem o mesmo efeito de nulo (era o caso que crashava o original)."""
        vazio = Q(pesoPorcao__isnull=True) | Q(pesoPorcao=0)
        vazio_anvisa = Q(pesoAnvisa__isnull=True) | Q(pesoAnvisa=0)
        sem_peso = Ficha.objects.filter(vazio & vazio_anvisa)
        if not sem_peso.exists():
            self.stdout.write("S4 fichas sem peso de porção: nenhuma.")
            return
        ids = ", ".join(str(pk) for pk in sem_peso.values_list("pk", flat=True)[:10])
        self.stdout.write(
            self.style.WARNING(
                f"S4 {sem_peso.count()} ficha(s) sem peso de porção (exibem “0 porções”): {ids}"
            )
        )

    def _s6_chave(self, simular):
        total = Chave.objects.count()
        if total == 0:
            self.stdout.write(
                self.style.WARNING(
                    "S6 nenhuma chave de cadastro definida — defina uma na tela de Membros."
                )
            )
        else:
            self.stdout.write(f"S6 chave de cadastro: {total} registro(s), a última está em uso.")

    def _s7_configuracao(self, nome, ano_corte, simular):
        config = ConfiguracaoInstancia.atual()
        if config:
            self.stdout.write(
                f"S7 configuração já existe: {config.nome_exibicao} "
                f"(corte {config.ano_corte_ingredientes or 'sem corte'})."
            )
            return
        self.stdout.write(
            self.style.WARNING(
                f"S7 criando configuração da instância: {nome} "
                f"(corte {ano_corte or 'sem corte'})."
            )
        )
        if not simular:
            ConfiguracaoInstancia.objects.create(
                nome_exibicao=nome, ano_corte_ingredientes=ano_corte or None
            )
