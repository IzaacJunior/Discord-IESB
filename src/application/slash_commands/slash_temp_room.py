"""
🎮 Comandos Slash para Salas Temporárias
💡 Boa Prática: Comandos modernos com autocompletar para controle de salas
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

if TYPE_CHECKING:
    from discord import VoiceChannel

logger = logging.getLogger(__name__)


class TempRoomSlashCommands(commands.Cog):
    """
    🎮 Comandos slash para controlar salas temporárias.
    
    💡 Python 3.13: Type hints modernos e pattern matching
    🚀 Boa Prática: Comandos slash para melhor UX
    """
    
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
    
    async def _get_temp_room_info(
        self, 
        interaction: discord.Interaction
    ) -> tuple[VoiceChannel | None, int | None]:
        """
        🔍 Valida e retorna informações da sala temporária.
        
        Returns:
            Tupla (canal_de_voz, owner_id) ou (None, None) se inválido
        """
        # Verifica se está em um canal de voz
        if not interaction.user.voice or not interaction.user.voice.channel:
            return None, None
        
        voice_channel = interaction.user.voice.channel
        
        # Busca no banco de dados quem é o dono
        try:
            from pathlib import Path
            import aiosqlite
            
            db_path = Path("database/discord_bot.db")
            async with aiosqlite.connect(db_path) as db:
                cursor = await db.execute(
                    """
                    SELECT owner_id 
                    FROM temporary_channels 
                    WHERE channel_id = ? 
                    AND guild_id = ? 
                    AND is_active = 1
                    """,
                    (voice_channel.id, interaction.guild_id)
                )
                result = await cursor.fetchone()
                
                if result:
                    return voice_channel, result[0]
                
        except Exception as e:
            logger.error("❌ Erro ao buscar dono da sala: %s", str(e))
        
        return None, None
    
    @app_commands.command(
        name="sala-adicionar",
        description="🎯 Adiciona alguém à sua sala temporária privada"
    )
    @app_commands.describe(
        usuario="Usuário que você quer adicionar à sala"
    )
    async def add_to_room(
        self,
        interaction: discord.Interaction,
        usuario: discord.Member
    ) -> None:
        """
        👁️ Adiciona usuário específico à sala temporária.
        
        💡 Vantagem: Discord faz autocompletar automático!
        🎯 Python 3.13: Type hints modernos
        """
        # Valida se está em sala temporária
        voice_channel, owner_id = await self._get_temp_room_info(interaction)
        
        if not voice_channel:
            await interaction.response.send_message(
                "❌ Você precisa estar em uma **sala temporária** para usar este comando!",
                ephemeral=True
            )
            return
        
        # Valida se é o dono
        if owner_id != interaction.user.id:
            await interaction.response.send_message(
                "❌ Apenas o **dono da sala** pode adicionar pessoas!",
                ephemeral=True
            )
            return
        
        # Verifica se não está adicionando a si mesmo
        if usuario.id == interaction.user.id:
            await interaction.response.send_message(
                "😅 Você já está na sala! Não precisa se adicionar.",
                ephemeral=True
            )
            return
        
        # Verifica se não é bot
        if usuario.bot:
            await interaction.response.send_message(
                "🤖 Não é possível adicionar bots à sala!",
                ephemeral=True
            )
            return
        
        try:
            # Adiciona permissão para o usuário
            await voice_channel.set_permissions(
                usuario,
                view_channel=True,
                connect=True,
                speak=True
            )
            
            await interaction.response.send_message(
                f"✅ **{usuario.display_name}** agora pode ver e entrar na sua sala!\n"
                f"💡 Eles receberão acesso imediato ao canal {voice_channel.mention}",
                ephemeral=True
            )
            
            logger.info(
                "👁️ Usuário adicionado via comando | channel=%s | user=%s | by=%s",
                voice_channel.name,
                usuario.name,
                interaction.user.name
            )
            
            # Tenta notificar o usuário adicionado
            try:
                await usuario.send(
                    f"🎉 **{interaction.user.display_name}** te adicionou à sala temporária!\n"
                    f"📍 Servidor: **{interaction.guild.name}**\n"
                    f"🔊 Canal: {voice_channel.mention}\n\n"
                    f"💡 Você já pode entrar na sala!"
                )
            except discord.Forbidden:
                # Usuário tem DMs fechadas, ignora
                pass
            
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ Sem permissão para modificar permissões da sala!\n"
                "💡 Verifique se o bot tem permissão de **Gerenciar Canais**.",
                ephemeral=True
            )
        except Exception as e:
            logger.exception("❌ Erro ao adicionar usuário")
            await interaction.response.send_message(
                f"❌ Erro ao adicionar usuário: {e!s}",
                ephemeral=True
            )
    
    @app_commands.command(
        name="sala-remover",
        description="🚫 Remove alguém da sua sala temporária"
    )
    @app_commands.describe(
        usuario="Usuário que você quer remover da sala"
    )
    async def remove_from_room(
        self,
        interaction: discord.Interaction,
        usuario: discord.Member
    ) -> None:
        """
        🚫 Remove usuário específico da sala temporária.
        
        💡 Boa Prática: Permite gerenciar quem tem acesso
        """
        # Valida se está em sala temporária
        voice_channel, owner_id = await self._get_temp_room_info(interaction)
        
        if not voice_channel:
            await interaction.response.send_message(
                "❌ Você precisa estar em uma **sala temporária** para usar este comando!",
                ephemeral=True
            )
            return
        
        # Valida se é o dono
        if owner_id != interaction.user.id:
            await interaction.response.send_message(
                "❌ Apenas o **dono da sala** pode remover pessoas!",
                ephemeral=True
            )
            return
        
        # Verifica se não está removendo a si mesmo
        if usuario.id == interaction.user.id:
            await interaction.response.send_message(
                "😅 Você não pode se remover da própria sala!",
                ephemeral=True
            )
            return
        
        try:
            # Remove permissões específicas do usuário
            await voice_channel.set_permissions(
                usuario,
                view_channel=False,
                connect=False
            )
            
            # Se o usuário estiver na sala, desconecta
            if usuario.voice and usuario.voice.channel == voice_channel:
                await usuario.move_to(None)
            
            await interaction.response.send_message(
                f"✅ **{usuario.display_name}** foi removido da sala!\n"
                f"🔒 Eles não podem mais ver ou entrar no canal.",
                ephemeral=True
            )
            
            logger.info(
                "🚫 Usuário removido via comando | channel=%s | user=%s | by=%s",
                voice_channel.name,
                usuario.name,
                interaction.user.name
            )
            
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ Sem permissão para modificar permissões da sala!",
                ephemeral=True
            )
        except Exception as e:
            logger.exception("❌ Erro ao remover usuário")
            await interaction.response.send_message(
                f"❌ Erro ao remover usuário: {e!s}",
                ephemeral=True
            )
    
    @app_commands.command(
        name="sala-info",
        description="ℹ️ Mostra informações sobre sua sala temporária"
    )
    async def room_info(
        self,
        interaction: discord.Interaction
    ) -> None:
        """
        ℹ️ Exibe informações detalhadas da sala temporária.
        
        💡 Útil para ver quem tem acesso e configurações atuais
        """
        # Valida se está em sala temporária
        voice_channel, owner_id = await self._get_temp_room_info(interaction)
        
        if not voice_channel:
            await interaction.response.send_message(
                "❌ Você precisa estar em uma **sala temporária** para usar este comando!",
                ephemeral=True
            )
            return
        
        try:
            # Busca o dono
            owner = interaction.guild.get_member(owner_id) if owner_id else None
            
            # Informações básicas
            current_users = len(voice_channel.members)
            user_limit = voice_channel.user_limit
            limit_text = "∞ Ilimitado" if user_limit == 0 else f"{user_limit} usuários"
            
            # Status de privacidade
            everyone_perms = voice_channel.overwrites_for(interaction.guild.default_role)
            is_private = everyone_perms.view_channel is False
            privacy_text = "🔒 Privada" if is_private else "🌍 Pública"
            
            # Lista usuários com permissão especial (em sala privada)
            special_access = []
            if is_private:
                for target, overwrite in voice_channel.overwrites.items():
                    if isinstance(target, discord.Member) and target.id != owner_id:
                        if overwrite.view_channel is True:
                            special_access.append(target.mention)
            
            # Cria embed informativa
            embed = discord.Embed(
                title=f"ℹ️ Informações da Sala Temporária",
                description=f"**{voice_channel.name}**",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="👤 Dono",
                value=owner.mention if owner else "Desconhecido",
                inline=True
            )
            
            embed.add_field(
                name="📊 Status",
                value=privacy_text,
                inline=True
            )
            
            embed.add_field(
                name="👥 Ocupação",
                value=f"{current_users}/{limit_text}",
                inline=True
            )
            
            if special_access:
                embed.add_field(
                    name="👁️ Acesso Especial",
                    value=", ".join(special_access[:10]) + (
                        f"\n... e mais {len(special_access) - 10}" 
                        if len(special_access) > 10 
                        else ""
                    ),
                    inline=False
                )
            
            embed.add_field(
                name="🎮 Comandos Disponíveis",
                value=(
                    "• `/sala-adicionar @usuário` - Adicionar pessoa\n"
                    "• `/sala-remover @usuário` - Remover pessoa\n"
                    "• Use os botões da embed para outras configurações!"
                ),
                inline=False
            )
            
            embed.set_footer(
                text="Esta sala será deletada automaticamente quando ficar vazia"
            )
            
            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )
            
        except Exception as e:
            logger.exception("❌ Erro ao buscar informações da sala")
            await interaction.response.send_message(
                f"❌ Erro ao buscar informações: {e!s}",
                ephemeral=True
            )


async def setup(bot: commands.Bot) -> None:
    """
    🔧 Registra os comandos slash no bot.
    
    💡 Type hint completo para melhor documentação
    """
    await bot.add_cog(TempRoomSlashCommands(bot))
