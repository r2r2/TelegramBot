import json
import requests
from aiogram.dispatcher.filters.state import State, StatesGroup


class APIException(Exception):
    pass


class ConvertionException(Exception):
    pass


class Converter:
    @staticmethod
    def get_price(quote: str, base: str, amount: str):
        r = requests.get(f'https://min-api.cryptocompare.com/data/price?fsym={quote}&tsyms={base}')
        total_base = json.loads(r.content)[base]
        return round(total_base * amount, 5)


class FSMAdmin(StatesGroup):
    quote = State()
    base = State()
    amount = State()


# БД для хранения ответов пользователя
user_dict = dict()
