"""
🏗️ Repository Implementations - Infrastructure Layer
💡 Boa Prática: Implementa as interfaces do domain usando Discord.py!
"""

import logging
from typing import cast

import discord

from domain.entities import Channel, ChannelType, TextChannel, VoiceChannel
from domain.repositories import ChannelRepository

logger = logging.getLogger(__name__)


class DiscordChannelRepository(ChannelRepository):
    """
    🔗 Implementação concreta do ChannelRepository usando Discord.py
    
    💡 Boa Prática: Implementa a interface do domain usando
    a biblioteca específica (Discord.py)!
    """
    
    def __init__(self, bot: discord.Client):
        self.bot = bot
    
    async def create_text_channel(
        self,
        name: str,
        guild_id: int,
        category_id: int | None = None,
        topic: str | None = None,
    ) -> TextChannel:
        """
        💬 Cria um canal de texto no Discord
        
        💡 Boa Prática: Traduz entidades do domain para objetos Discord.py!
        """
        logger.info("💬 Criando canal de texto: %s", name)
        
        guild = self.bot.get_guild(guild_id)
        if not guild:
            raise ValueError(f"Guild não encontrada: {guild_id}")
        
        category = None
        if category_id:
            category = guild.get_channel(category_id)
            if not isinstance(category, discord.CategoryChannel):
                category = None
        
        # Cria o canal no Discord
        discord_channel = await guild.create_text_channel(
            name=name,
            category=category,
            topic=topic,
        )
        
        # Converte para entidade do domain
        return TextChannel(
            id=discord_channel.id,
            name=discord_channel.name,
            guild_id=discord_channel.guild.id,
            category_id=discord_channel.category.id if discord_channel.category else None,
            topic=discord_channel.topic,
        )
    
    async def create_voice_channel(
        self,
        name: str,
        guild_id: int,
        category_id: int | None = None,
        user_limit: int = 0,
        bitrate: int = 64000,
    ) -> VoiceChannel:
        """
        🔊 Cria um canal de voz no Discord
        
        💡 Boa Prática: Parâmetros com valores padrão sensatos!
        """
        logger.info("🔊 Criando canal de voz: %s", name)
        
        guild = self.bot.get_guild(guild_id)
        if not guild:
            raise ValueError(f"Guild não encontrada: {guild_id}")
        
        category = None
        if category_id:
            category = guild.get_channel(category_id)
            if not isinstance(category, discord.CategoryChannel):
                category = None
        
        # Cria o canal no Discord
        discord_channel = await guild.create_voice_channel(
            name=name,
            category=category,
            user_limit=user_limit,
            bitrate=bitrate,
        )
        
        # Converte para entidade do domain
        return VoiceChannel(
            id=discord_channel.id,
            name=discord_channel.name,
            guild_id=discord_channel.guild.id,
            category_id=discord_channel.category.id if discord_channel.category else None,
            user_limit=discord_channel.user_limit,
            bitrate=discord_channel.bitrate,
        )
    
    async def get_channel_by_id(self, channel_id: int) -> Channel | None:
        """
        🔍 Busca canal por ID
        
        💡 Boa Prática: Conversão segura para entidades do domain!
        """
        discord_channel = self.bot.get_channel(channel_id)
        if not discord_channel:
            return None
        
        # Converte para entidade do domain baseado no tipo
        if isinstance(discord_channel, discord.TextChannel):
            return TextChannel(
                id=discord_channel.id,
                name=discord_channel.name,
                guild_id=discord_channel.guild.id,
                category_id=discord_channel.category.id if discord_channel.category else None,
                topic=discord_channel.topic,
            )
        elif isinstance(discord_channel, discord.VoiceChannel):
            return VoiceChannel(
                id=discord_channel.id,
                name=discord_channel.name,
                guild_id=discord_channel.guild.id,
                category_id=discord_channel.category.id if discord_channel.category else None,
                user_limit=discord_channel.user_limit,
                bitrate=discord_channel.bitrate,
            )
        
        # Tipo de canal não suportado
        return None
    
    async def delete_channel(self, channel_id: int) -> bool:
        """
        🗑️ Remove um canal
        
        💡 Boa Prática: Tratamento de erros e retorno claro!
        """
        try:
            discord_channel = self.bot.get_channel(channel_id)
            if not discord_channel:
                return False
            
            await discord_channel.delete()
            logger.info("🗑️ Canal removido: %s", discord_channel.name)
            return True
        
        except discord.Forbidden:
            logger.warning("❌ Sem permissão para deletar canal: %s", channel_id)
            return False
        except discord.NotFound:
            logger.warning("❌ Canal não encontrado: %s", channel_id)
            return False
        except Exception:
            logger.exception("❌ Erro ao deletar canal: %s", channel_id)
            return False
    
    async def list_channels_by_guild(self, guild_id: int) -> list[Channel]:
        """
        📋 Lista todos os canais de um servidor
        
        💡 Boa Prática: Conversão em lote com tratamento de erros!
        """
        guild = self.bot.get_guild(guild_id)
        if not guild:
            return []
        
        channels: list[Channel] = []
        
        for discord_channel in guild.channels:
            if isinstance(discord_channel, discord.TextChannel):
                channels.append(TextChannel(
                    id=discord_channel.id,
                    name=discord_channel.name,
                    guild_id=discord_channel.guild.id,
                    category_id=discord_channel.category.id if discord_channel.category else None,
                    topic=discord_channel.topic,
                ))
            elif isinstance(discord_channel, discord.VoiceChannel):
                channels.append(VoiceChannel(
                    id=discord_channel.id,
                    name=discord_channel.name,
                    guild_id=discord_channel.guild.id,
                    category_id=discord_channel.category.id if discord_channel.category else None,
                    user_limit=discord_channel.user_limit,
                    bitrate=discord_channel.bitrate,
                ))
        
        return channels
