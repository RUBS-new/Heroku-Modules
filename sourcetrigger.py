# ========================
# ✨ DEVELOPER: @RUBS_New ✨
# ========================

# meta developer: @YouRooni - @RnPlugins - @RUBS_New
# meta banner: https://yufic.ru/api/hc/?a=SourceTrigger&b=Ответ%20медиа%20по%20триггеру
# meta name: SourceTrigger
# scope: hikka_only
# meta version: 1.2.0
# сделал модуль круче - @RUBS_New 

import logging
import re
import asyncio
import datetime
from typing import Optional
from .. import loader, utils
from telethon.tl.patched import Message

logger = logging.getLogger(__name__)

__version__ = (1, 2, 0)

@loader.tds
class SourceTriggerMod(loader.Module):
    """Отправляет медиа или текст из канала в ответ на текстовые триггеры."""

    strings = {
        "name": "SourceTrigger",
        "parsing_started": (
            "<emoji document_id=5204189706237004154>➡️</emoji> <b>Parsing started.</b> "
            "This will clear all old triggers and scan the channel from scratch. Please wait..."
        ),
        "parsing_progress": (
            "<emoji document_id=5429411030960711866>💬</emoji> <b>Parsing in progress...</b>\n"
            "Processed <b>{}</b> messages."
        ),
        "stats_header": "📊 <b>Статистика использования триггеров:</b>\n<blockquote>",
        "stats_trigger": "🔷 {} ({})\n└ Использовано: {} раз(а)\nПоследнее: {}\n",
        "stats_empty": "😕 <b>Статистика пока не собрана...</b>\nИспользуйте триггеры, чтобы начать сбор статистики!",
        "stats_total": "</blockquote>\n📈 <b>Всего использований:</b> {}\n",
        "parsing_complete": (
            "<emoji document_id=5260726538302660868>✅</emoji> <b>Parsing complete!</b>\n"
            "Parsed trigger definitions:\n"
            "<b>{}</b> exact (<code>~</code>)\n"
            "<b>{}</b> contains (<code>~~</code>)\n"
            "<b>{}</b> exact+del (<code>~~~</code>)\n"
            "<b>{}</b> regex (<code>~|</code>)\n"
            "<b>{}</b> regex+del (<code>~~~|</code>)"
        ),
        "channel_error": (
            "<emoji document_id=5260342697075416641>❌</emoji> <b>Error accessing channel.</b> "
            "Make sure the ID is correct and you are a member of the channel."
            " Try forwarding any message from it to your Saved Messages."
        ),
        "add_trigger_error": (
            "<emoji document_id=5258474669769497337>❗️</emoji> <b>Failed to add trigger.</b>\n"
            "Make sure your userbot is a member of the source channel and has permission to post messages."
        ),
        "config_source_channel": "ID of the source channel with triggers and media/text.",
        "config_auto_parse_on_start": "Automatically run parsing when the module loads.",
        "trigger_added": "<emoji document_id=5260726538302660868>✅</emoji> <b>New response for trigger <code>{}</code> added.</b> <a href='{}'>Go to message</a>.",
        "must_be_reply": "<emoji document_id=5260450573768990626>➡️</emoji> <b>You must reply to a message.</b>",
        "no_trigger_specified": "<emoji document_id=5257965174979042426>📝</emoji> <b>You must specify a trigger.</b> Example: <code>.addtrigger ~hi</code>",
        "invalid_trigger_format": "<emoji document_id=5260342697075416641>❌</emoji> <b>Invalid trigger format.</b> Must start with <code>~</code>, <code>~~</code>, or <code>~~~</code>.",
        "processing_add": "<emoji document_id=5427181942934088912>💬</emoji> <b>Processing...</b>",
        "_cls_doc": "Sends media/text based on triggers. Formats: ~exact, ~~contains, ~~~exact+del, ~|regex, ~~~|regex+del.",
        "_cmd_doc_parsetriggers": "Scan the source channel to update triggers.",
        "_cmd_doc_addtrigger": "<reply to message> <trigger> - Add a new trigger.",
    }

    strings_ru = {
        "parsing_started": (
            "<emoji document_id=5204189706237004154>➡️</emoji> <b>Индексация начата.</b> "
            "Все старые триггеры будут удалены, канал будет просканирован заново. Пожалуйста, подождите..."
        ),
        "parsing_progress": (
            "<emoji document_id=5429411030960711866>💬</emoji> <b>Индексация в процессе...</b>\n"
            "Обработано <b>{}</b> сообщений."
        ),
        "parsing_complete": (
            "<emoji document_id=5260726538302660868>✅</emoji> <b>Индексация"
            " завершена!</b>\nОбработано определений триггеров:\n"
            "<b>{}</b> точных (<code>~</code>)\n"
            "<b>{}</b> по вхождению (<code>~~</code>)\n"
            "<b>{}</b> точных+удалить (<code>~~~</code>)\n"
            "<b>{}</b> regex (<code>~|</code>)\n"
            "<b>{}</b> regex+удалить (<code>~~~|</code>)"
        ),
        "channel_error": (
            "<emoji document_id=5260342697075416641>❌</emoji> <b>Ошибка доступа к"
            " каналу.</b> Убедитесь, что ID указан верно и вы состоите в канале."
            " Попробуйте переслать любое сообщение из него в 'Избранное'."
        ),
        "add_trigger_error": (
            "<emoji document_id=5258474669769497337>❗️</emoji> <b>Не удалось добавить триггер.</b>\n"
            "Убедитесь, что ваш юзербот является участником исходного канала и имеет права на отправку сообщений."
        ),
        "config_source_channel": "ID исходного канала с триггерами и медиа/текстом.",
        "config_auto_parse_on_start": "Автоматически запускать индексацию при загрузке модуля.",
        "trigger_added": "<emoji document_id=5260726538302660868>✅</emoji> <b>Новый ответ для триггера <code>{}</code> добавлен.</b> <a href='{}'>Перейти к сообщению</a>.",
        "must_be_reply": "<emoji document_id=5260450573768990626>➡️</emoji> <b>Нужно ответить на сообщение.</b>",
        "no_trigger_specified": "<emoji document_id=5257965174979042426>📝</emoji> <b>Нужно указать триггер.</b> Пример: <code>.addtrigger ~привет</code>",
        "invalid_trigger_format": "<emoji document_id=5260342697075416641>❌</emoji> <b>Неверный формат триггера.</b> Должен начинаться с <code>~</code>, <code>~~</code>, или <code>~~~</code>.",
        "processing_add": "<emoji document_id=5427181942934088912>💬</emoji> <b>Обработка...</b>",
        "_cls_doc": "Отправляет медиа/текст по триггерам. Форматы: ~точно, ~~содержит, ~~~точно+удал, ~|regex, ~~~|regex+удал.",
        "_cmd_doc_parsetriggers": "Сканировать исходный канал для обновления триггеров.",
        "_cmd_doc_addtrigger": "<ответ на сообщение> <триггер> - Добавить новый триггер.",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "source_channel_id",
                None,
                lambda: self.strings("config_source_channel"),
                validator=loader.validators.Integer(),
            ),
            loader.ConfigValue(
                "auto_parse_on_start",
                True,
                lambda: self.strings("config_auto_parse_on_start"),
                validator=loader.validators.Boolean(),
            )
        )
        self.triggers = {}
        self.stats = {}
        self._regex_cache = {}
        self._indexed_triggers = {
            'exact': {},
            'exact_delete': {},
            'contains': {},
            'regex': {},
            'regex_delete': {}
        }
        self.BATCH_SIZE = 200
        self.client = None
        self.db = None

    async def on_dlmod(self):
        """Вызывается после загрузки модуля для инициализации триггеров из БД."""
        self.triggers.update(self.db.get("SourceTrigger", "triggers", {}))
        self.stats.update(self.db.get("SourceTrigger", "stats", {}))
        self._index_triggers()

    async def client_ready(self, client, db):
        self.client = client
        self.db = db
        if self.config["auto_parse_on_start"]:
            logger.info("Auto-parsing triggers on startup...")
            await self._run_parser(message=None)

    def _get_source_channel(self):
        channel_id = self.config["source_channel_id"]
        return [channel_id] if channel_id else []

    def _compile_regex(self, pattern: str) -> Optional[re.Pattern]:
        """Компилирует и кэширует регулярное выражение."""
        if pattern not in self._regex_cache:
            try:
                self._regex_cache[pattern] = re.compile(pattern, re.IGNORECASE)
            except re.error:
                return None
        return self._regex_cache[pattern]

    def _index_triggers(self):
        """Индексирует триггеры для быстрого поиска."""
        self._indexed_triggers = {
            'exact': {},
            'exact_delete': {},
            'contains': {},
            'regex': {},
            'regex_delete': {}
        }
        
        for key, msg_ids in self.triggers.items():
            ttype, trigger = key.split("::", 1)
            if ttype in ('exact', 'exact_delete'):
                self._indexed_triggers[ttype][trigger] = msg_ids
            elif ttype == 'contains':
                self._indexed_triggers[ttype][trigger] = msg_ids
            elif ttype in ('regex', 'regex_delete'):
                if regex := self._compile_regex(trigger):
                    self._indexed_triggers[ttype][trigger] = (regex, msg_ids)

    async def _process_message_for_triggers(self, msg):
        """Processes a message to find a trigger definition and its target content."""
        if not msg or not getattr(msg, 'text', None): return None

        trigger_def_msg = msg
        content_msg = msg

        if msg.is_reply:
            replied = await msg.get_reply_message()
            if replied:
                content_msg = replied
            else:
                return None
        
        text = trigger_def_msg.text.strip()
        first_line = text.split('\n', 1)[0].strip()
        ttype, trigger = None, None
        
        # Regex for all trigger types starting with ~
        if re.match(r"^~{1,3}", first_line):
            if first_line.startswith("~~~"):
                content_after = first_line[3:].lstrip()
                if content_after.startswith("|"):
                    pattern = content_after[1:].strip()
                    if pattern:
                        try:
                            re.compile(pattern, re.IGNORECASE)
                            ttype, trigger = "regex_delete", pattern
                        except re.error: pass
                else:
                    ttype, trigger = "exact_delete", content_after.strip().lower()
            elif first_line.startswith("~~"):
                ttype, trigger = "contains", first_line[2:].strip().lower()
            elif first_line.startswith("~"):
                content_after = first_line[1:].lstrip()
                if content_after.startswith("|"):
                    pattern = content_after[1:].strip()
                    if pattern:
                        try:
                            re.compile(pattern, re.IGNORECASE)
                            ttype, trigger = "regex", pattern
                        except re.error: pass
                else:
                    ttype, trigger = "exact", content_after.strip().lower()
        
        if ttype and trigger:
            return ttype, trigger, content_msg.id
        return None

    async def _process_batch(self, tasks: list, triggers_dict: dict, counts_dict: dict, status_msg, total_processed: int):
        """Processes a batch of tasks and updates the data structures."""
        results = await asyncio.gather(*tasks)
        for result in results:
            if not result:
                continue
            ttype, trigger, msg_id = result
            
            key = f"{ttype}::{trigger}"
            if key not in triggers_dict:
                triggers_dict[key] = []
            
            if msg_id not in triggers_dict[key]:
                triggers_dict[key].append(msg_id)

            counts_dict[ttype] += 1
        
        if status_msg and total_processed % (self.BATCH_SIZE * 5) == 0:
            try:
                await utils.answer(status_msg, self.strings("parsing_progress").format(total_processed))
            except Exception:
                pass

    @loader.command(ru_doc="Показать статистику использования триггеров")
    async def trstats(self, message: Message):
        """Display trigger usage statistics"""
        if not self.stats:
            await utils.answer(message, self.strings['stats_empty'])
            return

        total_uses = 0
        text = self.strings['stats_header']
        
        sorted_stats = sorted(
            self.stats.items(),
            key=lambda x: x[1].get('count', 0) if isinstance(x[1], dict) else 0,
            reverse=True
        )
        
        for key, stat in sorted_stats:
            if not isinstance(stat, dict):
                continue
                
            count = stat.get('count', 0)
            last_used = stat.get('last_used', 'никогда')
            if isinstance(last_used, float):
                last_used = datetime.datetime.fromtimestamp(last_used).strftime('%d.%m.%Y %H:%M')
            
            total_uses += count
            ttype, trigger = key.split("::", 1)
            
            text += self.strings['stats_trigger'].format(
                utils.escape_html(trigger),
                ttype.replace("_", " "),
                count,
                last_used
            )

        text += self.strings['stats_total'].format(total_uses)
        await utils.answer(message, text)

    def _update_stats(self, trigger_key):
        """Обновляет статистику использования триггера."""
        if not isinstance(self.stats.get(trigger_key), dict):
            self.stats[trigger_key] = {'count': 0, 'last_used': 0}
            
        self.stats[trigger_key]['count'] = self.stats[trigger_key].get('count', 0) + 1
        self.stats[trigger_key]['last_used'] = datetime.datetime.now().timestamp()
        self.db.set("SourceTrigger", "stats", self.stats)

    async def _run_parser(self, message: Message = None):
        """Core logic for scanning the source channel and updating the trigger database.
        Runs silently if message is None."""
        
        if message:
            status_msg = await utils.answer(message, self.strings("parsing_started"))
        else:
            status_msg = None
        
        self.triggers.clear()
        
        counts = {"exact": 0, "contains": 0, "exact_delete": 0, "regex": 0, "regex_delete": 0}
        source_id = self.config["source_channel_id"]
        if not source_id:
            if message:
                await utils.answer(status_msg, self.strings("channel_error") + "\n<code>Source channel ID not configured.</code>")
            return

        try:
            channel_entity = await self.client.get_entity(source_id)
            tasks = []
            processed_count = 0

            async for msg in self.client.iter_messages(channel_entity, limit=None):
                tasks.append(asyncio.create_task(self._process_message_for_triggers(msg)))
                processed_count += 1
                if len(tasks) >= self.BATCH_SIZE:
                    await self._process_batch(tasks, self.triggers, counts, status_msg, processed_count)
                    tasks.clear()

            if tasks:
                await self._process_batch(tasks, self.triggers, counts, status_msg, processed_count)

            self.db.set("SourceTrigger", "triggers", self.triggers)
            
            if status_msg:
                await utils.answer(
                    status_msg,
                    self.strings("parsing_complete").format(
                        counts["exact"], counts["contains"], counts["exact_delete"], counts["regex"], counts["regex_delete"]
                    ),
                )
            
        except Exception as e:
            logger.exception("Failed to parse triggers")
            if status_msg:
                await utils.answer(status_msg, self.strings("channel_error") + f"\n<code>{utils.escape_html(str(e))}</code>")


    @loader.command(ru_doc="Обновить базу триггеров из канала")
    async def parsetriggers(self, message: Message):
        """Scans the source channel to update the trigger database."""
        await self._run_parser(message)

    def _parse_trigger_string(self, text: str):
        """Parses a raw trigger string into ttype and trigger."""
        text = text.strip()
        ttype, trigger = None, None
        if text.startswith("~~~"):
            content_after = text[3:].lstrip()
            if content_after.startswith("|"):
                pattern = content_after[1:].strip()
                if pattern:
                    try:
                        re.compile(pattern, re.IGNORECASE)
                        ttype, trigger = "regex_delete", pattern
                    except re.error: return None, None
            else:
                ttype, trigger = "exact_delete", content_after.strip().lower()
        elif text.startswith("~~"):
            ttype, trigger = "contains", text[2:].strip().lower()
        elif text.startswith("~"):
            content_after = text[1:].lstrip()
            if content_after.startswith("|"):
                pattern = content_after[1:].strip()
                if pattern:
                    try:
                        re.compile(pattern, re.IGNORECASE)
                        ttype, trigger = "regex", pattern
                    except re.error: return None, None
            else:
                ttype, trigger = "exact", content_after.strip().lower()
        return ttype, trigger

    @loader.command(ru_doc="<ответ на сообщение> <триггер> - Добавить новый триггер")
    async def addtrigger(self, message: Message):
        """<reply to message> <trigger> - Add a new trigger"""
        reply = await message.get_reply_message()
        if not reply:
            await utils.answer(message, self.strings("must_be_reply"))
            return

        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings("no_trigger_specified"))
            return

        ttype, trigger = self._parse_trigger_string(args)
        if not ttype or not trigger:
            await utils.answer(message, self.strings("invalid_trigger_format"))
            return
        
        status_msg = await utils.answer(message, self.strings("processing_add"))
        source_id = self.config["source_channel_id"]
        if not source_id:
            await utils.answer(status_msg, self.strings("channel_error") + "\n<code>Source channel ID not configured.</code>")
            return
        
        try:
            content_msg = await self.client.send_file(source_id, reply)
            trigger_msg = await self.client.send_message(source_id, args, reply_to=content_msg.id)
            
            key = f"{ttype}::{trigger}"
            if key not in self.triggers:
                self.triggers[key] = []
            
            if content_msg.id not in self.triggers[key]:
                self.triggers[key].append(content_msg.id)
            
            self.db.set("SourceTrigger", "triggers", self.triggers)
            
            channel_id_str = str(source_id).replace("-100", "")
            link = f"https://t.me/c/{channel_id_str}/{trigger_msg.id}"
            await utils.answer(status_msg, self.strings("trigger_added").format(utils.escape_html(args), link))
            
            if message.out:
                await message.delete()

        except Exception as e:
            logger.exception("Failed to add trigger")
            await utils.answer(status_msg, self.strings("add_trigger_error") + f"\n<code>{utils.escape_html(str(e))}</code>")


    @loader.watcher(chats=_get_source_channel, only_messages=True)
    async def source_channel_watcher(self, message: Message):
        """Watches the source channel for new posts and updates triggers automatically."""
        result = await self._process_message_for_triggers(message)
        if not result: return

        ttype, trigger, msg_id = result
        key = f"{ttype}::{trigger}"
        if key not in self.triggers:
            self.triggers[key] = []
        
        if msg_id not in self.triggers[key]:
            self.triggers[key].append(msg_id)

        self.db.set("SourceTrigger", "triggers", self.triggers)

    async def _process_and_send(self, trigger_message: Message, msg_id: int):
        """Helper to fetch, prepare, and send a single response message."""
        source_id = self.config["source_channel_id"]

        try:
            source_msg = await self.client.get_messages(source_id, ids=msg_id)
            if not source_msg: return

            caption = source_msg.text or ""
            if caption:
                first_line = caption.split('\n', 1)[0].strip()
                if re.match(r"^~{1,3}", first_line):
                    lines = caption.split('\n')
                    caption = '\n'.join(lines[1:]).strip()

            reply_to_id = trigger_message.reply_to_msg_id if trigger_message.is_reply else None
            
            if source_msg.media:
                await self.client.send_file(
                    trigger_message.peer_id,
                    source_msg, 
                    caption=caption or None,
                    reply_to=reply_to_id
                )
            elif caption:
                await utils.answer(trigger_message, caption, reply_to=reply_to_id)
            
        except Exception as e:
            logger.error(f"Error sending trigger response for msg_id {msg_id}: {e}")
            pass

    @loader.watcher(no_commands=True)
    async def watcher(self, message: Message):
        """Watches for outgoing messages and responds with media if a trigger is found."""
        if not hasattr(message, "out") or not message.out or not message.text:
            return

        text = message.raw_text
        low_text_stripped = text.strip().lower()

        matched_key = None

        exact_delete_key = f"exact_delete::{low_text_stripped}"
        exact_key = f"exact::{low_text_stripped}"

        if exact_delete_key in self.triggers:
            matched_key = exact_delete_key
        elif exact_key in self.triggers:
            matched_key = exact_key
        else:
            text_lower = text.lower()
            for pattern, (regex, msg_ids) in self._indexed_triggers['regex_delete'].items():
                if regex.fullmatch(text_lower):
                    matched_key = f"regex_delete::{pattern}"
                    break

            if not matched_key:
                for pattern, (regex, msg_ids) in self._indexed_triggers['regex'].items():
                    if regex.fullmatch(text_lower):
                        matched_key = f"regex::{pattern}"
                        break

            if not matched_key:
                for trigger, msg_ids in self._indexed_triggers['contains'].items():
                    if trigger in text_lower:
                        matched_key = f"contains::{trigger}"
                        break

        if matched_key:
            self._update_stats(matched_key)
            
            msg_ids = self.triggers[matched_key]
            if not msg_ids: return

            should_delete = "delete" in matched_key.split("::", 1)[0]
            
            tasks = [self._process_and_send(message, msg_id) for msg_id in msg_ids]
            await asyncio.gather(*tasks)
            
            if should_delete and message.out:
                await message.delete()