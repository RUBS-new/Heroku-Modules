# ========================
# ✨ DEVELOPER: @RUBS_New ✨
# ========================
# meta developer: @RUBS_New
# meta banner: https://raw.githubusercontent.com/RUBS-new/Heroku-Modules/refs/heads/main/banner/banner_newyear.png
# meta pic: https://raw.githubusercontent.com/RUBS-new/Heroku-Modules/refs/heads/main/banner/banner_newyear.png
# meta name: NewYearCountdown
# scope: hikka_only
# meta version: 1.2.5 

import datetime
import random
import asyncio 
from .. import loader, utils
from telethon.tl.patched import Message
import logging

logger = logging.getLogger(__name__)

DEFAULT_BANNER_URL = "https://raw.githubusercontent.com/RUBS-new/Heroku-Modules/refs/heads/main/banner/banner_newyear.png"

@loader.tds
class NewYearCountdownMod(loader.Module):
    """
    Показывает, сколько осталось до Нового года с автообновлением.
    ⚙️ Настройки: .cfg NewYearCountdown
    """
    
    def config_complete(self):
        if self.config["Banner URL"] == "CHANGE_ME":
            self.config["Banner URL"] = DEFAULT_BANNER_URL

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "Banner URL",
                "CHANGE_ME",
                lambda: "URL-адрес картинки для отображения вместе с отсчётом. "
                        "Если URL не задан, используется баннер из метаданных модуля.",
            ),
            loader.ConfigValue(
                "UpdateIntervalSeconds",
                5,  
                lambda: "Интервал обновления таймера (в секундах). Рекомендуется: 60 (1 минута). Минимум: 5 секунд.",
            ),
            loader.ConfigValue(
                "TotalDurationSeconds",
                15, 
                lambda: "Общая продолжительность работы таймера (в секундах). После этого времени обновление сообщения прекратится.",
            ),
        )
        self.messages = [
            "✨ Скоро будет ёлка и мандарины! ✨",
            "🎁 Пора готовить подарки! 🎁",
            "🌟 Новый год уже совсем близко! 🌟",
            "💫 Время загадывать желания! 💫",
            "🍽️ Готовьте оливье! 🍽️",
            "🎄 Скоро будем наряжать ёлку! 🎄",
            "🎅 Дед Мороз уже в пути! 🎅",
            "📝 Пора писать список желаний! ✨",
            "✨ Скоро будет самая волшебная ночь в году! ✨",
            "🌠 Время чудес приближается! 🌠",
            "❄️ Пусть Новый год принесёт много радости! ❄️",
            "🎆 До волшебства осталось совсем немного! 🎆"
        ]
        self.active_timers = {} 


    strings = {
        "name": "NewYearCountdown",
        "countdown": (
            "🎄 <b>══════ New Year {next_year} ══════</b> 🎄\n\n"
            "<emoji document_id=5298599677461216652>🎆</emoji> <b>До Нового {next_year} года осталось:</b>\n\n"
            "<blockquote>🎇 <b>Дней:</b> <code>{days}</code>\n"
            "❄️ <b>Часов:</b> <code>{hours}</code>\n"
            "🎁 <b>Минут:</b> <code>{minutes}</code>\n"
            "⭐️ <b>Секунд:</b> <code>{seconds}</code></blockquote>\n\n"
            "🎅 <i>{message}</i>\n\n"
            "❆═══════════════════════❆"
        ),
        "no_photo": "<b>🎄 До Нового {next_year} года осталось:</b>\n\n{countdown_text}\n\n<i>⚠️ Баннер не найден. Проверьте настройки модуля.</i>",
        "update_stopped": "⏸️ <b>Обновление остановлено.</b> Достигнута максимальная продолжительность таймера ({duration} сек) или команда остановлена.",
        "timer_running": "⚠️ **Таймер уже запущен** в этом чате. Для его остановки используйте команду `.stopcountdown`.",
        "no_active_timer": "⚠️ **Нет активного таймера** в этом чате."
    }
    
    def _get_countdown(self):
        now = datetime.datetime.now()
        next_year = now.year + 1
        new_year = datetime.datetime(next_year, 1, 1)
        delta = new_year - now

        days = delta.days
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60
        seconds = delta.seconds % 60

        message = random.choice(self.messages)

        return {
            "next_year": next_year,
            "days": days,
            "hours": hours,
            "minutes": minutes,
            "seconds": seconds,
            "message": message
        }

    async def _update_loop(self, chat_id, status_msg, photo_url, update_interval, total_duration):
        """Внутренняя функция для цикла обновления сообщения."""
        start_time = datetime.datetime.now()
        
        try:
            while (datetime.datetime.now() - start_time).total_seconds() < total_duration:
                # Ожидание интервала
                await asyncio.sleep(update_interval)

                # Проверка, не удалено ли сообщение
                if not status_msg.media and not status_msg.text:
                    break 

                countdown_data = self._get_countdown()
                new_caption = self.strings["countdown"].format(**countdown_data)

                # Используем text= вместо caption= при редактировании
                if countdown_data["days"] >= 0:
                    await status_msg.edit(text=new_caption, file=photo_url, parse_mode="HTML")
                else:
                    break # Новый год наступил

            # Используем text= вместо caption= для завершающего сообщения
            await status_msg.edit(text=self.strings["update_stopped"].format(duration=total_duration), file=photo_url, parse_mode="HTML")
            
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in NewYear countdown loop: {e}")
        finally:
            if chat_id in self.active_timers:
                del self.active_timers[chat_id]


    @loader.command(ru_doc="Показать и запустить отсчёт до Нового года с автообновлением.")
    async def newyear(self, message: Message):
        
        chat_id = utils.get_chat_id(message)
        
        if chat_id in self.active_timers:
            await utils.answer(message, self.strings["timer_running"])
            return

        update_interval = max(5, self.config["UpdateIntervalSeconds"]) 
        total_duration = max(update_interval, self.config["TotalDurationSeconds"])

        countdown = self._get_countdown()
        caption_text = self.strings["countdown"].format(**countdown)
        photo_url = self.config["Banner URL"]
        
        status_message = None

        if photo_url and photo_url != "CHANGE_ME":
            try:
                # При отправке медиа используется caption
                status_message = await message.client.send_file(
                    message.to_id, 
                    photo_url, 
                    caption=caption_text, 
                    parse_mode="HTML" 
                )
                await message.delete() 
            except Exception as e:
                logger.warning(f"Failed to send photo: {e}")
                photo_url = None 
                
        if status_message is None:
            text_only = caption_text.replace("🎄 <b>══════ New Year {next_year} ══════</b> 🎄\n\n".format(**countdown), "")
            output = self.strings["no_photo"].format(next_year=countdown["next_year"], countdown_text=text_only)
            status_message = await utils.answer(message, output)
            await message.delete() 


        task = asyncio.create_task(
            self._update_loop(chat_id, status_message, photo_url, update_interval, total_duration)
        )
        self.active_timers[chat_id] = task


    @loader.command(ru_doc="Остановить запущенный отсчёт до Нового года.")
    async def stopcountdown(self, message: Message):
        """Останавливает активный таймер."""
        
        chat_id = utils.get_chat_id(message)
        
        if chat_id in self.active_timers:
            task = self.active_timers[chat_id]
            task.cancel()
            await utils.answer(message, "✅ **Таймер успешно остановлен**.")
            
            if chat_id in self.active_timers:
                del self.active_timers[chat_id] 
        else:
            await utils.answer(message, self.strings["no_active_timer"])