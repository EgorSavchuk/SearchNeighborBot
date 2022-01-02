import django
import os
from asgiref.sync import sync_to_async
from aiogram import types
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "search_neighbor_bot.settings")
django.setup()
logo = 'AgACAgIAAxkBAAIEpGG8-85TBKAl62k4gqcs3ESy3Fz6AAIHtjEbYWPpSbdD8CHoJ2EyAQADAgADcwADIwQ'
welcome_message = """Я бот для поиска соседей среди студентов вышки или выпускников.\nС помощью меня можно найти 
соседа к себе в квартиру или же найти человека, у которого есть квартира, и он рад поделить плату за нее с новым \
соседом! 

Я работаю по модели tinder'a. 🔥

Для начала ты создаешь свою анкету, после чего тебе открываются анкеты других людей, которые ты можешь либо \
лайкнуть либо пропустить. 

Если с кем-то у тебя случается "match", я отправляю вам контакты друг друга

Подробная информая: /help

<b>Правила:</b>

❗ Данный бот используется <strong>только</strong> для поиска соседей

❗ Информация, указанная в анкете должна быть достоверной

Если все понятно то вперед создавать анкету!"""

help_message = f"<b>Как работает этот бот?</b>\n\nДля начала ты создаешь анкету, указывая критерии для поиска:\n\n"\
                "Соседа какого пола ты хочешь найти: тебе будут показывать анкеты только того пола, " \
                "который ты выберешь\n\n"\
                "Соседа с какого курса ты хочешь найти: тебе будут показываться анкеты людей, " \
                "обучающихся на данном курсе\n\n"\
                "Максимальная цена(для искателей квартиры): тебе будут показываться анкеты квартир, " \
                "которые по стоимости не превышают "\
                "заданную, а так же все анкеты таких же искателей квартир как и ты\n\n" \
               "После чего ты можешь смотреть анкеты других пользователей и как в tinder`e ставить им лайк либо " \
               "пропускать, если кто-то поставит лайк твоей анкете, а ты его, я отправлю вам уведомление о match`e " \
               "с контактами друг друга\n\n" \
               "Функция 'Смотреть анкеты' -  тебе будут предложены все анкеты, удовлетворяющие твоим требованиям\n\n" \
               "Функция 'Смотреть мэтчи' - Здесь собраны все твои мэтчи\n\n" \
               "Ты всегда можешь изменить свою анкету, либо создать новую"

match_message = "🎉  <b>У вас новый match!</b>  🎉\n"


# Функция, выводящее правльную форму слова лет, года, год (для анкеты)
def get_current_age_name(age):
    if age % 10 == 1 and age != 11 and age % 100 != 11:
        return 'год'
    elif 1 < age % 10 <= 4 and age != 12 and age != 13 and age != 14:
        return 'года'
    else:
        return 'лет'


# Функция, выводящее цену в формате 10.000, разделяет точкой
def get_price_to_view(price):
    result_price = ''
    price = str(price)
    if len(price) <= 3:
        return price
    else:
        for i in range(0, len(price)):
            if i == (len(price) - 3):
                result_price += '.'
            result_price += price[i]
        return result_price


# Возвращает pk пользователя по chat_id
def get_pk_from_chat_id(chat_id):
    from bot.models import UserGeneralInformation
    if UserGeneralInformation.objects.filter(chat_id=chat_id).exists():
        user = UserGeneralInformation.objects.filter(chat_id=chat_id)[0]
        pk = user.pk
        return pk
    else:
        return 'Error: get_pk_from_chat_id: Пользователя не существует'


# Выводит анкету
async def print_form(user_form, message, bot, for_searching=False, for_notification=0):
    if for_searching:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(text="👎", callback_data="dislike"),
                     types.InlineKeyboardButton(text="👍", callback_data="like"))
    else:
        keyboard = types.ReplyKeyboardRemove()
    if for_notification != 0:
        if user_form.apartment_photos != 'None':
            await bot.send_photo(for_notification, photo=user_form.avatar, caption=user_form.caption,
                                 reply_markup=keyboard)
            await bot.send_media_group(for_notification, media=user_form.apartment_photos)
        else:
            await bot.send_photo(for_notification, photo=user_form.avatar, caption=user_form.caption,
                                 reply_markup=keyboard)
    else:
        if user_form.apartment_photos != 'None':
            await bot.send_photo(message.chat.id, photo=user_form.avatar, caption=user_form.caption, reply_markup=keyboard)
            await message.answer_media_group(media=user_form.apartment_photos)
        else:
            await bot.send_photo(message.chat.id, photo=user_form.avatar, caption=user_form.caption, reply_markup=keyboard)


# Выводит сообщение в котором спрашивается какой пункт хочет изменить пользователь
def get_change_caption(user_form):
    caption = f'<b>0</b> - Аватарку\n' \
              f'<b>1</b> - Имя\n' \
              f'<b>2</b> - О себе\n' \
              f'<b>3</b> - Возраст\n' \
              f'<b>4</b> - Пол\n' \
              f'<b>5</b> - Курс\n' \
              f'<b>6</b> - Ссылки на соцсети\n' \
              f'<b>7</b> - Какого соседа хочешь найти\n' \
              f'<b>8</b> - Желаемый пол соседа\n' \
              f'<b>9</b> - Желаемый курс соседа\n'
    comment = f'Поле "Кого ты ищешь?" поменять нельзя т.к оно влияет на уже сформировавшиеся мэтчи,' \
              f' для этого создай новую анкету\n'
    if user_form.apartment_photos == 'None':
        caption += f'<b>10</b> - Цена, которая устроит за квартиру\n' \
                   f'<b>11</b> - Станции метро, рядом с которыми ищешь квартиру\n' \
                   f'<b>12</b> - Отмена\n{comment}'
    else:
        caption += f'<b>10</b> - Цена квартиры\n' \
                   f'<b>11</b> - Станция метро квартиры\n' \
                   f'<b>12</b> - Время до корпусов вышки\n' \
                   f'<b>13</b> - Описание квартиры\n' \
                   f'<b>14</b> - Фотографии квартиры\n' \
                   f'<b>15</b> - Отмена\n{comment}'
    return caption


def get_change_caption_v2(user_form):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text='Аватарку', callback_data='0'))
    keyboard.add(types.InlineKeyboardButton(text='Имя', callback_data='1'))
    keyboard.add(types.InlineKeyboardButton(text='О себе', callback_data='2'))
    keyboard.add(types.InlineKeyboardButton(text='Возраст', callback_data='3'))
    keyboard.add(types.InlineKeyboardButton(text='Пол', callback_data='4'))
    keyboard.add(types.InlineKeyboardButton(text='Курс', callback_data='5'))
    keyboard.add(types.InlineKeyboardButton(text='Ссылки на соцсети', callback_data='6'))
    keyboard.add(types.InlineKeyboardButton(text='Какого соседа хочешь найти', callback_data='7'))
    keyboard.add(types.InlineKeyboardButton(text='Желаемый пол соседа', callback_data='8'))
    keyboard.add(types.InlineKeyboardButton(text='Желаемый курс соседа', callback_data='9'))
    if user_form.apartment_photos == 'None':
        keyboard.add(types.InlineKeyboardButton(text='Цена за квартиру', callback_data='10'))
        keyboard.add(types.InlineKeyboardButton(text='Станции метро', callback_data='11'))
        keyboard.add(types.InlineKeyboardButton(text='Назад', callback_data='12'))
    else:
        keyboard.add(types.InlineKeyboardButton(text='Цена квартиры', callback_data='10'))
        keyboard.add(types.InlineKeyboardButton(text='Станция метро кваритры', callback_data='11'))
        keyboard.add(types.InlineKeyboardButton(text='Адрес квартиры', callback_data='12'))
        keyboard.add(types.InlineKeyboardButton(text='Время до корпусов вышки', callback_data='13'))
        keyboard.add(types.InlineKeyboardButton(text='Описание квартиры', callback_data='14'))
        keyboard.add(types.InlineKeyboardButton(text='Фотографии квартиры', callback_data='15'))
        keyboard.add(types.InlineKeyboardButton(text='Назад', callback_data='16'))
    return keyboard


# -------------------------------- Функции для корректного ввода значений в бд ----------------------------------------#
def insert_current_gender(input_string) -> bool:
    result_value = 'Error'
    if input_string == 'М':
        result_value = True
    if input_string == 'Ж':
        result_value = False
    return bool(result_value)


def insert_current_user_class(input_value) -> int:
    if input_value == 'Выпускник':
        result_value = 7
    else:
        result_value = int(input_value)
    return int(result_value)


def insert_current_neighbor_gender(input_value) -> int:
    result_value = 'Error'
    if input_value == 'Важно, хочу соседа мужчину':
        result_value = 1
    elif input_value == 'Важно, хочу соседа девушку':
        result_value = 2
    elif input_value == 'Неважно':
        result_value = 3
    return int(result_value)


def insert_current_neighbor_class(input_value) -> int:
    result_value = 'Error'
    if input_value == 'Да, 1-2':
        result_value = 1
    elif input_value == 'Да, 3-4':
        result_value = 2
    elif input_value == 'Да, 5-6':
        result_value = 3
    elif input_value == 'Да, 1-4':
        result_value = 4
    elif input_value == 'Да, выпускник':
        result_value = 5
    elif input_value == 'Не важен':
        result_value = 6
    return int(result_value)


def insert_current_user_point(input_value) -> int:
    result_value = 'Error'
    if input_value == 'Соседа в свою квартиру':
        result_value = 1
    elif input_value == 'Квартиру':
        result_value = 2
    return int(result_value)
# -------------------------------------------------------------------------------------------------------------------- #


# Проверяет существует ли анкета у пользователя
@sync_to_async
def check_user(chat_id):
    if get_pk_from_chat_id(chat_id) == 'Error: get_pk_from_chat_id: Пользователя не существует':
        return False
    else:
        return True
