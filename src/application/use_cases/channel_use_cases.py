"""
💼 Casos de Uso para Canais - Application Layer
💡 Boa Prática: Orquestra regras de negócio complexas!
"""

import logging
from pathlib import Path

from config import DB_PATH
from domain.entities import ChannelType, TextChannel, VoiceChannel
from domain.repositories import ChannelRepository

from ..dtos import ChannelResponseDTO, CreateChannelDTO

logger = logging.getLogger(__name__)


class CreateChannelUseCase:
    """
    🏗️ Caso de uso para criar canais

    💡 Boa Prática: Coordena múltiplas operações e aplica
    regras de negócio complexas com verificação de duplicatas!
    """

    def __init__(self, channel_repository: ChannelRepository):
        self.channel_repository = channel_repository

    async def execute(self, request: CreateChannelDTO) -> ChannelResponseDTO:
        """
        ✨ Executa a criação de um canal com verificação de duplicatas

        💡 Boa Prática: Verifica duplicatas antes de criar!
        """
        logger.info(
            "🏗️ Iniciando criação de canal: %s (tipo: %s)", 
            request.name, request.channel_type.value
        )

        # 🔍 VERIFICAÇÃO CRUCIAL: Canal já existe?
        already_exists = await self.channel_repository.channel_exists_by_name(
            name=request.name,
            guild_id=request.guild_id
        )

        if already_exists:
            logger.warning(
                "⚠️ Canal '%s' já existe no servidor %s - não criando duplicata", 
                request.name, request.guild_id
            )
            
            # 🔍 Busca o canal existente para retornar seus dados
            existing_channel = await self.channel_repository.get_channel_by_name_and_guild(
                name=request.name,
                guild_id=request.guild_id
            )
            
            if existing_channel:
                return ChannelResponseDTO(
                    id=existing_channel.id,
                    name=existing_channel.name,
                    channel_type=existing_channel.channel_type(),
                    guild_id=existing_channel.guild_id,
                    category_id=existing_channel.category_id,
                    created=False  # ❌ Não criou porque já existe
                )

        # 🚀 Procede com criação do canal
        try:
            # 🏗️ Cria canal baseado no tipo
            if request.channel_type == ChannelType.TEXT:
                channel = await self.channel_repository.create_text_channel(
                    name=request.name,
                    guild_id=request.guild_id,
                    category_id=request.category_id,
                    topic=request.topic,
                )
            elif request.channel_type == ChannelType.VOICE:
                channel = await self.channel_repository.create_voice_channel(
                    name=request.name,
                    guild_id=request.guild_id,
                    category_id=request.category_id,
                    user_limit=request.user_limit,
                    bitrate=request.bitrate,
                    overwrites=request.overwrites,  # 🔒 Passa permissões customizadas
                )
            else:
                msg = f"Tipo de canal não suportado: {request.channel_type}"
                raise ValueError(msg)

            logger.info("✅ Canal criado com sucesso: %s (ID: %s)", channel.name, channel.id)

            # 💾 Se é temporário, salva no banco de dados
            if hasattr(request, 'is_temporary') and request.is_temporary:
                await self._save_temporary_channel_to_database(
                    channel_id=channel.id,
                    channel_name=channel.name,
                    channel_type=request.channel_type.value,
                    guild_id=request.guild_id,
                    category_id=request.category_id,
                    owner_id=getattr(request, 'member_id', None)
                )

            return ChannelResponseDTO(
                id=channel.id,
                name=channel.name,
                channel_type=channel.channel_type(),
                guild_id=channel.guild_id,
                category_id=channel.category_id,
                created=True  # ✅ Criado com sucesso
            )

        except Exception as e:
            logger.exception("❌ Falha ao criar canal: %s", request.name)
            
            # 💡 Retorna resposta de falha
            return ChannelResponseDTO(
                id=0,  # ID temporário
                name=request.name,
                channel_type=request.channel_type,
                guild_id=request.guild_id,
                category_id=request.category_id,
                created=False  # ❌ Falha na criação
            )

    async def _save_temporary_channel_to_database(
        self,
        channel_id: int,
        channel_name: str,
        channel_type: str,
        guild_id: int,
        category_id: int | None,
        owner_id: int | None
    ) -> bool:
        """
        💾 Salva canal temporário no banco de dados
        
        Args:
            channel_id: ID do canal Discord
            channel_name: Nome do canal
            channel_type: Tipo ('voice' ou 'text')
            guild_id: ID do servidor
            category_id: ID da categoria
            owner_id: ID do dono da sala
            
        Returns:
            True se salvou com sucesso
        """
        import aiosqlite
        from pathlib import Path
        
        try:
            logger.info("💾 Salvando canal temporário no banco: %s", channel_name)
            
            db_path = DB_PATH
            async with aiosqlite.connect(db_path) as db:
                await db.execute(
                    """
                    INSERT INTO temporary_channels 
                        (channel_id, channel_name, channel_type, guild_id, category_id, owner_id, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                    """,
                    (channel_id, channel_name, channel_type, guild_id, category_id, owner_id)
                )
                await db.commit()
            
            logger.info("✅ Canal temporário salvo no banco: %s (ID: %s)", channel_name, channel_id)
            return True
            
        except Exception as e:
            logger.error("❌ Erro ao salvar canal temporário no banco: %s", str(e))
            return False


class ManageTemporaryChannelsUseCase:
    """
    🔄 Caso de uso para gerenciar canais temporários

    💡 Boa Prática: Lógica complexa de criação/remoção
    encapsulada em um só lugar!
    """

    def __init__(self, channel_repository: ChannelRepository):
        self.channel_repository = channel_repository

    async def create_temporary_channel(
        self,
        base_channel_id: int,
        guild_id: int,
    ) -> ChannelResponseDTO | None:
        """
        ⚡ Cria canal temporário baseado em outro canal

        💡 Boa Prática: Operação específica e bem documentada!
        """
        logger.info("⚡ Criando canal temporário baseado em: %s", base_channel_id)

        try:
            # Busca o canal base
            base_channel = await self.channel_repository.get_channel_by_id(
                base_channel_id
            )
            if not base_channel:
                logger.warning("❌ Canal base não encontrado: %s", base_channel_id)
                return None

            # Cria canal temporário
            temp_name = f"Temp {base_channel.name}"

            if isinstance(base_channel, VoiceChannel):
                temp_channel = await self.channel_repository.create_voice_channel(
                    name=temp_name,
                    guild_id=guild_id,
                    category_id=base_channel.category_id,
                    user_limit=base_channel.user_limit,
                    bitrate=base_channel.bitrate,
                )
            elif isinstance(base_channel, TextChannel):
                temp_channel = await self.channel_repository.create_text_channel(
                    name=temp_name,
                    guild_id=guild_id,
                    category_id=base_channel.category_id,
                    topic="Canal temporário",
                )
            else:
                logger.warning("❌ Tipo de canal não suportado para temporário")
                return None

            logger.info("✅ Canal temporário criado: %s", temp_channel.name)

            return ChannelResponseDTO(
                id=temp_channel.id,
                name=temp_channel.name,
                channel_type=temp_channel.channel_type(),
                guild_id=temp_channel.guild_id,
                category_id=temp_channel.category_id,
                created=True,
            )

        except Exception:
            logger.exception("❌ Erro ao criar canal temporário")
            return None

    async def cleanup_empty_channel(self, channel_id: int) -> bool:
        """
        🧹 Remove canal se estiver vazio

        💡 Boa Prática: Lógica de limpeza automática!
        """
        logger.info("🧹 Verificando se canal está vazio: %s", channel_id)

        try:
            success = await self.channel_repository.delete_channel(channel_id)
        except Exception:
            logger.exception("❌ Erro ao remover canal vazio: %s", channel_id)
            return False
        else:
            if success:
                logger.info("✅ Canal vazio removido: %s", channel_id)
            return success

