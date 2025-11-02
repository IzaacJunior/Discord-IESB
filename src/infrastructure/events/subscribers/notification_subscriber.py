"""
🔔 Notification Subscriber - Envia notificações sobre eventos
💡 Boa Prática: Centraliza lógica de notificações em um lugar!
"""

import logging

import discord

from domain.events import DomainEvent

logger = logging.getLogger(__name__)


class NotificationSubscriber:
    """
    🔔 Subscriber para notificações
    
    Envia notificações para admins, webhooks e canais específicos
    quando eventos importantes acontecem no sistema.
    
    💡 Boa Prática: Notificações isoladas facilitam gerenciamento
    de múltiplos canais de comunicação!
    
    Examples:
        >>> notif = NotificationSubscriber(bot_client)
        >>> event_bus.subscribe("temp_room_created", notif.on_temp_room_created)
    """
    
    def __init__(self, bot: discord.Client | None = None) -> None:
        """
        Inicializa subscriber de notificações
        
        Args:
            bot: Cliente Discord para enviar mensagens (opcional)
        """
        self.bot = bot
        self.notifications_sent: list[dict] = []
        logger.info("🔔 Notification Subscriber inicializado")
    
    async def on_temp_room_created(self, event: DomainEvent) -> None:
        """
        🔔 Notifica sobre criação de sala temporária
        
        Pode enviar notificação para:
        - Canal de logs do servidor
        - Webhook Discord para admins
        - Sistema de notificações interno
        
        Args:
            event: Evento com dados da sala criada
        """
        try:
            data = event.data
            channel_name = data.get("channel_name", "Desconhecida")
            owner_id = data.get("owner_id")
            guild_id = data.get("guild_id")
            
            # 📝 Registra notificação
            notification = {
                "type": "temp_room_created",
                "message": f"🎉 Nova sala temporária criada: {channel_name}",
                "channel_name": channel_name,
                "owner_id": owner_id,
                "guild_id": guild_id,
                "timestamp": event.timestamp.isoformat()
            }
            
            self.notifications_sent.append(notification)
            
            logger.info(
                "🔔 Notificação preparada: sala '%s' criada por <@%s>",
                channel_name,
                owner_id
            )
            
            # 💡 Aqui você integraria com sistemas reais:
            # await self._send_to_discord_webhook(notification)
            # await self._send_to_admin_channel(guild_id, notification)
            # await self._send_to_logging_channel(guild_id, notification)
            
        except Exception as e:
            logger.error("❌ Erro ao enviar notificação: %s", str(e))
    
    async def on_temp_room_deleted(self, event: DomainEvent) -> None:
        """
        🔔 Notifica sobre exclusão de sala temporária
        
        Args:
            event: Evento com dados da sala deletada
        """
        try:
            data = event.data
            channel_id = data.get("channel_id")
            duration = data.get("duration_seconds", 0)
            
            # 📝 Registra notificação
            notification = {
                "type": "temp_room_deleted",
                "message": f"🗑️ Sala temporária ID {channel_id} deletada após {duration}s",
                "channel_id": channel_id,
                "duration_seconds": duration,
                "timestamp": event.timestamp.isoformat()
            }
            
            self.notifications_sent.append(notification)
            
            logger.info(
                "🔔 Notificação preparada: sala ID %s deletada após %s segundos",
                channel_id,
                duration
            )
            
        except Exception as e:
            logger.error("❌ Erro ao notificar exclusão: %s", str(e))
    
    async def on_member_joined_guild(self, event: DomainEvent) -> None:
        """
        👋 Notifica sobre novo membro no servidor
        
        Args:
            event: Evento com dados do novo membro
        """
        try:
            data = event.data
            member_id = data.get("member_id")
            guild_id = data.get("guild_id")
            member_name = data.get("member_name", "Desconhecido")
            
            notification = {
                "type": "member_joined",
                "message": f"👋 Novo membro: {member_name}",
                "member_id": member_id,
                "guild_id": guild_id,
                "timestamp": event.timestamp.isoformat()
            }
            
            self.notifications_sent.append(notification)
            
            logger.info(
                "🔔 Notificação preparada: novo membro %s (%s) entrou no servidor",
                member_name,
                member_id
            )
            
            # 💡 Pode enviar mensagem de boas-vindas
            # await self._send_welcome_message(guild_id, member_id)
            
        except Exception as e:
            logger.error("❌ Erro ao notificar novo membro: %s", str(e))
    
    async def _send_to_discord_webhook(self, notification: dict) -> None:
        """
        📡 Envia notificação via webhook Discord
        
        💡 Webhooks permitem enviar mensagens sem bot estar online!
        
        Args:
            notification: Dados da notificação
        """
        # Implementação exemplo (você adicionaria a URL do webhook):
        """
        webhook_url = os.getenv("ADMIN_WEBHOOK_URL")
        
        if webhook_url:
            async with aiohttp.ClientSession() as session:
                embed = {
                    "title": notification["message"],
                    "color": 0x00ff00,
                    "timestamp": notification["timestamp"]
                }
                
                await session.post(
                    webhook_url,
                    json={"embeds": [embed]}
                )
        """
        logger.debug("📡 Webhook enviado (implementar integração real)")
    
    async def _send_to_admin_channel(self, guild_id: int, notification: dict) -> None:
        """
        📢 Envia notificação para canal de admins
        
        Args:
            guild_id: ID do servidor
            notification: Dados da notificação
        """
        if not self.bot:
            return
        
        # Implementação exemplo:
        """
        guild = self.bot.get_guild(guild_id)
        if guild:
            admin_channel = discord.utils.get(guild.channels, name="admin-logs")
            if admin_channel and isinstance(admin_channel, discord.TextChannel):
                await admin_channel.send(notification["message"])
        """
        logger.debug("📢 Mensagem admin preparada (implementar integração real)")
    
    def get_notification_count(self, notification_type: str | None = None) -> int:
        """
        📊 Retorna contagem de notificações enviadas
        
        Args:
            notification_type: Tipo específico ou None para todas
        
        Returns:
            Número de notificações
        """
        if notification_type:
            return sum(
                1 for n in self.notifications_sent 
                if n["type"] == notification_type
            )
        return len(self.notifications_sent)
