import django
import os
from asgiref.sync import sync_to_async
from createbot import dp, bot
from aiogram import types
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "search_neighbor_bot.settings")
django.setup()
from bot.models import UserGeneralInformation, UserCriteria, UserStatus, ApartmentOwner


def get_criteria(chat_id):
    from lib import get_pk_from_chat_id
    pk = get_pk_from_chat_id(chat_id)
    user_criteria = UserCriteria.objects.filter(for_user_id=pk)[0]
    criteria = {
        'search_what': 'None',
        'required_price': 'None',
        'neighbor_gender': 'None',
        'neighbor_class': 'None',
    }
    if user_criteria.required_price is None:
        criteria['search_what'] = 1
    else:
        criteria['search_what'] = 2
        criteria['required_price'] = user_criteria.required_price
    criteria['neighbor_gender'] = user_criteria.neighbor_gender
    criteria['neighbor_class'] = user_criteria.neighbor_class
    return criteria


def check_criteria(chat_id, pk):
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
def get_user_watched(chat_id):
    user = UserGeneralInformation.objects.filter(chat_id=chat_id)[0]
    array = user.watched_profiles
    return array


@sync_to_async
def get_new_profiles(chat_id):
    """
    :param chat_id: пользователь, который запросил анкеты
    :return: pk еще не просмотренной анкеты
    """
    profiles = UserGeneralInformation.objects.all().values_list("pk", flat=True)
    user = UserGeneralInformation.objects.filter(chat_id=chat_id)[0]
    for profile in profiles:
        if profile not in user.watched_profiles and profile != user.pk and check_criteria(chat_id, profile):
            return int(profile)
    return 'NoNew'


@sync_to_async
def add_to_watched(chat_id, pk):
    user = UserGeneralInformation.objects.filter(chat_id=chat_id)[0]
    array = user.watched_profiles
    array.append(pk)
    UserGeneralInformation.objects.filter(chat_id=chat_id).update(watched_profiles=array)


def last_watched(chat_id):
    user = UserGeneralInformation.objects.filter(chat_id=chat_id)[0]
    array = user.watched_profiles
    return array[-1]


@sync_to_async
def last_watched_for_notification(chat_id):
    user = UserGeneralInformation.objects.filter(chat_id=chat_id)[0]
    array = user.watched_profiles[-1]
    return UserGeneralInformation.objects.filter(pk=array)[0].chat_id


async def show_profiles(message):
    from getform import get_form
    from lib import print_form
    array = await get_user_watched(message.chat.id)
    pk = await get_new_profiles(message.chat.id)
    if pk == 'NoNew' and len(array) != 0:
        if len(array) == 0:
            await message.answer("Анкет по твоим критериям еще не создали, можешь поменять их или подождать ")
        else:
            await message.answer("Новых анкет по твоим критериям нет, можем посмотреть старые, "
                                 "удалив историю просмотренных анкет, "
                                 "для этого введи /delete_history")
    else:
        @sync_to_async
        def get_user_form():
            result_user_form = get_form(message.chat.id, True, pk=pk)
            return result_user_form

        form = await get_user_form()
        await print_form(form, message, bot, for_searching=True)
        await add_to_watched(message.chat.id, pk)


@dp.callback_query_handler(text="like")
async def do_if_like(call: types.CallbackQuery):
    await write_like(call.message.chat.id)
    last = await last_watched_for_notification(call.message.chat.id)
    if await search_match_v2(call.message.chat.id, last):
        await send_notification(call.message.chat.id, last)
    await show_profiles(call.message)


@dp.callback_query_handler(text="dislike")
async def do_if_like(call: types.CallbackQuery):
    await show_profiles(call.message)


@sync_to_async
def write_like(chat_id):
    user = UserGeneralInformation.objects.filter(chat_id=chat_id)[0]
    liked_user = UserGeneralInformation.objects.filter(pk=last_watched(chat_id))[0]
    user.liked_user.add(liked_user)


@sync_to_async
def delete_history(chat_id):
    UserGeneralInformation.objects.filter(chat_id=chat_id).update(watched_profiles=[])


class UsersMatch:
    def __init__(self, user1, user2):
        self.user1 = user1
        self.user2 = user2


async def send_notification(chat1, chat2):
    from lib import match_message
    try:
        await bot.send_message(chat1, match_message)
        await send_match_form(chat1, chat2)
    except:
        await print_error(chat1)
    try:
        await bot.send_message(chat2, match_message)
        await send_match_form(chat2, chat1)
    except:
        await print_error(chat2)


@sync_to_async
def print_error(chat):
    print(f"Пользователь {chat} отписался")


@sync_to_async
def get_match_form(chat_id):
    from getform import get_form
    result_user_form = get_form(chat_id, True)
    return result_user_form


@sync_to_async
def get_pk(chat):
    from lib import get_pk_from_chat_id
    return get_pk_from_chat_id(chat)


async def send_match_form(user, match):  # user - кому match - chat_id кто
    from lib import print_form
    form = await get_match_form(match)
    await print_form(form, None, bot, for_searching=False, for_notification=user)
    contacts = await get_contacts(await get_pk(match))
    await bot.send_message(user, contacts)


@sync_to_async
def search_match_v2(chat_id, last):
    user = UserGeneralInformation.objects.filter(chat_id=chat_id)[0]
    user2 = UserGeneralInformation.objects.filter(chat_id=last)[0]
    for user_like in user.liked_user.all():
        if user_like == user2 and user in user2.liked_user.all() \
                and user.pk not in user2.matches and user2.pk not in user.matches:
            user.matches.append(user2.pk)
            user2.matches.append(user.pk)
            user.save()
            user2.save()
            return True
    return False


@sync_to_async
def get_matches(chat_id):
    matches = UserGeneralInformation.objects.filter(chat_id=chat_id)[0].matches
    return matches


async def get_count_matches(chat_id):
    return len(await get_matches(chat_id))


@sync_to_async
def get_contacts(match):
    vk = UserGeneralInformation.objects.filter(pk=match)[0].user_vk
    tg = UserGeneralInformation.objects.filter(pk=match)[0].user_tg
    if tg is None:
        return f'<b>Ссылки на соцсети:</b>\n' \
               f'{vk}'
    else:
        return f'<b>Ссылки на соцсети:</b>\n' \
               f'{vk}\n' \
               f'<b>Ссылка telegram:</b>\n' \
               f'@{tg}'
