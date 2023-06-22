from createbot import dp, bot
from aiogram import types
from aiogram.utils import executor
from lib import logo, welcome_message, check_user
from asgiref.sync import sync_to_async
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.utils.executor import start_webhook
import createform
import logging

logging.basicConfig(
    level=logging.WARNING,
    filename='botlog.log'
)


class BotAdmin(StatesGroup):
    insert_chat_id = State()


class SendNews(StatesGroup):
    ask_users = State()
    ask_message = State()
    send_message = State()


WEBHOOK_HOST = 'https://bot.worknear.ru'
WEBHOOK_PATH = ''
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

WEBAPP_HOST = 'localhost'  # or ip
WEBAPP_PORT = 3001


def bot_start():
    @dp.message_handler(commands="start")
    async def cmd_start(message: types.Message):
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text="Создать анкету", callback_data="create_form"))
        await bot.send_photo(message.from_user.id, photo=logo,
                             caption=f'<b>Привет,  {message.from_user.first_name}</b> '
                             f'😃\n{welcome_message}', reply_markup=keyboard)

    @dp.message_handler(commands="help")
    async def cmd_start(message: types.Message):
        from lib import help_message
        await message.answer(help_message)

    @dp.message_handler(commands="show_profile")
    async def show_profile(message: types.Message):
        if await check_user(message.chat.id):
            from getform import get_form

            @sync_to_async
            def get_user_form():
                result_user_form = get_form(message.chat.id, True)
                return result_user_form
            user_form = await get_user_form()
            from lib import print_form
            await print_form(user_form, message, bot)
        else:
            await message.answer("Анкеты еще не создана")

    @dp.message_handler(commands="change_profile")
    async def change_profile(message: types.Message):
        if await check_user(message.chat.id):
            from getform import get_form

            @sync_to_async
            def get_user_form():
                result_user_form = get_form(message.chat.id)
                return result_user_form
            user_form = await get_user_form()
            await message.answer("<b>Вот все данные из твоего профиля:</b>\n" + user_form.full_info)
            from changeform import change_form
            await change_form(message, user_form)
        else:
            await message.answer("Анкеты не существует")

    @dp.message_handler(commands="delete_profile")
    async def delete_profile(message: types.Message):
        if await check_user(message.chat.id):
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton(text="Удалить", callback_data="delete_form"),
                         types.InlineKeyboardButton(text="Отмена", callback_data="cancel"))
            await message.answer("Вы действительно хотите удалить свой профиль?", reply_markup=keyboard)
        else:
            await message.answer("Анкеты не существует")

    @dp.callback_query_handler(text='delete_form')
    async def delete(call: types.CallbackQuery):
        if await check_user(call.message.chat.id):
            from changeform import delete_profile
            await delete_profile(call.message.chat.id)
            await call.message.answer("Анкета удалена")
        else:
            await call.message.answer("Анкеты не существует")

    @dp.callback_query_handler(text='cancel')
    async def delete(call: types.CallbackQuery):
        await call.message.answer("Хорошо, не удаляем")

    @dp.message_handler(commands="watch_profiles")
    async def watch_profiles(message: types.Message):
        if await check_user(message.chat.id):
            from watch_forms import show_profiles
            await show_profiles(message)
        else:
            await message.answer("Для начала нужно создать анкету")

    @dp.message_handler(commands="delete_history")
    async def delete_history(message: types.Message):
        if await check_user(message.chat.id):
            from watch_forms import delete_history
            await delete_history(message.chat.id)
            await message.answer("История просмотренных анкет удалена")
        else:
            await message.answer("Для начала нужно создать анкету")

    @dp.message_handler(commands="watch_matches")
    async def watch_profiles(message: types.Message):
        if await check_user(message.chat.id):
            from getform import get_form
            from watch_forms import get_matches, get_count_matches, get_contacts
            count_matches = await get_count_matches(message.chat.id)
            logging.warning(f'count_matches :: {count_matches}')

            @sync_to_async
            def get_match_form(match):
                result_user_form = get_form(chat_id=None, only_profile=True, pk=match)
                return result_user_form
            if count_matches == 0:
                await message.answer("Пока что у тебя не случился ни один match 🙁")
            elif count_matches == 1:
                from lib import print_form
                await message.answer("У тебя только 1 match")
                matches = await get_matches(message.chat.id)
                one_match = matches[0]
                match_form = await get_match_form(one_match)
                await print_form(match_form, message, bot)
                await message.answer(await get_contacts(one_match))
            else:
                from changeform import get_watched_matches, clear_watched_matches, add_watched_matches
                await clear_watched_matches(message.chat.id)
                keyboard = types.InlineKeyboardMarkup()
                keyboard.add(types.InlineKeyboardButton(text="Далее", callback_data="next_match"))
                await message.answer(f"Вау, ты взаимно понравился {count_matches} пользователям, "
                                     f"чтобы посмотреть их, нажми далее", reply_markup=keyboard)

                @dp.callback_query_handler(text='next_match')
                async def next_match(call: types.CallbackQuery):
                    from lib import print_form
                    watched_matches = await get_watched_matches(call.message.chat.id)
                    if watched_matches != 'Error: user with this chat_id is not exist':
                        matches_next = await get_matches(call.message.chat.id)
                        logging.warning(f'wathced_matches :: {watched_matches}')
                        logging.warning(f'count_matches :: {count_matches}')
                        if len(watched_matches) == count_matches:
                            await call.message.answer("Ты посмотрел все мэтчи")
                        else:
                            logging.warning(f'matches :: {matches_next}')
                            for match in matches_next:
                                logging.warning(f'match :: {match}')
                                if match not in watched_matches:
                                    user_form = await get_match_form(match)
                                    await print_form(user_form=user_form, message=call.message, bot=bot)
                                    await call.message.answer(await get_contacts(match))
                                    await call.message.answer("Чтобы посмотреть следующий match нажми далее",
                                                              reply_markup=keyboard)
                                    await add_watched_matches(call.message.chat.id, match)
                                    break
        else:
            await message.answer("Для начала нужно создать анкету")

    @dp.message_handler(commands="admin")
    async def admin(message: types.Message):
        from lib import ADMINS
        if message.chat.id in ADMINS:
            await message.answer('Введите chat_id удаляемого пользователя')
            await BotAdmin.insert_chat_id.set()
        else:
            await message.answer("Такую команду не знаю")

    @dp.message_handler(state=BotAdmin.insert_chat_id)
    async def delete_for_admin(message: types.Message, state: FSMContext):
        from changeform import delete_profile
        if await delete_profile(message.text):
            await message.answer(f'Пользователь {message.text} удален')
        else:
            await message.answer('Не существует пользователя с таким chat_id')
        await state.finish()

    @dp.message_handler(commands='send_news')
    async def send_news(message: types.Message):
        from lib import ADMINS
        if message.chat.id in ADMINS:
            await message.answer('Кому отправляем сообщение?\nЕсли определенному пользователю – пришли его chat_id\n'
                                 'Если всем – напиши "всем"')
            await SendNews.ask_users.set()
        else:
            await message.answer("Такую команду не знаю")

    @dp.message_handler(state=SendNews.ask_users)
    async def ask_users(message: types.Message, state: FSMContext):
        async with state.proxy() as data:
            if message.text == 'всем':
                data['users'] = 'all'
                await message.answer("Напиши какое сообщение мы отправим всем пользователям")
                await SendNews.next()
            elif message.text.isdigit():
                data['users'] = message.text
                await message.answer(f"Напиши какое сообщение мы отправляем пользователю "
                                     f"с chat_id {message.text}")
                await SendNews.next()
            else:
                await message.answer("Не понял, варианты:\n"
                                     "всем\n"
                                     "9 цифр (chat_id)")
                await state.finish()

    @dp.message_handler(state=SendNews.ask_message)
    async def ask_news(message: types.Message, state: FSMContext):
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text='Да', callback_data='Отправить'),
                     types.InlineKeyboardButton(text='Нет', callback_data='Отмена'))
        await message.answer('Отправляю следующее сообщение?')
        async with state.proxy() as data:
            data['message'] = message.text
        await message.answer(message.text, reply_markup=keyboard)
        await SendNews.next()

    @dp.callback_query_handler(state=SendNews.send_message, text='Отправить')
    async def send_news(call: types.CallbackQuery, state: FSMContext):
        from watch_forms import get_users_chats
        news = []
        for_who = []
        async with state.proxy() as data:
            news.append(data['message'])
            for_who.append(data['users'])
            await state.finish()
        if for_who[0] == 'all':
            users = await get_users_chats()
            errors = []
            for user in users:
                try:
                    await bot.send_message(user, news[0])
                except:
                    errors.append(user)
            await call.message.answer("Сообщения отправлены")
            logging.warning(f' ADMIN:INFO :: Сообщения не отправлены {len(errors)} пользователям :: {errors}')
        else:
            try:
                await bot.send_message(for_who[0], news[0])
                await call.message.answer("Сообщение отправлено")
            except:
                await call.message.answer("Error: Сообщение не отправлено, проверь chat_id")

    @dp.callback_query_handler(state=SendNews.send_message, text='Отмена')
    async def send_news(call: types.CallbackQuery, state: FSMContext):
        await call.message.answer("Ок, не отправляем")
        await state.finish()

    @dp.message_handler()
    async def echo_send(message: types.Message):
        await message.answer("Такую команду не знаю")

    async def on_startup(dp):
        await bot.set_webhook(WEBHOOK_URL)

    async def on_shutdown(dp):
        await bot.delete_webhook()
        await dp.storage.close()
        await dp.storage.wait_closed()

    start_webhook(dispatcher=dp,
                  webhook_path=WEBHOOK_PATH,
                  on_startup=on_startup,
                  on_shutdown=on_shutdown,
                  skip_updates=True,
                  host=WEBAPP_HOST,
                  port=WEBAPP_PORT)
