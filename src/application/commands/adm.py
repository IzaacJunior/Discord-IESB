import logging
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from application.use_cases.bot_use_cases import BotLifecycleUseCase
from infrastructure.repositories import (
    DiscordChannelRepository,
    SQLiteCategoryRepository,
)
from presentation.controllers.bot_controller import BotController
from presentation.controllers.channel_controller import ChannelController

if TYPE_CHECKING:
    from discord import CategoryChannel

logger = logging.getLogger(__name__)


class ADM(commands.Cog):
    """
    🔧 Comandos administrativos do bot
    """

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

        # 🏗️ Injeção de dependência (Clean Architecture!)
        category_db_repository = SQLiteCategoryRepository()
        channel_repository = DiscordChannelRepository(bot, category_db_repository)
        self.channel_controller = ChannelController(channel_repository)
        
        # 🤖 Bot lifecycle controller
        bot_lifecycle_use_case = BotLifecycleUseCase(bot)
        self.bot_controller = BotController(bot_lifecycle_use_case)

    async def _validate_voice_state(
        self, ctx: commands.Context
    ) -> "CategoryChannel | None":
        """
        🔍 Valida se o usuário está em um canal de voz válido com categoria.
        Returns:
            CategoryChannel se válido, None caso contrário
        """
        match (ctx.author.voice, ctx.author.voice and ctx.author.voice.channel):
            case (None, _) | (_, None):
                await ctx.send(
                    "❌ Você precisa estar em um canal de voz!", delete_after=5
                )
                return None
            case (_, channel) if channel.category is None:
                await ctx.send(
                    "❌ O canal de voz precisa estar em uma categoria!", delete_after=5
                )
                return None
            case (_, channel):
                return channel.category

    @commands.command(name="des", help="Desconecta o bot e o faz ficar offline")
    @commands.has_permissions(administrator=True)
    async def desconectar(self, ctx: commands.Context) -> None:
        """
        🔌 Desconecta o bot do Discord.
        """
        await ctx.send("Desconectando o bot com carinho... Até logo! 💕")
        
        # Usa o controller seguindo Clean Architecture
        response = await self.bot_controller.shutdown(
            admin_name=ctx.author.name,
            guild_name=ctx.guild.name,
            reason="Comando !des executado"
        )
        
        if not response.success:
            await ctx.send(f"❌ {response.message}", delete_after=5)

    @commands.command(
        name="cls", help="Limpa o canal de texto atual, de todo ou @ de um usuário"
    )
    @commands.has_permissions(manage_messages=True)
    async def clear_text_channel(
        self,
        ctx: commands.Context,
        limit: int = 100,
        user: discord.Member | None = None,
    ) -> None:
        """
        🧹 Limpa mensagens do canal de texto atual.
        Args:
            ctx: Contexto do comando
            limit: Quantidade máxima de mensagens a deletar (padrão: 100)
            user: Usuário específico para filtrar (opcional)
        """

        def check(msg: discord.Message) -> bool:
            """Filtra mensagens baseado no usuário ou ignora bots."""
            return msg.author == user if user else not msg.author.bot

        deleted = await ctx.channel.purge(limit=limit, check=check)

        count = len(deleted)
        message = (
            f"🧹 {count} mensagem(ns) de {user.mention} deletada(s)!"
            if user
            else f"🧹 {count} mensagem(ns) deletada(s)!"
        )

        await ctx.send(message, delete_after=5)
        logger.info(
            "🗑️ Canal limpo | mensagens=%d | user=%s | admin=%s",
            count,
            user.name if user else "todos",
            ctx.author.name,
        )

    @commands.command(
        name="+voice", help="Marca categoria atual como geradora de salas temporárias"
    )
    @commands.has_permissions(administrator=True)
    async def add_category(self, ctx: commands.Context) -> None:
        """
        🎙️ Marca uma categoria como geradora de salas temporárias.
        Funcionamento:
        1. Admin usa comando em canal de voz
        2. Categoria do canal é marcada como "temp room generator"
        3. Sistema salva no banco de dados
        4. Quando alguém entrar em canais dessa categoria, cria sala temporária
        """
        # 🔍 Validação com método auxiliar reutilizável
        if not (category := await self._validate_voice_state(ctx)):
            return

        try:
            # 🚀 Delega para o controller marcar categoria como temp room generator
            success = (
                await self.channel_controller.handle_mark_category_as_temp_generator(
                    category=category, guild_id=ctx.guild.id
                )
            )

            # 💬 Feedback baseado no resultado com match/case (Python 3.13)
            match success:
                case True:
                    await ctx.send(
                        f"✅ Categoria **{category.name}** marcada como geradora de salas temporárias!\n"
                        f"💡 Agora, quando alguém entrar em qualquer canal desta categoria, "
                        f"uma sala temporária será criada automaticamente! 🎉",
                        delete_after=10,
                    )
                    logger.info(
                        "✅ Categoria configurada | categoria=%s | guild=%s | admin=%s",
                        category.name,
                        ctx.guild.name,
                        ctx.author.name,
                    )
                case False:
                    await ctx.send(
                        f"⚠️ A categoria **{category.name}** já está configurada como geradora!",
                        delete_after=5,
                    )
                    logger.warning(
                        "⚠️ Categoria já configurada | categoria=%s", category.name
                    )

        except Exception as e:
            logger.exception(
                "❌ Erro ao configurar categoria | categoria=%s | erro=%s",
                category.name,
                type(e).__name__,
            )
            await ctx.send(f"❌ Erro ao configurar categoria: {e!s}", delete_after=5)

    @commands.command(
        name="-voice", help="Remove configuração de categoria de salas temporárias"
    )
    @commands.has_permissions(administrator=True)
    async def remove_category(self, ctx: commands.Context) -> None:
        """
        🗑️ Remove marcação de categoria e deleta todas salas temporárias.

        💡 Python 3.13: Reutiliza validação e usa pattern matching
        💡 Boa Prática: Operação completa - desmarcar + limpar canais

        Funcionamento:
        1. Admin usa comando em canal de voz
        2. Categoria do canal deixa de gerar salas temporárias
        3. TODOS os canais temporários da categoria são deletados
        4. Sistema remove configuração do banco
        """
        # 🔍 Validação com método auxiliar reutilizável
        if not (category := await self._validate_voice_state(ctx)):
            return

        try:
            # 🗑️ Delega para o controller remover categoria e canais
            success = (
                await self.channel_controller.handle_unmark_category_as_temp_generator(
                    category_id=category.id, guild_id=ctx.guild.id
                )
            )

            # 💬 Feedback baseado no resultado com match/case (Python 3.13)
            match success:
                case True:
                    await ctx.send(
                        f"✅ Categoria **{category.name}** não gera mais salas temporárias!\n"
                        f"🧹 Todas as salas temporárias dessa categoria foram deletadas!",
                        delete_after=10,
                    )
                    logger.info(
                        "✅ Categoria removida e limpa | categoria=%s | guild=%s | admin=%s",
                        category.name,
                        ctx.guild.name,
                        ctx.author.name,
                    )
                case False:
                    await ctx.send(
                        f"⚠️ A categoria **{category.name}** não estava configurada!",
                        delete_after=5,
                    )
                    logger.warning(
                        "⚠️ Categoria não estava configurada | categoria=%s",
                        category.name,
                    )

        except Exception as e:
            logger.exception(
                "❌ Erro ao remover categoria | categoria=%s | erro=%s",
                category.name,
                type(e).__name__,
            )
            await ctx.send(f"❌ Erro ao remover categoria: {e!s}", delete_after=5)

    @commands.command(
        name="+channel",
        help="🏠 Marca categoria para criar fóruns privados únicos quando membro entrar",
    )
    @commands.has_permissions(administrator=True)
    async def add_unique_channel_category(
        self, ctx: commands.Context, category: discord.CategoryChannel | None = None
    ) -> None:
        """
        🏠 Marca categoria como geradora de fóruns únicos por membro.

        💡 Boa Prática: Cada membro recebe UM ÚNICO fórum nesta categoria
        🔒 Sistema inteligente: Verifica se categoria já existe antes de criar
        ✨ NOVO: Cria salas para TODOS os membros existentes que não têm

        Funcionamento:
        1. Admin usa comando: !+channel #categoria
        2. OU usa sem parâmetro para usar categoria do canal atual
        3. Categoria é marcada como "unique channel generator"
        4. Sistema salva no banco de dados
        5. 🎁 BÔNUS: Cria salas para membros que já estão no servidor (exceto bots)
        6. Quando novos membros entrarem:
           - Verifica se JÁ tem canal nesta categoria
           - Se NÃO tem: cria fórum privado único
           - Se JÁ tem: ignora criação (evita duplicatas)

        Args:
            category: Categoria Discord (opcional). Se não fornecido, usa categoria do canal atual
        """
        # 🔍 STEP 1: Determina qual categoria usar
        target_category = category

        if not target_category:
            # 💡 Usa categoria do canal de texto atual
            if not ctx.channel.category:
                await ctx.send(
                    "❌ Este canal não está em nenhuma categoria!\n"
                    "💡 Use: `!+channel #categoria` para especificar uma categoria",
                    delete_after=10,
                )
                return

            target_category = ctx.channel.category

        logger.info(
            "🔍 Categoria selecionada: '%s' (ID: %s)",
            target_category.name,
            target_category.id,
        )

        try:
            # 🚀 Delega para o controller marcar categoria como unique channel generator
            success = (
                await self.channel_controller.handle_mark_category_as_unique_generator(
                    category=target_category, guild_id=ctx.guild.id
                )
            )

            # 💬 Feedback baseado no resultado com match/case (Python 3.13)
            match success:
                case True:
                    # 🎉 Mensagem inicial de confirmação
                    initial_message = await ctx.send(
                        f"✅ Categoria **{target_category.name}** marcada para fóruns únicos!\n"
                        f"🏗️ Criando salas para membros existentes...",
                    )

                    logger.info(
                        "✅ Categoria configurada para fóruns únicos | categoria=%s | guild=%s | admin=%s",
                        target_category.name,
                        ctx.guild.name,
                        ctx.author.name,
                    )

                    # 🏗️ Cria salas para membros existentes
                    created_count = 0
                    skipped_count = 0

                    for member in ctx.guild.members:
                        # 🤖 Ignora bots
                        if member.bot:
                            logger.debug("🤖 Ignorando bot: %s", member.name)
                            continue

                        # 🏠 Tenta criar sala única para o membro
                        try:
                            result = await self.channel_controller.handle_create_unique_member_channel(
                                member=member, category_id=target_category.id
                            )

                            if result:
                                created_count += 1
                                logger.info(
                                    "✅ Sala criada | member=%s | categoria=%s",
                                    member.display_name,
                                    target_category.name,
                                )
                            else:
                                skipped_count += 1
                                logger.debug(
                                    "⏭️ Sala já existe | member=%s", member.display_name
                                )

                        except Exception:
                            skipped_count += 1
                            logger.exception(
                                "❌ Erro ao criar sala para %s",
                                member.display_name,
                            )

                    # 📊 Mensagem final com estatísticas
                    await initial_message.edit(
                        content=(
                            f"✅ Categoria **{target_category.name}** configurada com sucesso!\n\n"
                            f"📊 **Resultado da criação em massa:**\n"
                            f"• 🏠 Salas criadas: **{created_count}**\n"
                            f"• ⏭️ Membros já tinham sala: **{skipped_count}**\n"
                            f"• 🤖 Bots ignorados: **{sum(1 for m in ctx.guild.members if m.bot)}**\n\n"
                            f"💡 Novos membros receberão salas automaticamente ao entrar! 🎉"
                        )
                    )

                    logger.info(
                        "📊 Criação em massa concluída | criadas=%d | ignoradas=%d | categoria=%s",
                        created_count,
                        skipped_count,
                        target_category.name,
                    )

                case False:
                    await ctx.send(
                        f"⚠️ A categoria **{target_category.name}** já está configurada para fóruns únicos!",
                        delete_after=5,
                    )
                    logger.warning(
                        "⚠️ Categoria já configurada | categoria=%s",
                        target_category.name,
                    )

        except Exception as e:
            logger.exception(
                "❌ Erro ao configurar categoria | categoria=%s | erro=%s",
                target_category.name,
                type(e).__name__,
            )
            await ctx.send(f"❌ Erro ao configurar categoria: {e!s}", delete_after=5)

    @commands.command(
        name="-channel", help="🗑️ Remove configuração de categoria de fóruns únicos"
    )
    @commands.has_permissions(administrator=True)
    async def remove_unique_channel_category(
        self, ctx: commands.Context, category: discord.CategoryChannel | None = None
    ) -> None:
        """
        🗑️ Remove marcação de categoria e limpa relacionamentos.

        💡 Boa Prática: Operação completa - desmarcar + limpar registros
        ⚠️ IMPORTANTE: NÃO deleta os canais, apenas remove configuração

        Funcionamento:
        1. Admin usa comando: !-channel #categoria
        2. OU usa sem parâmetro para usar categoria do canal atual
        3. Categoria deixa de gerar fóruns únicos
        4. Registros de canais existentes são mantidos
        5. Sistema remove apenas a configuração do banco

        Args:
            category: Categoria Discord (opcional). Se não fornecido, usa categoria do canal atual
        """
        # 🔍 STEP 1: Determina qual categoria usar
        target_category = category

        if not target_category:
            # 💡 Usa categoria do canal de texto atual
            if not ctx.channel.category:
                await ctx.send(
                    "❌ Este canal não está em nenhuma categoria!\n"
                    "💡 Use: `!-channel #categoria` para especificar uma categoria",
                    delete_after=10,
                )
                return

            target_category = ctx.channel.category

        logger.info(
            "🔍 Categoria selecionada para remoção: '%s' (ID: %s)",
            target_category.name,
            target_category.id,
        )

        try:
            # 🗑️ Delega para o controller remover categoria
            success = await self.channel_controller.handle_unmark_category_as_unique_generator(
                category_id=target_category.id, guild_id=ctx.guild.id
            )

            # 💬 Feedback baseado no resultado com match/case (Python 3.13)
            match success:
                case True:
                    await ctx.send(
                        f"✅ Categoria **{target_category.name}** não gera mais fóruns únicos!\n"
                        f"💡 Canais existentes foram mantidos (não deletados)",
                        delete_after=10,
                    )
                    logger.info(
                        "✅ Categoria removida de fóruns únicos | categoria=%s | guild=%s | admin=%s",
                        target_category.name,
                        ctx.guild.name,
                        ctx.author.name,
                    )
                case False:
                    await ctx.send(
                        f"⚠️ A categoria **{target_category.name}** não estava configurada!",
                        delete_after=5,
                    )
                    logger.warning(
                        "⚠️ Categoria não estava configurada | categoria=%s",
                        target_category.name,
                    )

        except Exception as e:
            logger.exception(
                "❌ Erro ao remover categoria | categoria=%s | erro=%s",
                target_category.name,
                type(e).__name__,
            )
            await ctx.send(f"❌ Erro ao remover categoria: {e!s}", delete_after=5)

    @commands.command(name="+forum", help="Cria fórum de sala de aula")
    @commands.has_permissions(administrator=True)
    async def create_class_forum(
        self,
        ctx: commands.Context,
        forum_name: str,
        category: discord.CategoryChannel | None = None,
    ) -> None:
        """
        🏫 Cria fórum de sala de aula na categoria especificada.

        💡 Boa Prática: Facilita organização de discussões acadêmicas
        💡 Uso: !+forum "Nome do Fórum" ou !+forum "Nome do Fórum" #categoria
        💡 Arquitetura: Segue Clean Architecture com Use Case e persistência

        Funcionamento:
        1. Admin usa comando: !+forum "Nome do Fórum"
        2. Usa categoria do canal atual OU menciona uma categoria (#nome)
        3. Controller delega para Use Case que valida e cria
        4. Fórum é salvo no banco de dados para auditoria
        5. Fórum aparece na categoria e está pronto para uso

        Args:
            ctx: Contexto do comando
            forum_name: Nome do fórum (obrigatório)
            category: Categoria Discord (opcional, usa canal atual se não fornecido)
        """
        # 🔍 STEP 1: Valida nome do fórum
        if not forum_name or not forum_name.strip():
            await ctx.send(
                "❌ Você precisa fornecer um nome para o fórum!\n"
                '💡 Use: `!+forum "Nome do Fórum"`',
                delete_after=5,
            )
            logger.warning(
                "⚠️ Tentativa de criar fórum sem nome | admin=%s", ctx.author.name
            )
            return

        # 🔍 STEP 2: Determina qual categoria usar
        target_category = category

        if not target_category:
            # 💡 Usa categoria do canal de texto atual
            if not ctx.channel.category:
                await ctx.send(
                    "❌ Este canal não está em nenhuma categoria!\n"
                    '💡 Use: `!+forum "Nome" #categoria` para especificar uma categoria',
                    delete_after=10,
                )
                logger.warning(
                    "❌ Canal sem categoria | admin=%s | channel=%s",
                    ctx.author.name,
                    ctx.channel.name,
                )
                return

            target_category = ctx.channel.category

        logger.info(
            "✅ Categoria selecionada: '%s' (ID: %s)",
            target_category.name,
            target_category.id,
        )

        try:
            # 🏗️ STEP 3: Delega para controller que segue Clean Architecture
            success = await self.channel_controller.handle_create_forum(
                forum_name=forum_name.strip(),
                category=target_category,
                guild_id=ctx.guild.id,
                creator_id=ctx.author.id,
            )

            # 💬 Feedback baseado no resultado
            if success:
                await ctx.send(
                    f"✅ Fórum **{forum_name}** criado com sucesso! 🎉\n"
                    f"📍 Localização: Categoria **{target_category.name}**\n"
                    f"💾 Salvo no banco de dados para auditoria",
                    delete_after=10,
                )

                logger.info(
                    "✅ Fórum criado | forum=%s | categoria=%s | guild=%s | admin=%s",
                    forum_name,
                    target_category.name,
                    ctx.guild.name,
                    ctx.author.name,
                )
            else:
                await ctx.send(
                    f"⚠️ Não foi possível criar o fórum **{forum_name}**.\n"
                    f"💡 Ele pode já existir ou houve um erro.",
                    delete_after=5,
                )
                logger.warning(
                    "⚠️ Fórum não criado | forum=%s | admin=%s",
                    forum_name,
                    ctx.author.name,
                )

        except discord.Forbidden:
            await ctx.send(
                "❌ Permissão negada! Verifique se o bot tem permissão para criar fóruns.",
                delete_after=5,
            )
            logger.exception(
                "❌ Permissão negada ao criar fórum | categoria=%s | admin=%s",
                target_category.name,
                ctx.author.name,
            )

        except Exception as e:
            await ctx.send(
                f"❌ Erro ao criar fórum: {e!s}",
                delete_after=5,
            )
            logger.exception(
                "❌ Erro ao criar fórum | forum_name=%s | categoria=%s | erro=%s",
                forum_name,
                target_category.name,
                type(e).__name__,
            )

    @commands.command(name="-forum", help="Remove configuração de categoria de fóruns")
    @commands.has_permissions(administrator=True)
    async def delete_class_forum(
        self, ctx: commands.Context, category: discord.CategoryChannel | None = None
    ) -> None:
        """
        🗑️ Remove configuração de categoria geradora de fóruns do banco de dados.

        💡 Boa Prática: Remove configuração do banco de dados
        💡 Uso: !-forum ou !-forum #categoria
        💡 Arquitetura: Segue Clean Architecture com Controller
        ⚠️ IMPORTANTE: NÃO deleta fóruns, apenas remove configuração

        Funcionamento:
        1. Admin usa comando: !-forum (usa categoria do canal atual)
        2. OU: !-forum #categoria (especifica categoria)
        3. Sistema valida se categoria existe
        4. Controller remove configuração do banco de dados
        5. Categoria deixa de gerar fóruns automaticamente
        6. Fóruns existentes são mantidos

        Args:
            ctx: Contexto do comando
            category: Categoria Discord (opcional - usa canal atual se não fornecido)
        """
        # 🔍 STEP 1: Determina qual categoria usar
        target_category = category

        if not target_category:
            # 💡 Usa categoria do canal de texto atual
            if not ctx.channel.category:
                await ctx.send(
                    "❌ Este canal não está em nenhuma categoria!\n"
                    "💡 Use: `!-forum #categoria` para especificar uma categoria",
                    delete_after=10,
                )
                logger.warning(
                    "❌ Canal sem categoria | admin=%s | channel=%s",
                    ctx.author.name,
                    ctx.channel.name,
                )
                return

            target_category = ctx.channel.category

        logger.info(
            "🗑️ Admin solicitando remoção de categoria: '%s' (ID: %s)",
            target_category.name,
            target_category.id,
        )

        try:
            # 🗑️ STEP 2: Delega para controller remover configuração da categoria
            success = await self.channel_controller.handle_unmark_category_as_unique_generator(
                category_id=target_category.id, guild_id=ctx.guild.id
            )

            # 💬 Feedback baseado no resultado
            if success:
                await ctx.send(
                    f"✅ Categoria **{target_category.name}** removida com sucesso! 🗑️\n"
                    f"💾 Configuração removida do banco de dados\n"
                    f"� Fóruns existentes foram mantidos (não deletados)\n"
                    f"🚫 Novos membros NÃO receberão fóruns automaticamente",
                    delete_after=10,
                )

                logger.info(
                    "✅ Categoria removida | categoria=%s | id=%s | guild=%s | admin=%s",
                    target_category.name,
                    target_category.id,
                    ctx.guild.name,
                    ctx.author.name,
                )
            else:
                await ctx.send(
                    f"⚠️ A categoria **{target_category.name}** não estava configurada!\n"
                    f"💡 Nenhuma configuração foi encontrada no banco de dados.",
                    delete_after=5,
                )
                logger.warning(
                    "⚠️ Categoria não estava configurada | categoria=%s | id=%s | admin=%s",
                    target_category.name,
                    target_category.id,
                    ctx.author.name,
                )

        except Exception as e:
            await ctx.send(
                f"❌ Erro ao remover categoria: {e!s}",
                delete_after=5,
            )
            logger.exception(
                "❌ Erro ao remover categoria | categoria=%s | id=%s | erro=%s",
                target_category.name,
                target_category.id,
                type(e).__name__,
            )

    @commands.command(
        name="test", help="🧪 Comando de teste para depuração e desenvolvimento"
    )
    @commands.has_permissions(administrator=True)
    async def test_command(self, ctx: commands.Context, texto) -> None:
        """
        🧪 Comando de teste para depuração e desenvolvimento.
        """
        await ctx.send(f"Teste recebido: {texto}")


async def setup(bot: commands.Bot) -> None:
    """
    🔧 Registra o Cog ADM no bot.

    💡 Type hint completo para melhor documentação
    """
    await bot.add_cog(ADM(bot))
