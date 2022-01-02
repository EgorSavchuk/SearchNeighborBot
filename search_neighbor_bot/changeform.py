from lib import insert_current_gender, insert_current_user_class, get_change_caption_v2
from lib import insert_current_neighbor_gender, insert_current_neighbor_class
from bot.models import UserGeneralInformation, UserCriteria, ApartmentOwner
from createbot import dp
from aiogram import types
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from asgiref.sync import sync_to_async


# Изменение анкеты пользователя, создаются два класса для машины состояний ChangeSearcherForm и ChangeApartmentOwnerForm
# При вызове из основного файла вызывается фунция change_form, спрашивающая какое значение пользователь хочет изменить
# Эта функция также определяет тип пользователя, искатель квартиры либо владелец квартиры
# После определения типа пользователя запускается соответствующая машина состояний


# ------------------------------------------ Классы для машины состояний --------------------------------------------- #
class ChangeSearcherForm(StatesGroup):
    ask_field = State()
    check_changes = State()


class ChangeApartmentOwnerForm(StatesGroup):
    ask_field = State()
    load_apartment_images = State()
    check_changes = State()


# -------------------------------------------------------------------------------------------------------------------- #


# Функция, вызываемая из homeet_bot.py
async def change_form(message, user_form):
    keyboard = get_change_caption_v2(user_form)
    await message.answer("Какое поле ты хочешь изменить?", reply_markup=keyboard)
    if user_form.apartment_photos == 'None':
        await ChangeSearcherForm.ask_field.set()
    else:
        await ChangeApartmentOwnerForm.ask_field.set()

# -------------------------------------- Изменяем анкету искателя квартиры ------------------------------------------- #
    # Сохранение выбора пользователя и вызов соответсвующей функции для вывода вопроса про изменяемое поле
    @dp.callback_query_handler(state=ChangeSearcherForm.ask_field)
    async def check_command(call: types.CallbackQuery, state: FSMContext):
        async with state.proxy() as data:
            data['field'] = int(call.data)
        if data['field'] == 12:
            await state.finish()
            await message.answer("Изменение анкеты прекращено")
        elif data['field'] <= 9:
            await answer_what_change_main(int(call.data), call.message)
            await ChangeSearcherForm.next()
        else:
            await answer_what_change_searcher(int(call.data), call.message)
            await ChangeSearcherForm.next()

    @dp.message_handler(content_types=['photo'], state=ChangeSearcherForm.check_changes)
    async def check_changes_photo(message: types.Message, state: FSMContext):
        async with state.proxy() as data:
            if data['field'] == 0 and await check_main_changes(data['field'], message) == 'Ok':
                await write_main_changes(message, data['field'])
                await message.answer("Данные успешно обновлены")
                await state.finish()

    @dp.message_handler(state=ChangeSearcherForm.check_changes)
    async def check_changes(message: types.Message, state: FSMContext):
        async with state.proxy() as data:
            field = data['field']
            if field == 10 and (not message.text.isdigit() or int(message.text) > 999999) and field != 0:
                await message.answer("Введи цену в правильном формате:\nЧислом, до 99999")
            elif await check_main_changes(data['field'], message) == 'Ok' and field != 0:
                if field <= 9:
                    await write_main_changes(message, field)
                elif field == 10 or field == 11:
                    await write_searcher_changes(message, field)
                markup = types.ReplyKeyboardRemove()
                await message.answer("Данные успешно обновлены", reply_markup=markup)
                await state.finish()

# -------------------------------------------------------------------------------------------------------------------- #

# -------------------------------------- Изменяем анкету владельца квартиры ------------------------------------------ #
    @dp.callback_query_handler(state=ChangeApartmentOwnerForm.ask_field)
    async def check_command(call: types.CallbackQuery, state: FSMContext):
        async with state.proxy() as data:
            data['field'] = int(call.data)
            data["apartment_images"] = []
        if data['field'] == 16:
            await state.finish()
            await message.answer("Изменение анкеты прекращено")
        elif data['field'] <= 9:
            await answer_what_change_main(int(call.data), call.message)
            await ChangeApartmentOwnerForm.check_changes.set()
        elif data['field'] == 15:
            await message.answer("Загрузи новые фотографии квартиры")
            await ChangeApartmentOwnerForm.next()
        else:
            await answer_what_change_apartment_owner(int(call.data), call.message)
            await ChangeApartmentOwnerForm.check_changes.set()

    @dp.message_handler(content_types=['photo'], state=ChangeApartmentOwnerForm.load_apartment_images)
    async def load_photos(message: types.Message, state: FSMContext):
        keyboard_images = types.InlineKeyboardMarkup()
        keyboard_images.add(types.InlineKeyboardButton(text="Дальше", callback_data="next_for_change"))
        async with state.proxy() as data:
            if len(data["apartment_images"]) == 9:
                await message.reply("Больше 9 фотографий загрузить нельзя, нажми 'дальше'",
                                    reply_markup=keyboard_images)
            else:
                data['apartment_images'].append(message.photo[0].file_id)
        if len(data["apartment_images"]) >= 2:
            await message.reply(f"Загрузи еще фотографии"
                                f"\nЕсли это последняя фотография, нажми 'дальше'", reply_markup=keyboard_images)
        elif len(data["apartment_images"]) != 9:
            await message.reply(f"Загрузи еще фотографии")

    @dp.callback_query_handler(text='next_for_change', state=ChangeApartmentOwnerForm.load_apartment_images)
    async def write_apartments_photo(call: types.CallbackQuery, state: FSMContext):
        async with state.proxy() as data:
            await write_apartment_owner_changes(call.message, 15, data)
        await state.finish()
        await call.message.answer("Фотографии обновлены")

    @dp.message_handler(state=ChangeApartmentOwnerForm.check_changes)
    async def check_changes(message: types.Message, state: FSMContext):
        async with state.proxy() as data:
            field = data['field']
            if field == 10 and (not message.text.isdigit() or int(message.text) > 99999):
                await message.answer("Введи цену в правильном формате:\nЧислом, до 99999")
            elif await check_main_changes(data['field'], message) == 'Ok':
                if field <= 9:
                    await write_main_changes(message, field)
                elif field in [10, 11, 12, 13]:
                    await write_apartment_owner_changes(message, field, data)
                await message.answer("Данные успешно обновлены")
                await state.finish()


# -------------------------------------------------------------------------------------------------------------------- #


# Функция, записывающая в бд измененный данные
@sync_to_async
def write_main_changes(message: types.Message, field):
    if field == 0:
        UserGeneralInformation.objects.filter(chat_id=message.chat.id).update(avatar=message.photo[0].file_id)
    elif field == 1:
        UserGeneralInformation.objects.filter(chat_id=message.chat.id).update(name=message.text)
    elif field == 2:
        UserGeneralInformation.objects.filter(chat_id=message.chat.id).update(user_about=message.text)
    elif field == 3:
        UserGeneralInformation.objects.filter(chat_id=message.chat.id).update(user_age=int(message.text))
    elif field == 4:
        UserGeneralInformation.objects.filter(chat_id=message.chat.id).update(
            user_gender=insert_current_gender(message.text))
    elif field == 5:
        UserGeneralInformation.objects.filter(chat_id=message.chat.id).update(
            user_class=insert_current_user_class(message.text))
    elif field == 6:
        UserGeneralInformation.objects.filter(chat_id=message.chat.id).update(user_vk=message.text)
    elif field == 7:
        UserGeneralInformation.objects.filter(chat_id=message.chat.id).update(neighbor_about=message.text)
    elif field == 8:
        UserCriteria.objects.filter(for_user=UserGeneralInformation.objects.filter(chat_id=message.chat.id)[0]).update(
            neighbor_gender=insert_current_neighbor_gender(message.text))
    elif field == 9:
        UserCriteria.objects.filter(for_user=UserGeneralInformation.objects.filter(chat_id=message.chat.id)[0]).update(
            neighbor_class=insert_current_neighbor_class(message.text))


@sync_to_async
def write_searcher_changes(message: types.Message, field):
    if field == 10:
        UserCriteria.objects.filter(for_user=UserGeneralInformation.objects.filter(chat_id=message.chat.id)[0]).update(
            required_price=int(message.text))
    elif field == 11:
        UserCriteria.objects.filter(for_user=UserGeneralInformation.objects.filter(chat_id=message.chat.id)[0]).update(
            required_metro=message.text)


@sync_to_async
def write_apartment_owner_changes(message: types.Message, field, data):
    if field == 10:
        ApartmentOwner.objects.filter(apartment_owner=UserGeneralInformation.objects.filter(
            chat_id=message.chat.id)[0]).update(price=int(message.text))
    elif field == 11:
        ApartmentOwner.objects.filter(apartment_owner=UserGeneralInformation.objects.filter(
            chat_id=message.chat.id)[0]).update(metro=message.text)
    elif field == 12:
        ApartmentOwner.objects.filter(apartment_owner=UserGeneralInformation.objects.filter(
            chat_id=message.chat.id)[0]).update(address=message.text)
    elif field == 13:
        ApartmentOwner.objects.filter(apartment_owner=UserGeneralInformation.objects.filter(
            chat_id=message.chat.id)[0]).update(time_to_hse=message.text)
    elif field == 14:
        ApartmentOwner.objects.filter(apartment_owner=UserGeneralInformation.objects.filter(
            chat_id=message.chat.id)[0]).update(about_apartment=message.text)
    elif field == 15:
        ApartmentOwner.objects.filter(apartment_owner=UserGeneralInformation.objects.filter(
            chat_id=message.chat.id)[0]).update(apartment_images=data['apartment_images'])


# Функция, проверяющая значения пользовательского ввода для полей основной информации из анкеты
async def check_main_changes(field, message: types.Message):
    if field == 0 and len(message.photo) == 0:
        await message.answer("Ты прислал не фото")
    elif field == 3 and not message.text.isdigit():
        await message.answer("Введи возраст числом")
    elif field == 3 and int(message.text) == 0:
        await message.answer("Автору реально 0 лет?\nВведи корректное значение")
    elif field == 3 and int(message.text) > 118:
        await message.answer(f"Самому старому человеку (из ныне живущих) 2 января 2021 исполняется 118 лет\n"
                             f"Если тебе действительно {message.text}, советую обратиться сюда\n"
                             f"https://www.guinnessworldrecords.com/ \nКак только ты там появишься я сразу создам"
                             f" твою анкету, а пока что введи возраст поменьше")
    elif field == 4 and message.text not in ['М', 'Ж']:
        await message.answer("Такого пола не знаю, выбери значение с клавиатуры")
    elif field == 5 and message.text not in ['1', '2', '3', '4', '5', '6', 'Выпускник']:
        await message.answer("Такой курс не знаю, выбери значение с клавиатуры")
    elif field == 8 and message.text not in ['Важно, хочу соседа девушку', 'Важно, хочу соседа мужчину', 'Неважно']:
        await message.answer("Такой пол не знаю, выбери значение с клавиатуры")
    elif field == 9 and message.text not in ['Да, 1-2', 'Да, 3-4', 'Да, 5-6', 'Да, 1-4', 'Да, выпускник', 'Не важен']:
        await message.answer("Такой курс не знаю, выбери значение с клавиатуры")
    else:
        return 'Ok'


# -------------------------- Функции, возвращающие вопрос на выбор изменяемого поля пользователя --------------------- #

async def answer_what_change_main(field, message: types.Message):
    if field == 0:
        await message.answer("Загрузи новую аватарку")
    elif field == 1:
        await message.answer("Введи новое имя")
    elif field == 2:
        await message.answer("Введи новое значение поля 'О себе'")
    elif field == 3:
        await message.answer("Введи новый возраст")
    elif field == 4:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
        markup.add("М", "Ж")
        await message.answer("Собираешься изменить пол?\nЛадно, вводи новый", reply_markup=markup)
    elif field == 5:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
        markup.add('1', '2', '3', '4', '5', '6', 'Выпускник')
        await message.answer("Введи новый курс", reply_markup=markup)
    elif field == 6:
        await message.answer("Введи новые ссылки на соцсети")
    elif field == 7:
        await message.answer("Введи новое значение поля 'Какого соседа хочу найти'")
    elif field == 8:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True, row_width=1)
        markup.add('Важно, хочу соседа девушку', 'Важно, хочу соседа мужчину', 'Неважно')
        await message.answer("Введи новый желаемый пол соседа", reply_markup=markup)
    elif field == 9:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
        markup.add('Да, 1-2', 'Да, 3-4', 'Да, 5-6', 'Да, 1-4', 'Да, выпускник', 'Не важен')
        await message.answer("Введи новый желаемый курс соседа", reply_markup=markup)


async def answer_what_change_searcher(field, message: types.Message):
    if field == 10:
        await message.answer("Введи новую максимальную цену за квартиру")
    elif field == 11:
        await message.answer("Введи новое значение поля 'Станции метро, рядом с которыми ищешь квартиру'")


async def answer_what_change_apartment_owner(field, message: types.Message):
    if field == 10:
        await message.answer("Введи новую цену квартиры")
    elif field == 11:
        await message.answer("Введи новое значение поля 'Станция метро квартиры'")
    elif field == 12:
        await message.answer("Введи новое значение поля 'Точный адрес квартиры'")
    elif field == 13:
        await message.answer("Введи новое значение поля 'Время до корпусов вышки'")
    elif field == 14:
        await message.answer("Введи новое описание квартиры")
    elif field == 15:
        await message.answer("Загрузи новые фотографии квартиры")


# -------------------------------------------------------------------------------------------------------------------- #

# ------------------------------------------- Удаление анкеты ---------------------------------------------------------#


@sync_to_async
def delete_profile(chat_id):
    from bot.models import UserStatus
    from lib import get_pk_from_chat_id
    pk = get_pk_from_chat_id(chat_id)
    user_criteria_for_delete = UserCriteria.objects.get(for_user_id=pk)
    user_status_for_delete = UserStatus.objects.get(status_for_user_id=pk)
    user_general_info = UserGeneralInformation.objects.get(id=pk)
    if user_status_for_delete.user_intention == 1:
        apartment_owner_for_delete = ApartmentOwner.objects.get(apartment_owner_id=pk)
        apartment_owner_for_delete.delete()
    users = UserGeneralInformation.objects.all()
    for user in users:
        if pk in user.watched_profiles:
            array = user.watched_profiles
            array.remove(pk)
            UserGeneralInformation.objects.filter(pk=user.pk).update(watched_profiles=array)
        if pk in user.matches:
            array = user.matches
            array.remove(pk)
            UserGeneralInformation.objects.filter(pk=user.pk).update(matches=array)
    user_general_info.liked_user.remove(pk)
    user_criteria_for_delete.delete()
    user_status_for_delete.delete()
    user_general_info.delete()
