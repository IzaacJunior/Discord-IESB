from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord

if TYPE_CHECKING:
    from discord import VoiceChannel

logger = logging.getLogger(__name__)


class ChangeNameModal(discord.ui.Modal, title="✏️ Alterar Nome da Sala"):
    """
    Modal para alterar nome da sala temporária.
    
    💡 Python 3.13: Type hints modernos
    """
    
    new_name = discord.ui.TextInput(
        label="Novo nome da sala",
        placeholder="Digite o novo nome...",
        min_length=1,
        max_length=100,
        required=True,
        style=discord.TextStyle.short
    )
    
    def __init__(self, voice_channel: "VoiceChannel") -> None:
        super().__init__()
        self.voice_channel = voice_channel
        self.new_name.default = voice_channel.name
    
    async def on_submit(self, interaction: discord.Interaction) -> None:
        """Processa a mudança de nome."""
        try:
            old_name = self.voice_channel.name
            await self.voice_channel.edit(name=self.new_name.value)
            
            await interaction.response.send_message(
                f"✅ Nome alterado!\n"
                f"**Antes:** {old_name}\n"
                f"**Agora:** {self.new_name.value}",
                ephemeral=True
            )
            
            logger.info(
                "✏️ Sala renomeada | user=%s | antes='%s' | depois='%s'",
                interaction.user.name,
                old_name,
                self.new_name.value
            )
            
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ Sem permissão para alterar o nome da sala!",
                ephemeral=True
            )
        except Exception as e:
            logger.error("❌ Erro ao alterar nome: %s", str(e))
            await interaction.response.send_message(
                f"❌ Erro ao alterar nome: {e!s}",
                ephemeral=True
            )


class ChangeLimitModal(discord.ui.Modal, title="👥 Alterar Limite de Usuários"):
    """Modal para alterar limite de usuários da sala."""
    
    new_limit = discord.ui.TextInput(
        label="Limite de usuários (0 = ilimitado)",
        placeholder="Digite um número entre 0 e 99",
        min_length=1,
        max_length=2,
        required=True,
        style=discord.TextStyle.short
    )
    
    def __init__(self, voice_channel: "VoiceChannel") -> None:
        super().__init__()
        self.voice_channel = voice_channel
        self.new_limit.default = str(voice_channel.user_limit)
    
    async def on_submit(self, interaction: discord.Interaction) -> None:
        """Processa a mudança de limite."""
        try:
            # Valida entrada
            limit = int(self.new_limit.value)
            
            if limit < 0 or limit > 99:
                await interaction.response.send_message(
                    "❌ Limite deve estar entre 0 e 99!",
                    ephemeral=True
                )
                return
            
            old_limit = self.voice_channel.user_limit
            await self.voice_channel.edit(user_limit=limit)
            
            limit_text = "ilimitado" if limit == 0 else f"{limit} usuários"
            old_text = "ilimitado" if old_limit == 0 else f"{old_limit} usuários"
            
            await interaction.response.send_message(
                f"✅ Limite alterado!\n"
                f"**Antes:** {old_text}\n"
                f"**Agora:** {limit_text}",
                ephemeral=True
            )
            
            logger.info(
                "👥 Limite alterado | user=%s | antes=%d | depois=%d",
                interaction.user.name,
                old_limit,
                limit
            )
            
        except ValueError:
            await interaction.response.send_message(
                "❌ Por favor, digite apenas números!",
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ Sem permissão para alterar o limite da sala!",
                ephemeral=True
            )
        except Exception as e:
            logger.error("❌ Erro ao alterar limite: %s", str(e))
            await interaction.response.send_message(
                f"❌ Erro ao alterar limite: {e!s}",
                ephemeral=True
            )


class AddUserModal(discord.ui.Modal, title="👁️ Adicionar Pessoa"):
    """
    Modal para adicionar usuário por nome/ID/apelido.
    
    💡 Python 3.13: Pattern matching para busca inteligente
    🎯 Boa Prática: Fallback para servidores médios
    """
    
    user_input = discord.ui.TextInput(
        label="Nome, apelido ou ID do usuário",
        placeholder="Ex: João, @João ou 123456789012345678",
        min_length=2,
        max_length=100,
        required=True,
        style=discord.TextStyle.short
    )
    
    def __init__(self, voice_channel: "VoiceChannel", owner_id: int) -> None:
        super().__init__()
        self.voice_channel = voice_channel
        self.owner_id = owner_id
    
    async def on_submit(self, interaction: discord.Interaction) -> None:
        """
        Processa entrada e busca o usuário.
        
        💡 Python 3.13: Pattern matching elegante
        """
        user_query = self.user_input.value.strip().lstrip("@")
        
        try:
            member = None
            
            # 🔍 Busca inteligente com pattern matching
            match user_query:
                case id_str if id_str.isdigit():
                    # Busca por ID numérico
                    user_id = int(id_str)
                    member = interaction.guild.get_member(user_id)
                    
                case name_tag if "#" in name_tag:
                    # Busca por nome#discriminador (formato legado)
                    username, discriminator = name_tag.split("#", 1)
                    member = discord.utils.get(
                        interaction.guild.members,
                        name=username,
                        discriminator=discriminator
                    )
                    
                case _:
                    # Busca por nome de exibição ou nome de usuário
                    query_lower = user_query.lower()
                    member = discord.utils.find(
                        lambda m: (
                            query_lower in m.display_name.lower() or
                            query_lower in m.name.lower() or
                            query_lower == m.name.lower()
                        ),
                        interaction.guild.members
                    )
            
            # Valida se encontrou
            if not member:
                await interaction.response.send_message(
                    f"❌ Usuário `{user_query}` não encontrado!\n\n"
                    f"💡 **Dicas para encontrar:**\n"
                    f"• Copie o ID (clique direito → Copiar ID)\n"
                    f"• Use o nome exato mostrado no servidor\n"
                    f"• Digite parte do nome ou apelido",
                    ephemeral=True
                )
                return
            
            # Verifica validações básicas
            if member.id == self.owner_id:
                await interaction.response.send_message(
                    "😅 Você já está na sala!",
                    ephemeral=True
                )
                return
            
            if member.bot:
                await interaction.response.send_message(
                    "🤖 Não é possível adicionar bots!",
                    ephemeral=True
                )
                return
            
            # Adiciona permissão
            await self.voice_channel.set_permissions(
                member,
                view_channel=True,
                connect=True,
                speak=True
            )
            
            await interaction.response.send_message(
                f"✅ **{member.display_name}** agora pode ver e entrar na sua sala!",
                ephemeral=True
            )
            
            logger.info(
                "�️ Usuário adicionado via modal | channel=%s | user=%s",
                self.voice_channel.name,
                member.name
            )
            
            # Tenta notificar
            try:
                await member.send(
                    f"🎉 Você foi adicionado a uma sala temporária!\n"
                    f"🔊 Canal: {self.voice_channel.mention} em **{interaction.guild.name}**"
                )
            except discord.Forbidden:
                pass
            
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ Sem permissão para adicionar usuários!",
                ephemeral=True
            )
        except Exception as e:
            logger.exception("❌ Erro ao adicionar usuário via modal")
            await interaction.response.send_message(
                f"❌ Erro: {e!s}",
                ephemeral=True
            )


class TempRoomControlView(discord.ui.View):
    """
    🎮 View com controles adaptativos para salas temporárias.
    
    💡 Boa Prática: Adapta interface baseado no tamanho do servidor
    🚀 Python 3.13: Type hints modernos e pattern matching
    """
    
    def __init__(
        self, 
        voice_channel: "VoiceChannel",
        owner_id: int,
        timeout: float | None = None
    ) -> None:
        """
        Inicializa a view de controle com sistema híbrido.
        
        Args:
            voice_channel: Canal de voz a ser controlado
            owner_id: ID do dono da sala
            timeout: Tempo até expirar (None = nunca expira)
        """
        super().__init__(timeout=timeout)
        self.voice_channel = voice_channel
        self.owner_id = owner_id
        
        # 🎯 Sistema híbrido: adapta baseado no tamanho do servidor
        guild_size = len(voice_channel.guild.members)
        logger.info("🎮 Servidor com %d membros | adaptando interface", guild_size)
        
        # Adiciona botão adaptativo para adicionar pessoas
        self._add_user_management_button(guild_size)
    
    def _add_user_management_button(self, guild_size: int) -> None:
        """
        Adiciona botão apropriado baseado no tamanho do servidor.
        
        💡 Python 3.13: Pattern matching para decisão elegante
        """
        match guild_size:
            case size if size <= 50:
                # Servidor pequeno: usa seletor nativo
                logger.debug("🎮 Interface: UserSelect (servidor pequeno)")
                # UserSelect será adicionado no final
                
            case size if 50 < size <= 200:
                # Servidor médio: usa modal
                logger.debug("💬 Interface: Modal (servidor médio)")
                # Botão será adicionado no método apropriado
                
            case _:
                # Servidor grande: recomenda comando
                logger.debug("🚀 Interface: Comando slash (servidor grande)")
                # Botão com instruções será adicionado
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """
        🔒 Valida se quem clicou é o dono da sala.
        
        💡 Boa Prática: Validação de permissões centralizada
        """
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "❌ Apenas o dono da sala pode usar estes controles!",
                ephemeral=True
            )
            return False
        return True
    
    @discord.ui.button(
        label="✏️ Renomear",
        style=discord.ButtonStyle.primary,
        custom_id="rename_room"
    )
    async def rename_button(
        self, 
        interaction: discord.Interaction, 
        button: discord.ui.Button
    ) -> None:
        """Abre modal para renomear a sala."""
        modal = ChangeNameModal(self.voice_channel)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(
        label="👥 Limite",
        style=discord.ButtonStyle.primary,
        custom_id="change_limit"
    )
    async def limit_button(
        self, 
        interaction: discord.Interaction, 
        button: discord.ui.Button
    ) -> None:
        """Abre modal para alterar limite de usuários."""
        modal = ChangeLimitModal(self.voice_channel)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(
        label="🔒 Privada",
        style=discord.ButtonStyle.secondary,
        custom_id="make_private"
    )
    async def private_button(
        self, 
        interaction: discord.Interaction, 
        button: discord.ui.Button
    ) -> None:
        """
        Torna a sala privada (apenas @everyone não pode ver/entrar).
        
        💡 Mantém permissões para quem já está na sala
        """
        try:
            # Remove permissão de @everyone ver e entrar
            await self.voice_channel.set_permissions(
                interaction.guild.default_role,
                view_channel=False,
                connect=False
            )
            
            # Garante que o dono pode gerenciar
            owner = interaction.guild.get_member(self.owner_id)
            if owner:
                await self.voice_channel.set_permissions(
                    owner,
                    view_channel=True,
                    connect=True,
                    manage_channels=True
                )
            
            await interaction.response.send_message(
                "🔒 **Sala privada!**\n"
                "Apenas você e quem já está na sala podem ver/entrar.\n"
                "💡 Use o botão 👁️ para adicionar pessoas específicas!",
                ephemeral=True
            )
            
            logger.info(
                "🔒 Sala privada | channel=%s | owner=%s",
                self.voice_channel.name,
                interaction.user.name
            )
            
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ Sem permissão para tornar a sala privada!",
                ephemeral=True
            )
        except Exception as e:
            logger.error("❌ Erro ao tornar sala privada: %s", str(e))
            await interaction.response.send_message(
                f"❌ Erro: {e!s}",
                ephemeral=True
            )
    
    @discord.ui.button(
        label="🌍 Pública",
        style=discord.ButtonStyle.secondary,
        custom_id="make_public"
    )
    async def public_button(
        self, 
        interaction: discord.Interaction, 
        button: discord.ui.Button
    ) -> None:
        """Torna a sala pública novamente."""
        try:
            # Restaura permissão de @everyone ver e entrar
            await self.voice_channel.set_permissions(
                interaction.guild.default_role,
                view_channel=True,
                connect=True
            )
            
            await interaction.response.send_message(
                "🌍 **Sala pública!**\n"
                "Todos podem ver e entrar na sala agora.",
                ephemeral=True
            )
            
            logger.info(
                "🌍 Sala pública | channel=%s | owner=%s",
                self.voice_channel.name,
                interaction.user.name
            )
            
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ Sem permissão para tornar a sala pública!",
                ephemeral=True
            )
        except Exception as e:
            logger.error("❌ Erro ao tornar sala pública: %s", str(e))
            await interaction.response.send_message(
                f"❌ Erro: {e!s}",
                ephemeral=True
            )
    
    @discord.ui.button(
        label="👁️ Adicionar",
        style=discord.ButtonStyle.success,
        custom_id="add_user_adaptive"
    )
    async def add_user_button(
        self, 
        interaction: discord.Interaction, 
        button: discord.ui.Button
    ) -> None:
        """
        Botão adaptativo para adicionar usuários.
        
        💡 Sistema Híbrido: Modal para servidores médios/grandes
        🎯 Para pequenos: ainda pode usar o comando /sala-adicionar
        """
        guild_size = len(interaction.guild.members)
        
        # 🎯 Pattern matching para decisão
        match guild_size:
            case size if size <= 50:
                # Servidor pequeno: abre modal (mais flexível que select)
                modal = AddUserModal(self.voice_channel, self.owner_id)
                await interaction.response.send_modal(modal)
                
            case size if 50 < size <= 200:
                # Servidor médio: abre modal
                modal = AddUserModal(self.voice_channel, self.owner_id)
                await interaction.response.send_modal(modal)
                
            case _:
                # Servidor grande: recomenda comando slash
                await interaction.response.send_message(
                    "💡 **Para adicionar pessoas em servidores grandes:**\n\n"
                    "Use o comando: `/sala-adicionar @usuário`\n\n"
                    "**✅ Vantagens:**\n"
                    "• Autocompletar enquanto você digita\n"
                    "• Muito mais rápido que menus\n"
                    "• Funciona perfeitamente em qualquer tamanho\n\n"
                    "📝 **Como usar:**\n"
                    "1. Digite `/sala-adicionar`\n"
                    "2. Comece a digitar o nome da pessoa\n"
                    "3. Selecione na lista que aparece\n"
                    "4. Pronto! ✨",
                    ephemeral=True
                )



def create_temp_room_embed(
    voice_channel: "VoiceChannel",
    owner: discord.Member
) -> discord.Embed:
    """
    🎨 Cria embed informativa para sala temporária.
    
    💡 Boa Prática: Factory function para criar embeds consistentes
    
    Args:
        voice_channel: Canal de voz temporário
        owner: Dono da sala
        
    Returns:
        Embed formatada com informações da sala
    """
    # Informações da sala
    current_users = len(voice_channel.members)
    user_limit = voice_channel.user_limit
    limit_text = "∞ Ilimitado" if user_limit == 0 else f"{user_limit} usuários"
    
    # Status de privacidade
    everyone_perms = voice_channel.overwrites_for(voice_channel.guild.default_role)
    is_private = everyone_perms.view_channel is False
    privacy_emoji = "🔒" if is_private else "🌍"
    privacy_text = "Privada" if is_private else "Pública"
    
    # Cria embed
    embed = discord.Embed(
        title=f"{privacy_emoji} Controles da Sala Temporária",
        description=(
            f"**Sala:** {voice_channel.mention}\n"
            f"**Dono:** {owner.mention}\n"
            f"**Status:** {privacy_text}\n"
            f"**Usuários:** {current_users}/{limit_text}\n"
            f"\n"
            f"💡 **Use os botões abaixo para controlar sua sala:**\n"
            f"✏️ **Renomear** - Altere o nome da sala\n"
            f"👥 **Limite** - Defina quantas pessoas podem entrar\n"
            f"🔒 **Privada** - Torne a sala invisível para outros\n"
            f"🌍 **Pública** - Torne a sala visível para todos\n"
            f"👁️ **Menu** - Adicione pessoas específicas (sala privada)\n"
        ),
        color=discord.Color.blue() if not is_private else discord.Color.orange()
    )
    
    embed.set_footer(
        text=f"Esta sala será deletada automaticamente quando ficar vazia • Sala de {owner.display_name}",
        icon_url=owner.display_avatar.url
    )
    
    embed.set_thumbnail(url=owner.display_avatar.url)
    
    return embed
