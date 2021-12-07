from aiogram import Bot, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor
from aiogram.dispatcher.filters import Text
from config import TOKEN, keys
from extensions import *


storage = MemoryStorage()
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=storage)


async def on_startup(_):
    print('Bot is online')


# Хранение ответов от пользователя
async def user_data(state):
    async with state.proxy() as data:
        for k, v in data.items():
            user_dict[k] = v


def get_keyboard():
    keyboard = InlineKeyboardMarkup()
    inline_btns = [InlineKeyboardButton(text='биткоин(BTC)', callback_data='BTC'),
                   InlineKeyboardButton(text='эфириум(ETH)', callback_data='ETH'),
                   InlineKeyboardButton(text='доллар(USD)', callback_data='USD'),
                   InlineKeyboardButton(text='рубль(RUB)', callback_data='RUB'),
                   InlineKeyboardButton(text='евро(EUR)', callback_data='EUR'),
                   InlineKeyboardButton(text='фунт(GBP)', callback_data='GBP')]
    keyboard.add(*inline_btns)
    return keyboard


@dp.message_handler(commands=['start', 'help'])
async def handle_start_help(message: types.Message):
    text = "Конвертировать валюты:/convert\n" \
           "____________________________________\n" \
           "Список всех доступных валют:/values\n" \
           "____________________________________\n" \
           "Вызов помощи:/help\n" \
           "____________________________________\n" \
           "Отмена конвертации:/cancel\n" \
           "____________________________________\n" \
           "Источник котировок:/source\n" \
           "____________________________________"
    if message.from_user.username:
        await message.answer(f'Hello, {message.from_user.username}')
    else:
        await message.answer(f"Hello, User:{message.from_user.id}")
    await message.answer(text)


@dp.message_handler(commands=['values'])
async def values(message: types.Message):
    text = 'Доступные валюты: \n' \
           '________________________'
    for key, value in keys.items():
        text = '\n'.join((text, f"{key} : {value}")) + "\n"
    await message.answer(text)


@dp.message_handler(commands='source')
async def source(message: types.Message):
    url_kbrd = InlineKeyboardMarkup(row_width=1)
    url_btn = InlineKeyboardButton(text='Источник данных: ', url='https://www.cryptocompare.com/')
    url_kbrd.add(url_btn)
    await message.answer('www.cryptocompare.com', reply_markup=url_kbrd)


@dp.message_handler(commands='convert', state=None)
async def cm_convert(message: types.Message):
    text = 'Выберите валюту для конвертации\n' \
           '_______________________________'
    await FSMAdmin.quote.set()
    await message.answer(text, reply_markup=get_keyboard())


# Отмена конвертации
@dp.message_handler(state="*", commands='cancel')
@dp.message_handler(Text(equals='cancel', ignore_case=True), state="*")
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()
    await message.reply('Bye!')


# ловим ответ от пользователя
@dp.callback_query_handler(text=['BTC', 'ETH', 'USD', 'RUB', 'EUR', 'GBP'], state=FSMAdmin.quote)
async def callback_quote(callback: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['quote'] = callback.data
    await FSMAdmin.next()
    text = 'Выберите валюту, в которую конвертировать\n' \
           '_______________________________'
    await callback.message.answer(text, reply_markup=get_keyboard())
    await callback.answer(f'Выбрана валюта: {callback.data}')
    await bot.answer_callback_query(callback_query_id=callback.id)


# ловим следующий ответ от пользователя
@dp.callback_query_handler(text=['BTC', 'ETH', 'USD', 'RUB', 'EUR', 'GBP'], state=FSMAdmin.base)
async def callback_base(callback: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['base'] = callback.data
    await FSMAdmin.next()
    text = 'Введите количество валюты для конвертации:\n' \
           '_______________________________'
    await callback.message.answer(text)
    await callback.answer(f'Выбрана валюта: {callback.data}')
    await bot.answer_callback_query(callback_query_id=callback.id)


# Количество валюты для конвертации
@dp.message_handler(content_types=['text'], state=FSMAdmin.amount)
async def ask_amount(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        try:
            data['amount'] = abs(float(message.text))
        except ValueError:
            return await message.answer(f"Ошибка пользователя.\nНе удалось вычислить {message.text}. Введите число.")
    await user_data(state)

    result = Converter.get_price(user_dict['quote'], user_dict['base'], user_dict['amount'])
    text = f"{user_dict['amount']} {user_dict['quote']} = {result} {user_dict['base']}"

    await message.answer(text)
    await state.finish()


executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
