"""
?? Channel Controller - Presentation Layer
Coordena eventos Discord com casos de uso da aplica��o.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import TYPE_CHECKING

import discord

if TYPE_CHECKING:
    from infrastructure.repositories import DiscordChannelRepository

from application.dtos import CreateChannelDTO
from application.use_cases import CreateChannelUseCase
from config import DB_PATH
from domain.entities import ChannelType
from presentation.views import TempRoomControlView, create_temp_room_embed

logger = logging.getLogger(__name__)


class ChannelController:
    """
    Controller para gerenciamento de canais Discord.
    
    Responsabilidades:
    - Criar canais de texto e voz
    - Gerenciar salas tempor�rias autom�ticas
    - Coordenar eventos de voz (entrada/sa�da)
    """

    def __init__(
        self,
        channel_repository: DiscordChannelRepository,
    ) -> None:
        """Inicializa controller."""
        self.channel_repository = channel_repository
        self.create_channel_use_case = CreateChannelUseCase(channel_repository)

    async def handle_create_text_channel(
        self,
        interaction: discord.Interaction,
        name: str,
        topic: str | None = None,
    ) -> None:
        """Cria canal de texto via comando slash."""
        logger.info("?? Processando cria��o de canal de texto: %s", name)

        if not name or not name.strip():
            await interaction.response.send_message(
                "? Nome do canal n�o pode estar vazio!",
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
                            f"?? Canal **{result.name}** j� existe! N�o criado duplicata.",
                            ephemeral=True,
                        )
                    else:
                        await interaction.response.send_message(
                            f"? Falha ao criar canal **{name}**. Tente novamente.",
                            ephemeral=True,
                        )

        except Exception as e:
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
        logger.info("?? Processando cria��o de canal de voz: %s", name)

        if not name or not name.strip():
            await interaction.response.send_message(
                "? Nome do canal n�o pode estar vazio!",
                ephemeral=True,
            )
            return

        # Valida��o do limite de usu�rios
        match user_limit:
            case x if x < 0:
                await interaction.response.send_message(
                    "? Limite de usu�rios n�o pode ser negativo!",
                    ephemeral=True,
                )
                return
            case x if x > 99:
                await interaction.response.send_message(
                    "? Limite m�ximo � 99 usu�rios!",
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
                            f"?? Canal **{result.name}** j� existe! N�o criado duplicata.",
                            ephemeral=True,
                        )
                    else:
                        await interaction.response.send_message(
                            f"? Falha ao criar canal **{name}**. Tente novamente.",
                            ephemeral=True,
                        )

        except Exception as e:
            logger.exception("? Erro inesperado ao criar canal de voz: %s", name)
            await interaction.response.send_message(
                "? Erro interno do servidor. Tente novamente em alguns minutos.",
                ephemeral=True,
            )

    async def handle_create_member_text_channel(
        self, 
        member: discord.Member, 
        category_id: int | None = None
    ) -> bool:
        """
        ?? Cria f�rum privado para novo membro
        
        ?? Boa Pr�tica: F�rum totalmente privado onde membro tem controle total!
        ?? Permiss�es: Apenas o membro pode ver, editar e gerenciar
        
        Funcionalidades:
        - ? Canal vis�vel apenas para o membro
        - ? Pode modificar nome do canal
        - ? Pode gerenciar mensagens (deletar, editar)
        - ? Pode criar threads privadas (posts privados)
        - ? N�O pode criar threads p�blicas
        - ? Threads criadas herdam as mesmas permiss�es do f�rum
        
        Args:
            member: Membro que receber� o f�rum privado
            category_id: ID da categoria (opcional)
            
        Returns:
            bool: True se f�rum foi criado com sucesso
        """
        try:
            logger.info("?? Criando f�rum privado para %s", member.display_name)

            # ??? Gera nome do f�rum baseado no membro
            forum_name = f"??-{member.display_name.lower()}"
            
            # ?? Chama repository para criar f�rum com permiss�es especiais
            forum_channel = await self.channel_repository.create_private_forum_channel(
                name=forum_name,
                guild_id=member.guild.id,
                member_id=member.id,
                category_id=category_id,
            )
            
            # ?? Envia mensagem de boas-vindas no f�rum
            try:
                # Cria thread inicial com instru��es
                welcome_thread = await forum_channel.create_thread(
                    name="?? Bem-vindo ao seu f�rum!",
                    content=(
                        f"## ?? Ol�, {member.mention}!\n\n"
                        f"Este � o seu **f�rum privado pessoal**! ??\n\n"
                        f"### ? O que voc� pode fazer aqui:\n"
                        f"- ? **Criar threads privadas**: Clique em 'Nova Postagem' para criar t�picos privados\n"
                        f"- ?? **Editar o nome**: Clique com bot�o direito no canal ? 'Editar Canal'\n"
                        f"- ??? **Gerenciar mensagens**: Delete ou edite qualquer mensagem\n"
                        f"- ? **Privacidade total**: Apenas voc� pode ver este canal e seus posts!\n"
                        f"- ?? **Personalizar**: Mude o nome, descri��o, tags e tudo mais!\n\n"
                        f"### ?? Dicas:\n"
                        f"- Use tags para organizar seus t�picos\n"
                        f"- Threads s�o arquivadas automaticamente ap�s 7 dias de inatividade\n"
                        f"- Voc� tem controle total sobre este espa�o! ??\n"
                        f"- ?? **Importante**: Voc� s� pode criar posts PRIVADOS (n�o p�blicos)\n\n"
                        f"**Divirta-se organizando suas ideias!** ?"
                    ),
                )
                
                logger.info(
                    "? Thread de boas-vindas criada | thread=%s",
                    welcome_thread.thread.name
                )
                
            except Exception as thread_error:
                logger.warning(
                    "?? N�o foi poss�vel criar thread de boas-vindas: %s",
                    str(thread_error)
                )
            
            logger.info(
                "? F�rum privado criado | member=%s | forum=%s | id=%s",
                member.display_name,
                forum_channel.name,
                forum_channel.id
            )
            
            return True
            
        except Exception as e:
            logger.exception(
                "? Erro ao criar f�rum para membro %s: %s",
                member.display_name,
                str(e)
            )
            return False

    # ---------------------------------------------------------------
    # ?? GERENCIAMENTO DE SALAS TEMPOR�RIAS
    # ---------------------------------------------------------------

    async def handle_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState
    ) -> bool:
        """
        Ponto de entrada principal para eventos de voz.
        
        Fluxo:
        - Entrada em canal ? Cria sala tempor�ria se categoria for geradora
        - Sa�da de canal ? Remove sala se ficou vazia
        """
        try:
            # Entrada em novo canal
            if after.channel and after.channel.category and before.channel != after.channel:
                logger.debug(
                    "?? ENTRADA: %s ? '%s'",
                    member.display_name,
                    after.channel.name
                )
                await self._handle_channel_entry(member, after)

            # Sa�da de canal
            if before.channel and before.channel != after.channel:
                logger.debug(
                    "? SA�DA: %s ? '%s'",
                    member.display_name,
                    before.channel.name
                )
                await self._handle_channel_exit(member, before)

            return True

        except Exception as e:
            logger.error("? Erro em handle_voice_state_update: %s", str(e))
            return False

    async def _handle_channel_entry(
        self,
        member: discord.Member,
        after: discord.VoiceState
    ) -> bool:
        """
        Processa entrada em canal de voz.
        
        Verifica:
        1. Se j� est� em sala tempor�ria ? Ignora
        2. Se categoria � geradora ? Cria sala tempor�ria
        """
        if not after.channel:
            return False

        logger.info(
            "? SOLICITA��O: %s entrou no canal '%s' (ID: %s)",
            member.display_name,
            after.channel.name,
            after.channel.id
        )

        # CHECK 1: J� est� em sala tempor�ria?
        is_temp_channel = await self.channel_repository.is_temporary_channel(
            channel_id=after.channel.id,
            guild_id=member.guild.id
        )

        if is_temp_channel:
            logger.info(
                "?? IGNORADO: %s entrou em sala tempor�ria existente",
                member.display_name
            )
            return True

        # CHECK 2: Categoria � geradora?
        if not after.channel.category:
            logger.debug("?? IGNORADO: Canal sem categoria")
            return False

        is_generator_category = await self.channel_repository.is_temp_room_category(
            category_id=after.channel.category.id,
            guild_id=member.guild.id,
            category_name=after.channel.category.name
        )

        if not is_generator_category:
            logger.info(
                "?? IGNORADO: Categoria '%s' n�o � geradora",
                after.channel.category.name
            )
            return False

        # Categoria � geradora ? Cria sala tempor�ria
        logger.info(
            "?? ACEITO: Criando sala tempor�ria para %s",
            member.display_name
        )
        return await self._create_temporary_room(member, after)

    async def _create_temporary_room(
        self,
        member: discord.Member,
        after: discord.VoiceState
    ) -> bool:
        """
        Cria sala tempor�ria para o membro.
        
        ?? Boa Pr�tica: Clona TODAS as configura��es do canal gerador!
        ?? Inclui: nome, limite, bitrate E permiss�es de roles
        """
        try:
            parent_channel = after.channel
            
            # ?? Copia as permiss�es (overwrites) do canal gerador
            # ?? Isso garante que roles como "tecno" tenham as mesmas permiss�es
            overwrites = parent_channel.overwrites.copy()
            
            # ? Adiciona permiss�es especiais para o dono da sala
            overwrites[member] = discord.PermissionOverwrite(
                connect=True,
                speak=True,
                stream=True,
                manage_channels=True,  # ?? Pode editar configura��es da sala
            )
            
            logger.debug(
                "?? Copiando %d permiss�es do canal gerador '%s'",
                len(parent_channel.overwrites),
                parent_channel.name
            )
            
            # Cria DTO de cria��o com TODAS as configura��es
            create_dto = CreateChannelDTO(
                name=f"{parent_channel.name} - {member.display_name}",
                channel_type=ChannelType.VOICE,
                guild_id=member.guild.id,
                category_id=after.channel.category.id,
                member_id=member.id,
                is_temporary=True,
                user_limit=parent_channel.user_limit,
                bitrate=parent_channel.bitrate,
                overwrites=overwrites,  # ?? Passa permiss�es clonadas + dono
            )

            logger.info(
                "? Criando sala tempor�ria '%s' para %s (clone completo)",
                create_dto.name,
                member.display_name
            )

            # Executa cria��o
            result = await self.create_channel_use_case.execute(create_dto)

            if result.id > 0:
                # ?? Envia embed com controles ANTES de mover (evita duplicatas)
                # ?? Boa Pr�tica: Envia embed APENAS se sala foi CRIADA (result.created = True)
                new_channel = member.guild.get_channel(result.id)
                
                if new_channel and isinstance(new_channel, discord.VoiceChannel):
                    # ? Verifica se sala foi REALMENTE criada nesta chamada
                    if result.created:
                        try:
                            # Cria embed informativa
                            embed = create_temp_room_embed(new_channel, member)
                            
                            # Cria view com bot�es de controle
                            view = TempRoomControlView(
                                voice_channel=new_channel,
                                owner_id=member.id,
                                timeout=None  # View nunca expira
                            )
                            
                            # ?? Envia diretamente no canal de voz (como mensagem inicial)
                            await new_channel.send(
                                content=f"?? {member.mention} Bem-vindo � sua sala tempor�ria!",
                                embed=embed,
                                view=view
                            )
                            
                            logger.info(
                                "?? Embed de controle enviada APENAS na cria��o | canal_voz=%s",
                                new_channel.name
                            )
                        
                        except Exception as embed_error:
                            logger.error(
                                "? Erro ao enviar embed de controle: %s",
                                str(embed_error)
                            )
                            # N�o falha a cria��o da sala se embed der erro
                    else:
                        logger.debug(
                            "?? Sala j� existia, embed N�O enviada | canal=%s",
                            new_channel.name
                        )
                    
                    # ?? Move usu�rio para sala (depois da embed)
                    await member.move_to(new_channel)
                    logger.info(
                        "? %s movido para sala '%s' (ID: %s)",
                        member.display_name,
                        new_channel.name,
                        new_channel.id
                    )
                    
                    return True
                else:
                    logger.error("? Canal ID %s n�o encontrado", result.id)
                    return False
            else:
                logger.error("? Falha ao criar sala para %s", member.display_name)
                return False

        except Exception as e:
            logger.error("? Erro ao criar sala tempor�ria: %s", str(e))
            return False

    async def _handle_channel_exit(
        self,
        member: discord.Member,
        before: discord.VoiceState
    ) -> bool:
        """
        Processa sa�da de canal de voz.
        Remove sala tempor�ria se ficou vazia ap�s 3 segundos.
        """
        if not before.channel:
            return False

        logger.debug(
            "?? %s saiu do canal '%s' (ID: %s)",
            member.display_name,
            before.channel.name,
            before.channel.id
        )

        # Verifica se � sala tempor�ria
        is_temp_channel = await self.channel_repository.is_temporary_channel(
            channel_id=before.channel.id,
            guild_id=member.guild.id
        )

        if not is_temp_channel:
            logger.debug(
                "?? Canal '%s' n�o � tempor�rio, ignorando",
                before.channel.name
            )
            return False

        # Verifica se est� vazio
        channel_is_empty = len(before.channel.members) == 0

        if not channel_is_empty:
            logger.debug(
                "?? Sala tempor�ria '%s' ainda tem %d membros",
                before.channel.name,
                len(before.channel.members)
            )
            return False

        # Sala est� vazia ? Aguarda 3s antes de deletar
        logger.info(
            "??? Sala tempor�ria '%s' ficou vazia. Aguardando 3s antes de deletar...",
            before.channel.name
        )

        await asyncio.sleep(3)

        # Verifica novamente ap�s aguardar
        try:
            channel_check = member.guild.get_channel(before.channel.id)

            if channel_check is None:
                logger.debug(
                    "?? Canal '%s' j� foi removido",
                    before.channel.name
                )
                return True

            if len(channel_check.members) > 0:
                logger.debug(
                    "?? Canal '%s' n�o est� mais vazio (%d membros), mantendo",
                    channel_check.name,
                    len(channel_check.members)
                )
                return True

            # Confirma vazio ? Deleta
            logger.info(
                "??? Confirmado vazio ap�s 3s. Deletando: '%s'",
                channel_check.name
            )

            # Marca no banco como inativo
            await self._remove_temp_channel_from_database(
                channel_id=channel_check.id,
                channel_name=channel_check.name,
                category_name=channel_check.category.name if channel_check.category else ""
            )

            # Remove do Discord
            await channel_check.delete(
                reason=f"Sala tempor�ria vazia - �ltimo usu�rio: {member.display_name}"
            )

            logger.info(
                "? Sala tempor�ria '%s' removida com sucesso",
                channel_check.name
            )
            return True

        except Exception as delete_error:
            logger.error(
                "? Erro ao deletar canal '%s': %s",
                before.channel.name,
                str(delete_error)
            )
            return False

    # ---------------------------------------------------------------
    # ??? GERENCIAMENTO DE CATEGORIAS GERADORAS
    # ---------------------------------------------------------------

    async def handle_mark_category_as_temp_generator(
        self,
        category: discord.CategoryChannel,
        guild_id: int
    ) -> bool:
        """
        Marca categoria como geradora de salas tempor�rias.
        Quando algu�m entrar em canal dessa categoria, cria sala tempor�ria.
        """
        try:
            logger.info("??? Marcando categoria '%s' como geradora", category.name)

            # Verifica se j� est� marcada
            is_already_marked = await self.channel_repository.is_temp_room_category(
                category_id=category.id,
                guild_id=guild_id
            )

            if is_already_marked:
                logger.warning("?? Categoria '%s' j� est� marcada", category.name)
                return False

            # Marca categoria
            success = await self.channel_repository.mark_category_as_temp_generator(
                category_id=category.id,
                category_name=category.name,
                guild_id=guild_id
            )

            if success:
                logger.info("? Categoria '%s' marcada como geradora", category.name)
            else:
                logger.error("? Falha ao marcar categoria '%s'", category.name)

            return success

        except Exception as e:
            logger.error("? Erro ao marcar categoria: %s", str(e))
            return False

    async def handle_unmark_category_as_temp_generator(
        self,
        category_id: int,
        guild_id: int
    ) -> bool:
        """
        ??? Remove marca��o de categoria e deleta todas salas tempor�rias
        
        ?? Boa Pr�tica: Opera��o at�mica - desmarcar + limpar canais
        ?? Python 3.13: Pattern matching para status de limpeza
        
        Returns:
            bool: True se categoria foi desmarcada (independente de haver canais)
        """
        try:
            logger.info("??? Removendo marca��o de categoria ID %s", category_id)

            # ?? Primeiro busca todos os canais tempor�rios dessa categoria
            channel_ids = await self.channel_repository.get_temp_channels_by_category(
                category_id=category_id,
                guild_id=guild_id
            )

            # ?? Deleta todos os canais tempor�rios encontrados
            deleted_count = 0
            if channel_ids:
                logger.info(
                    "?? Deletando %d canais tempor�rios da categoria %s",
                    len(channel_ids),
                    category_id
                )
                
                for channel_id in channel_ids:
                    try:
                        # ??? Deleta canal do Discord
                        success = await self.channel_repository.delete_channel(
                            channel_id=channel_id
                        )
                        
                        if success:
                            deleted_count += 1
                            logger.debug("? Canal %s deletado", channel_id)
                        else:
                            logger.warning(
                                "?? Canal %s n�o encontrado no Discord", 
                                channel_id
                            )
                            
                    except Exception as channel_error:
                        logger.error(
                            "? Erro ao deletar canal %s: %s",
                            channel_id,
                            str(channel_error)
                        )
                
                # ?? Log do resultado da limpeza com pattern matching
                match deleted_count:
                    case 0:
                        logger.warning("?? Nenhum canal foi deletado")
                    case count if count == len(channel_ids):
                        logger.info(
                            "? Todos os %d canais deletados com sucesso!", 
                            count
                        )
                    case count:
                        logger.warning(
                            "?? Apenas %d de %d canais foram deletados",
                            count,
                            len(channel_ids)
                        )
            else:
                logger.info("?? Nenhum canal tempor�rio encontrado na categoria")

            # ??? Remove marca��o da categoria (independente dos canais)
            success = await self.channel_repository.unmark_category_as_temp_generator(
                category_id=category_id,
                guild_id=guild_id
            )

            if success:
                logger.info(
                    "? Categoria ID %s desmarcada | Canais deletados: %d/%d",
                    category_id,
                    deleted_count,
                    len(channel_ids)
                )
            else:
                logger.warning("?? Categoria ID %s n�o estava marcada", category_id)

            return success

        except Exception as e:
            logger.error("? Erro ao desmarcar categoria: %s", str(e))
            return False

    # ---------------------------------------------------------------
    # ?? GERENCIAMENTO DE F�RUNS �NICOS POR MEMBRO
    # ---------------------------------------------------------------

    async def handle_mark_category_as_unique_generator(
        self,
        category: discord.CategoryChannel,
        guild_id: int
    ) -> bool:
        """
        ?? Marca categoria como geradora de f�runs �nicos por membro.
        
        ?? Quando membro entra no servidor, cria UM f�rum privado nesta categoria
        ?? Sistema inteligente evita duplicatas
        
        Returns:
            bool: True se categoria foi marcada com sucesso
        """
        try:
            logger.info(
                "?? Marcando categoria '%s' para f�runs �nicos",
                category.name
            )

            # ?? Marca categoria no banco de dados
            success = await self.channel_repository.mark_category_as_unique_generator(
                category_id=category.id,
                category_name=category.name,
                guild_id=guild_id
            )

            if success:
                logger.info(
                    "? Categoria '%s' marcada para f�runs �nicos",
                    category.name
                )
            else:
                logger.warning(
                    "?? Categoria '%s' j� estava marcada",
                    category.name
                )

            return success

        except Exception as e:
            logger.exception(
                "? Erro ao marcar categoria para f�runs �nicos: %s",
                str(e)
            )
            return False

    async def handle_unmark_category_as_unique_generator(
        self,
        category_id: int,
        guild_id: int
    ) -> bool:
        """
        ??? Remove marca��o de categoria como geradora de f�runs �nicos.
        
        ?? Remove apenas configura��o, mant�m canais existentes
        
        Returns:
            bool: True se categoria foi desmarcada
        """
        try:
            logger.info(
                "??? Removendo marca��o de categoria ID %s",
                category_id
            )

            # ??? Remove marca��o do banco
            success = await self.channel_repository.unmark_category_as_unique_generator(
                category_id=category_id,
                guild_id=guild_id
            )

            if success:
                logger.info(
                    "? Categoria ID %s desmarcada",
                    category_id
                )
            else:
                logger.warning(
                    "?? Categoria ID %s n�o estava marcada",
                    category_id
                )

            return success

        except Exception as e:
            logger.error(
                "? Erro ao desmarcar categoria: %s",
                str(e)
            )
            return False

    async def handle_create_unique_member_channel(
        self,
        member: discord.Member,
        category_id: int
    ) -> bool:
        """
        ?? Cria f�rum privado �nico para membro em categoria espec�fica.
        
        ?? Boa Pr�tica: Verifica duplicatas ANTES de criar
        ?? Sistema inteligente evita m�ltiplos canais na mesma categoria
        
        Fluxo:
        1. Verifica se membro J� tem canal nesta categoria
        2. Se J� tem: ignora cria��o (retorna True silenciosamente)
        3. Se N�O tem: cria f�rum privado �nico
        4. Registra relacionamento no banco de dados
        
        Args:
            member: Membro que receber� o f�rum
            category_id: ID da categoria configurada
            
        Returns:
            bool: True se canal foi criado ou j� existe
        """
        try:
            # ?? CHECK 1: Membro j� tem canal nesta categoria?
            already_has_channel = await self.channel_repository.member_has_unique_channel_in_category(
                member_id=member.id,
                category_id=category_id,
                guild_id=member.guild.id
            )

            if already_has_channel:
                logger.info(
                    "?? IGNORADO: Membro %s j� tem canal �nico na categoria %s",
                    member.display_name,
                    category_id
                )
                return True  # N�o � erro, apenas j� existe

            # ??? Cria f�rum privado �nico
            logger.info(
                "?? Criando f�rum �nico para %s na categoria %s",
                member.display_name,
                category_id
            )

            forum_name = f"??-{member.display_name.lower()}"

            # ?? Chama repository para criar f�rum
            forum_channel = await self.channel_repository.create_private_forum_channel(
                name=forum_name,
                guild_id=member.guild.id,
                member_id=member.id,
                category_id=category_id
            )

            # ?? Registra no banco de dados
            registered = await self.channel_repository.register_member_unique_channel(
                member_id=member.id,
                channel_id=forum_channel.id,
                channel_name=forum_channel.name,
                guild_id=member.guild.id,
                category_id=category_id
            )

            if registered:
                logger.info(
                    "? F�rum �nico criado e registrado | member=%s | channel=%s | category=%s",
                    member.display_name,
                    forum_channel.name,
                    category_id
                )

                # ?? Envia mensagem de boas-vindas no f�rum
                try:
                    welcome_thread = await forum_channel.create_thread(
                        name="?? Bem-vindo ao seu espa�o �nico!",
                        content=(
                            f"## ?? Ol�, {member.mention}!\n\n"
                            f"Este � o seu **f�rum privado �nico**! ??\n\n"
                            f"### ? Caracter�sticas especiais:\n"
                            f"- ?? **Totalmente privado**: Apenas voc� pode ver!\n"
                            f"- ?? **Personaliz�vel**: Edite nome, descri��o e tudo mais\n"
                            f"- ?? **Organize suas ideias**: Crie posts privados\n"
                            f"- ??? **Controle total**: Gerencie todas as mensagens\n"
                            f"- ?? **�nico**: Este � seu �NICO f�rum nesta categoria!\n\n"
                            f"**Aproveite seu espa�o pessoal!** ?"
                        ),
                    )
                    logger.debug("? Thread de boas-vindas criada")
                except Exception as thread_error:
                    logger.warning(
                        "?? N�o foi poss�vel criar thread de boas-vindas: %s",
                        str(thread_error)
                    )

                return True
            else:
                logger.error(
                    "? F�rum criado mas n�o foi registrado no banco",
                )
                return False

        except Exception as e:
            logger.exception(
                "? Erro ao criar f�rum �nico para %s: %s",
                member.display_name,
                str(e)
            )
            return False

    # ---------------------------------------------------------------
    # ?? LIMPEZA E MANUTEN��O
    # ---------------------------------------------------------------

    async def _remove_temp_channel_from_database(self, channel_id: int, channel_name: str = "", category_name: str = "") -> bool:
        """Marca canal tempor�rio como inativo no banco de dados."""
        import aiosqlite
        from pathlib import Path

        try:
            db_path = DB_PATH
            async with aiosqlite.connect(db_path) as db:
                await db.execute(
                    """
                    UPDATE temporary_channels
                    SET is_active = 0, deleted_at = CURRENT_TIMESTAMP
                    WHERE channel_id = ?
                    """,
                    (channel_id,)
                )
                await db.commit()

            logger.info(
                "?? Canal tempor�rio marcado como inativo | Nome: '%s' | Categoria: '%s' | ID: %s",
                channel_name or "Desconhecido",
                category_name or "Desconhecida",
                channel_id
            )
            return True

        except Exception as e:
            logger.error("? Erro ao remover canal do banco: %s", str(e))
            return False

    async def cleanup_all_temp_channels(self, guild: discord.Guild) -> int:
        """
        Remove todas as salas tempor�rias do servidor.
        Chamado quando bot desconecta.
        """
        import aiosqlite
        from pathlib import Path

        removed_count = 0

        try:
            logger.info("?? Iniciando limpeza de todas as salas tempor�rias...")

            db_path = DB_PATH
            async with aiosqlite.connect(db_path) as db:
                cursor = await db.execute(
                    """
                    SELECT channel_id, channel_name
                    FROM temporary_channels
                    WHERE guild_id = ? AND is_active = 1
                    """,
                    (guild.id,)
                )
                temp_channels = await cursor.fetchall()

                logger.info(f"?? Encontradas {len(temp_channels)} salas tempor�rias ativas")

                # Remove cada sala
                for channel_id, channel_name in temp_channels:
                    try:
                        channel = guild.get_channel(channel_id)
                        if channel:
                            category_name = channel.category.name if channel.category else "Sem categoria"
                            await channel.delete(reason="Limpeza autom�tica - Bot desconectando")
                            logger.info(f"? Sala removida: '{channel_name}' (Categoria: '{category_name}')")
                            removed_count += 1
                            
                            await self._remove_temp_channel_from_database(
                                channel_id=channel_id,
                                channel_name=channel_name,
                                category_name=category_name
                            )
                        else:
                            await self._remove_temp_channel_from_database(
                                channel_id=channel_id,
                                channel_name=channel_name
                            )

                    except Exception as e:
                        logger.error(f"? Erro ao remover sala {channel_name}: {str(e)}")
                        continue

            logger.info(f"? Limpeza conclu�da! {removed_count} salas removidas")
            return removed_count

        except Exception as e:
            logger.error(f"? Erro na limpeza geral: {str(e)}")
            return removed_count

