from aiogram.fsm.state import State, StatesGroup

class AdminMovie(StatesGroup):
    movie_file = State()
    movie_desc = State()

class ReklamaState(StatesGroup):
    waiting_for_ad = State()

class SearchState(StatesGroup):
    waiting_for_query = State()