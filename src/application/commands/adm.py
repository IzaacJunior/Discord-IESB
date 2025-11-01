import logging
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from infrastructure.repositories import DiscordChannelRepository
from presentation.controllers.channel_controller import ChannelController

if TYPE_CHECKING:
    from discord import CategoryChannel

logger = logging.getLogger(__name__)


class ADM(commands.Cog):
    """
    🔧 Comandos administrativos do bot
    
    💡 Boa Prática: Injeta dependências para manter
    baixo acoplamento e facilitar testes!
    
    🚀 Python 3.13: Type hints modernos e validações otimizadas
    """
    
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        
        # 🏗️ Injeção de dependência - Clean Architecture!
        channel_repository = DiscordChannelRepository(bot)
        self.channel_controller = ChannelController(channel_repository)

    # 🛠️ Métodos auxiliares privados - DRY Principle!
    async def _validate_voice_state(
        self, 
        ctx: commands.Context
    ) -> "CategoryChannel | None":
        """
        🔍 Valida se o usuário está em um canal de voz válido com categoria.
        
        💡 Python 3.13: Pattern matching para validações mais limpas
        💡 String literal no type hint quando tipo está em TYPE_CHECKING
        
        Returns:
            CategoryChannel se válido, None caso contrário
        """
        match (ctx.author.voice, ctx.author.voice and ctx.author.voice.channel):
            case (None, _) | (_, None):
                await ctx.send(
                    "❌ Você precisa estar em um canal de voz!",
                    delete_after=5
                )
                return None
            case (_, channel) if channel.category is None:
                await ctx.send(
                    "❌ O canal de voz precisa estar em uma categoria!",
                    delete_after=5
                )
                return None
            case (_, channel):
                return channel.category

    @commands.command(name="des", help="Desconecta o bot e o faz ficar offline")
    @commands.has_permissions(administrator=True)
    async def desconectar(self, ctx: commands.Context) -> None:
        """
        🔌 Desconecta o bot do Discord.
        
        💡 Type hint completo para melhor documentação
        """
        await ctx.send("Desconectando o bot... Até logo!")
        logger.info(
            "🤖 Bot desconectado | admin=%s | guild=%s",
            ctx.author.name,
            ctx.guild.name
        )
        await self.bot.close()

    @commands.command(
        name="cls", 
        help="Limpa o canal de texto atual, de todo ou @ de um usuário"
    )
    @commands.has_permissions(manage_messages=True)
    async def clear_text_channel(
        self, 
        ctx: commands.Context, 
        limit: int = 100, 
        user: discord.Member | None = None
    ) -> None:
        """
        🧹 Limpa mensagens do canal de texto.
        
        💡 Python 3.13: Union type com | é mais limpo que Optional
        💡 Lambda inline para filtro mais conciso
        
        Args:
            ctx: Contexto do comando
            limit: Quantidade máxima de mensagens a deletar (padrão: 100)
            user: Usuário específico para filtrar (opcional)
        """
        # 🎯 Filtro inline mais pythônico com Python 3.13
        check = (
            lambda msg: msg.author == user 
            if user 
            else lambda msg: not msg.author.bot
        )
        
        # 🗑️ Deleta mensagens com o filtro aplicado
        deleted = await ctx.channel.purge(limit=limit, check=check)
        
        # 💬 Feedback contextualizado com f-string otimizada (Python 3.13)
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
            ctx.author.name
        )

    @commands.command(
        name="+voice", 
        help="Marca categoria atual como geradora de salas temporárias"
    )
    @commands.has_permissions(administrator=True)
    async def add_category(self, ctx: commands.Context) -> None:
        """
        🎙️ Marca uma categoria como geradora de salas temporárias.
        
        💡 Python 3.13: Usa pattern matching para validação
        💡 Método auxiliar reutilizável elimina código duplicado
        
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
            success = await self.channel_controller.handle_mark_category_as_temp_generator(
                category=category,
                guild_id=ctx.guild.id
            )
            
            # 💬 Feedback baseado no resultado com match/case (Python 3.13)
            match success:
                case True:
                    await ctx.send(
                        f"✅ Categoria **{category.name}** marcada como geradora de salas temporárias!\n"
                        f"💡 Agora, quando alguém entrar em qualquer canal desta categoria, "
                        f"uma sala temporária será criada automaticamente! 🎉",
                        delete_after=10
                    )
                    logger.info(
                        "✅ Categoria configurada | categoria=%s | guild=%s | admin=%s",
                        category.name,
                        ctx.guild.name,
                        ctx.author.name
                    )
                case False:
                    await ctx.send(
                        f"⚠️ A categoria **{category.name}** já está configurada como geradora!",
                        delete_after=5
                    )
                    logger.warning(
                        "⚠️ Categoria já configurada | categoria=%s",
                        category.name
                    )
                
        except Exception as e:
            logger.exception(
                "❌ Erro ao configurar categoria | categoria=%s | erro=%s",
                category.name,
                type(e).__name__
            )
            await ctx.send(
                f"❌ Erro ao configurar categoria: {e!s}",
                delete_after=5
            )

    @commands.command(
        name="-voice", 
        help="Remove configuração de categoria de salas temporárias"
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
            success = await self.channel_controller.handle_unmark_category_as_temp_generator(
                category_id=category.id,
                guild_id=ctx.guild.id
            )
            
            # 💬 Feedback baseado no resultado com match/case (Python 3.13)
            match success:
                case True:
                    await ctx.send(
                        f"✅ Categoria **{category.name}** não gera mais salas temporárias!\n"
                        f"🧹 Todas as salas temporárias dessa categoria foram deletadas!",
                        delete_after=10
                    )
                    logger.info(
                        "✅ Categoria removida e limpa | categoria=%s | guild=%s | admin=%s",
                        category.name,
                        ctx.guild.name,
                        ctx.author.name
                    )
                case False:
                    await ctx.send(
                        f"⚠️ A categoria **{category.name}** não estava configurada!",
                        delete_after=5
                    )
                    logger.warning(
                        "⚠️ Categoria não estava configurada | categoria=%s",
                        category.name
                    )
                
        except Exception as e:
            logger.exception(
                "❌ Erro ao remover categoria | categoria=%s | erro=%s",
                category.name,
                type(e).__name__
            )
            await ctx.send(
                f"❌ Erro ao remover categoria: {e!s}",
                delete_after=5
            )

    @commands.command(
        name="+channel",
        help="🏠 Marca categoria para criar fóruns privados únicos quando membro entrar"
    )
    @commands.has_permissions(administrator=True)
    async def add_unique_channel_category(
        self, 
        ctx: commands.Context,
        category_name: str | None = None
    ) -> None:
        """
        🏠 Marca categoria como geradora de fóruns únicos por membro.
        
        💡 Boa Prática: Cada membro recebe UM ÚNICO fórum nesta categoria
        🔒 Sistema inteligente: Verifica se categoria já existe antes de criar
        ✨ NOVO: Cria salas para TODOS os membros existentes que não têm
        
        Funcionamento:
        1. Admin usa comando em canal de texto: !+channel "Nome da Categoria"
        2. OU usa sem parâmetro para usar categoria do canal atual
        3. Categoria é marcada como "unique channel generator"
        4. Sistema salva no banco de dados
        5. 🎁 BÔNUS: Cria salas para membros que já estão no servidor (exceto bots)
        6. Quando novos membros entrarem:
           - Verifica se JÁ tem canal nesta categoria
           - Se NÃO tem: cria fórum privado único
           - Se JÁ tem: ignora criação (evita duplicatas)
           
        Args:
            category_name: Nome da categoria (opcional). Se não fornecido, usa categoria do canal atual
        """
        # 🔍 STEP 1: Determina qual categoria usar
        category = None
        
        if category_name:
            # 💡 Busca categoria pelo nome fornecido
            category = discord.utils.get(ctx.guild.categories, name=category_name)
            
            if not category:
                await ctx.send(
                    f"❌ Categoria **{category_name}** não encontrada!\n"
                    f"💡 Verifique se o nome está correto (maiúsculas/minúsculas importam)",
                    delete_after=10
                )
                return
        else:
            # 💡 Usa categoria do canal de texto atual
            if not ctx.channel.category:
                await ctx.send(
                    "❌ Este canal não está em nenhuma categoria!\n"
                    f"💡 Use: `!+channel \"Nome da Categoria\"` para especificar uma categoria",
                    delete_after=10
                )
                return
            
            category = ctx.channel.category
        
        logger.info(
            "🔍 Categoria selecionada: '%s' (ID: %s)",
            category.name,
            category.id
        )
        
        try:
            # 🚀 Delega para o controller marcar categoria como unique channel generator
            success = await self.channel_controller.handle_mark_category_as_unique_generator(
                category=category,
                guild_id=ctx.guild.id
            )
            
            # 💬 Feedback baseado no resultado com match/case (Python 3.13)
            match success:
                case True:
                    # 🎉 Mensagem inicial de confirmação
                    initial_message = await ctx.send(
                        f"✅ Categoria **{category.name}** marcada para fóruns únicos!\n"
                        f"� Criando salas para membros existentes...",
                    )
                    
                    logger.info(
                        "✅ Categoria configurada para fóruns únicos | categoria=%s | guild=%s | admin=%s",
                        category.name,
                        ctx.guild.name,
                        ctx.author.name
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
                                member=member,
                                category_id=category.id
                            )
                            
                            if result:
                                created_count += 1
                                logger.info(
                                    "✅ Sala criada | member=%s | categoria=%s",
                                    member.display_name,
                                    category.name
                                )
                            else:
                                skipped_count += 1
                                logger.debug(
                                    "⏭️ Sala já existe | member=%s",
                                    member.display_name
                                )
                        
                        except Exception as member_error:
                            skipped_count += 1
                            logger.error(
                                "❌ Erro ao criar sala para %s: %s",
                                member.display_name,
                                str(member_error)
                            )
                    
                    # 📊 Mensagem final com estatísticas
                    await initial_message.edit(
                        content=(
                            f"✅ Categoria **{category.name}** configurada com sucesso!\n\n"
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
                        category.name
                    )
                    
                case False:
                    await ctx.send(
                        f"⚠️ A categoria **{category.name}** já está configurada para fóruns únicos!",
                        delete_after=5
                    )
                    logger.warning(
                        "⚠️ Categoria já configurada | categoria=%s",
                        category.name
                    )
                
        except Exception as e:
            logger.exception(
                "❌ Erro ao configurar categoria | categoria=%s | erro=%s",
                category.name,
                type(e).__name__
            )
            await ctx.send(
                f"❌ Erro ao configurar categoria: {e!s}",
                delete_after=5
            )

    @commands.command(
        name="-channel",
        help="🗑️ Remove configuração de categoria de fóruns únicos"
    )
    @commands.has_permissions(administrator=True)
    async def remove_unique_channel_category(
        self,
        ctx: commands.Context,
        category_name: str | None = None
    ) -> None:
        """
        🗑️ Remove marcação de categoria e limpa relacionamentos.
        
        💡 Boa Prática: Operação completa - desmarcar + limpar registros
        ⚠️ IMPORTANTE: NÃO deleta os canais, apenas remove configuração
        
        Funcionamento:
        1. Admin usa comando: !-channel "Nome da Categoria"
        2. OU usa sem parâmetro para usar categoria do canal atual
        3. Categoria deixa de gerar fóruns únicos
        4. Registros de canais existentes são mantidos
        5. Sistema remove apenas a configuração do banco
        
        Args:
            category_name: Nome da categoria (opcional). Se não fornecido, usa categoria do canal atual
        """
        # 🔍 STEP 1: Determina qual categoria usar
        category = None
        
        if category_name:
            # 💡 Busca categoria pelo nome fornecido
            category = discord.utils.get(ctx.guild.categories, name=category_name)
            
            if not category:
                await ctx.send(
                    f"❌ Categoria **{category_name}** não encontrada!\n"
                    f"💡 Verifique se o nome está correto (maiúsculas/minúsculas importam)",
                    delete_after=10
                )
                return
        else:
            # 💡 Usa categoria do canal de texto atual
            if not ctx.channel.category:
                await ctx.send(
                    "❌ Este canal não está em nenhuma categoria!\n"
                    f"💡 Use: `!-channel \"Nome da Categoria\"` para especificar uma categoria",
                    delete_after=10
                )
                return
            
            category = ctx.channel.category
        
        logger.info(
            "🔍 Categoria selecionada para remoção: '%s' (ID: %s)",
            category.name,
            category.id
        )
        
        try:
            # 🗑️ Delega para o controller remover categoria
            success = await self.channel_controller.handle_unmark_category_as_unique_generator(
                category_id=category.id,
                guild_id=ctx.guild.id
            )
            
            # 💬 Feedback baseado no resultado com match/case (Python 3.13)
            match success:
                case True:
                    await ctx.send(
                        f"✅ Categoria **{category.name}** não gera mais fóruns únicos!\n"
                        f"💡 Canais existentes foram mantidos (não deletados)",
                        delete_after=10
                    )
                    logger.info(
                        "✅ Categoria removida de fóruns únicos | categoria=%s | guild=%s | admin=%s",
                        category.name,
                        ctx.guild.name,
                        ctx.author.name
                    )
                case False:
                    await ctx.send(
                        f"⚠️ A categoria **{category.name}** não estava configurada!",
                        delete_after=5
                    )
                    logger.warning(
                        "⚠️ Categoria não estava configurada | categoria=%s",
                        category.name
                    )
                
        except Exception as e:
            logger.exception(
                "❌ Erro ao remover categoria | categoria=%s | erro=%s",
                category.name,
                type(e).__name__
            )
            await ctx.send(
                f"❌ Erro ao remover categoria: {e!s}",
                delete_after=5
            )


async def setup(bot: commands.Bot) -> None:
    """
    🔧 Registra o Cog ADM no bot.
    
    💡 Type hint completo para melhor documentação
    """
    await bot.add_cog(ADM(bot))
