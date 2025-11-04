from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

import discord

if TYPE_CHECKING:
    from infrastructure.repositories import DiscordChannelRepository

from application.dtos import CreateChannelDTO
from application.use_cases import (
    CreateChannelUseCase,
    CreateForumUseCase,
)
from config import DB_PATH
from domain.entities import ChannelType
from presentation.views import TempRoomControlView, create_temp_room_embed

logger = logging.getLogger(__name__)


class ChannelController:
    """
    Controller para gerenciamento de canais Discord.

    Responsabilidades:
    - Criar canais de texto e voz
    - Gerenciar salas temporárias automáticas
    - Coordenar eventos de voz (entrada/saída)
    """

    def __init__(
        self,
        channel_repository: DiscordChannelRepository,
    ) -> None:
        """Inicializa controller."""
        self.channel_repository = channel_repository
        self.create_channel_use_case = CreateChannelUseCase(channel_repository)
        self.create_forum_use_case = CreateForumUseCase(channel_repository)

    async def handle_create_text_channel(
        self,
        interaction: discord.Interaction,
        name: str,
        topic: str | None = None,
    ) -> None:
        """Cria canal de texto via comando slash."""
        logger.info("?? Processando criação de canal de texto: %s", name)

        if not name or not name.strip():
            await interaction.response.send_message(
                "? Nome do canal não pode estar vazio!",
                ephemeral=True,
            )
            return

        try:
            request = CreateChannelDTO(
                name=name,
                guild_id=interaction.guild_id or 0,
                channel_type=ChannelType.TEXT,
                topic=topic,
            )

            result = await self.create_channel_use_case.execute(request)

            # Responde baseado no resultado
            match result.created:
                case True:
                    await interaction.response.send_message(
                        f"? Canal de texto **{result.name}** criado com sucesso!",
                        ephemeral=True,
                    )
                case False:
                    if result.id > 0:
                        await interaction.response.send_message(
                            f"?? Canal **{result.name}** já existe! Não criado duplicata.",
                            ephemeral=True,
                        )
                    else:
                        await interaction.response.send_message(
                            f"? Falha ao criar canal **{name}**. Tente novamente.",
                            ephemeral=True,
                        )

        except Exception:
            logger.exception("? Erro inesperado ao criar canal: %s", name)
            await interaction.response.send_message(
                "? Erro interno do servidor. Tente novamente em alguns minutos.",
                ephemeral=True,
            )

    async def handle_create_voice_channel(
        self,
        interaction: discord.Interaction,
        name: str,
        user_limit: int = 0,
    ) -> None:
        """Cria canal de voz via comando slash."""
        logger.info("Processando criação de canal de voz: %s", name)

        if not name or not name.strip():
            await interaction.response.send_message(
                "Nome do canal não pode estar vazio!",
                ephemeral=True,
            )
            return

        # Validação do limite de usuários
        match user_limit:
            case x if x < 0:
                await interaction.response.send_message(
                    "? Limite de usuários não pode ser negativo!",
                    ephemeral=True,
                )
                return
            case x if x > 99:
                await interaction.response.send_message(
                    "? Limite máximo é 99 usuários!",
                    ephemeral=True,
                )
                return

        try:
            request = CreateChannelDTO(
                name=name,
                guild_id=interaction.guild_id or 0,
                channel_type=ChannelType.VOICE,
                user_limit=user_limit,
            )

            result = await self.create_channel_use_case.execute(request)

            match result.created:
                case True:
                    await interaction.response.send_message(
                        f"? Canal de voz **{result.name}** criado com sucesso!",
                        ephemeral=True,
                    )
                case False:
                    if result.id > 0:
                        await interaction.response.send_message(
                            "?? Canal já existe! Não criado duplicata.",
                            ephemeral=True,
                        )
                    else:
                        await interaction.response.send_message(
                            f"? Falha ao criar canal **{name}**. Tente novamente.",
                            ephemeral=True,
                        )

        except Exception:
            logger.exception("Erro inesperado ao criar canal de voz: %s", name)
            await interaction.response.send_message(
                "Erro interno do servidor. Tente novamente em alguns minutos.",
                ephemeral=True,
            )

    async def handle_create_member_text_channel(
        self,
        member: discord.Member,
        category_id: int | None = None,
    ) -> bool:
        """
        Cria fórum privado para novo membro

        Boa Prática: Fórum totalmente privado onde membro tem controle total!
        Permissões: Apenas o membro pode ver, editar e gerenciar

        Funcionalidades:
        - Canal visível apenas para o membro
        - Pode modificar nome do canal
        - Pode gerenciar mensagens (deletar, editar)
        - Pode criar threads privadas (posts privados)
        - NÃO pode criar threads públicas
        - Threads criadas herdam as mesmas permissões do fórum

        Args:
            member: Membro que receberá o fórum privado
            category_id: ID da categoria (opcional)

        Returns:
            bool: True se fórum foi criado com sucesso
        """
        try:
            logger.info("?? Criando fórum privado para %s", member.display_name)

            # Gera nome do fórum baseado no membro
            forum_name = f"{member.display_name.lower()}"

            # Chama repository para criar fórum com permissões especiais
            forum_channel = await self.channel_repository.create_private_forum_channel(
                name=forum_name,
                guild_id=member.guild.id,
                member_id=member.id,
                category_id=category_id,
            )

            # ?? Envia mensagem de boas-vindas no fórum
            try:
                # Cria thread inicial com instruções
                welcome_thread = await forum_channel.create_thread(
                    name="Bem-vindo ao seu fórum!",
                    content=(
                        f"## Olá, {member.mention}!\n\n"
                        f"Este é o seu **fórum privado pessoal**!\n\n"
                        f"### O que você pode fazer aqui:\n"
                        f"-  **Criar threads privadas**: Clique em 'Nova Postagem'\n"
                        f"   para criar tópicos privados\n"
                        f"-  **Editar o nome**: Clique com botão direito em 'Editar Canal'\n"
                        f"-  **Gerenciar mensagens**: Delete ou edite mensagens\n"
                        f"-  **Privacidade total**: Apenas você pode ver este canal\n"
                        f"   e seus posts!\n"
                        f"-  **Personalizar**: Mude nome, descrição, tags e tudo mais!\n\n"
                        f"### Dicas:\n"
                        f"- Use tags para organizar seus tópicos\n"
                        f"- Threads são arquivadas após 7 dias de inatividade\n"
                        f"- Você tem controle total sobre este espaço!\n"
                        f"- **Importante**: Criar posts PRIVADOS (não públicos)\n\n"
                        f"**Divirta-se organizando suas ideias!**"
                    ),
                )

                logger.info(
                    "? Thread de boas-vindas criada | thread=%s",
                    welcome_thread.thread.name,
                )

            except (
                discord.HTTPException,
                discord.Forbidden,
                discord.InvalidArgument,
            ) as thread_error:
                logger.warning(
                    "?? Não foi possível criar thread de boas-vindas: %s",
                    str(thread_error),
                )

            logger.info(
                "Fórum privado criado | member=%s | forum=%s | id=%s",
                member.display_name,
                forum_channel.name,
                forum_channel.id,
            )

        except Exception:
            logger.exception(
                "Erro ao criar fórum para membro %s",
                member.display_name,
            )
            return False
        else:
            return True

    # ---------------------------------------------------------------
    # GERENCIAMENTO DE FÓRUNS
    # ---------------------------------------------------------------

    async def handle_create_forum(
        self,
        forum_name: str,
        category: discord.CategoryChannel,
        guild_id: int,
        creator_id: int,
    ) -> bool:
        """
        🏫 Cria fórum seguindo Clean Architecture

        💡 Boa Prática: Delega para Use Case que valida e persiste
        💡 Pattern matching para cada caso de resultado

        Args:
            forum_name: Nome do fórum
            category: Categoria Discord
            guild_id: ID do servidor
            creator_id: ID do criador

        Returns:
            bool: True se fórum foi criado com sucesso
        """
        try:
            logger.info(
                "🏫 Processando criação de fórum: %s na categoria %s",
                forum_name,
                category.name,
            )

            # 🚀 Delega para Use Case
            result = await self.create_forum_use_case.execute(
                forum_name=forum_name,
                guild_id=guild_id,
                category_id=category.id,
                creator_id=creator_id,
            )

            # 💡 Boa Prática: Pattern matching para cada caso específico
            match result.created, result.id > 0:
                case True, _:
                    # ✅ Sucesso! Fórum criado
                    logger.info(
                        "✅ Fórum criado com sucesso | forum=%s | id=%s",
                        result.name,
                        result.id,
                    )
                case False, True:
                    # ⚠️ Aviso: Fórum já existe (NÃO é erro!)
                    logger.warning(
                        "⚠️ Fórum já existe | forum=%s | id=%s",
                        forum_name,
                        result.id,
                    )
                case False, False:
                    # ❌ Erro: Falha na criação
                    logger.error(
                        "❌ Falha ao criar fórum | forum=%s | motivo=desconhecido",
                        forum_name,
                    )
                    return False

        except Exception:
            logger.exception("❌ Erro ao processar criação de fórum: %s", forum_name)
            return False
        else:
            return True

    # ---------------------------------------------------------------
    # GERENCIAMENTO DE SALAS TEMPORÁRIAS
    # ---------------------------------------------------------------

    async def handle_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> bool:
        """
        Ponto de entrada principal para eventos de voz.

        Fluxo:
        - Entrada em canal -> Cria sala temporária se categoria for geradora
        - Saída de canal -> Remove sala se ficou vazia
        """
        try:
            # Entrada em novo canal
            if (
                after.channel
                and after.channel.category
                and before.channel != after.channel
            ):
                logger.debug(
                    "ENTRADA: %s -> '%s'",
                    member.display_name,
                    after.channel.name,
                )
                await self._handle_channel_entry(member, after)

            # Saída de canal
            if before.channel and before.channel != after.channel:
                logger.debug(
                    "SAÍDA: %s -> '%s'",
                    member.display_name,
                    before.channel.name,
                )
                await self._handle_channel_exit(member, before)

        except (discord.HTTPException, RuntimeError):
            logger.exception("Erro em handle_voice_state_update")
            return False
        else:
            return True

    async def _handle_channel_entry(
        self,
        member: discord.Member,
        after: discord.VoiceState,
    ) -> bool:
        """
        Processa entrada em canal de voz.

        Verifica:
        1. Se já está em sala temporária => Ignora
        2. Se categoria é geradora => Cria sala temporária
        """
        if not after.channel:
            return False

        logger.info(
            "SOLICITAÇÃO: %s entrou no canal '%s' (ID: %s)",
            member.display_name,
            after.channel.name,
            after.channel.id,
        )

        # CHECK 1: Já está em sala temporária?
        is_temp_channel = await self.channel_repository.is_temporary_channel(
            channel_id=after.channel.id,
            guild_id=member.guild.id,
        )

        if is_temp_channel:
            logger.info(
                "IGNORADO: %s entrou em sala temporária existente",
                member.display_name,
            )
            return True

        # CHECK 2: Categoria é geradora?
        if not after.channel.category:
            logger.debug("IGNORADO: Canal sem categoria")
            return False

        is_generator_category = await self.channel_repository.is_temp_room_category(
            category_id=after.channel.category.id,
            guild_id=member.guild.id,
            category_name=after.channel.category.name,
        )

        if not is_generator_category:
            logger.info(
                "IGNORADO: Categoria '%s' não é geradora",
                after.channel.category.name,
            )
            return False

        # Categoria é geradora ? Cria sala temporária
        logger.info("ACEITO: Criando sala temporária para %s", member.display_name)
        return await self._create_temporary_room(member, after)

    async def _create_temporary_room(
        self,
        member: discord.Member,
        after: discord.VoiceState,
    ) -> bool:
        """
        Cria sala temporária para o membro.

        Boa Prática: Clona TODAS as configurações do canal gerador!
        Inclui: nome, limite, bitrate E permissões de roles
        """
        try:
            parent_channel = after.channel

            # Copia as permissões (overwrites) do canal gerador
            # Isso garante que roles como "tecno" tenham as mesmas permissões
            overwrites = parent_channel.overwrites.copy()

            # Adiciona permissões especiais para o dono da sala
            overwrites[member] = discord.PermissionOverwrite(
                connect=True,
                speak=True,
                stream=True,
                manage_channels=True,  # Pode editar configurações da sala
            )

            logger.debug(
                "Copiando %d permissões do canal gerador '%s'",
                len(parent_channel.overwrites),
                parent_channel.name,
            )

            # Cria DTO de criação com TODAS as configurações
            create_dto = CreateChannelDTO(
                name=f"{parent_channel.name} - {member.display_name}",
                channel_type=ChannelType.VOICE,
                guild_id=member.guild.id,
                category_id=after.channel.category.id,
                member_id=member.id,
                is_temporary=True,
                user_limit=parent_channel.user_limit,
                bitrate=parent_channel.bitrate,
                overwrites=overwrites,  # Passa permissões clonadas + dono
            )

            logger.info(
                "? Criando sala temporária '%s' para %s (clone completo)",
                create_dto.name,
                member.display_name,
            )

            # Executa criação
            result = await self.create_channel_use_case.execute(create_dto)

            if result.id > 0:
                # Envia embed com controles ANTES de mover (evita duplicatas)
                # Boa Prática: Envia embed APENAS se sala foi CRIADA
                # (result.created = True)
                new_channel = member.guild.get_channel(result.id)

                if new_channel and isinstance(new_channel, discord.VoiceChannel):
                    # ? Verifica se sala foi REALMENTE criada nesta chamada
                    if result.created:
                        try:
                            # Cria embed informativa
                            embed = create_temp_room_embed(new_channel, member)

                            # Cria view com botões de controle
                            view = TempRoomControlView(
                                voice_channel=new_channel,
                                owner_id=member.id,
                                timeout=None,  # View nunca expira
                            )

                            # Envia diretamente no canal de voz
                            # (como mensagem inicial)
                            await new_channel.send(
                                content=(
                                    f"{member.mention} Bem-vindo à sua sala temporária!"
                                ),
                                embed=embed,
                                view=view,
                            )

                            logger.info(
                                "Embed de controle enviada APENAS na criação "
                                "| canal_voz=%s",
                                new_channel.name,
                            )

                        except (
                            discord.HTTPException,
                            discord.Forbidden,
                        ):
                            logger.exception(
                                "Erro ao enviar embed de controle",
                            )
                            # Não falha a criação da sala se embed der erro
                    else:
                        logger.debug(
                            "Sala já existia, embed NÂO enviada | canal=%s",
                            new_channel.name,
                        )

                    # Move usuário para sala (depois da embed)
                    await member.move_to(new_channel)
                    logger.info(
                        "%s movido para sala '%s' (ID: %s)",
                        member.display_name,
                        new_channel.name,
                        new_channel.id,
                    )

                else:
                    logger.error("Canal ID %s não encontrado", result.id)
            else:
                logger.error("Falha ao criar sala para %s", member.display_name)

        except (discord.HTTPException, RuntimeError):
            logger.exception("Erro ao criar sala temporária")
            return False
        else:
            return True

    async def _handle_channel_exit(
        self,
        member: discord.Member,
        before: discord.VoiceState,
    ) -> bool:
        """
        Processa saída de canal de voz.
        Remove sala temporária se ficou vazia após 3 segundos.
        """
        if not before.channel:
            return False

        logger.debug(
            "%s saiu do canal '%s' (ID: %s)",
            member.display_name,
            before.channel.name,
            before.channel.id,
        )

        # Verifica se é sala temporária
        is_temp_channel = await self.channel_repository.is_temporary_channel(
            channel_id=before.channel.id,
            guild_id=member.guild.id,
        )

        if not is_temp_channel:
            logger.debug("Canal '%s' não é temporário, ignorando", before.channel.name)
            return False

        # Verifica se está vazio
        channel_is_empty = len(before.channel.members) == 0

        if not channel_is_empty:
            logger.debug(
                "Sala temporária '%s' ainda tem %d membros",
                before.channel.name,
                len(before.channel.members),
            )
            return False

        # Sala está vazia ? Aguarda 3s antes de deletar
        logger.info(
            "Sala temporária '%s' ficou vazia. Aguardando 3s antes de deletar...",
            before.channel.name,
        )

        await asyncio.sleep(3)

        # Verifica novamente após aguardar
        try:
            channel_check = member.guild.get_channel(before.channel.id)

            if channel_check is None:
                logger.debug("Canal '%s' já foi removido", before.channel.name)
                return True

            if len(channel_check.members) > 0:
                logger.debug(
                    "Canal '%s' não está mais vazio (%d membros), mantendo",
                    channel_check.name,
                    len(channel_check.members),
                )
                return True

            # Confirma vazio ? Deleta
            logger.info("Confirmado vazio após 3s. Deletando: '%s'", channel_check.name)

            # Marca no banco como inativo
            await self._remove_temp_channel_from_database(
                channel_id=channel_check.id,
                channel_name=channel_check.name,
                category_name=channel_check.category.name
                if channel_check.category
                else "",
            )

            # Remove do Discord
            await channel_check.delete(
                reason=f"Sala temporária vazia - último usuário: {member.display_name}",
            )

            logger.info("Sala temporária '%s' removida com sucesso", channel_check.name)

        except (discord.HTTPException, discord.Forbidden):
            logger.exception(
                "Erro ao deletar canal '%s'",
                before.channel.name,
            )
            return False
        else:
            return True

    # ---------------------------------------------------------------
    # GERENCIAMENTO DE CATEGORIAS GERADORAS
    # ---------------------------------------------------------------

    async def handle_mark_category_as_temp_generator(
        self,
        category: discord.CategoryChannel,
        guild_id: int,
    ) -> bool:
        """
        Marca categoria como geradora de salas temporárias.
        Quando alguém entrar em canal dessa categoria, cria sala temporária.
        """
        try:
            logger.info("Marcando categoria '%s' como geradora", category.name)

            # Verifica se já está marcada
            is_already_marked = await self.channel_repository.is_temp_room_category(
                category_id=category.id,
                guild_id=guild_id,
            )

            if is_already_marked:
                logger.warning("Categoria '%s' já está marcada", category.name)
                return False

            # Marca categoria
            success = await self.channel_repository.mark_category_as_temp_generator(
                category_id=category.id,
                category_name=category.name,
                guild_id=guild_id,
            )

            if success:
                logger.info("Categoria '%s' marcada como geradora", category.name)
            else:
                logger.error("Falha ao marcar categoria '%s'", category.name)

        except (ValueError, OSError):
            logger.exception("Erro ao marcar categoria")
            return False
        else:
            return success

    async def handle_unmark_category_as_temp_generator(
        self,
        category_id: int,
        guild_id: int,
    ) -> bool:
        """
        Remove marcação de categoria e deleta todas salas temporárias

        Boa Prática: Operação atômica - desmarcar + limpar canais
        Python 3.13: Pattern matching para status de limpeza

        Returns:
            bool: True se categoria foi desmarcada (independente de haver canais)
        """
        try:
            logger.info("Removendo marcação de categoria ID %s", category_id)

            # Primeiro busca todos os canais temporários dessa categoria
            channel_ids = await self.channel_repository.get_temp_channels_by_category(
                category_id=category_id,
                guild_id=guild_id,
            )

            # Deleta todos os canais temporários encontrados
            deleted_count = 0
            if channel_ids:
                logger.info(
                    "Deletando %d canais temporários da categoria %s",
                    len(channel_ids),
                    category_id,
                )

                for channel_id in channel_ids:
                    try:
                        # Deleta canal do Discord
                        success = await self.channel_repository.delete_channel(
                            channel_id=channel_id,
                        )

                        if success:
                            deleted_count += 1
                            logger.debug("Canal %s deletado", channel_id)
                        else:
                            logger.warning(
                                "Canal %s não encontrado no Discord",
                                channel_id,
                            )

                    except (discord.HTTPException, discord.Forbidden):
                        logger.exception(
                            "Erro ao deletar canal %s",
                            channel_id,
                        )

                # Log do resultado da limpeza com pattern matching
                match deleted_count:
                    case 0:
                        logger.warning("Nenhum canal foi deletado")
                    case count if count == len(channel_ids):
                        logger.info("Todos os %d canais deletados com sucesso!", count)
                    case count:
                        logger.warning(
                            "Apenas %d de %d canais foram deletados",
                            count,
                            len(channel_ids),
                        )
            else:
                logger.info("Nenhum canal temporário encontrado na categoria")

            # Remove marcação da categoria (independente dos canais)
            success = await self.channel_repository.unmark_category_as_temp_generator(
                category_id=category_id,
                guild_id=guild_id,
            )

            if success:
                logger.info(
                    "Categoria ID %s desmarcada | Canais deletados: %d/%d",
                    category_id,
                    deleted_count,
                    len(channel_ids),
                )
            else:
                logger.warning("Categoria ID %s não estava marcada", category_id)

        except (ValueError, OSError):
            logger.exception("Erro ao desmarcar categoria")
            return False
        else:
            return success

    # ---------------------------------------------------------------
    # GERENCIAMENTO DE FÓRUNS ÚNICOS POR MEMBRO
    # ---------------------------------------------------------------

    async def handle_mark_category_as_unique_generator(
        self,
        category: discord.CategoryChannel,
        guild_id: int,
    ) -> bool:
        """
        Marca categoria como geradora de fóruns únicos por membro.

        Quando membro entra no servidor, cria UM fórum privado nesta categoria
        Sistema inteligente evita duplicatas

        Returns:
            bool: True se categoria foi marcada com sucesso
        """
        try:
            logger.info("Marcando categoria '%s' para fóruns únicos", category.name)

            # Marca categoria no banco de dados
            success = await self.channel_repository.mark_category_as_unique_generator(
                category_id=category.id,
                category_name=category.name,
                guild_id=guild_id,
            )

            if success:
                logger.info("Categoria '%s' marcada para fóruns únicos", category.name)
            else:
                logger.warning("Categoria '%s' já estava marcada", category.name)

        except Exception:
            logger.exception("Erro ao marcar categoria para fóruns únicos")
            return False
        else:
            return success

    async def handle_unmark_category_as_unique_generator(
        self,
        category_id: int,
        guild_id: int,
    ) -> bool:
        """
        Remove marcação de categoria como geradora de fóruns únicos.

        Remove apenas configuração, mantém canais existentes

        Returns:
            bool: True se categoria foi desmarcada
        """
        try:
            logger.info("Removendo marcação de categoria ID %s", category_id)

            # Remove marcação do banco
            success = await self.channel_repository.unmark_category_as_unique_generator(
                category_id=category_id,
                guild_id=guild_id,
            )

            if success:
                logger.info("Categoria ID %s desmarcada", category_id)
            else:
                logger.warning("Categoria ID %s não estava marcada", category_id)

        except (ValueError, OSError):
            logger.exception("Erro ao desmarcar categoria")
            return False
        else:
            return success

    async def handle_create_unique_member_channel(
        self,
        member: discord.Member,
        category_id: int,
    ) -> bool:
        """
        Cria fórum privado único para membro em categoria específica.

        Boa Prática: Verifica duplicatas ANTES de criar
        Sistema inteligente evita múltiplos canais na mesma categoria

        Fluxo:
        1. Verifica se membro JÁ tem canal nesta categoria
        2. Se JÁ tem: ignora criação (retorna True silenciosamente)
        3. Se NÃO tem: cria fórum privado único
        4. Registra relacionamento no banco de dados

        Args:
            member: Membro que receberá o fórum
            category_id: ID da categoria configurada

        Returns:
            bool: True se canal foi criado ou já existe
        """
        try:
            # CHECK 1: Membro já tem canal nesta categoria?
            already_has_channel = (
                await self.channel_repository.member_has_unique_channel_in_category(
                    member_id=member.id,
                    category_id=category_id,
                    guild_id=member.guild.id,
                )
            )

            if already_has_channel:
                logger.info(
                    "IGNORADO: Membro %s já tem canal único na categoria %s",
                    member.display_name,
                    category_id,
                )
                return True  # Não é erro, apenas já existe

            # Cria fórum privado único
            logger.info(
                "Criando fórum único para %s na categoria %s",
                member.display_name,
                category_id,
            )

            forum_name = f"- {member.display_name.lower()}"

            # Chama repository para criar fórum
            forum_channel = await self.channel_repository.create_private_forum_channel(
                name=forum_name,
                guild_id=member.guild.id,
                member_id=member.id,
                category_id=category_id,
            )

            # Registra no banco de dados
            registered = await self.channel_repository.register_member_unique_channel(
                member_id=member.id,
                channel_id=forum_channel.id,
                channel_name=forum_channel.name,
                guild_id=member.guild.id,
                category_id=category_id,
            )

            if registered:
                logger.info(
                    "Fórum único criado e registrado | member=%s | "
                    "channel=%s | category=%s",
                    member.display_name,
                    forum_channel.name,
                    category_id,
                )

                # Envia mensagem de boas-vindas no fórum
                try:
                    await forum_channel.create_thread(
                        name="Bem-vindo ao seu espaço único!",
                        content=(
                            f"## Olá, {member.mention}!\n\n"
                            f"Este é o seu **fórum privado único**! 🎉\n\n"
                            f"### Características especiais:\n"
                            f"- 🔒 **Totalmente privado**: Apenas você pode ver!\n"
                            f"- ✏️ **Personalizável**: Edite nome, descrição\n"
                            f"- 🗂️ **Organize suas ideias**: Crie posts privados\n"
                            f"- 🔧 **Controle total**: Gerencie mensagens\n"
                            f"- 🌟 **Único**: Seu ÚNICO fórum nesta categoria!\n\n"
                            f"**Aproveite seu espaço pessoal!** 🎊"
                        ),
                    )
                    logger.debug("Thread de boas-vindas criada")
                except (
                    discord.HTTPException,
                    discord.Forbidden,
                    discord.InvalidArgument,
                ) as thread_error:
                    logger.warning(
                        "Não foi possível criar thread de boas-vindas: %s",
                        str(thread_error),
                    )

            else:
                logger.error(
                    "Fórum criado mas não foi registrado no banco",
                )
                return False

        except Exception:
            logger.exception(
                "Erro ao criar fórum único para %s",
                member.display_name,
            )
            return False
        else:
            return True

    # ---------------------------------------------------------------
    # LIMPEZA E MANUTENÇÃO
    # ---------------------------------------------------------------

    async def _remove_temp_channel_from_database(
        self,
        channel_id: int,
        channel_name: str = "",
        category_name: str = "",
    ) -> bool:
        """Marca canal temporário como inativo no banco de dados."""
        import aiosqlite

        try:
            db_path = DB_PATH
            async with aiosqlite.connect(db_path) as db:
                await db.execute(
                    """
                    UPDATE temporary_channels
                    SET is_active = 0, deleted_at = CURRENT_TIMESTAMP
                    WHERE channel_id = ?
                    """,
                    (channel_id,),
                )
                await db.commit()

            logger.info(
                "Canal temporário marcado como inativo | Nome: '%s' | "
                "Categoria: '%s' | ID: %s",
                channel_name or "Desconhecido",
                category_name or "Desconhecida",
                channel_id,
            )

        except Exception:
            logger.exception("Erro ao remover canal do banco")
            return False
        else:
            return True

    async def cleanup_all_temp_channels(self, guild: discord.Guild) -> int:
        """
        Remove todas as salas temporárias do servidor.
        Chamado quando bot desconecta.
        """
        import aiosqlite

        removed_count = 0

        try:
            logger.info("Iniciando limpeza de todas as salas temporárias...")

            db_path = DB_PATH
            async with aiosqlite.connect(db_path) as db:
                cursor = await db.execute(
                    """
                    SELECT channel_id, channel_name
                    FROM temporary_channels
                    WHERE guild_id = ? AND is_active = 1
                    """,
                    (guild.id,),
                )
                temp_channels = await cursor.fetchall()

                logger.info(
                    f"Encontradas {len(temp_channels)} salas temporárias ativas",
                )

                # Remove cada sala
                for channel_id, channel_name in temp_channels:
                    try:
                        channel = guild.get_channel(channel_id)
                        if channel:
                            category_name = (
                                channel.category.name
                                if channel.category
                                else "Sem categoria"
                            )
                            await channel.delete(
                                reason="Limpeza automática - Bot desconectando",
                            )
                            logger.info(
                                f"Sala removida: '{channel_name}' "
                                f"(Categoria: '{category_name}')",
                            )
                            removed_count += 1

                            await self._remove_temp_channel_from_database(
                                channel_id=channel_id,
                                channel_name=channel_name,
                                category_name=category_name,
                            )
                        else:
                            await self._remove_temp_channel_from_database(
                                channel_id=channel_id,
                                channel_name=channel_name,
                            )

                    except Exception:
                        logger.exception(f"Erro ao remover sala {channel_name}")
                        continue

            logger.info(f"Limpeza concluída! {removed_count} salas removidas")

        except Exception:
            logger.exception("Erro na limpeza geral")
            return removed_count
        else:
            return removed_count
