from createbot import dp, bot
from aiogram import types
from aiogram.utils import executor
from lib import logo, welcome_message, check_user
from asgiref.sync import sync_to_async
import createform


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
            await message.answer("Анкеты не существует")

    @dp.message_handler(commands="change_profile")
    async def change_profile(message: types.Message):
        if await check_user(message.chat.id):
            from getform import get_form

            @sync_to_async
            def get_user_form():
                result_user_form = get_form(message.chat.id)
                return result_user_form
            user_form = await get_user_form()
            await message.answer("Вот все данные из твоего профиля:\n" + user_form.full_info)
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
            await message.answer("Анкеты не существует")

    @dp.message_handler(commands="delete_history")
    async def delete_history(message: types.Message):
        if await check_user(message.chat.id):
            from watch_forms import delete_history
            await delete_history(message.chat.id)
            await message.answer("История просмотренных анкет удалена")
        else:
            await message.answer("Анкеты не существует")

    @dp.message_handler(commands="watch_matches")
    async def watch_profiles(message: types.Message):
        if await check_user(message.chat.id):
            from getform import get_form
            from watch_forms import get_matches, get_count_matches, get_contacts
            count_matches = await get_count_matches(message.chat.id)

            @sync_to_async
            def get_match_form(match):
                result_user_form = get_form(None, True, match)
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
                watched_matches = []
                keyboard = types.InlineKeyboardMarkup()
                keyboard.add(types.InlineKeyboardButton(text="Далее", callback_data="next_match"))
                await message.answer(f"Вау, ты взаимно понравился {count_matches} пользователям, "
                                     f"чтобы посмотреть их, нажми далее", reply_markup=keyboard)
                matches = await get_matches(message.chat.id)

                @dp.callback_query_handler(text='next_match')
                async def next_match(call: types.CallbackQuery):
                    from lib import print_form
                    if len(watched_matches) == count_matches:
                        await message.answer("Ты посмотрел все мэтчи")
                    for match in matches:
                        if match not in watched_matches:
                            user_form = await get_match_form(match)
                            await print_form(user_form, call.message, bot)
                            await message.answer(await get_contacts(match))
                            await message.answer("Чтобы посмотреть следующий match нажми далее", reply_markup=keyboard)
                            watched_matches.append(match)
                            break
        else:
            await message.answer("Анкеты не существует")

    @dp.message_handler()
    async def echo_send(message: types.Message):
        await message.answer("Такую команду не знаю")

    executor.start_polling(dp, skip_updates=True)
