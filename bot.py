import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, BufferedInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ——— НАСТРОЙКИ ———
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")  # например: https://my-bot.onrender.com
WEBHOOK_PATH = f"/webhook/{TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
WEB_SERVER_HOST = "0.0.0.0"
WEB_SERVER_PORT = int(os.getenv("PORT", "8080"))

if not TOKEN:
    raise ValueError("BOT_TOKEN не задан!")
if not WEBHOOK_HOST:
    raise ValueError("WEBHOOK_HOST не задан!")

bot = Bot(token=TOKEN)
storage = RedisStorage.from_url(REDIS_URL)
dp = Dispatcher(storage=storage)


# ——— СОСТОЯНИЯ ———
class OrderForm(StatesGroup):
    name = State()
    task = State()
    budget = State()


class Quiz(StatesGroup):
    q1 = State()
    q2 = State()
    q3 = State()


# ——— КАРТИНКИ ———
IMAGES = {
    "bot_starter":  "images/01-bot-starter.png",
    "lead_catcher": "images/02-lead-catcher.png",
    "shop_pocket":  "images/03-shop-pocket.png",
    "ai_reply":     "images/04-ai-reply.png",
    "auto_pilot":   "images/05-auto-pilot.png",
}


async def get_photo(key):
    path = IMAGES.get(key)
    if path and os.path.exists(path):
        with open(path, "rb") as f:
            return BufferedInputFile(f.read(), filename=f"{key}.png")
    return None


# ——— ДАННЫЕ УСЛУГ ———
SERVICES = {
    "svc_bot_starter": {
        "img": "bot_starter",
        "desc": (
            "<b>BOT / STARTER</b>\n"
            "<i>Telegram-бот «под ключ» — базовый</i>\n\n"
            "Подходит для старта: визитка, поддержка, простая автоматизация.\n\n"
            "<b>Что входит:</b>\n"
            "— Inline-меню с кнопками\n"
            "— Автоответы и команды\n"
            "— Уведомления администратору\n"
            "— Деплой на сервер\n"
            "— Инструкция по использованию\n\n"
            "⏱ Срок: <b>1–3 дня</b>\n"
            "💰 Стоимость: <b>от 5 000 ₽</b>"
        ),
    },
    "svc_lead_catcher": {
        "img": "lead_catcher",
        "desc": (
            "<b>LEAD / CATCHER</b>\n"
            "<i>Сбор заявок с валидацией и выгрузкой в CRM</i>\n\n"
            "Бот собирает заявки 24/7, квалифицирует клиентов и передаёт данные куда нужно.\n\n"
            "<b>Что входит:</b>\n"
            "— Анкета с валидацией данных\n"
            "— Уведомления оператору\n"
            "— Выгрузка в Google Sheets или CRM\n"
            "— Антидубль заявок\n"
            "— Статусы заявок (новая / в работе)\n\n"
            "⏱ Срок: <b>3–5 дней</b>\n"
            "💰 Стоимость: <b>от 12 000 ₽</b>"
        ),
    },
    "svc_shop_pocket": {
        "img": "shop_pocket",
        "desc": (
            "<b>SHOP / POCKET</b>\n"
            "<i>Мини-магазин в Telegram: каталог, корзина, оплата</i>\n\n"
            "Полноценный магазин прямо в чате — без сайта и лишних переходов.\n\n"
            "<b>Что входит:</b>\n"
            "— Каталог с фото и категориями\n"
            "— Корзина и оформление заказа\n"
            "— Приём оплаты (ЮKassa / Tinkoff)\n"
            "— Статусы заказов для клиента\n"
            "— Админ-панель для управления\n\n"
            "⏱ Срок: <b>7–10 дней</b>\n"
            "💰 Стоимость: <b>от 25 000 ₽</b>"
        ),
    },
    "svc_ai_reply": {
        "img": "ai_reply",
        "desc": (
            "<b>AI / REPLY</b>\n"
            "<i>Бот отвечает по базе знаний. Сложные кейсы — оператору</i>\n\n"
            "GPT-4 обученный на ваших документах. Отвечает как живой менеджер, без выходных.\n\n"
            "<b>Что входит:</b>\n"
            "— Интеграция с GPT-4\n"
            "— Обучение на ваших материалах (PDF, сайт, FAQ)\n"
            "— Переключение на оператора\n"
            "— История диалогов\n"
            "— Аналитика обращений\n\n"
            "⏱ Срок: <b>5–7 дней</b>\n"
            "💰 Стоимость: <b>от 18 000 ₽</b>"
        ),
    },
    "svc_auto_pilot": {
        "img": "auto_pilot",
        "desc": (
            "<b>AUTO / PILOT</b>\n"
            "<i>Автоворонки и сегментные рассылки</i>\n\n"
            "Прогревает подписчиков и возвращает аудиторию на автопилоте.\n\n"
            "<b>Что входит:</b>\n"
            "— Цепочка сообщений до 10 шагов\n"
            "— Сегментация базы\n"
            "— A/B тест сообщений\n"
            "— Статистика: открытия, клики, отписки\n"
            "— Интеграция с каналом/группой\n\n"
            "⏱ Срок: <b>4–6 дней</b>\n"
            "💰 Стоимость: <b>от 15 000 ₽</b>"
        ),
    },
}

# ——— FAQ ———
FAQ = [
    {
        "q": "Сколько времени занимает разработка?",
        "a": "Зависит от сложности. Простой бот — 1–3 дня. Магазин или AI-ассистент — 7–10 дней. Точный срок называю после обсуждения задачи."
    },
    {
        "q": "Как происходит оплата?",
        "a": "50% предоплата до начала работы, 50% после сдачи. Работаю через Кворк — это безопасная сделка, деньги замораживаются и приходят ко мне только после вашего подтверждения."
    },
    {
        "q": "Даёте гарантию на бота?",
        "a": "Да. После сдачи — на связи для правок и вопросов. Баги исправляю бесплатно. Если что-то пошло не так — разберёмся."
    },
    {
        "q": "Нужен ли мне сервер для бота?",
        "a": "Деплой на сервер входит в стоимость. Если своего сервера нет — помогу выбрать подходящий VPS от 150 ₽/месяц."
    },
    {
        "q": "Можно доработать уже готового бота?",
        "a": "Да, берусь за доработку чужих ботов. Сначала смотрю код, оцениваю задачу, называю цену. Пишите — разберёмся."
    },
]




# ——— КЛАВИАТУРЫ ———
def kb_main():
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="🛠 Услуги и цены", callback_data="services"))
    b.row(InlineKeyboardButton(text="🎯 Подобрать бота под задачу", callback_data="quiz_start"))
    b.row(InlineKeyboardButton(text="❓ FAQ", callback_data="faq_0"))
    b.row(InlineKeyboardButton(text="✉️ Оставить заявку", callback_data="order_start"))
    b.row(InlineKeyboardButton(text="🌐 Сайт-портфолио", url="https://dfdev.ru"))
    return b.as_markup()


def kb_services():
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="Bot Starter — от 5 000 ₽", callback_data="svc_bot_starter"))
    b.row(InlineKeyboardButton(text="Lead Catcher — от 12 000 ₽", callback_data="svc_lead_catcher"))
    b.row(InlineKeyboardButton(text="Shop Pocket — от 25 000 ₽", callback_data="svc_shop_pocket"))
    b.row(InlineKeyboardButton(text="AI Reply — от 18 000 ₽", callback_data="svc_ai_reply"))
    b.row(InlineKeyboardButton(text="Auto Pilot — от 15 000 ₽", callback_data="svc_auto_pilot"))
    b.row(InlineKeyboardButton(text="← Главное меню", callback_data="main"))
    return b.as_markup()


def kb_service_detail():
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="✉️ Хочу такой бот", callback_data="order_start"))
    b.row(InlineKeyboardButton(text="← К услугам", callback_data="services"))
    return b.as_markup()


def kb_back(to="main"):
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="← Назад", callback_data=to))
    return b.as_markup()


def kb_cancel():
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="❌ Отмена", callback_data="main"))
    return b.as_markup()


def kb_faq(idx):
    b = InlineKeyboardBuilder()
    row = []
    if idx > 0:
        row.append(InlineKeyboardButton(text="←", callback_data=f"faq_{idx-1}"))
    if idx < len(FAQ) - 1:
        row.append(InlineKeyboardButton(text="→", callback_data=f"faq_{idx+1}"))
    if row:
        b.row(*row)
    b.row(InlineKeyboardButton(text="← Главное меню", callback_data="main"))
    return b.as_markup()




# ——— ХЕЛПЕР: отправить/редактировать ———
async def edit_or_send(call: types.CallbackQuery, text: str, kb):
    try:
        await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await call.message.answer(text, reply_markup=kb, parse_mode="HTML")


# ——— /start ———
@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    text = (
        "Привет! Я живой пример того, что может сделать мой создатель для вашего бизнеса. "
        "Здесь вы можете ознакомиться с услугами, ценами и оставить заявку. "
        "Смотрите, трогайте, пробуйте 👇"
    )
    await message.answer(text, reply_markup=kb_main(), parse_mode="HTML")


# ——— Главное меню (кнопка) ———
@dp.callback_query(F.data == "main")
async def cb_main(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    text = (
        "Привет! Я живой пример того, что может сделать мой создатель для вашего бизнеса. "
        "Здесь вы можете ознакомиться с услугами, ценами и оставить заявку. "
        "Смотрите, трогайте, пробуйте 👇"
    )
    await edit_or_send(call, text, kb_main())


# ——— Услуги — список ———
@dp.callback_query(F.data == "services")
async def cb_services(call: types.CallbackQuery):
    try:
        await call.message.delete()
    except Exception:
        pass
    await call.message.answer(
        "Выберите интересующую услугу — покажу подробное описание и пример работы 👇\n\n"
        "<i>После нажатия подождите пару секунд — изображение загружается.</i>",
        reply_markup=kb_services(),
        parse_mode="HTML"
    )


# ——— Услуга — детально с картинкой ———
@dp.callback_query(F.data.startswith("svc_"))
async def cb_service_detail(call: types.CallbackQuery):
    svc = SERVICES.get(call.data)
    if not svc:
        return
    photo = await get_photo(svc["img"])
    try:
        await call.message.delete()
    except Exception:
        pass
    if photo:
        await call.message.answer_photo(
            photo=photo,
            caption=svc["desc"],
            reply_markup=kb_service_detail(),
            parse_mode="HTML"
        )
    else:
        await call.message.answer(svc["desc"], reply_markup=kb_service_detail(), parse_mode="HTML")


# ——— FAQ — пагинация ———
@dp.callback_query(F.data.startswith("faq_"))
async def cb_faq(call: types.CallbackQuery):
    idx = int(call.data.split("_")[1])
    item = FAQ[idx]
    text = (
        f"<b>❓ Вопрос {idx+1} из {len(FAQ)}</b>\n\n"
        f"<b>{item['q']}</b>\n\n"
        f"{item['a']}"
    )
    await edit_or_send(call, text, kb_faq(idx))


# ——— КВИЗ — старт ———
@dp.callback_query(F.data == "quiz_start")
async def cb_quiz_start(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(Quiz.q1)
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="Принимать заявки / лиды", callback_data="q1_leads"))
    b.row(InlineKeyboardButton(text="Продавать товары / услуги", callback_data="q1_shop"))
    b.row(InlineKeyboardButton(text="Отвечать на вопросы клиентов", callback_data="q1_support"))
    b.row(InlineKeyboardButton(text="Рассылки и прогрев аудитории", callback_data="q1_mailing"))
    b.row(InlineKeyboardButton(text="❌ Отмена", callback_data="main"))
    await edit_or_send(call,
        "🎯 <b>Подберём бота под твою задачу</b>\n\n"
        "<b>Вопрос 1 из 3.</b> Что нужно боту делать?",
        b.as_markup()
    )


@dp.callback_query(F.data.startswith("q1_"))
async def cb_quiz_q2(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(q1=call.data)
    await state.set_state(Quiz.q2)
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="До 10 000 ₽", callback_data="q2_low"))
    b.row(InlineKeyboardButton(text="10 000 – 25 000 ₽", callback_data="q2_mid"))
    b.row(InlineKeyboardButton(text="Больше 25 000 ₽", callback_data="q2_high"))
    b.row(InlineKeyboardButton(text="Пока не знаю", callback_data="q2_unknown"))
    await edit_or_send(call,
        "<b>Вопрос 2 из 3.</b> Какой бюджет на разработку?",
        b.as_markup()
    )


@dp.callback_query(F.data.startswith("q2_"))
async def cb_quiz_q3(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(q2=call.data)
    await state.set_state(Quiz.q3)
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="Как можно быстрее", callback_data="q3_asap"))
    b.row(InlineKeyboardButton(text="Неделя–две", callback_data="q3_week"))
    b.row(InlineKeyboardButton(text="Не горит", callback_data="q3_chill"))
    await edit_or_send(call,
        "<b>Вопрос 3 из 3.</b> Когда нужен бот?",
        b.as_markup()
    )


@dp.callback_query(F.data.startswith("q3_"))
async def cb_quiz_result(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    q1 = data.get("q1", "")
    q2 = data.get("q2", "")

    if q1 == "q1_leads":
        rec = "svc_lead_catcher"
        rec_name = "Lead Catcher"
        reason = "Ты хочешь собирать заявки — Lead Catcher именно для этого."
    elif q1 == "q1_shop":
        rec = "svc_shop_pocket"
        rec_name = "Shop Pocket"
        reason = "Продажи в Telegram — это Shop Pocket с каталогом и оплатой."
    elif q1 == "q1_support":
        rec = "svc_ai_reply"
        rec_name = "AI Reply"
        reason = "Для ответов на вопросы клиентов лучше всего подойдёт AI Reply на GPT-4."
    elif q1 == "q1_mailing":
        rec = "svc_auto_pilot"
        rec_name = "Auto Pilot"
        reason = "Для рассылок и прогрева — Auto Pilot с воронками и A/B тестом."
    else:
        rec = "svc_bot_starter"
        rec_name = "Bot Starter"
        reason = "Для старта подойдёт Bot Starter — базовый бот под ключ."

    budget_note = "\n⚠️ При бюджете до 10 000 ₽ подойдёт базовый вариант без сложных интеграций." if q2 == "q2_low" else ""

    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text=f"Подробнее про {rec_name}", callback_data=rec))
    b.row(InlineKeyboardButton(text="✉️ Оставить заявку", callback_data="order_start"))
    b.row(InlineKeyboardButton(text="← Главное меню", callback_data="main"))

    await edit_or_send(call,
        f"🎯 <b>Результат подбора</b>\n\n"
        f"Рекомендую: <b>{rec_name}</b>\n\n"
        f"{reason}{budget_note}\n\n"
        f"Хочешь узнать подробнее или сразу оставить заявку?",
        b.as_markup()
    )


# ——— ЗАЯВКА ———
@dp.callback_query(F.data == "order_start")
async def cb_order_start(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(OrderForm.name)
    await edit_or_send(call,
        "✉️ <b>Оставить заявку</b>\n\n"
        "Шаг 1 из 3. Как тебя зовут?",
        kb_cancel()
    )


@dp.message(OrderForm.name)
async def order_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(OrderForm.task)
    await message.answer(
        f"Отлично, <b>{message.text}</b>!\n\n"
        "Шаг 2 из 3. Опиши свою задачу — что должен делать бот?",
        reply_markup=kb_cancel(),
        parse_mode="HTML"
    )


@dp.message(OrderForm.task)
async def order_task(message: types.Message, state: FSMContext):
    await state.update_data(task=message.text)
    await state.set_state(OrderForm.budget)
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="До 10 000 ₽", callback_data="budget_low"))
    b.row(InlineKeyboardButton(text="10 000 – 25 000 ₽", callback_data="budget_mid"))
    b.row(InlineKeyboardButton(text="Больше 25 000 ₽", callback_data="budget_high"))
    b.row(InlineKeyboardButton(text="Обсудим", callback_data="budget_discuss"))
    await message.answer("Шаг 3 из 3. Какой бюджет?", reply_markup=b.as_markup())


@dp.callback_query(F.data.startswith("budget_"), OrderForm.budget)
async def order_budget(call: types.CallbackQuery, state: FSMContext):
    budgets = {
        "budget_low":     "До 10 000 ₽",
        "budget_mid":     "10 000 – 25 000 ₽",
        "budget_high":    "Больше 25 000 ₽",
        "budget_discuss": "Обсудим",
    }
    budget = budgets.get(call.data, "Не указан")
    data = await state.get_data()
    await state.clear()

    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="← Главное меню", callback_data="main"))
    await edit_or_send(call,
        "✅ <b>Заявка принята!</b>\n\n"
        "Отвечу в течение часа. Если срочно — напиши напрямую в Кворк.\n\n"
        f"🌐 <a href='https://kwork.ru/user/Daniil_shiki'>kwork.ru/user/Daniil_shiki</a>",
        b.as_markup()
    )

    if ADMIN_ID:
        admin_text = (
            "📩 <b>Новая заявка!</b>\n\n"
            f"👤 Имя: {data.get('name', '—')}\n"
            f"📋 Задача: {data.get('task', '—')}\n"
            f"💰 Бюджет: {budget}\n"
            f"🔗 Username: @{call.from_user.username or '—'}"
        )
        try:
            await bot.send_message(ADMIN_ID, admin_text, parse_mode="HTML")
        except Exception:
            pass


# ——— WEBHOOK LIFECYCLE ———
async def on_startup(app: web.Application):
    await bot.set_webhook(WEBHOOK_URL)
    logger.info(f"Webhook установлен: {WEBHOOK_URL}")


async def on_shutdown(app: web.Application):
    await bot.delete_webhook()
    logger.info("Webhook удалён")


# ——— HEALTH CHECK ———
async def health(request):
    return web.Response(text="OK")


# ——— ЗАПУСК ———
def main():
    app = web.Application()
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    app.router.add_get("/", health)

    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)


if __name__ == "__main__":
    main()
