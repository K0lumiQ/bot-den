import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ⚠️ ВСТАВЬ СВОЙ ТОКЕН СЮДА
TOKEN = "ВСТАВЬ_ТОКЕН_СЮДА"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- Главное меню ---
def main_menu():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🛠 Услуги и цены", callback_data="services"))
    builder.row(InlineKeyboardButton(text="📁 Кейсы", callback_data="cases"))
    builder.row(InlineKeyboardButton(text="⚙️ Стек технологий", callback_data="stack"))
    builder.row(InlineKeyboardButton(text="🌐 Сайт-портфолио", url="https://dfdev.ru"))
    builder.row(InlineKeyboardButton(text="✉️ Написать мне", url="https://kwork.ru/user/Daniil_shiki"))
    return builder.as_markup()

def back_btn():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="← Назад", callback_data="back"))
    return builder.as_markup()

# --- /start ---
@dp.message(CommandStart())
async def start(message: types.Message):
    text = (
        "Привет! Я <b>Даниил Федоренко</b> — разработчик Telegram-ботов.\n\n"
        "Делаю ботов под любую задачу:\n"
        "— приём заявок и лидов\n"
        "— магазины с оплатой\n"
        "— AI-ассистенты на GPT-4\n"
        "— рассылки и воронки\n\n"
        "Сдаю с первого раза, без «доработаем позже».\n\n"
        "Выбери что тебя интересует 👇"
    )
    await message.answer(text, reply_markup=main_menu(), parse_mode="HTML")

# --- Услуги ---
@dp.callback_query(F.data == "services")
async def services(call: types.CallbackQuery):
    text = (
        "<b>Услуги и цены</b>\n\n"
        "🤖 <b>Бот с нуля</b> — от 3 000 ₽\n"
        "Меню, анкеты, уведомления. Деплой включён.\n\n"
        "🛒 <b>Telegram-магазин</b> — от 20 000 ₽\n"
        "Каталог, корзина, оплата картой, админка.\n\n"
        "🧠 <b>AI-ассистент</b> — от 18 000 ₽\n"
        "GPT-4 на твоих документах. Отвечает 24/7.\n\n"
        "📨 <b>Воронки и рассылки</b> — от 13 000 ₽\n"
        "Автосерия сообщений, A/B тест, статистика.\n\n"
        "🔗 <b>CRM-интеграция</b> — от 8 000 ₽\n"
        "amoCRM, Bitrix24, Google Sheets.\n\n"
        "🕷 <b>Парсинг данных</b> — от 5 000 ₽\n"
        "Собираю данные с любых сайтов."
    )
    await call.message.edit_text(text, reply_markup=back_btn(), parse_mode="HTML")

# --- Кейсы ---
@dp.callback_query(F.data == "cases")
async def cases(call: types.CallbackQuery):
    text = (
        "<b>Примеры работ</b>\n\n"
        "<b>01. AI-ассистент для онлайн-школы</b>\n"
        "Бот отвечает на вопросы студентов 24/7, записывает на курсы. "
        "Обучен на 300+ документах. Срок: 7 дней.\n\n"
        "<b>02. Telegram-магазин одежды</b>\n"
        "200+ товаров, корзина, оплата картой, "
        "статусы заказов. Срок: 5 дней.\n\n"
        "<b>03. Лид-бот для агентства недвижимости</b>\n"
        "Квалификация клиентов через анкету + выгрузка в amoCRM. "
        "Срок: 3 дня.\n\n"
        "<b>04. Автоворонка для инфобизнеса</b>\n"
        "8 писем за 5 дней прогревают подписчика до покупки. "
        "A/B тест, аналитика. Срок: 4 дня."
    )
    await call.message.edit_text(text, reply_markup=back_btn(), parse_mode="HTML")

# --- Стек ---
@dp.callback_query(F.data == "stack")
async def stack(call: types.CallbackQuery):
    text = (
        "<b>Стек технологий</b>\n\n"
        "<code>Python · Aiogram 3 · PostgreSQL</code>\n"
        "<code>Redis · Docker · Linux / VPS</code>\n"
        "<code>OpenAI API · REST API · Selenium</code>\n"
        "<code>ЮKassa · amoCRM · Google Sheets</code>"
    )
    await call.message.edit_text(text, reply_markup=back_btn(), parse_mode="HTML")

# --- Назад ---
@dp.callback_query(F.data == "back")
async def back(call: types.CallbackQuery):
    text = (
        "Привет! Я <b>Даниил Федоренко</b> — разработчик Telegram-ботов.\n\n"
        "Делаю ботов под любую задачу:\n"
        "— приём заявок и лидов\n"
        "— магазины с оплатой\n"
        "— AI-ассистенты на GPT-4\n"
        "— рассылки и воронки\n\n"
        "Сдаю с первого раза, без «доработаем позже».\n\n"
        "Выбери что тебя интересует 👇"
    )
    await call.message.edit_text(text, reply_markup=main_menu(), parse_mode="HTML")

async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
