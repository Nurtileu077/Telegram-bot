"""
Nobilis Education — AI News Publisher
======================================
Канал = новостное медиа об образовании за рубежом.

Рубрики:
  📰 Новости      — изменения в вузах, требованиях, визах, рейтингах
  📊 Статистика   — цифры, тренды, рейтинги
  💡 Лайфхак      — конкретные советы по поступлению
  🏛 Вуз недели   — разбор конкретного университета
  🌍 Страна       — обзор направления
  🎓 Nobilis      — вы пишете сами (бот не трогает)

Установка:
  pip install anthropic python-telegram-bot schedule python-dotenv

.env:
  TELEGRAM_BOT_TOKEN=...
  TELEGRAM_CHANNEL_ID=@nobilis_education
  TELEGRAM_MANAGER_ID=123456789
  ANTHROPIC_API_KEY=sk-ant-...
"""

import os, asyncio, schedule, logging, random
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

BOT_TOKEN   = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID  = os.getenv("TELEGRAM_CHANNEL_ID")
MANAGER_ID  = int(os.getenv("TELEGRAM_MANAGER_ID", "0"))
ai          = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


# ─────────────────────────────────────────────────────────────────
# РУБРИКИ — каждый пост получает одну рубрику и тему
# ─────────────────────────────────────────────────────────────────

RUBRICS = {

    "📰 Новости": [
        "Оксфорд и Кембридж ужесточили требования к IELTS для 2026 года — что изменилось",
        "Германия упрощает студенческие визы: новые правила для граждан Казахстана",
        "Канада ограничила выдачу study permit — что это значит для поступающих",
        "Нидерланды вводят ограничения на англоязычные программы — какие вузы затронуты",
        "QS World University Rankings 2025 вышел — главные неожиданности и взлёты",
        "THE Rankings 2025: Европа обгоняет США по количеству топ-вузов",
        "Австралия ужесточила финансовые требования для студенческих виз",
        "Великобритания снизила прожиточный минимум для Graduate Route Visa",
        "США отменили требование GRE в ряде топ-университетов — список вузов",
        "Швейцария открыла новые стипендии для студентов из Центральной Азии",
        "Япония запустила новую программу привлечения иностранных студентов",
        "ОАЭ расширяет список университетов с государственным финансированием",
        "Франция удвоила квоту на стипендии Eiffel для Центральной Азии",
        "Изменения в UCAS 2026: новые правила подачи документов в вузы Великобритании",
        "Дубай открывает новый кампус топового европейского университета",
    ],

    "📊 Статистика": [
        "Сколько студентов из Казахстана учатся за рубежом — свежие данные 2024",
        "Средняя стоимость обучения за рубежом выросла на 12% — разбор по странам",
        "Какие специальности приносят наибольшую отдачу после зарубежного диплома",
        "Топ-10 самых популярных направлений для казахстанских студентов в 2024",
        "Сколько зарабатывают выпускники топ-университетов через 5 лет",
        "Статистика: сколько студентов получают стипендии vs платят сами",
        "Процент отказов в студенческой визе по странам — реальные цифры",
        "Рейтинг вузов по трудоустройству выпускников QS Graduate Employability 2025",
        "Средний IELTS балл поступивших в топ-50 университетов мира",
        "Сколько студентов остаются работать за рубежом после учёбы — по странам",
        "Рост заработной платы после MBA в разных странах — сравнение данных",
        "Инфляция стоимости обучения: как изменились цены за 5 лет",
    ],

    "💡 Лайфхак": [
        "Как поднять IELTS с 6.0 до 7.0 за 2 месяца — конкретный план",
        "5 ошибок в мотивационном письме, из-за которых отказывают топ-вузы",
        "Как найти научного руководителя в иностранном университете до подачи документов",
        "Чек-лист: что проверить в оффере от университета прежде чем принять",
        "Как получить рекомендательное письмо у профессора, который вас почти не знает",
        "LinkedIn для поступающих: как правильно заполнить профиль под вузовские требования",
        "Как читать отзывы студентов о вузах — что важно, что игнорировать",
        "Ранняя подача vs обычный дедлайн — в чём реальная разница шансов",
        "Как сравнить офферы от двух университетов и выбрать правильно",
        "Финансовый план студента за рубежом: как рассчитать реальный бюджет",
        "Как пройти визовое собеседование — частые вопросы и правильные ответы",
        "Как найти жильё в новом городе до приезда — пошаговый алгоритм",
        "Блокированный счёт для немецкой визы — как открыть из Казахстана за 3 дня",
        "Апостиль на диплом: где делать, сколько стоит, сколько ждать",
        "Как написать CV в европейском формате — 7 отличий от казахстанского",
    ],

    "🏛 Разбор вуза": [
        "University of Amsterdam: всё что нужно знать перед подачей документов",
        "TU Munich изнутри: программы, стоимость, жизнь в Мюнхене",
        "LSE vs Warwick: куда поступать на Finance и Economics",
        "University of Waterloo — почему он лучший для IT-специалистов",
        "ETH Zurich: как поступить в лучший технический университет Европы",
        "University of Melbourne: плюсы, минусы, реальная стоимость жизни",
        "McGill University: французский Монреаль и один из лучших вузов Канады",
        "NUS Singapore: топ-10 мира и ворота в азиатский рынок",
        "Erasmus University Rotterdam: бизнес-образование с нидерландским характером",
        "King's College London: медицина, право и гуманитарные науки в центре Лондона",
        "University of Edinburgh: шотландское образование с мировым именем",
        "Aalto University: дизайн, инженерия и стартапы в Хельсинки",
        "KAIST: бесплатное образование + стипендия в топ-100 университете Кореи",
        "Sciences Po Paris: лучший вуз мира по международным отношениям",
        "Durham University: Russell Group без лондонских цен",
    ],

    "🌍 Страна": [
        "Учёба в Финляндии: бесплатно ли, как поступить, где работать потом",
        "Дания для студентов: дорого, но есть нюансы которые меняют картину",
        "Польша как старт в Европу: доступно, качественно, с перспективой",
        "Чехия: почти бесплатное образование в сердце Европы на английском",
        "Италия для международных студентов — сюрпризы и реальность",
        "Португалия: европейский диплом с южным климатом и низкими ценами",
        "Ирландия: страна, где Google, Meta и Apple дают работу выпускникам",
        "Израиль для студентов: сильная наука и Technion в топ мировых рейтингов",
        "Малайзия: азиатское образование с европейскими дипломами за треть цены",
        "Венгрия: стипендия Stipendium Hungaricum — полное покрытие от государства",
        "Австрия: Вена и почти бесплатные государственные университеты",
        "Норвегия: бесплатное образование даже для иностранцев — как это работает",
    ],
}

# ─────────────────────────────────────────────────────────────────
# ПРОМПТЫ ПО РУБРИКАМ
# ─────────────────────────────────────────────────────────────────

SYSTEM_BASE = """Ты — главный редактор Telegram-канала Nobilis Education.
Канал для казахстанских студентов, которые хотят учиться за рубежом.

СТИЛЬ КАНАЛА:
- Как умный друг-эксперт, не как официальный справочник
- Конкретика: цифры, даты, названия, сравнения
- Без воды, без "как известно", без "в заключение"
- Короткие абзацы (2–4 предложения), воздух между блоками
- Эмодзи — по одному на смысловой блок, не в каждом предложении
- Длина: 220–350 слов

СТРУКТУРА ПОСТА:
[рубрика] [цепляющий заголовок — факт или вопрос, не "топ советов"]

[лид: почему это важно прямо сейчас — 2–3 предложения]

[основной контент — 3–4 блока]

[практический вывод для читателя]

👉 Есть вопросы по поступлению? @NobilisBot — пишите, разберём.

ЗАПРЕЩЕНО: общие фразы, советы типа "главное верить в себя", 
списки из 10+ пунктов, официозный тон, слово "данный"."""

SYSTEM_NEWS = SYSTEM_BASE + """

ДЛЯ НОВОСТЕЙ:
- Пиши как журналист: что случилось → почему важно → что делать читателю
- Если есть конкретные даты изменений — указывай
- Заканчивай практическим советом "что делать если вы планируете поступать"
- Можно добавить: "Следите за обновлениями в нашем канале" """

SYSTEM_STATS = SYSTEM_BASE + """

ДЛЯ СТАТИСТИКИ:
- Начинай с самой неожиданной или важной цифры
- Объясняй что за каждой цифрой стоит для обычного студента
- Сравнивай: рост/падение, страна A vs страна B, 2023 vs 2024
- Делай вывод: что эти данные значат для тех, кто планирует поступать"""

SYSTEM_HACK = SYSTEM_BASE + """

ДЛЯ ЛАЙФХАКОВ:
- Давай конкретный алгоритм, а не общие советы
- Примеры из реальной жизни приветствуются
- Если есть конкретные инструменты/сервисы — называй их
- Тон: "мы в Nobilis видели сотни заявок, вот что реально работает" """

SYSTEM_UNI = SYSTEM_BASE + """

ДЛЯ РАЗБОРА ВУЗА:
- Структура: факты → программы → стоимость → реальность жизни → вердикт
- Вердикт в конце: для кого этот вуз подходит, для кого нет
- Не хвали всё подряд — честный взгляд ценнее"""

SYSTEM_COUNTRY = SYSTEM_BASE + """

ДЛЯ ОБЗОРА СТРАНЫ:
- Факты которые удивляют (не банальщина из Википедии)
- Реальная стоимость жизни + обучения
- Перспективы после учёбы: остаться / вернуться / перебраться
- Для кого эта страна — идеальный вариант"""

RUBRIC_SYSTEMS = {
    "📰 Новости":   SYSTEM_NEWS,
    "📊 Статистика": SYSTEM_STATS,
    "💡 Лайфхак":   SYSTEM_HACK,
    "🏛 Разбор вуза": SYSTEM_UNI,
    "🌍 Страна":    SYSTEM_COUNTRY,
}

# ─────────────────────────────────────────────────────────────────
# РАСПИСАНИЕ РУБРИК ПО ДНЯМ
# Каждый день — своя логика, контент не повторяется
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

# Отслеживаем использованные темы чтобы не повторяться
used_topics: set = set()


def pick_topic(rubric: str) -> str:
    topics = RUBRICS[rubric]
    available = [t for t in topics if t not in used_topics]
    if not available:        # Если все использованы — сброс
        used_topics.clear()
        available = topics
    topic = random.choice(available)
    used_topics.add(topic)
    return topic


# ─────────────────────────────────────────────────────────────────
# ГЕНЕРАЦИЯ ПОСТА
# ─────────────────────────────────────────────────────────────────

def generate_post(rubric: str, topic: str) -> str:
    system = RUBRIC_SYSTEMS.get(rubric, SYSTEM_BASE)
    prompt = f"Напиши пост для рубрики {rubric}\nТема: {topic}"

    resp = ai.messages.create(
        model="claude-opus-4-5",
        max_tokens=800,
        system=system,
        messages=[{"role": "user", "content": prompt}]
    )
    return resp.content[0].text


# ─────────────────────────────────────────────────────────────────
# ПУБЛИКАЦИЯ
# ─────────────────────────────────────────────────────────────────

async def publish(app: Application, slot: int):
    """slot: 0=утро, 1=день, 2=вечер"""
    try:
        weekday = datetime.now().weekday()
        rubric  = DAILY_SCHEDULE[weekday][slot]
        topic   = pick_topic(rubric)

        log.info(f"Generating [{rubric}] — {topic}")
        text = generate_post(rubric, topic)

        await app.bot.send_message(
            chat_id=CHANNEL_ID,
            text=text,
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        log.info("✅ Published")
    except Exception as e:
        log.error(f"Publish error: {e}")


def setup_schedule(app: Application):
    """09:00, 13:00, 19:00 — три поста в день"""
    loop = asyncio.get_event_loop()

    schedule.every().day.at("09:00").do(lambda: loop.create_task(publish(app, 0)))
    schedule.every().day.at("13:00").do(lambda: loop.create_task(publish(app, 1)))
    schedule.every().day.at("19:00").do(lambda: loop.create_task(publish(app, 2)))

    async def runner():
        while True:
            schedule.run_pending()
            await asyncio.sleep(60)

    loop.create_task(runner())


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

    ("timeline", "📅 Когда планируете начать?",
     [["Сентябрь 2025", "Январь 2026", "Сентябрь 2026", "Позже"]]),

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
        f"🔥 <b>Новый лид!</b>\n"
        f"👤 @{username or user_id} (id: {user_id})\n\n"
        f"🌍 {session.get('country')}  |  🎓 {session.get('degree')}\n"
        f"📚 {session.get('field')}  |  📅 {session.get('timeline')}\n"
        f"💰 {session.get('budget')}\n\n"
        f"<a href='tg://user?id={user_id}'>💬 Написать клиенту</a>"
    )
    await ctx.bot.send_message(chat_id=MANAGER_ID, text=msg, parse_mode="HTML")


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user_sessions[uid] = {"step": 0}
    await send_question(uid, 0, ctx)


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ <b>Nobilis Education</b>\n\n"
        "Помогаем поступить в лучшие университеты мира.\n\n"
        "/start — подбор программы\n"
        "/consult — бесплатная консультация\n\n"
        "Или просто напишите вопрос — передам консультанту.",
        parse_mode="HTML"
    )


async def cmd_consult(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    await update.message.reply_text(
        "📞 Оставьте свои данные и мы свяжемся с вами сегодня:\n\n"
        "— Ваше имя\n— Интересующая страна\n— Удобное время",
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
                f"📚 {s.get('field')}  •  📅 {s.get('timeline')}\n"
                f"💰 {s.get('budget')}\n\n"
                "Наш консультант подготовит список университетов "
                "и напишет вам в течение рабочего дня. 🙌"
            ),
            parse_mode="HTML"
        )
        await notify_manager(uid, q.from_user.username or "", s, ctx)


async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    await update.message.reply_text(
        "📨 Получили! Консультант ответит в течение рабочего дня.\n\n"
        "Для быстрого подбора программы нажмите /start"
    )
    if MANAGER_ID:
        await ctx.bot.send_message(
            chat_id=MANAGER_ID,
            text=(
                f"💬 <b>Новое сообщение</b>\n"
                f"👤 @{u.username or u.id} (id: {u.id})\n\n"
                f"<i>{update.message.text}</i>\n\n"
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
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    async def on_startup(a):
        setup_schedule(a)
        log.info("🚀 Nobilis Publisher started")

    app.post_init = on_startup
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
