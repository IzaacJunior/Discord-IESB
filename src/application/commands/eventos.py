"""
🎯 MÓDULO DE EVENTOS DO BOT DISCORD

📌 Responsabilidades:
    - Detectar eventos do Discord (voz, membros entrando)
    - Delegar ações para o Controller (Presentation Layer)
    - Logging de atividades importantes

💡 Arquitetura: Segue Clean Architecture
    Discord Events → Presentation Layer → Use Cases → Domain → Infrastructure
"""

import logging

import discord
from discord.ext import commands

from infrastructure.repositories import (
    DiscordChannelRepository,
    SQLiteCategoryRepository,
)
from presentation.controllers.channel_controller import ChannelController

logger = logging.getLogger(__name__)
audit = logging.getLogger("audit")


class Eventos(commands.Cog):
    """
    🎧 Gerenciador de Eventos do Discord

    💡 Boa Prática: Usa Cog para organizar eventos relacionados
    🏗️ Arquitetura: Camada de entrada que delega para Controllers
    """

    def __init__(self, bot: commands.Bot) -> None:
        """
        Inicializa o módulo de eventos.

        Args:
            bot: Instância do bot Discord.py

        💡 Boa Prática: Injeção de dependências no construtor
        """
        self.bot = bot

        # 🏗️ Injeção de dependência correta - Clean Architecture!
        # 💡 Boa Prática: Repository de banco separado do repository Discord
        category_db_repository = SQLiteCategoryRepository()
        channel_repository = DiscordChannelRepository(bot, category_db_repository)
        self.channel_controller = ChannelController(channel_repository)

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> None:
        """
        🔄 PONTO DE ENTRADA: Detecta mudanças de estado de voz

        💡 Fluxo: Discord Event → Presentation Layer → Use Cases → Domain

        Args:
            member: Membro que teve mudança no estado de voz
            before: Estado de voz anterior
            after: Novo estado de voz

        🎯 Casos de uso:
            - Criar sala temporária ao entrar em canal criador
            - Deletar sala temporária quando ficar vazia
            - Transferir ownership se dono sair
        """
        logger.debug("🎧 Voice state update: %s", member.name)

        # 🎯 STEP 1: Delega para o Controller (Presentation Layer)
        await self.channel_controller.handle_voice_state_update(
            member=member,
            before=before,
            after=after,
        )

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """
        👋 Cria fórum privado único quando membro entra no servidor

        💡 Sistema Inteligente com Categorias:
        1. Verifica se há categoria configurada para fóruns únicos
        2. Se SIM: cria fórum único na categoria configurada
        3. Se NÃO: ignora criação (sistema desativado)

        🏠 Fluxo: Discord Event → Controller → Repository → Discord API

        Funcionalidades do fórum criado:
        - 🔒 Completamente privado (só o membro vê)
        - ✏️ Membro pode editar nome e configurações do canal
        - 🗑️ Membro pode gerenciar todas as mensagens
        - 📝 Membro pode criar threads (posts) no fórum
        - 🎨 Threads herdam as mesmas permissões privadas
        - ♻️ ÚNICO por categoria (evita duplicatas)

        Args:
            member: Membro que acabou de entrar no servidor

        💡 Design Pattern: Event-Driven Architecture
        """
        logger.info("👋 %s entrou no servidor %s", member.name, member.guild.name)
        
        # 📊 Auditando entrada de membro (evento importante)
        audit.info(
            "👋 Membro entrou no servidor",
            extra={
                'member_id': member.id,
                'member_name': member.display_name,
                'guild_id': member.guild.id,
                'guild_name': member.guild.name,
                'action': 'member_join',
            },
        )

        # 🤖 Ignora bots - eles não precisam de fóruns privados
        if member.bot:
            logger.debug("🤖 Membro é bot, ignorando criação de fórum")
            return

        # 🔍 STEP 1: Busca no banco se existe categoria configurada (apenas UMA por guilda)
        try:
            guild = member.guild

            # 💾 Consulta banco de dados para buscar categoria configurada
            configured_category = await self.channel_controller.channel_repository.get_unique_channel_category(
                guild_id=guild.id
            )

            # 🎯 STEP 2: Se NÃO há categoria configurada, ignora criação
            if not configured_category:
                logger.info(
                    "⏭️ Nenhuma categoria configurada para fóruns únicos | servidor=%s",
                    guild.name,
                )
                return

            # 🔍 Busca a categoria no Discord
            category = guild.get_channel(configured_category["category_id"])

            if not category:
                logger.warning(
                    "⚠️ Categoria configurada não encontrada no Discord | category_id=%s | servidor=%s",
                    configured_category["category_id"],
                    guild.name,
                )
                return

            # 🏠 STEP 3: Cria fórum único na categoria configurada
            logger.info(
                "🎯 Categoria configurada encontrada: '%s' | Criando fórum único",
                configured_category["category_name"],
            )

            success = await self.channel_controller.handle_create_unique_member_channel(
                member=member, category_id=category.id
            )

            # 💬 Log do resultado
            if success:
                logger.info(
                    "✅ Fórum único criado | member=%s | categoria=%s",
                    member.display_name,
                    category.name,
                )
                
                # 📊 Auditando criação bem-sucedida de fórum único
                audit.info(
                    "🏠 Fórum único criado com sucesso",
                    extra={
                        'member_id': member.id,
                        'member_name': member.display_name,
                        'category_id': category.id,
                        'category_name': category.name,
                        'guild_id': guild.id,
                        'guild_name': guild.name,
                        'action': 'unique_forum_created',
                    },
                )
            else:
                logger.info(
                    "⏭️ Fórum não criado (pode já existir) | member=%s | categoria=%s",
                    member.display_name,
                    category.name,
                )

        except Exception:
            logger.exception(
                "❌ Erro ao processar entrada de membro %s",
                member.display_name,
            )
            
            # 📊 Auditando erro na criação de fórum
            audit.info(
                "❌ Erro ao processar entrada de membro",
                extra={
                    'member_id': member.id,
                    'member_name': member.display_name,
                    'guild_id': member.guild.id,
                    'guild_name': member.guild.name,
                    'action': 'member_join_error',
                },
            )


async def setup(bot: commands.Bot) -> None:
    """
    🔧 Função de setup para carregar o Cog

    💡 Boa Prática: Padrão obrigatório do Discord.py para extensões
    """
    await bot.add_cog(Eventos(bot))
