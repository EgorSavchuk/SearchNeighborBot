from aiogram import types
import django
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "search_neighbor_bot.settings")
django.setup()
import logging


# Класс для передачи в фунцию вывода анкеты в чат
class UserForm:
    def __init__(self, avatar, caption, full_info, apartment_photos):
        self.avatar = avatar
        self.caption = caption
        self.full_info = full_info
        self.apartment_photos = apartment_photos


# Функция, возвращающая объект класса UserForm
def get_form(chat_id, only_profile: bool = False, pk='default'):
    from lib import get_pk_from_chat_id, get_current_age_name, get_price_to_view
    from bot.models import UserGeneralInformation, UserStatus, UserCriteria
    if pk == 'default':
        pk = get_pk_from_chat_id(chat_id)
    logging.warning(f'pk :: {pk}')
    user = UserGeneralInformation.objects.filter(pk=pk).first()
    logging.warning(f'user ::: {user}')
    user_status = UserStatus.objects.filter(status_for_user=user)[0]
    user_criteria = UserCriteria.objects.filter(for_user=user)[0]
    # ----------- переменные, используемые более двух раз ------------ #
    user_intention = get_current_intention(user_status.user_intention)
    user_age = user.user_age
    # ---------------------------------------------------------------- #
    neighbor_emoji = '🧍‍♂‍'
    if user_criteria.neighbor_gender == 2:
        neighbor_emoji = '🧍‍♀'
    # Расматриваем случай, когда у пользователя нет имени пользователя tg
    user_telegram = f'<b>Ссылка tg:</b>\n@{user.user_tg}\n'
    if user.user_tg == 'null':
        user_telegram = ''
    # Чтобы не делать нексколько запросов к БД, в одну функцию объединяем вывод анкеты и полной информации
    # Существуют вызовы, когда нужна только анкета, в этом случае нет нужды заполнять переменную full_info
    if not only_profile:
        full_info = f'<b>Имя:</b>\n{user.name}\n' \
                    f'<b>О себе:</b>\n{user.user_about}\n' \
                    f'<b>Возраст:</b>\n{user_age}\n' \
                    f'<b>Пол:</b>\n{get_current_gender(user.user_gender)}\n' \
                    f'<b>Курс:</b>\n{get_current_class(user.user_class)}\n' \
                    f'<b>Твои ссылки на соцсети:</b>\n{user.user_vk}\n' \
                    f'{user_telegram}' \
                    f'<b>Какого соседа хочешь найти:</b>\n{user.neighbor_about}\n' \
                    f'<b>Желаемый пол соседа:</b>\n{get_current_neighbor_gender(user_criteria.neighbor_gender)}\n' \
                    f'<b>Желаемый курс соседа:</b>\n{get_current_neighbor_class(user_criteria.neighbor_class)}\n' \
                    f'<b>Ищешь:</b>\n{user_intention}\n'
    else:
        full_info = 'None'
    caption = f'<b>{user.name}</b>, {user_age} {get_current_age_name(user_age)}, ' \
              f'{get_current_class(user.user_class)}\n\n' \
              f'<b>Ищу:</b> {user_intention.lower()}\n\n' \
              f'<b>ℹ️ О себе:</b> \n{user.user_about}\n\n' \
              f'<b>{neighbor_emoji} Какого соседа хочу найти:</b>\n{user.neighbor_about}\n'
    if user_intention == 'Соседа в свою квартиру':
        from bot.models import ApartmentOwner
        apartment_owner = ApartmentOwner.objects.filter(apartment_owner=user)[0]
        if not only_profile:
            full_info += f'<b>Станция метро квартиры:\n</b>{apartment_owner.metro}\n' \
                     f'<b>Адрес квартиры:</b>\n{apartment_owner.address}\n' \
                     f'<b>Время до корпусов вышки от квартиры:</b>\n{apartment_owner.time_to_hse}\n' \
                     f'<b>Стоимость проживания в квартире:</b>\n{apartment_owner.price}\n' \
                     f'<b>Про квартиру:</b>\n{apartment_owner.about_apartment}\n'
        caption += f'\n<i>О квартире:</i>\n\n' \
                   f'<b>💲 Цена: </b>{get_price_to_view(apartment_owner.price)} ₽\n' \
                   f'<b>Ⓜ️ Станция метро: </b>{apartment_owner.metro}\n' \
                   f'<b>📍 Адрес: </b>{apartment_owner.address}\n\n' \
                   f'<b>⏱ Время до корпусов вышки:</b>\n{apartment_owner.time_to_hse}\n\n' \
                   f'<b>ℹ️ Описание квартиры:</b>\n{apartment_owner.about_apartment}'
        photos = apartment_owner.apartment_images
        media = types.MediaGroup()
        for photo in photos:
            media.attach_photo(photo)
        user_form = UserForm(avatar=user.avatar, caption=caption, full_info=full_info, apartment_photos=media)
    else:
        if not only_profile:
            full_info += f'<b>Цена, которая устроит за квартиру:</b>\n{user_criteria.required_price}\n' \
                         f'<b>Станции метро, рядом с которыми хочешь найти квартиру</b>\n{user_criteria.required_metro}'
        caption += f'\n<b>💲 Максимальная цена за квартиру: </b>{get_price_to_view(user_criteria.required_price)} ₽\n' \
                   f'\n<b>Ⓜ️ Станции метро, рядом с которыми ищу квартиру</b>\n{user_criteria.required_metro}'
        user_form = UserForm(avatar=user.avatar, caption=caption, full_info=full_info, apartment_photos='None')
    return user_form

# ---------------------------------------------------------------------------------------------------------------------#

# --------------------------------- Функции для корректного вывода значений из БД -------------------------------------#


def get_current_intention(db_intention):
    if db_intention == 1:
        return 'Соседа в свою квартиру'
    if db_intention == 2:
        return 'Квартиру'


def get_current_class(db_class):
    if db_class == 7:
        return 'Выпускник'
    else:
        return f'{db_class} курс'


def get_current_gender(db_gender):
    if db_gender:
        return 'М'
    else:
        return 'Ж'


def get_current_neighbor_gender(db_neighbor_gender):
    if db_neighbor_gender == 1:
        return 'Важен, мужской'
    elif db_neighbor_gender == 2:
        return 'Важен, женский'
    else:
        return 'Неважен'


def get_current_neighbor_class(db_neighbor_class):
    if db_neighbor_class == 6:
        return 'Неважен'
    elif db_neighbor_class == 1:
        return 'Важен, 1-2'
    elif db_neighbor_class == 2:
        return 'Важен, 3-4'
    elif db_neighbor_class == 3:
        return 'Важен, 5-6'
    elif db_neighbor_class == 4:
        return 'Важен, 1-4'
    else:
        return 'Важен, выпускник'

# ---------------------------------------------------------------------------------------------------------------------#
