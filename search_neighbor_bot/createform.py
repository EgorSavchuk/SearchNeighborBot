from bot.models import UserGeneralInformation, UserStatus, UserCriteria, ApartmentOwner
from createbot import dp, bot
from asgiref.sync import sync_to_async
from aiogram import types
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from lib import insert_current_gender, insert_current_user_class, insert_current_neighbor_gender
from lib import insert_current_neighbor_class, insert_current_user_point


# ----------------------------------- Функции для сохранения анкеты в БД ----------------------------------------------#
def get_user_main_info(data):
    user = UserGeneralInformation(
        name=data["user_name"],
        user_vk=data["user_vk"],
        user_tg=data["user_tg"],
        chat_id=data["user_chat_id"],
        avatar=data["user_photo"],
        user_about=data["about_user"],
        user_age=data["user_age"],
        user_gender=insert_current_gender(data["user_gender"]),
        user_class=insert_current_user_class(data["user_class"]),
        neighbor_about=data["neighbor_about"]
    )
    return user


def get_user_status(user, data):
    user_status = UserStatus(
        status_for_user=user,
        form_active=True,
        user_intention=insert_current_user_point(data["user_point"])
    )
    return user_status


@sync_to_async
def save_apartment_searcher(data):
    user = get_user_main_info(data)
    user_status = get_user_status(user, data)
    user_criteria = UserCriteria(
        for_user=user,
        neighbor_gender=insert_current_neighbor_gender(data["neighbor_gender"]),
        neighbor_class=insert_current_neighbor_class(data["neighbor_class"]),
        required_price=data["user_required_price"],
        required_metro=data["user_required_metro"]
    )
    user.save()
    user_status.save()
    user_criteria.save()


@sync_to_async
def save_apartment_owner(data):
    user = get_user_main_info(data)
    user_status = get_user_status(user, data)
    user_criteria = UserCriteria(
        for_user=user,
        neighbor_gender=insert_current_neighbor_gender(data["neighbor_gender"]),
        neighbor_class=insert_current_neighbor_class(data["neighbor_class"])
    )
    user_apartments = ApartmentOwner(
        apartment_owner=user,
        metro=data['metro'],
        address=data['address'],
        time_to_hse=data['time_to_hse'],
        price=int(data['price']),
        about_apartment=data['about_apartment'],
        apartment_images=data['apartment_images']
    )
    user.save()
    user_status.save()
    user_criteria.save()
    user_apartments.save()
# ---------------------------------------------------------------------------------------------------------------------#


# -------------------------------------- Классы для машины состояний --------------------------------------------------#


class CreateGeneralForm(StatesGroup):
    user_name = State()
    user_age = State()
    about_user = State()
    neighbor_about = State()
    user_gender = State()
    user_class = State()
    user_vk = State()
    user_photo = State()
    neighbor_gender = State()
    neighbor_class = State()
    user_point = State()
    metro = State()
    address = State()
    time_to_hse = State()
    price = State()
    about_apartment = State()
    apartment_images = State()
    user_required_price = State()
    user_required_metro = State()

# ---------------------------------------------------------------------------------------------------------------------#

# ------------------------------------------- Создание анкеты ---------------------------------------------------------#


# -------------- Создаем возможность прекратить создание анкеты ----------------#
@dp.message_handler(state='*', commands='cancel')
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()
    await message.reply('Создание анкеты прекращено')


# ------------- Создаем возможность вернуться на один вопрос назад -------------#
@dp.message_handler(state='*', commands='back')
async def back_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    elif current_state == 'CreateGeneralForm:user_required_price':
        await CreateGeneralForm.user_point.set()
    elif current_state == 'CreateGeneralForm:user_name':
        await message.reply("Создание анкеты прекращено")
        await state.finish()
    else:
        await CreateGeneralForm.previous()
        await message.reply('Вернулись назад, введи корректное значение из предыдущего вопроса')


# ------------------------- Записываем основную информацию ---------------------#
@dp.callback_query_handler(text="create_form")
async def ask_name(call: types.CallbackQuery):
    from lib import check_user
    if await check_user(call.message.chat.id):
        await call.message.answer("Анкета уже существует, чтобы внести изменения напиши\n/change_profile")
    else:
        await CreateGeneralForm.user_name.set()
        await call.message.answer(str("<b>Создание анкеты:</b>"
                                      "\nВ любой момент ты можешь написать:\n/cancel для прекращения создания анкеты"
                                      "\n/back для возврата на один вопрос назад"))
        await call.message.answer(str("<b>Поехали, первый вопрос:</b>"
                                      "\nВведи имя для анкеты"))


@dp.message_handler(state=CreateGeneralForm.user_name)
async def write_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['user_name'] = message.text
    await CreateGeneralForm.next()
    await message.reply("Сколько тебе лет?")


@dp.message_handler(lambda message: not message.text.isdigit(), state=CreateGeneralForm.user_age)
async def process_age_invalid(message: types.Message):
    return await message.reply("Напиши возраст - числом")


@dp.message_handler(lambda message: message.text.isdigit() and int(message.text) > 118,
                    state=CreateGeneralForm.user_age)
async def process_age_invalid(message: types.Message):
    return await message.reply(f"Самому старому человеку (из ныне живущих) 2 января исполнилось 118 лет\n"
                               f"Если тебе действительно {message.text}, советую обратиться сюда\n"
                               f"https://www.guinnessworldrecords.com/ \nКак только ты там появишься я сразу создам"
                               f" твою анкету, а пока что введи возраст поменьше")


@dp.message_handler(lambda message: message.text.isdigit() and int(message.text) == 0, state=CreateGeneralForm.user_age)
async def process_age_invalid(message: types.Message):
    return await message.reply(f"Автору реально 0 лет?\nВведи корректное значение :)")


@dp.message_handler(state=CreateGeneralForm.user_age)
async def write_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['user_age'] = int(message.text)
    await CreateGeneralForm.next()
    await message.reply("Расскажи о себе, это будет видно всем пользователям в твоей анкете")


@dp.message_handler(state=CreateGeneralForm.about_user)
async def write_about_user(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['about_user'] = message.text
    await CreateGeneralForm.next()
    await message.reply(str("Расскажи какого соседа ты бы хотел(а) найти?\nЭто тоже будет отображаться в твоей анкете"))


@dp.message_handler(state=CreateGeneralForm.neighbor_about)
async def write_neighbor_about(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['neighbor_about'] = message.text
    await CreateGeneralForm.next()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add("М", "Ж")
    await message.reply(str("Укажи свой пол"), reply_markup=markup)


@dp.message_handler(lambda message: message.text not in ["М", "Ж"], state=CreateGeneralForm.user_gender)
async def process_gender_invalid(message: types.Message):
    return await message.reply("Укажи пол кнопкой на клавиатуре")


@dp.message_handler(state=CreateGeneralForm.user_gender)
async def write_user_gender(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["user_gender"] = message.text
    await CreateGeneralForm.next()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add('1', '2', '3', '4', '5', '6', 'Выпускник')
    await message.reply(str("На каком курсе ты учишься? Или выпускник?"), reply_markup=markup)


@dp.message_handler(lambda message:
                    message.text not in ['1', '2', '3', '4', '5', '6', 'Выпускник'],
                    state=CreateGeneralForm.user_class)
async def process_choose_course_invalid(message: types.Message):
    return await message.reply("Укажи курс кнопкой на клавиатуре")


@dp.message_handler(state=CreateGeneralForm.user_class)
async def write_user_class(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['user_class'] = message.text
    await CreateGeneralForm.next()
    markup = types.ReplyKeyboardRemove()
    await message.reply(str("Укажи ссылку на свои соцсети\nСсылку на telegram я уже записал 😊"), reply_markup=markup)


@dp.message_handler(state=CreateGeneralForm.user_vk)
async def write_user_vk(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['user_vk'] = message.text
        data['user_tg'] = message.from_user.username
        data['user_chat_id'] = message.chat.id
    await CreateGeneralForm.next()
    await message.reply(str("Отправь мне фото, которое станет аватаркой твоей анкеты"))


@dp.message_handler(lambda message: len(message.photo) == 0, state=CreateGeneralForm.user_photo)
async def process_send_user_photo_invalid(message: types.Message):
    return await message.reply("Ты не прислал фото :(\n"
                               "Повтори еще раз, другие пользователи хотели бы увидеть тебя 🙂")


@dp.message_handler(content_types=['photo'], state=CreateGeneralForm.user_photo)
async def write_user_photo(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['user_photo'] = message.photo[0].file_id
    await CreateGeneralForm.next()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True, row_width=1)
    markup.add('Важно, хочу соседа девушку', 'Важно, хочу соседа мужчину', 'Неважно')
    await message.reply(str("Важен ли тебе пол соседа?"), reply_markup=markup)


@dp.message_handler(lambda message:
                    message.text not in ['Важно, хочу соседа девушку', 'Важно, хочу соседа мужчину', 'Неважно'],
                    state=CreateGeneralForm.neighbor_gender)
async def process_neighbor_gender_invalid(message: types.Message):
    return await message.reply("Такое значение не знаю, выбери с клавиатуры")


@dp.message_handler(state=CreateGeneralForm.neighbor_gender)
async def write_neighbor_gender(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["neighbor_gender"] = message.text
    await CreateGeneralForm.next()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add('Да, 1-2', 'Да, 3-4', 'Да, 5-6', 'Да, 1-4', 'Да, выпускник', 'Не важен')
    await message.reply(str("Важен ли тебе курс соседа?\nЕсли важен, укажи его"),
                        reply_markup=markup)


@dp.message_handler(lambda message:
                    message.text not in
                    ['Да, 1-2', 'Да, 3-4', 'Да, 5-6', 'Да, 1-4', 'Да, выпускник', 'Не важен'],
                    state=CreateGeneralForm.neighbor_class)
async def process_neighbor_class_invalid(message: types.Message):
    return await message.reply("Такое значение не знаю, выбери с клавиатуры")


@dp.message_handler(state=CreateGeneralForm.neighbor_class)
async def write_neighbor_class(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['neighbor_class'] = message.text
    await CreateGeneralForm.next()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True, row_width=1)
    markup.add('Соседа в свою квартиру', 'Квартиру')
    await message.reply(str("Кого ты хочешь найти?\n"
                            "Если выберешь 'Соседа в свою квартиру', тебе будут показываться"
                            " анкеты людей, ищущих квартиру\n"
                            "Если выберешь 'Квартиру' тебе будут показываться анкеты владельцев квартир,"
                            " а также анкеты такиж же искателей жилья, как и ты,"
                            " чтобы вы могли объединиться и вместе найти квартиру"), reply_markup=markup)


@dp.message_handler(lambda message:
                    message.text not in
                    ['Соседа в свою квартиру',
                     'Квартиру'],
                    state=CreateGeneralForm.user_point)
async def process_user_point_invalid(message: types.Message):
    return await message.reply("Такое значение не знаю, выбери с клавиатуры")


@dp.message_handler(state=CreateGeneralForm.user_point)
async def write_user_point(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['user_point'] = message.text
    markup = types.ReplyKeyboardRemove()
    if data['user_point'] == 'Соседа в свою квартиру':
        await message.reply(f'<i>Осталось совсем немного, указать информацию о квартире</i>\n'
                            f'Рядом с какой станцией метро она находится?', reply_markup=markup)
        await CreateGeneralForm.next()
    else:
        await CreateGeneralForm.user_required_price.set()
        await message.reply("Введи максимальную стоимость проживания в квартире\n"
                            "Анкеты с большей ценой отображаться не будут\nВведи сумму в формате"
                            " 25250, без пробелов, запятых, точек", reply_markup=markup)


# ---------------- Записываем информацию о владельце квартиры-------------------------#
@dp.message_handler(state=CreateGeneralForm.metro)
async def write_metro(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['metro'] = message.text
    await CreateGeneralForm.next()
    await message.reply("Укажи точный адрес квартиры")


@dp.message_handler(state=CreateGeneralForm.address)
async def write_address(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['address'] = message.text
    await CreateGeneralForm.next()
    await message.reply("Напиши сколько добираться до корпусов вышки\nМожешь указать несколько корпусов")


@dp.message_handler(state=CreateGeneralForm.time_to_hse)
async def write_time_to_hse(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['time_to_hse'] = message.text
    await CreateGeneralForm.next()
    await message.reply("Сколько проживание в твоей квартире будет стоить?\n"
                        "Введи сумму в формате 25250, без пробелов, запятых, точек")


@dp.message_handler(lambda message: not message.text.isdigit(), state=CreateGeneralForm.price)
async def process_price_invalid(message: types.Message):
    return await message.reply("Введи цену в правильном формате")


@dp.message_handler(lambda message: message.text.isdigit() and int(message.text) > 999999,
                    state=CreateGeneralForm.price)
async def process_price_invalid(message: types.Message):
    return await message.reply("Максимальная цена - 999.999")


@dp.message_handler(state=CreateGeneralForm.price)
async def write_price(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['price'] = message.text
    await CreateGeneralForm.next()
    await message.reply("Расскажи о своей квартире")


@dp.message_handler(state=CreateGeneralForm.about_apartment)
async def write_about_apartment(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['about_apartment'] = message.text
        data['apartment_images'] = []
    await CreateGeneralForm.next()
    await message.reply("Загрузи фотографии квартиры, по одной")


@dp.message_handler(lambda message: len(message.photo) == 0, state=CreateGeneralForm.apartment_images)
async def process_get_apartment_images(message: types.Message):
    return await message.reply("Ты прислал не фото :(")


@dp.message_handler(content_types=['photo'], state=CreateGeneralForm.apartment_images)
async def load_photos(message: types.Message, state: FSMContext):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="Дальше", callback_data="next"))
    async with state.proxy() as data:
        if len(data["apartment_images"]) == 9:
            await message.reply("Больше 9 фотографий загрузить нельзя, нажми 'дальше'", reply_markup=keyboard)
        else:
            data['apartment_images'].append(message.photo[0].file_id)
    if len(data["apartment_images"]) >= 2:
        await message.reply(f"Загрузи еще фотографии"
                            f"\nЕсли это последняя фотография, нажми 'дальше'", reply_markup=keyboard)
    elif len(data["apartment_images"]) != 9:
        await message.reply(f"Загрузи еще фотографии")


@dp.callback_query_handler(text="next", state=CreateGeneralForm.apartment_images)
async def get_profile(call: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        await save_apartment_owner(data)
        await send_notify_new_form(data)
        await call.message.answer(str('<b>Твоя анкета готова!</b>\nВот все данные из нее:'))
        from getform import get_form

        @sync_to_async
        def get_user_form():
            result_user_form = get_form(call.message.chat.id)
            return result_user_form
        user_form = await get_user_form()
        await call.message.answer(user_form.full_info)
        await call.message.answer("<b>А вот так ее будут видеть другие пользователи</b>")
        await bot.send_photo(call.message.chat.id, photo=user_form.avatar,
                             caption=user_form.caption)
        await call.message.answer_media_group(media=user_form.apartment_photos)
        await call.message.answer("Ты всегда можешь изменить анкету в главном меню бота")
        await state.finish()


# ------------------ Записываем информацию об искателе квартиры-------------------------#
@dp.message_handler(lambda message: not message.text.isdigit() or int(message.text) > 999999,
                    state=CreateGeneralForm.user_required_price)
async def process_price_invalid(message: types.Message):
    return await message.reply("Введи цену в правильном формате,\nминимальная цена - 0"
                               "\nмаксимальная цена -999.999")


@dp.message_handler(state=CreateGeneralForm.user_required_price)
async def write_required_metro(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['user_required_price'] = int(message.text)
    markup = types.ReplyKeyboardRemove()
    await CreateGeneralForm.next()
    await message.answer("Напиши рядом с какими станциями метро ты хочешь найти квартиру?", reply_markup=markup)


@dp.message_handler(state=CreateGeneralForm.user_required_metro)
async def write_required_metro(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['user_required_metro'] = message.text
        await save_apartment_searcher(data)
        await send_notify_new_form(data)
        await message.answer(str('<b>Твоя анкета готова!</b>\nВот все данные из нее:'))
        from getform import get_form

        @sync_to_async
        def get_user_form():
            result_user_form = get_form(message.chat.id)
            return result_user_form
        user_form = await get_user_form()
        await message.answer(user_form.full_info)
        await message.answer("<b>А вот так ее будут видеть другие пользователи</b>")
        await bot.send_photo(message.chat.id, photo=user_form.avatar,
                             caption=user_form.caption)
        await message.answer("Ты всегда можешь изменить анкету в главном меню бота")
        await state.finish()

# ---------------------------------------------------------------------------------------------------------------------#


async def send_notify_new_form(data):
    pk = await get_user_pk(data)
    users_chats = await get_all_user()
    for user in users_chats:
        if await check_criteria(user, pk) and await get_pk_from_chat_id(user) != pk:
            try:
                await bot.send_message(user, '<b>Появилась новая анкета для тебя!\n</b>'
                                             'посмотреть можно в "смотреть анкеты"')
            except:
                print(f'Пользователь {user} отписался')


@sync_to_async
def get_all_user():
    cur_users = UserGeneralInformation.objects.all()
    chat_ids = []
    for user in cur_users:
        chat_ids.append(user.chat_id)
    return chat_ids


@sync_to_async
def get_user_pk(data):
    pk = UserGeneralInformation.objects.filter(chat_id=data['user_chat_id']).first().pk
    return pk


@sync_to_async
def check_criteria(chat_id, pk):
    from watch_forms import get_criteria
    criteria = get_criteria(chat_id)
    form = UserGeneralInformation.objects.filter(pk=pk)[0]
    form_intention = UserStatus.objects.filter(status_for_user_id=pk)[0].user_intention
    if criteria['search_what'] == 1 and form_intention == 1:
        return False
    if criteria['neighbor_gender'] == 1 and not form.user_gender:
        return False
    elif criteria['neighbor_gender'] == 2 and form.user_gender:
        return False
    elif criteria['neighbor_class'] == 1 and form.user_class not in [1, 2]:
        return False
    elif criteria['neighbor_class'] == 2 and form.user_class not in [3, 4]:
        return False
    elif criteria['neighbor_class'] == 3 and form.user_class not in [5, 6]:
        return False
    elif criteria['neighbor_class'] == 4 and form.user_class not in [1, 4]:
        return False
    elif criteria['neighbor_class'] == 5 and form.user_class != 7:
        return False
    if criteria['search_what'] == 2 and form_intention == 1:
        price = ApartmentOwner.objects.filter(apartment_owner_id=pk)[0].price
        if price > criteria['required_price']:
            return False
    return True


@sync_to_async
def get_pk_from_chat_id(chat_id):
    from bot.models import UserGeneralInformation
    if UserGeneralInformation.objects.filter(chat_id=chat_id).exists():
        user = UserGeneralInformation.objects.filter(chat_id=chat_id)[0]
        pk = user.pk
        return pk
    else:
        return 'Error: get_pk_from_chat_id: Пользователя не существует'
