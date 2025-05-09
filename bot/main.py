from settings import Settings
from rate_limit import TokenBucket
from progress_tracker import ProgressTracker
from safety import AntiDetectionSafety

from telethon import TelegramClient
from telethon.tl.types import Message, MessageService
from telethon.errors import FloodWaitError, SlowModeWaitError, ChatWriteForbiddenError

import asyncio
from datetime import datetime
import logging
from typing import Optional, Dict, List, Set

logging.basicConfig(
    format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
    level=logging.INFO
)

logger = logging.getLogger('CloneGram')

try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    logger.info("Using uvloop as the event loop.")
except ImportError:
    logger.info("uvloop not installed, using the default asyncio event loop.")

settings = Settings()

class Bot(TelegramClient):
    def __init__(self):
        self.messages_queue = asyncio.Queue()
        self.media_groups: Dict[str, List[Message]] = {}  # Store media groups by grouping ID
        self.processed_media_groups: Set[str] = set()  # Track processed media groups
        self.finished_queue = False

        # Progress tracking
        self.progress_tracker = ProgressTracker()
        
        # Anti-ban safety measures
        self.safety = AntiDetectionSafety(settings)

        # Rate limiting (based on settings)
        seconds_in_minute = 60
        self.rate_limit = 20
        self.interval = seconds_in_minute / self.rate_limit
        self.bucket = TokenBucket(
            initial_tokens=1,
            max_tokens=self.rate_limit,
            refill_interval=self.interval
        )

        # Initialize TelegramClient
        super().__init__(
            session="./sessions/"+settings.account_name,
            api_id=settings.api_id,
            api_hash=settings.api_hash,
            flood_sleep_threshold=11,
            
        )

    async def get_last_message(self, chat):
        """Get the last message ID in a chat"""
        async for message in self.iter_messages(entity=chat, limit=1, min_id=0):
            logger.info(f"Total messages in the group: {message.id}")
            return message.id
        return 0

    async def _get_chat_messages(
        self, 
        origin_chat,
        offset_id: int = 0,
        limit: int = 100,
        reverse: bool = True,
        offset_date: Optional[datetime] = None,
    ) -> None:
        """Fetch messages from origin chat and add them to the queue"""
        try:
            if offset_id is None:
                offset_id = 0

            message_count = 0
            async for message in self.iter_messages(
                entity=origin_chat,
                limit=limit,
                offset_id=offset_id,
                offset_date=offset_date,
                reverse=reverse,
                min_id=0,
            ):
                message_count += 1
                logger.info(f"Fetched message ID: {message.id}")
                
                # Check if message is part of a media group
                if message.grouped_id:
                    group_id = str(message.grouped_id)
                    if group_id not in self.processed_media_groups:
                        if group_id not in self.media_groups:
                            self.media_groups[group_id] = []
                        self.media_groups[group_id].append(message)
                else:
                    # Regular message, add to queue
                    await self.messages_queue.put(message)

                if message.id == self.last_msg_id:
                    self.finished_queue = True
                    logger.info("All messages fetched")
                    
                    # Process any remaining media groups
                    for group_id, messages in self.media_groups.items():
                        if group_id not in self.processed_media_groups:
                            # Sort messages by ID to maintain original order
                            messages.sort(key=lambda m: m.id)
                            await self.messages_queue.put(("media_group", group_id, messages))
                            self.processed_media_groups.add(group_id)
                    
                    return
            
            # Se não encontrou mais mensagens ou chegou ao limite
            if message_count == 0:
                self.finished_queue = True
                logger.info("No more messages to fetch")
            elif message_count < limit:
                self.finished_queue = True
                logger.info(f"Fetched final {message_count} messages (less than limit)")
            else:
                logger.info(f"Fetched {message_count} messages, continuing pagination...")
                
        except FloodWaitError as e:
            logger.warning(f"FloodError detected, waiting {e.seconds} seconds...")
            await asyncio.sleep(e.seconds)

    async def _send_media_group(
        self,
        chat_id: int | str,
        messages: List[Message],
        reply_to_message_id: int | None = None,
    ) -> List[Message] | None:
        """Forward a group of media messages as a group"""
        try:
            logger.info(f"Forwarding media group with {len(messages)} items")
            
            # Para evitar problemas com o limite de batch, garantimos que os media groups 
            # sejam tratados como uma única entidade, não como mensagens individuais
            # Aplicamos apenas um delay antes de enviar todo o grupo
            try:
                can_proceed = await self.safety.apply_delay(is_media=True)
                if not can_proceed:
                    logger.warning("Daily media limit reached, skipping media group")
                    return None
            except Exception as e:
                logger.error(f"Error in safety delay for media group: {str(e)}")
                # Continue with the forwarding even if the safety mechanism fails
                
            if not messages[0].noforwards:
                # Se o forwarding é permitido, encaminhe como um grupo
                # Adicionamos um tratamento de erro mais robusto aqui
                try:
                    result = await self.forward_messages(
                        entity=chat_id,
                        messages=messages,
                        from_peer=messages[0].chat.id,
                        drop_author=True,
                    )
                    return result
                except Exception as e:
                    logger.error(f"Error forwarding media group: {str(e)}")
                    # Em caso de erro, tente enviar novamente após um breve intervalo
                    await asyncio.sleep(5)
                    return await self.forward_messages(
                        entity=chat_id,
                        messages=messages,
                        from_peer=messages[0].chat.id,
                        drop_author=True,
                    )
            else:
                # If forwarding is not allowed, inform and skip
                logger.warning(f"Media group cannot be forwarded due to forward restrictions")
                return None
                
        except FloodWaitError as e:
            wait_time = e.seconds
            logger.warning(f"FloodWaitError detected. Waiting {wait_time} seconds...")
            await asyncio.sleep(wait_time)
            return None
        except Exception as e:
            logger.error(f"Error sending media group: {str(e)}")
            return None

    async def _forward_message(
        self,
        chat_id: int | str,
        message: Message,
        reply_to_message_id: int | None = None,
        group_policy: bool = False,
    ) -> Message | None:
        """Forward a message to the destination chat"""
        try:
            # Apply safety delay before forwarding
            # Check if message has media
            has_media = message.media is not None
            try:
                can_proceed = await self.safety.apply_delay(is_media=has_media)
                if not can_proceed:
                    logger.warning(f"Rate limit reached, skipping message ID {message.id}")
                    return None
            except Exception as e:
                logger.error(f"Error in safety delay for message {message.id}: {str(e)}")
                # Continue with the forwarding even if the safety mechanism fails
                
            if not message.noforwards and not group_policy: 
                return await self.forward_messages(
                    entity=chat_id,
                    messages=message,
                    from_peer=message.chat.id,
                    drop_author=True,
                )
            else:
                # For restricted content, simply send a text message
                if message.text:
                    # Include button URLs in message text if present
                    text = message.text
                    if message.buttons:
                        for row in message.buttons:
                            for button in row:
                                if button.url:
                                    text += f"\n**[Access]({button.url})**"
                                    
                    return await self.send_message(
                        entity=chat_id,
                        message=text,
                        reply_to=reply_to_message_id,
                    )
                else:
                    logger.warning(f"Cannot forward message ID {message.id} (protected content)")
                    return None
        except FloodWaitError as e:
            wait_time = e.seconds
            logger.warning(f"FloodWaitError. Waiting {wait_time} seconds...")
            await asyncio.sleep(wait_time)
            return None
        except Exception as e:
            logger.error(f"Unexpected error forwarding message {message.id}: {str(e)}")
            return None

    async def _process_message(
        self, 
        destiny_chat,
        origin_chat,
        message: Message,
        topic_id: Optional[int] = None
    ) -> Message | None:
        """Process individual messages"""
        # Skip service messages
        if isinstance(message, MessageService):
            logger.info(f"Skipping message ID {message.id} as it's a service message.")
            return None
        
        try:
            logger.info(f"Forwarding message_id: {message.id}")
            return await self._forward_message(
                chat_id=destiny_chat.id,
                message=message,
                reply_to_message_id=topic_id,
                group_policy=origin_chat.noforwards
            )
        except FloodWaitError as e:
            wait_time = e.seconds
            logger.warning(f"FloodWaitError. Waiting {wait_time} seconds...")
            await asyncio.sleep(wait_time)
            return None

    async def _process_messages(
        self,
        origin_chat,
        destiny_chat,
        topic_id: Optional[int] = None,
        offset_id: int = 0,
        offset_date: Optional[datetime] = None
    ) -> None:
        """Process messages from the queue and forward them to the destination"""
        self.last_processed_msg = offset_id
        self.last_msg_id = await self.get_last_message(origin_chat)

        # Adicionamos uma flag para garantir que não vamos quebrar media groups entre batches
        current_media_group_processing = False

        while True:
            if self.messages_queue.empty():
                if self.finished_queue:
                    break
                
                logger.info("All messages processed, fetching more...")
                try:
                    await self._get_chat_messages(
                        origin_chat=origin_chat,
                        offset_id=self.last_processed_msg,
                        offset_date=offset_date,
                    )
                except FloodWaitError as e:
                    wait_time = e.seconds
                    logger.warning(f"FloodWaitError when fetching messages. Waiting {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                    continue
                
                # Process any media groups that were collected
                for group_id, messages in list(self.media_groups.items()):
                    if group_id not in self.processed_media_groups:
                        # Sort messages by ID to maintain original order
                        messages.sort(key=lambda m: m.id)
                        await self.messages_queue.put(("media_group", group_id, messages))
                        self.processed_media_groups.add(group_id)
                        del self.media_groups[group_id]

            try:
                # Basic rate limiting is still applied to prevent API errors
                # IMPORTANTE: Se estamos no meio de um media group, não fazemos o rate limiting
                # para evitar que o grupo seja dividido
                if not current_media_group_processing:
                    while not self.bucket.consume():
                        logger.info(f"Preventing API flood, waiting {self.interval} seconds")
                        await asyncio.sleep(self.interval)
                
                # The more sophisticated safety delays are applied in the send methods

                item = await self.messages_queue.get()
                
                # Check if it's a media group
                if isinstance(item, tuple) and item[0] == "media_group":
                    _, group_id, messages = item
                    current_media_group_processing = True  # Estamos processando um media group
                    try:
                        result = await self._send_media_group(
                            chat_id=destiny_chat.id,
                            messages=messages,
                            reply_to_message_id=topic_id,
                        )
                        
                        if result is None:
                            # For protected content, we just continue
                            latest_msg_id = max(msg.id for msg in messages)
                            self.last_processed_msg = latest_msg_id
                            self.progress_tracker.save_progress(origin_chat.id, latest_msg_id)
                        else:
                            # Update progress with the latest message ID in the group
                            latest_msg_id = max(msg.id for msg in messages)
                            self.last_processed_msg = latest_msg_id
                            self.progress_tracker.save_progress(origin_chat.id, latest_msg_id)
                        
                        # Adicionamos um pequeno delay entre grupos de mídia
                        await asyncio.sleep(2)
                        
                    except FloodWaitError as e:
                        wait_time = e.seconds
                        logger.warning(f"FloodWaitError when sending media group. Waiting {wait_time} seconds...")
                        await asyncio.sleep(wait_time)
                        # Put the item back in the queue to try again later
                        await self.messages_queue.put(item)
                    finally:
                        current_media_group_processing = False  # Terminamos de processar o media group
                else:
                    # Regular message
                    message = item
                    try:
                        await self._process_message(
                            destiny_chat=destiny_chat, 
                            origin_chat=origin_chat,
                            message=message,
                            topic_id=topic_id,
                        )
                        self.last_processed_msg = message.id
                        self.progress_tracker.save_progress(origin_chat.id, message.id)
                    except FloodWaitError as e:
                        wait_time = e.seconds
                        logger.warning(f"FloodWaitError when sending message {message.id}. Waiting {wait_time} seconds...")
                        await asyncio.sleep(wait_time)
                        # Put the message back in the queue to try again
                        await self.messages_queue.put(message)
                    except SlowModeWaitError as e:
                        wait_time = e.seconds
                        logger.warning(f"SlowModeWaitError for message {message.id}. Waiting {wait_time} seconds...")
                        await asyncio.sleep(wait_time)
                        await self.messages_queue.put(message)
                    except ChatWriteForbiddenError:
                        logger.error(f"No permission to write in the destination chat. Skipping message {message.id}")
        
            except Exception as e:
                logger.error(f"Unexpected error processing message: {e}")
                # Continue processing other messages
                continue
            
            finally:
                self.messages_queue.task_done()

        logger.info("All messages processed")

    async def clone_messages(
        self, 
        origin_group_id: int|str,
        destiny_group_id: int|str,
        topic_id: Optional[int] = None,
        offset_id: Optional[int] = None,
        offset_date: Optional[datetime] = None
    ) -> None:
        """Main method to clone messages from one group to another"""
        # Get open dialogs, in case it's a private chat, etc...
        await self.get_dialogs()

        try:
            origin_chat = await self.get_entity(origin_group_id)
            logger.info(f"Origin group: {origin_chat.title if hasattr(origin_chat, 'title') else origin_chat.id} is connected")
        except Exception as e:
            logger.error(f"Error with origin chat: {e}")
            return

        try:
            destiny_chat = await self.get_entity(destiny_group_id)
            logger.info(f"Destiny group is connected")
        except Exception as e:
            logger.error(f"Error with destiny chat: {e}")
            return

        # Se estamos começando do zero (primeira execução)
        if offset_id is None and not self.progress_tracker.get_progress(origin_chat.id):
            logger.info("Primeira execução, processando todas as mensagens...")
            self.finished_queue = False  # Garantir que a flag está resetada
            await self._process_messages(
                destiny_chat=destiny_chat,
                origin_chat=origin_chat,
                topic_id=topic_id,
                offset_id=offset_id,
                offset_date=offset_date,
            )
        else:
            # Para execuções subsequentes, use o método otimizado
            await self.check_and_clone_new_messages(
                origin_chat=origin_chat,
                destiny_chat=destiny_chat,
                topic_id=topic_id,
                offset_date=offset_date
            )

    async def check_and_clone_new_messages(
        self,
        origin_chat,
        destiny_chat,
        topic_id: Optional[int] = None,
        offset_date: Optional[datetime] = None
    ) -> None:
        """Verifica e clona apenas mensagens novas"""
        
        # Obter o último ID processado
        last_processed_id = self.progress_tracker.get_progress(origin_chat.id)
        
        # Obter o ID da última mensagem no grupo de origem
        latest_message_id = await self.get_last_message(origin_chat)
        
        logger.info(f"Última mensagem processada: {last_processed_id}, última mensagem no grupo: {latest_message_id}")
        
        # Verificar se há novas mensagens
        if last_processed_id >= latest_message_id:
            logger.info("Nenhuma mensagem nova para processar.")
            return
        
        # Número de novas mensagens
        new_messages_count = latest_message_id - last_processed_id
        logger.info(f"Detectadas {new_messages_count} novas mensagens para processar.")
        
        # Reiniciar as filas e flags para nova execução
        self.messages_queue = asyncio.Queue()
        self.finished_queue = False
        self.processed_media_groups.clear()
        self.media_groups.clear()
        
        # Processar as novas mensagens
        await self._process_messages(
            destiny_chat=destiny_chat,
            origin_chat=origin_chat,
            topic_id=topic_id,
            offset_id=last_processed_id,
            offset_date=offset_date,
        )


async def main():
    bot = Bot()

    await bot.start(
        phone=settings.phone_number,
        password=settings.password
    )

    # Topic that you want to send (uncomment if needed)
    # topic_id = None

    # The last message it stopped at (if None, will use progress tracking)
    offset_id = None  # Using progress tracking

    logger.info("\n>>> Cloner up and running.\n")
    if settings.continuous_mode:
        logger.info(f"Modo contínuo ativado. Intervalo de verificação: {settings.check_interval} segundos")
    
    # Loop contínuo se continuous_mode estiver ativado
    first_run = True
    
    while True:
        try:
            # Execute a clonagem
            await bot.clone_messages(
                origin_group_id=settings.origin_group,
                destiny_group_id=settings.destiny_group,
                # topic_id=topic_id, (descomente se necessário)
                offset_id=None if first_run else 1  # Na primeira execução processa tudo, depois apenas as novas
            )
            
            first_run = False
            
            # Se não estiver em modo contínuo, saia do loop
            if not settings.continuous_mode:
                logger.info("Modo contínuo desativado. Encerrando após processamento.")
                break
            
            # Log informando que verificará novamente
            logger.info(f"Verificando novamente em {settings.check_interval} segundos...")
            
            # Aguarde o intervalo configurado
            await asyncio.sleep(settings.check_interval)
            
        except Exception as e:
            logger.error(f"Erro durante execução contínua: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Em caso de erro, aguarde um tempo antes de tentar novamente
            logger.info("Tentando novamente em 60 segundos...")
            await asyncio.sleep(60)  # Espera 1 minuto em caso de erro

    await bot.disconnect()
    

if __name__ == "__main__":
    asyncio.run(main())