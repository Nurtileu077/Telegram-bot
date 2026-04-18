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
        "https://images.unsplash.com/photo-1523050854058-8df90110c9f1?w=800",
        "https://images.unsplash.com/photo-1541339907198-e08756dedf3f?w=800",
        "https://images.unsplash.com/photo-1562774053-701939374585?w=800",
    ],
    "💡 Лайфхак дня": [
        "https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?w=800",
        "https://images.unsplash.com/photo-1434030216411-0b793f4b4173?w=800",
        "https://images.unsplash.com/photo-1513475382585-d06e58bcb0e0?w=800",
    ],
    "🏛 Разбор вуза": [
        "https://images.unsplash.com/photo-1607237138185-eedd9c632b0b?w=800",
        "https://images.unsplash.com/photo-1590012314607-cda9d9b699ae?w=800",
        "https://images.unsplash.com/photo-1571260899304-425eee4c7efc?w=800",
    ],
    "🌍 Страна": [
        "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=800",
        "https://images.unsplash.com/photo-1467269204594-9661b134dd2b?w=800",
        "https://images.unsplash.com/photo-1576502200916-3808e07386a5?w=800",
    ],
    "💰 Стипендии": [
        "https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?w=800",
        "https://images.unsplash.com/photo-1579621970563-ebec7560ff3e?w=800",
        "https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?w=800",
    ],
    "🎯 IELTS / Язык": [
        "https://images.unsplash.com/photo-1546410531-bb4caa6b424d?w=800",
        "https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=800",
        "https://images.unsplash.com/photo-1488190211105-8b0e65b80b4e?w=800",
    ],
    "📋 Документы": [
        "https://images.unsplash.com/photo-1568667256549-094345857637?w=800",
        "https://images.unsplash.com/photo-1450101499163-c8848c66ca85?w=800",
        "https://images.unsplash.com/photo-1586281380349-632531db7ed4?w=800",
    ],
    "📊 Цифры дня": [
        "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800",
        "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=800",
        "https://images.unsplash.com/photo-1504868584819-f8e8b4b6d7e3?w=800",
    ],
}

# ─────────────────────────────────────────────────────────────────
# УМНЫЕ CTA ПОД КАЖДУЮ РУБРИКУ
# ─────────────────────────────────────────────────────────────────

RUBRIC_CTA = {
    "📰 Новости":      ["Как это влияет на ваши планы? → @nobilissbot",
                        "Успеваете под новые требования? → @nobilissbot",
                        "Что это значит лично для вас → @nobilissbot"],
    "💡 Лайфхак дня": ["Применим к вашей заявке → @nobilissbot",
                        "Разберём вашу ситуацию → @nobilissbot",
                        "Проверим вашу заявку → @nobilissbot"],
    "🏛 Разбор вуза":  ["Подходит ли этот вуз вам? → @nobilissbot",
                        "Реальны ли ваши шансы → @nobilissbot",
                        "Вопросы по университету? → @nobilissbot"],
    "🌍 Страна":       ["Эта страна для вас? → @nobilissbot",
                        "Расскажем что реально нужно → @nobilissbot",
                        "Узнайте свои шансы → @nobilissbot"],
    "💰 Стипендии":    ["Подходите под эту стипендию? → @nobilissbot",
                        "Помогаем подготовить заявку → @nobilissbot",
                        "Какие стипендии доступны вам → @nobilissbot"],
    "🎯 IELTS / Язык": ["Разберём вашу слабую зону → @nobilissbot",
                        "План подготовки под ваш уровень → @nobilissbot",
                        "Какой балл нужен и как достичь → @nobilissbot"],
    "📋 Документы":    ["Проверим ваши документы → @nobilissbot",
                        "Помогаем с SOP, CV и рекомендациями → @nobilissbot",
                        "Что нужно для вашего вуза → @nobilissbot"],
    "📊 Цифры дня":    ["Где вы в этой статистике? → @nobilissbot",
                        "Разберём ваш профиль и шансы → @nobilissbot",
                        "Хотите в топ этих цифр? → @nobilissbot"],
}

# ─────────────────────────────────────────────────────────────────
# КОНТЕНТ-ПЛАН (расписание рубрик по дням и времени)
# ─────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────
# КОНТЕНТ-ПЛАН — 8 рубрик, каждый день разное
# ─────────────────────────────────────────────────────────────────

DAILY_SCHEDULE = {
    0: ["📰 Новости",     "💡 Лайфхак дня",  "🏛 Разбор вуза",  "💰 Стипендии",    "📊 Цифры дня",    "🌍 Страна"],       # Пн
    1: ["🎯 IELTS / Язык","📰 Новости",      "💡 Лайфхак дня",  "🏛 Разбор вуза",  "🌍 Страна",       "📋 Документы"],    # Вт
    2: ["🌍 Страна",      "💡 Лайфхак дня",  "📰 Новости",      "📋 Документы",    "📊 Цифры дня",    "💰 Стипендии"],    # Ср
    3: ["📰 Новости",     "💰 Стипендии",    "🏛 Разбор вуза",  "🎯 IELTS / Язык", "💡 Лайфхак дня",  "📊 Цифры дня"],    # Чт
    4: ["💡 Лайфхак дня", "📰 Новости",      "🌍 Страна",       "📋 Документы",    "💰 Стипендии",    "🏛 Разбор вуза"],  # Пт
    5: ["📊 Цифры дня",   "🏛 Разбор вуза",  "💡 Лайфхак дня",  "📰 Новости",      "🎯 IELTS / Язык", "🌍 Страна"],       # Сб
    6: ["🌍 Страна",      "📋 Документы",    "📰 Новости",       "💡 Лайфхак дня",  "🏛 Разбор вуза",  "💰 Стипендии"],    # Вс
}

PUBLISH_TIMES = ["09:00", "11:30", "14:00", "17:00", "20:00", "22:00"]

RUBRICS = {
    "📰 Новости": [
        "Оксфорд и Кембридж ужесточили требования к IELTS для 2026 года",
        "Германия упрощает студенческие визы для граждан Казахстана",
        "Канада ограничила выдачу study permit — что это значит",
        "QS World University Rankings 2025 — главные неожиданности",
        "Австралия ужесточила финансовые требования для студенческих виз",
        "США отменили требование GRE в топ-университетах",
        "Швейцария открыла стипендии для студентов из Центральной Азии",
        "Изменения в UCAS 2026: новые правила подачи в UK",
        "Нидерланды ограничивают англоязычные программы",
        "ОАЭ расширяет список университетов с господдержкой",
        "Япония запустила программу привлечения иностранных студентов",
        "Франция удвоила квоту стипендий Eiffel для Центральной Азии",
    ],
    "💡 Лайфхак дня": [
        "Как поднять IELTS с 6.0 до 7.0 за 2 месяца — конкретный план по неделям",
        "5 ошибок в мотивационном письме которые сразу видит приёмная комиссия",
        "Как найти научного руководителя в иностранном университете до подачи",
        "Ранняя подача vs обычный дедлайн — реальная разница в шансах на оффер",
        "Как получить рекомендацию у профессора который вас едва знает",
        "Финансовый план студента за рубежом: как рассчитать реальный бюджет",
        "Блокированный счёт для немецкой визы: как открыть из Казахстана за 3 дня",
        "Как написать CV в европейском формате — 7 ключевых отличий",
        "LinkedIn для поступающих: как заполнить профиль под требования вузов",
        "Как сравнить два оффера от университетов и выбрать правильно",
        "Как пройти визовое собеседование — частые вопросы и правильные ответы",
        "Чек-лист: что проверить в оффере от университета прежде чем принять",
        "Как найти жильё в новом городе ещё до приезда — пошаговый алгоритм",
        "Gap year перед магистратурой — плюс или минус для приёмной комиссии",
        "Как подготовить портфолио для творческих программ за рубежом",
    ],
    "🏛 Разбор вуза": [
        "University of Amsterdam — честный разбор плюсов и минусов",
        "TU Munich: программы, стоимость, жизнь в Мюнхене изнутри",
        "LSE vs Warwick — куда идти на Finance и Economics",
        "University of Waterloo — почему лучший для IT в Канаде",
        "ETH Zurich — как поступить в лучший технический в Европе",
        "University of Melbourne: реальная стоимость жизни и учёбы",
        "McGill: французский Монреаль и один из топ-вузов Канады",
        "King's College London — медицина, право, бизнес в центре Лондона",
        "KAIST — бесплатно плюс стипендия в топ-100 мира",
        "Durham University — Russell Group без лондонских цен",
        "NUS Singapore — топ-10 мира и ворота в азиатский рынок",
        "Sciences Po Paris — лучший по международным отношениям",
    ],
    "🌍 Страна": [
        "Финляндия: бесплатно ли, как поступить, карьера после",
        "Дания для студентов — дорого, но есть нюансы меняющие всё",
        "Польша как старт в Европу: доступно и с перспективой",
        "Ирландия — где Google, Meta и Apple сами ищут выпускников",
        "Португалия: европейский диплом с южным климатом",
        "Австрия: Вена и почти бесплатные государственные вузы",
        "Норвегия: бесплатное образование даже для иностранцев",
        "Малайзия: азиатское образование с европейскими дипломами",
        "Чехия: почти бесплатно в сердце Европы на английском",
        "Венгрия: стипендия Stipendium Hungaricum — полное покрытие",
    ],
    "💰 Стипендии": [
        "Chevening 2026 — полная стипендия UK: кто может подать из Казахстана",
        "DAAD Германия — как получить €1,200 в месяц на учёбу",
        "Erasmus Mundus — учёба в 3 странах Европы бесплатно",
        "Gates Cambridge — одна из самых престижных стипендий мира",
        "Swedish Institute — полное покрытие учёбы в Швеции",
        "MEXT Япония — правительственная стипендия полного покрытия",
        "GKS Korea — бесплатная учёба плюс стипендия от Кореи",
        "ETH Excellence — как поступить в ETH Zurich почти бесплатно",
        "Holland Scholarship — €5,000 на старт в Нидерландах",
        "Eiffel Excellence — французское правительство платит за учёбу",
        "NYU Abu Dhabi — полный пакет включая перелёты и жильё",
        "Vanier Canada — CAD $50,000 в год для PhD",
    ],
    "🎯 IELTS / Язык": [
        "IELTS Speaking 7+: конкретные техники которые работают на экзамене",
        "Writing Task 2 — структура эссе которую принимают все экзаменаторы",
        "Reading: как читать быстрее и находить ответы не читая весь текст",
        "Listening: почему казахстанцы теряют баллы и как это исправить",
        "IELTS vs TOEFL vs Duolingo — что выбрать для вашего вуза",
        "Как подготовиться к IELTS за 60 дней с нуля — план по неделям",
        "Academic Writing: 10 фраз которые поднимут ваш балл",
        "Самые частые ошибки казахстанцев в IELTS Speaking",
        "Как сдать IELTS на 6.5 если английский на среднем уровне",
        "GMAT vs GRE — что сдавать для MBA и магистратуры",
    ],
    "📋 Документы": [
        "Мотивационное письмо SOP: структура которую читают до конца",
        "Рекомендательное письмо: что должно быть внутри чтобы оно работало",
        "CV для европейских вузов: полный разбор с примерами",
        "Апостиль на диплом: где делать, сколько стоит, как быстро",
        "Финансовые документы для визы — что именно нужно и в каком формате",
        "Как перевести диплом и транскрипт: требования разных стран",
        "Personal Statement для UK вузов — чем отличается от SOP",
        "Портфолио для дизайн и арт программ — что включать",
        "Statement of Research для PhD — как написать чтобы приняли",
        "Чек-лист документов для UK, Германии, Канады, Нидерландов",
    ],
    "📊 Цифры дня": [
        "Сколько студентов из Казахстана учатся за рубежом — данные 2024",
        "Средняя стоимость обучения выросла на 12% — разбор по странам",
        "Какие специальности дают наибольший рост зарплаты после диплома",
        "Процент отказов в студенческой визе по странам — реальная статистика",
        "Рейтинг вузов по трудоустройству выпускников QS 2025",
        "Сколько студентов остаются работать за рубежом после учёбы",
        "Топ-10 направлений для казахстанцев по популярности в 2024",
        "Средний IELTS балл поступивших в топ-50 университетов мира",
        "Инфляция стоимости обучения: как изменились цены за 5 лет",
        "Рост зарплаты после MBA в разных странах — реальные цифры",
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

FORMATTING_RULES = """
ФОРМАТИРОВАНИЕ — только HTML теги Telegram:
- Жирный: <b>текст</b>  (НЕ **текст**)
- Курсив: <i>текст</i>  (НЕ *текст*)
- Никаких звёздочек *, никаких решёток #, никакого Markdown
- Разделители между блоками: пустая строка
- Эмодзи: одно в начале смыслового блока
- Сравнения и списки оформляй через символ —
"""

SYSTEM_PROMPTS = {
    "📰 Новости": """Ты редактор Telegram-канала Nobilis Education (Казахстан).
Пиши как умный журналист: что случилось → почему важно → что делать студенту.
Живо, конкретно, без воды. 220-300 слов. Абзацы по 2-3 предложения.""" + FORMATTING_RULES,

    "💡 Лайфхак дня": """Ты эксперт Nobilis с опытом сотен заявок.
Давай конкретный алгоритм по шагам. Называй реальные инструменты и сервисы.
Тон: "мы в Nobilis видели сотни заявок — вот что реально работает".
Структура: проблема → почему важно → конкретные шаги → результат.
200-280 слов.""" + FORMATTING_RULES,

    "🏛 Разбор вуза": """Ты консультант Nobilis. Разбирай честно: плюсы И минусы.
Структура обязательно:
<b>Факты:</b> рейтинг, размер, основан когда
<b>Сильные программы:</b> список через —
<b>Реальная стоимость:</b> обучение + жизнь в цифрах
<b>Плюсы:</b> 3-4 конкретных
<b>Минусы:</b> 2-3 честных
<b>Вердикт:</b> для кого подходит и для кого нет
Не хвали всё подряд. 280-350 слов.""" + FORMATTING_RULES,

    "🌍 Страна": """Ты эксперт Nobilis по международному образованию.
Факты которые удивляют, не банальщина. Структура:
<b>Почему сюда едут:</b> реальные причины
<b>Стоимость обучения:</b> конкретные цифры
<b>Стоимость жизни:</b> аренда, еда, транспорт
<b>После учёбы:</b> виза, работа, перспективы
<b>Для кого идеально:</b> конкретный профиль студента
230-300 слов.""" + FORMATTING_RULES,

    "💰 Стипендии": """Ты эксперт Nobilis по стипендиям и финансированию.
Структура поста:
<b>Что покрывает:</b> конкретно — обучение, жильё, перелёт, карманные
<b>Кто может подать:</b> требования чётко
<b>Дедлайн:</b> конкретная дата
<b>Конкурс:</b> сколько мест, шансы реально
<b>Главная ошибка заявителей:</b> что губит заявку
Мотивируй но без пустых обещаний. 220-280 слов.""" + FORMATTING_RULES,

    "🎯 IELTS / Язык": """Ты преподаватель IELTS с опытом подготовки казахстанских студентов.
Давай конкретные техники которые работают на экзамене.
Структура: в чём проблема → конкретное решение → пример → результат.
Называй реальные ресурсы: Cambridge IELTS books, BBC Learning English и тд.
200-270 слов.""" + FORMATTING_RULES,

    "📋 Документы": """Ты документный консультант Nobilis. Разбирай конкретный документ.
Объясняй что именно хочет видеть приёмная комиссия и что их отталкивает.
Давай структуру, примеры фраз, типичные ошибки.
Тон: практично, применимо сегодня. 220-280 слов.""" + FORMATTING_RULES,

    "📊 Цифры дня": """Ты аналитик Nobilis Education. Начинай с самой неожиданной цифры.
Структура:
<b>Цифра:</b> главный факт который удивит
<b>Контекст:</b> почему это важно
<b>Сравнение:</b> с прошлым годом или другими странами
<b>Что это значит для вас:</b> практический вывод
Никаких общих слов. Только цифры и выводы. 200-260 слов.""" + FORMATTING_RULES,
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

# ─────────────────────────────────────────────────────────────────
# ПУБЛИКАЦИЯ С ФОТО
# ─────────────────────────────────────────────────────────────────

_publishing = False

async def send_post_to_channel(bot, text: str, photo: str):
    """Отправляет фото + текст двумя отдельными сообщениями."""
    # Сначала фото без подписи
    try:
        await bot.send_photo(chat_id=CHANNEL_ID, photo=photo)
    except Exception as e:
        log.warning(f"Photo failed, skipping: {e}")
    # Потом полный текст отдельным сообщением
    await bot.send_message(
        chat_id=CHANNEL_ID,
        text=text,
        parse_mode="HTML",
        disable_web_page_preview=True
    )

async def publish(app: Application, slot: int):
    global _publishing
    if _publishing:
        log.warning("Already publishing, skipping duplicate")
        return
    _publishing = True
    try:
        weekday = datetime.now().weekday()
        rubric  = DAILY_SCHEDULE[weekday][slot]
        topic   = pick_topic(rubric)
        photo   = random.choice(RUBRIC_PHOTOS[rubric])

        log.info(f"Generating [{rubric}] — {topic}")
        text = generate_post(rubric, topic)
        await send_post_to_channel(app.bot, text, photo)
        log.info("✅ Published")
    except Exception as e:
        log.error(f"Publish error: {e}")
    finally:
        _publishing = False

async def check_and_publish_breaking(app: Application):
    """Проверяет реальные новости каждые 3 часа."""
    try:
        log.info("🔍 Checking breaking news...")
        text = search_breaking_news()
        if text:
            photo = random.choice(RUBRIC_PHOTOS["📰 Новости"])
            await send_post_to_channel(
                app.bot,
                f"🔴 <b>Срочно</b>\n\n{text}",
                photo
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
        name  = username or f"TG_{user_id}"
        phone = session.get('phone', '')
        comment = (
            f"📱 Источник: Telegram бот @nobilissbot\n"
            f"👤 Telegram: @{username or user_id}\n"
            f"🆔 ID: {user_id}\n\n"
            f"🌍 Страна: {session.get('country', '—')}\n"
            f"🎓 Уровень: {session.get('degree', '—')}\n"
            f"📚 Направление: {session.get('field', '—')}\n"
            f"💰 Бюджет: {session.get('budget', '—')}\n"
            f"📞 Телефон: {phone or '—'}"
        )
        fields = {
            "TITLE":              f"Telegram: @{name}",
            "NAME":               name,
            "SOURCE_ID":          "WEB",
            "SOURCE_DESCRIPTION": "Telegram бот Nobilis",
            "COMMENTS":           comment,
            "STATUS_ID":          "NEW",
        }
        if phone:
            fields["PHONE"] = [{"VALUE": phone, "VALUE_TYPE": "MOBILE"}]

        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{BITRIX_WEBHOOK}crm.lead.add.json",
                json={"fields": fields},
                timeout=10
            )
            data = r.json()
            if data.get("result"):
                log.info(f"✅ Bitrix lead created ID: {data['result']}")
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

# Последний вопрос — телефон (текстом, не кнопками)
PHONE_QUESTION = "📞 Оставьте номер телефона — наш консультант свяжется с вами в течение рабочего дня:\n\n<i>Например: +7 777 123 45 67</i>"

async def send_question(chat_id: int, step: int, ctx: ContextTypes.DEFAULT_TYPE):
    key, text, rows = QUESTIONS[step]
    kb = [[InlineKeyboardButton(o, callback_data=f"q:{step}:{o}") for o in row] for row in rows]
    await ctx.bot.send_message(chat_id=chat_id, text=text,
                               reply_markup=InlineKeyboardMarkup(kb))

async def notify_manager(user_id, username, session, ctx):
    if not MANAGER_ID:
        return
    phone = session.get('phone', 'не указан')
    msg = (
        f"🔥 <b>Новый лид из Telegram!</b>\n"
        f"👤 @{username or user_id} (id: {user_id})\n"
        f"📞 <b>{phone}</b>\n\n"
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
        # Берём случайную рубрику — не повторяем последнюю использованную
        all_rubrics = list(RUBRICS.keys())
        rubric = random.choice(all_rubrics)
        topic  = pick_topic(rubric)
        photo  = random.choice(RUBRIC_PHOTOS[rubric])
        text   = generate_post(rubric, topic)
        await send_post_to_channel(ctx.bot, text, photo)
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
            await send_post_to_channel(
                ctx.bot,
                f"🔴 <b>Срочно</b>\n\n{text}",
                photo
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
        # Анкета заполнена — спрашиваем телефон
        user_sessions[uid]["step"] = "phone"
        await ctx.bot.send_message(
            chat_id=uid,
            text=PHONE_QUESTION,
            parse_mode="HTML"
        )

async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    uid = u.id
    text = update.message.text

    # Ловим номер телефона если ждём его
    if uid in user_sessions and user_sessions[uid].get("step") == "phone":
        user_sessions[uid]["phone"] = text
        user_sessions[uid]["step"] = "done"
        s = user_sessions[uid]

        await update.message.reply_text(
            f"✅ <b>Отлично, всё записали!</b>\n\n"
            f"🌍 {s.get('country')}  •  🎓 {s.get('degree')}\n"
            f"📚 {s.get('field')}  •  💰 {s.get('budget')}\n"
            f"📞 {s.get('phone')}\n\n"
            "Наш консультант свяжется с вами в течение рабочего дня. 🙌",
            parse_mode="HTML"
        )
        await asyncio.gather(
            create_bitrix_lead(uid, u.username or "", s),
            notify_manager(uid, u.username or "", s, ctx)
        )
        return

    # Обычное сообщение — пересылаем менеджеру
    await update.message.reply_text(
        "📨 Получили! Консультант ответит в течение рабочего дня.\n\n"
        "Чтобы оставить заявку — /start"
    )
    if MANAGER_ID:
        await ctx.bot.send_message(
            chat_id=MANAGER_ID,
            text=(
                f"💬 <b>Новое сообщение</b>\n"
                f"👤 @{u.username or uid} (id: {uid})\n\n"
                f"<i>{text}</i>\n\n"
                f"<a href='tg://user?id={uid}'>Ответить</a>"
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
