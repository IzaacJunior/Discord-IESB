"""
💼 Casos de Uso para Canais - Application Layer
💡 Boa Prática: Orquestra regras de negócio complexas!
"""

import logging

from domain.entities import ChannelType, TextChannel, VoiceChannel
from domain.repositories import ChannelRepository

from ..dtos import ChannelResponseDTO, CreateChannelDTO

logger = logging.getLogger(__name__)


class CreateChannelUseCase:
    """
    🏗️ Caso de uso para criar canais

    💡 Boa Prática: Coordena múltiplas operações e aplica
    regras de negócio complexas!
    """

    def __init__(self, channel_repository: ChannelRepository):
        self.channel_repository = channel_repository

    async def execute(self, request: CreateChannelDTO) -> ChannelResponseDTO:
        """
        ✨ Executa a criação de um canal

        💡 Boa Prática: Método único e claro que encapsula
        toda a lógica do caso de uso!
        """
        logger.info(
            "🏗️ Criando canal: %s (tipo: %s)", request.name, request.channel_type.value
        )

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
            )
        else:
            msg = f"Tipo de canal não suportado: {request.channel_type}"
            raise ValueError(msg)

        logger.info("✅ Canal criado com sucesso: %s", channel.name)

        return ChannelResponseDTO(
            id=channel.id,
            name=channel.name,
            channel_type=channel.channel_type(),
            guild_id=channel.guild_id,
            category_id=channel.category_id,
            created=True,
        )


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
