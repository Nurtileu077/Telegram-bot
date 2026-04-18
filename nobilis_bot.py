"""
Nobilis Education Bot v3
- Bitrix24 лиды через вебхук
- Фото к постам по рубрикам
- Умные CTA под каждую тему
"""

import os, asyncio, schedule, logging, random, httpx
from datetime import datetime
from dotenv import load_dotenv
from anthropic import Anthropic
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

BOT_TOKEN      = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID     = os.getenv("TELEGRAM_CHANNEL_ID")
MANAGER_ID     = int(os.getenv("TELEGRAM_MANAGER_ID", "0"))
BITRIX_WEBHOOK = "https://nobilis.bitrix24.kz/rest/1/62glok0fbqwwj936/"

ai = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


# ─────────────────────────────────────────────────────────────────
# ФОТО ПО РУБРИКАМ
# Unsplash — бесплатные фото без регистрации
# Замените ссылки на свои фото если хотите брендированные
# ─────────────────────────────────────────────────────────────────

RUBRIC_PHOTOS = {
    "📰 Новости": [
        "https://images.unsplash.com/photo-1523050854058-8df90110c9f1?w=800",  # университет
        "https://images.unsplash.com/photo-1541339907198-e08756dedf3f?w=800",  # диплом
        "https://images.unsplash.com/photo-1562774053-701939374585?w=800",  # кампус
    ],
    "📊 Статистика": [
        "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800",  # графики
        "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=800",  # аналитика
        "https://images.unsplash.com/photo-1504868584819-f8e8b4b6d7e3?w=800",  # данные
    ],
    "💡 Лайфхак": [
        "https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?w=800",  # учёба
        "https://images.unsplash.com/photo-1434030216411-0b793f4b4173?w=800",  # ноутбук
        "https://images.unsplash.com/photo-1513475382585-d06e58bcb0e0?w=800",  # идея
    ],
    "🏛 Разбор вуза": [
        "https://images.unsplash.com/photo-1607237138185-eedd9c632b0b?w=800",  # вуз
        "https://images.unsplash.com/photo-1590012314607-cda9d9b699ae?w=800",  # здание
        "https://images.unsplash.com/photo-1571260899304-425eee4c7efc?w=800",  # библиотека
    ],
    "🌍 Страна": [
        "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=800",  # лондон
        "https://images.unsplash.com/photo-1467269204594-9661b134dd2b?w=800",  # германия
        "https://images.unsplash.com/photo-1576502200916-3808e07386a5?w=800",  # амстердам
    ],
}

# ─────────────────────────────────────────────────────────────────
# УМНЫЕ CTA ПОД КАЖДУЮ РУБРИКУ
# ─────────────────────────────────────────────────────────────────

RUBRIC_CTA = {
    "📰 Новости": [
        "Как это изменение влияет на ваши планы? Разберём → @nobilissbot",
        "Успеваете ли вы под новые требования? Проверьте → @nobilissbot",
        "Что это значит лично для вас — узнайте за 15 минут → @nobilissbot",
    ],
    "📊 Статистика": [
        "Где вы в этой статистике? Проверьте свои шансы → @nobilissbot",
        "Попадёте в эти цифры? Разберём ваш профиль → @nobilissbot",
        "Хотите быть в топе этой статистики — начните здесь → @nobilissbot",
    ],
    "💡 Лайфхак": [
        "Применим этот лайфхак к вашей заявке → @nobilissbot",
        "Проверим вашу заявку по этому чек-листу → @nobilissbot",
        "Разберём вашу ситуацию и найдём слабые места → @nobilissbot",
    ],
    "🏛 Разбор вуза": [
        "Подходит ли этот вуз именно вам? Проверим → @nobilissbot",
        "Реальны ли ваши шансы на этот вуз — узнайте честно → @nobilissbot",
        "Есть вопросы по этому университету? Ответим → @nobilissbot",
    ],
    "🌍 Страна": [
        "Эта страна для вас? Подберём программу под ваш профиль → @nobilissbot",
        "Хотите туда? Расскажем что реально нужно → @nobilissbot",
        "Узнайте ваши шансы на поступление в эту страну → @nobilissbot",
    ],
}

# ─────────────────────────────────────────────────────────────────
# КОНТЕНТ-ПЛАН (расписание рубрик по дням и времени)
# ─────────────────────────────────────────────────────────────────

DAILY_SCHEDULE = {
    0: ["📰 Новости",    "💡 Лайфхак",     "📊 Статистика"],   # Пн
    1: ["🏛 Разбор вуза","📰 Новости",     "💡 Лайфхак"],      # Вт
    2: ["🌍 Страна",     "💡 Лайфхак",     "📰 Новости"],      # Ср
    3: ["📰 Новости",    "🏛 Разбор вуза", "📊 Статистика"],   # Чт
    4: ["💡 Лайфхак",    "📰 Новости",     "🌍 Страна"],       # Пт
    5: ["📊 Статистика", "🏛 Разбор вуза", "💡 Лайфхак"],      # Сб
    6: ["🌍 Страна",     "📰 Новости",     "💡 Лайфхак"],      # Вс
}

PUBLISH_TIMES = ["09:00", "13:00", "19:00"]

RUBRICS = {
    "📰 Новости": [
        "Оксфорд и Кембридж ужесточили требования к IELTS для 2026 года",
        "Германия упрощает студенческие визы для граждан Казахстана",
        "Канада ограничила выдачу study permit — что это значит",
        "Нидерланды вводят ограничения на англоязычные программы",
        "QS World University Rankings 2025 вышел — главные неожиданности",
        "Австралия ужесточила финансовые требования для студенческих виз",
        "США отменили требование GRE в топ-университетах — список вузов",
        "Швейцария открыла стипендии для студентов из Центральной Азии",
        "Япония запустила программу привлечения иностранных студентов",
        "Изменения в UCAS 2026: новые правила подачи документов в UK",
        "Франция удвоила квоту на стипендии Eiffel для Центральной Азии",
        "ОАЭ расширяет список университетов с государственным финансированием",
    ],
    "📊 Статистика": [
        "Сколько студентов из Казахстана учатся за рубежом — данные 2024",
        "Средняя стоимость обучения за рубежом выросла на 12% — разбор",
        "Какие специальности дают наибольшую отдачу после зарубежного диплома",
        "Топ-10 популярных направлений для казахстанских студентов в 2024",
        "Сколько зарабатывают выпускники топ-университетов через 5 лет",
        "Процент отказов в студенческой визе по странам — реальные цифры",
        "Рейтинг вузов по трудоустройству выпускников QS 2025",
        "Сколько студентов остаются работать за рубежом после учёбы",
    ],
    "💡 Лайфхак": [
        "Как поднять IELTS с 6.0 до 7.0 за 2 месяца — конкретный план",
        "5 ошибок в мотивационном письме из-за которых отказывают топ-вузы",
        "Как найти научного руководителя до подачи документов",
        "Чек-лист: что проверить в оффере от университета",
        "Как получить рекомендательное письмо у профессора который вас не знает",
        "Ранняя подача vs обычный дедлайн — реальная разница в шансах",
        "Финансовый план студента за рубежом: как рассчитать бюджет",
        "Блокированный счёт для немецкой визы — как открыть из Казахстана",
        "Как написать CV в европейском формате — 7 отличий от казахстанского",
    ],
    "🏛 Разбор вуза": [
        "University of Amsterdam — стоит ли оно того честный разбор",
        "TU Munich изнутри: программы, стоимость, жизнь в Мюнхене",
        "LSE vs Warwick: куда поступать на Finance и Economics",
        "University of Waterloo — почему он лучший для IT-специалистов",
        "ETH Zurich: как поступить в лучший технический университет Европы",
        "University of Melbourne: плюсы, минусы, реальная стоимость жизни",
        "McGill University: французский Монреаль и один из лучших вузов Канады",
        "King's College London: медицина, право и гуманитарные науки в Лондоне",
        "KAIST: бесплатное образование плюс стипендия в топ-100 Кореи",
        "Durham University: Russell Group без лондонских цен",
    ],
    "🌍 Страна": [
        "Учёба в Финляндии: бесплатно ли, как поступить, где работать потом",
        "Дания для студентов: дорого, но есть нюансы меняющие картину",
        "Польша как старт в Европу: доступно, качественно, с перспективой",
        "Ирландия: страна где Google, Meta и Apple дают работу выпускникам",
        "Португалия: европейский диплом с южным климатом и низкими ценами",
        "Австрия: Вена и почти бесплатные государственные университеты",
        "Норвегия: бесплатное образование даже для иностранцев",
        "Малайзия: азиатское образование с европейскими дипломами за треть цены",
    ],
}

used_topics: set = set()

def pick_topic(rubric: str) -> str:
    topics = RUBRICS[rubric]
    available = [t for t in topics if t not in used_topics]
    if not available:
        used_topics.clear()
        available = topics
    topic = random.choice(available)
    used_topics.add(topic)
    return topic

# ─────────────────────────────────────────────────────────────────
# ГЕНЕРАЦИЯ ПОСТА
# ─────────────────────────────────────────────────────────────────

SYSTEM_PROMPTS = {
    "📰 Новости": """Ты редактор Telegram-канала Nobilis Education (Казахстан).
Пиши как умный журналист: что случилось → почему важно → что делать студенту.
Стиль: живой, конкретный, без воды. 220-300 слов. Абзацы по 2-3 предложения.
Эмодзи: 1 на блок, не в каждом предложении. Без "данный", без "в заключение".""",

    "📊 Статистика": """Ты аналитик Nobilis Education. Начинай с самой неожиданной цифры.
Объясняй что каждая цифра значит для обычного студента из Казахстана.
Сравнивай: рост/падение, страна A vs B, этот год vs прошлый.
220-300 слов. Конкретика, никаких общих слов.""",

    "💡 Лайфхак": """Ты эксперт Nobilis Education с опытом сотен заявок.
Давай конкретный алгоритм, не общие советы. Называй реальные инструменты и сервисы.
Тон: "мы в Nobilis видели сотни заявок, вот что реально работает".
200-280 слов. Практично, применимо сегодня.""",

    "🏛 Разбор вуза": """Ты консультант Nobilis Education. Разбирай честно: плюсы И минусы.
Структура: факты → программы → стоимость → реальность → вердикт для кого подходит.
Не хвали всё подряд — честность ценнее. 250-320 слов.""",

    "🌍 Страна": """Ты эксперт Nobilis по международному образованию.
Давай факты которые удивляют, не банальщину из Википедии.
Реальная стоимость жизни + обучения. Перспективы после учёбы.
Для кого идеально, для кого нет. 230-300 слов.""",
}

def generate_post(rubric: str, topic: str) -> str:
    cta = random.choice(RUBRIC_CTA[rubric])
    system = SYSTEM_PROMPTS.get(rubric, SYSTEM_PROMPTS["📰 Новости"])
    system += f"\n\nВ конце поста добавь эту строку:\n👉 {cta}"

    # Для новостей и статистики — ищем реальные данные
    use_search = rubric in ["📰 Новости", "📊 Статистика"]
    kwargs = dict(
        model="claude-opus-4-5",
        max_tokens=1200,
        system=system,
        messages=[{"role": "user", "content":
            f"Напиши пост. Рубрика: {rubric}. Тема: {topic}"
            + (" Найди свежие реальные данные по теме." if use_search else "")}]
    )
    if use_search:
        kwargs["tools"] = [{"type": "web_search_20250305", "name": "web_search"}]

    resp = ai.messages.create(**kwargs)
    return "".join(b.text for b in resp.content if hasattr(b, "text")).strip()


def search_breaking_news() -> str | None:
    """Ищет реальные свежие новости об образовании за рубежом."""
    try:
        cta = random.choice(RUBRIC_CTA["📰 Новости"])
        resp = ai.messages.create(
            model="claude-opus-4-5",
            max_tokens=1200,
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            system=SYSTEM_PROMPTS["📰 Новости"] + f"""

Ищи ТОЛЬКО реальные новости за последние 2-4 недели.
Темы: поступление в университеты, изменения визовых требований, новые стипендии,
рейтинги вузов, правила приёма — всё что важно студентам из Казахстана.

Если нашёл реально важную новость — напиши пост с реальными фактами.
Если ничего срочного нет — ответь одним словом: NOTHING

В конце поста: 👉 {cta}""",
            messages=[{"role": "user", "content":
                "Найди самую свежую важную новость об университетах или поступлении за рубеж "
                "которая важна для казахстанских студентов прямо сейчас."}]
        )
        text = "".join(b.text for b in resp.content if hasattr(b, "text")).strip()
        if "NOTHING" in text or len(text) < 150:
            return None
        return text
    except Exception as e:
        log.error(f"Breaking news search error: {e}")
        return None

# ─────────────────────────────────────────────────────────────────
# ПУБЛИКАЦИЯ С ФОТО
# ─────────────────────────────────────────────────────────────────

async def publish(app: Application, slot: int):
    try:
        weekday  = datetime.now().weekday()
        rubric   = DAILY_SCHEDULE[weekday][slot]
        topic    = pick_topic(rubric)
        photo    = random.choice(RUBRIC_PHOTOS[rubric])

        log.info(f"Generating [{rubric}] — {topic}")
        text = generate_post(rubric, topic)

        await app.bot.send_photo(
            chat_id=CHANNEL_ID,
            photo=photo,
            caption=text,
            parse_mode="HTML"
        )
        log.info("✅ Published with photo")
    except Exception as e:
        log.error(f"Publish error: {e}")
        try:
            await app.bot.send_message(
                chat_id=CHANNEL_ID, text=text,
                parse_mode="HTML", disable_web_page_preview=True
            )
        except:
            pass

async def check_and_publish_breaking(app: Application):
    """Проверяет реальные новости каждые 3 часа."""
    try:
        log.info("🔍 Checking breaking news...")
        text = search_breaking_news()
        if text:
            photo = random.choice(RUBRIC_PHOTOS["📰 Новости"])
            try:
                await app.bot.send_photo(
                    chat_id=CHANNEL_ID, photo=photo,
                    caption=f"🔴 <b>Срочно</b>\n\n{text}", parse_mode="HTML"
                )
            except:
                await app.bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=f"🔴 <b>Срочно</b>\n\n{text}", parse_mode="HTML"
                )
            log.info("✅ Breaking news published")
        else:
            log.info("No breaking news")
    except Exception as e:
        log.error(f"Breaking check error: {e}")


def setup_schedule(app: Application):
    loop = asyncio.get_event_loop()
    for i, t in enumerate(PUBLISH_TIMES):
        slot = i
        schedule.every().day.at(t).do(lambda s=slot: loop.create_task(publish(app, s)))

    # Реальные новости — каждые 3 часа
    schedule.every(3).hours.do(lambda: loop.create_task(check_and_publish_breaking(app)))

    async def runner():
        while True:
            schedule.run_pending()
            await asyncio.sleep(60)
    loop.create_task(runner())

# ─────────────────────────────────────────────────────────────────
# БИТРИКС24 — создание лида
# ─────────────────────────────────────────────────────────────────

async def create_bitrix_lead(user_id: int, username: str, session: dict):
    try:
        name = username or f"TG_{user_id}"
        fields = {
            "TITLE":      f"Telegram лид — {name}",
            "NAME":       name,
            "SOURCE_ID":  "WEB",
            "SOURCE_DESCRIPTION": "Telegram бот Nobilis",
            "COMMENTS": (
                f"Telegram: @{username or user_id}\n"
                f"Страна: {session.get('country', '—')}\n"
                f"Уровень: {session.get('degree', '—')}\n"
                f"Направление: {session.get('field', '—')}\n"
                f"Бюджет: {session.get('budget', '—')}\n"
                f"Ссылка: tg://user?id={user_id}"
            ),
            "UF_CRM_LEAD_COUNTRY":  session.get('country', ''),
            "UF_CRM_LEAD_DEGREE":   session.get('degree', ''),
        }
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{BITRIX_WEBHOOK}crm.lead.add.json",
                json={"fields": fields},
                timeout=10
            )
            data = r.json()
            if data.get("result"):
                log.info(f"✅ Bitrix lead created: {data['result']}")
            else:
                log.error(f"Bitrix error: {data}")
    except Exception as e:
        log.error(f"Bitrix lead error: {e}")

# ─────────────────────────────────────────────────────────────────
# БОТ — КВАЛИФИКАЦИЯ ЛИДОВ
# ─────────────────────────────────────────────────────────────────

user_sessions: dict[int, dict] = {}

QUESTIONS = [
    ("country", "👋 Привет! Я помогу подобрать программу за рубежом.\n\nКакая страна интересует?",
     [["🇬🇧 UK", "🇩🇪 Германия", "🇨🇦 Канада"],
      ["🇳🇱 Нидерланды", "🇦🇺 Австралия", "🇺🇸 США"],
      ["🇨🇭 Швейцария", "🇦🇪 ОАЭ", "Другое"]]),

    ("degree", "🎓 Какой уровень образования?",
     [["Бакалавриат", "Магистратура", "MBA", "PhD"]]),

    ("field", "📚 Направление?",
     [["IT / CS", "Инженерия"],
      ["Business / Finance", "Medicine"],
      ["Law / Social", "Design / Arts"],
      ["Sciences", "Другое"]]),

    ("budget", "💰 Годовой бюджет на обучение?",
     [["До $10K", "$10K–$25K", "$25K–$50K", "$50K+"]]),
]

async def send_question(chat_id: int, step: int, ctx: ContextTypes.DEFAULT_TYPE):
    key, text, rows = QUESTIONS[step]
    kb = [[InlineKeyboardButton(o, callback_data=f"q:{step}:{o}") for o in row] for row in rows]
    await ctx.bot.send_message(chat_id=chat_id, text=text,
                               reply_markup=InlineKeyboardMarkup(kb))

async def notify_manager(user_id, username, session, ctx):
    if not MANAGER_ID:
        return
    msg = (
        f"🔥 <b>Новый лид из Telegram!</b>\n"
        f"👤 @{username or user_id} (id: {user_id})\n\n"
        f"🌍 {session.get('country')}  |  🎓 {session.get('degree')}\n"
        f"📚 {session.get('field')}  |  💰 {session.get('budget')}\n\n"
        f"✅ Лид создан в Битрикс24\n"
        f"<a href='tg://user?id={user_id}'>💬 Написать клиенту</a>"
    )
    await ctx.bot.send_message(chat_id=MANAGER_ID, text=msg, parse_mode="HTML")

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user_sessions[uid] = {"step": 0}
    await send_question(uid, 0, ctx)

async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    is_manager = update.effective_user.id == MANAGER_ID
    text = (
        "ℹ️ <b>Nobilis Education</b>\n\n"
        "Помогаем поступить в лучшие университеты мира.\n\n"
        "/start — подбор программы\n"
        "/consult — бесплатная консультация"
    )
    if is_manager:
        text += (
            "\n\n<b>Команды менеджера:</b>\n"
            "/post — опубликовать пост прямо сейчас\n"
            "/news — проверить и опубликовать свежие новости"
        )
    await update.message.reply_text(text, parse_mode="HTML")


async def cmd_post(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Публикует пост прямо сейчас — только для менеджера."""
    if update.effective_user.id != MANAGER_ID:
        return
    msg = await update.message.reply_text("⏳ Генерирую пост...")
    try:
        weekday = datetime.now().weekday()
        hour    = datetime.now().hour
        slot    = 0 if hour < 11 else (1 if hour < 16 else 2)
        rubric  = DAILY_SCHEDULE[weekday][slot]
        topic   = pick_topic(rubric)
        photo   = random.choice(RUBRIC_PHOTOS[rubric])
        text    = generate_post(rubric, topic)
        try:
            await ctx.bot.send_photo(
                chat_id=CHANNEL_ID, photo=photo,
                caption=text, parse_mode="HTML"
            )
        except:
            await ctx.bot.send_message(
                chat_id=CHANNEL_ID, text=text, parse_mode="HTML"
            )
        await msg.edit_text(f"✅ Опубликовано!\nРубрика: {rubric}\nТема: {topic}")
    except Exception as e:
        await msg.edit_text(f"❌ Ошибка: {e}")


async def cmd_news(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Ищет и публикует реальные свежие новости — только для менеджера."""
    if update.effective_user.id != MANAGER_ID:
        return
    msg = await update.message.reply_text("🔍 Ищу свежие новости...")
    try:
        text = search_breaking_news()
        if text:
            photo = random.choice(RUBRIC_PHOTOS["📰 Новости"])
            try:
                await ctx.bot.send_photo(
                    chat_id=CHANNEL_ID, photo=photo,
                    caption=f"🔴 <b>Срочно</b>\n\n{text}", parse_mode="HTML"
                )
            except:
                await ctx.bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=f"🔴 <b>Срочно</b>\n\n{text}", parse_mode="HTML"
                )
            await msg.edit_text("✅ Свежая новость опубликована!")
        else:
            await msg.edit_text("ℹ️ Срочных новостей сейчас нет. Попробуйте позже.")
    except Exception as e:
        await msg.edit_text(f"❌ Ошибка: {e}")

async def cmd_consult(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    await update.message.reply_text(
        "📞 Оставьте данные и мы свяжемся сегодня:\n\n"
        "— Ваше имя\n— Интересующая страна\n— Удобное время для звонка"
    )
    if MANAGER_ID:
        await ctx.bot.send_message(
            chat_id=MANAGER_ID,
            text=f"📞 <b>Запрос консультации</b>\n👤 @{u.username or u.id} (id: {u.id})",
            parse_mode="HTML"
        )

async def handle_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id

    if not q.data.startswith("q:"):
        return

    _, step_s, answer = q.data.split(":", 2)
    step = int(step_s)
    key  = QUESTIONS[step][0]

    if uid not in user_sessions:
        user_sessions[uid] = {}
    user_sessions[uid][key] = answer

    nxt = step + 1
    if nxt < len(QUESTIONS):
        user_sessions[uid]["step"] = nxt
        await send_question(uid, nxt, ctx)
    else:
        s = user_sessions[uid]
        await ctx.bot.send_message(
            chat_id=uid,
            text=(
                f"✅ <b>Принято!</b>\n\n"
                f"🌍 {s.get('country')}  •  🎓 {s.get('degree')}\n"
                f"📚 {s.get('field')}  •  💰 {s.get('budget')}\n\n"
                "Наш консультант подготовит список университетов "
                "и напишет вам в течение рабочего дня. 🙌"
            ),
            parse_mode="HTML"
        )
        # Отправляем в Битрикс и менеджеру параллельно
        await asyncio.gather(
            create_bitrix_lead(uid, q.from_user.username or "", s),
            notify_manager(uid, q.from_user.username or "", s, ctx)
        )

async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    text = update.message.text
    await update.message.reply_text(
        "📨 Получили! Консультант ответит в течение рабочего дня.\n\n"
        "Для быстрого подбора программы — /start"
    )
    if MANAGER_ID:
        await ctx.bot.send_message(
            chat_id=MANAGER_ID,
            text=(
                f"💬 <b>Новое сообщение</b>\n"
                f"👤 @{u.username or u.id} (id: {u.id})\n\n"
                f"<i>{text}</i>\n\n"
                f"<a href='tg://user?id={u.id}'>Ответить</a>"
            ),
            parse_mode="HTML"
        )

# ─────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",   cmd_start))
    app.add_handler(CommandHandler("help",    cmd_help))
    app.add_handler(CommandHandler("consult", cmd_consult))
    app.add_handler(CommandHandler("post",    cmd_post))   # публикует сейчас
    app.add_handler(CommandHandler("news",    cmd_news))   # ищет реальные новости
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    async def on_startup(a):
        setup_schedule(a)
        log.info("🚀 Nobilis Bot v3 started — Bitrix24 + Photos enabled")

    app.post_init = on_startup
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
