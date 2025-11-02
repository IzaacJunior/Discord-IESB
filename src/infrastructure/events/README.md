# 🎯 Event Bus - Sistema de Eventos Desacoplados

## 📋 O Que É?

O **Event Bus** é um sistema de eventos implementando o padrão **Observer/Pub-Sub** que permite diferentes partes do sistema se comunicarem sem conhecer umas às outras.

## 🚀 Como Usar

### 1️⃣ Instalação

O Event Bus já está integrado no projeto! Nenhuma instalação adicional necessária.

### 2️⃣ Setup Básico

```python
from infrastructure.events import EventBus, setup_event_subscribers

# Cria Event Bus
event_bus = EventBus()

# Registra todos os subscribers
subscribers = setup_event_subscribers(event_bus, bot=None)
```

### 3️⃣ Publicando Eventos

```python
from domain.events import DomainEvent

# Publica evento de sala criada
await event_bus.publish(DomainEvent(
    event_type="temp_room_created",
    data={
        "channel_id": 123456789,
        "channel_name": "🎮 Sala do João",
        "owner_id": 987654321,
        "guild_id": 111222333,
    }
))
```

### 4️⃣ Criando Novo Subscriber

```python
# src/infrastructure/events/subscribers/meu_subscriber.py
import logging
from domain.events import DomainEvent

logger = logging.getLogger(__name__)

class MeuSubscriber:
    """Meu subscriber customizado"""

    async def on_temp_room_created(self, event: DomainEvent):
        """Reage a criação de sala"""
        try:
            channel_name = event.data.get("channel_name")
            logger.info(f"🎉 Nova sala: {channel_name}")

            # Sua lógica aqui!
            # - Enviar email
            # - Atualizar dashboard
            # - Integrar com API externa
            # - etc

        except Exception as e:
            logger.error(f"❌ Erro: {e}")

# Registrar no event_registry.py
from infrastructure.events.subscribers import MeuSubscriber

meu_subscriber = MeuSubscriber()
event_bus.subscribe("temp_room_created", meu_subscriber.on_temp_room_created)
```

## 🧪 Testando

Execute o exemplo completo:

```bash
# PowerShell
uv run python .\tools\example_event_bus.py
```

Você verá:

- ✅ Event Bus sendo configurado
- ✅ Eventos sendo publicados
- ✅ Subscribers reagindo em paralelo
- ✅ Estatísticas detalhadas
- ✅ Execução paralela demonstrada

## 📊 Eventos Disponíveis

### Salas Temporárias

- `temp_room_created` - Sala temporária criada
- `temp_room_deleted` - Sala temporária deletada
- `temp_room_owner_changed` - Dono da sala mudou

### Comandos

- `command_executed` - Comando executado
- `command_failed` - Comando falhou

### Membros

- `member_joined_guild` - Membro entrou no servidor
- `member_left_guild` - Membro saiu
- `member_banned` - Membro foi banido

## 💡 Boas Práticas

### ✅ DO (Faça)

```python
# ✅ Eventos no passado
event_type = "temp_room_created"  # CORRETO

# ✅ Handler com error handling
async def on_event(event: DomainEvent):
    try:
        # Lógica aqui
        pass
    except Exception as e:
        logger.error(f"Erro: {e}")
        # NÃO propague erro!

# ✅ Dados completos no evento
data = {
    "channel_id": 123,
    "owner_id": 456,
    "timestamp": datetime.now()
}
```

### ❌ DON'T (Não Faça)

```python
# ❌ Eventos no imperativo
event_type = "create_temp_room"  # ERRADO

# ❌ Propagar erro (quebra outros subscribers)
async def on_event(event: DomainEvent):
    result = do_something()
    if not result:
        raise Exception("Erro!")  # ERRADO!

# ❌ Dados insuficientes
data = {"id": 123}  # Faltam informações!
```

## 📈 Monitorando

```python
# Ver estatísticas do Event Bus
stats = event_bus.get_stats()
print(f"Eventos publicados: {stats['temp_room_created']['published']}")
print(f"Handlers executados: {stats['temp_room_created']['handlers_executed']}")
print(f"Handlers com falha: {stats['temp_room_created']['handlers_failed']}")

# Ver handlers registrados
handlers = event_bus.get_handlers("temp_room_created")
print(f"Total de handlers: {len(handlers)}")
```

## 🎯 Integrando com Use Cases

```python
# src/application/use_cases/channel_use_cases.py

class CreateChannelUseCase:
    def __init__(self, channel_repository, event_bus=None):
        self.channel_repository = channel_repository
        self.event_bus = event_bus

    async def execute(self, request):
        # 1. Cria canal
        channel = await self.channel_repository.create(request)

        # 2. Publica evento (se configurado)
        if self.event_bus:
            await self.event_bus.publish(DomainEvent(
                event_type="temp_room_created",
                data={"channel_id": channel.id, ...}
            ))

        return channel
```

## 🔧 Troubleshooting

### Evento não está sendo processado?

1. Verifique se subscriber está registrado:

   ```python
   handlers = event_bus.get_handlers("meu_evento")
   print(f"Handlers: {len(handlers)}")  # Deve ser > 0
   ```

2. Verifique logs:

   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

3. Verifique nome do evento:
   ```python
   # Deve ser exatamente igual!
   event_bus.subscribe("temp_room_created", handler)
   await event_bus.publish(DomainEvent(event_type="temp_room_created", ...))
   ```

### Handler falhando silenciosamente?

Os erros são logados mas não propagam (por design). Verifique os logs:

```python
logger.error("Erro no handler", exc_info=True)  # Mostra stack trace
```

## 📚 Mais Informações

- **Documentação Completa**: `docs/ARQUITETURA_PROJETO.md`
- **Código Event Bus**: `src/infrastructure/events/event_bus.py`
- **Exemplo Completo**: `tools/example_event_bus.py`
- **Subscribers**: `src/infrastructure/events/subscribers/`

## 💖 Benefícios

- ✅ **Desacoplamento**: Use cases não conhecem subscribers
- ✅ **Escalabilidade**: Fácil adicionar funcionalidades
- ✅ **Testabilidade**: Só mockar event_bus
- ✅ **Resiliência**: Falhas isoladas
- ✅ **Performance**: Execução paralela
- ✅ **Manutenibilidade**: Código limpo e organizado

---

**✨ Feito com muito carinho seguindo padrões enterprise! 💖**
