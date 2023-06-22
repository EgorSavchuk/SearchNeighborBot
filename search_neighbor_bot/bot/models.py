from django.db import models
from django.contrib.postgres.fields import ArrayField


class UserGeneralInformation(models.Model):  # Таблица с общей информацией о пользователе
    name = models.CharField("Имя пользователя", max_length=100)
    user_vk = models.URLField("Ссылки на соцсети")
    user_tg = models.CharField("Ссылка на tg", max_length=100, blank=True, null=True)
    chat_id = models.CharField("id чата с пользователем", max_length=200)
    avatar = models.CharField("file_id аватарки", max_length=500)
    user_about = models.CharField("О себе", max_length=1000)
    user_age = models.IntegerField("Возраст пользователя")
    user_gender = models.BooleanField("Пол пользователя - Мужской")
    user_class = models.IntegerField("Курс пользователя")
    neighbor_about = models.CharField("О соседе", max_length=1000)
    watched_profiles = ArrayField(models.IntegerField(), blank=True, null=True, default=list)
    # Просмотренные анкеты (pk)
    matches = ArrayField(models.IntegerField(), blank=True, null=True, default=list)
    # Мэтчи пользователя
    liked_user = models.ManyToManyField("self", blank=True, symmetrical=False)  # Пользователь, чья анкета понравилась
    watched_matches = ArrayField(models.IntegerField(), blank=True, null=True, default=list)

    def __str__(self):
        return f' Пользователь {self.name}'

    class Meta:
        verbose_name = "Основная информация о пользователе"
        verbose_name_plural = "Основная информация о пользователях"


class ApartmentOwner(models.Model):  # Таблица с данными о квартире
    apartment_owner = models.ForeignKey(UserGeneralInformation, on_delete=models.CASCADE)  # кв. какого пользователя?
    metro = models.CharField("Станция метро квартиры", max_length=100, blank=True)
    address = models.CharField("Точный адрес квартиры", max_length=100, blank=True)
    time_to_hse = models.CharField("Время до корпусов вышки от квартиры", max_length=300, blank=True)
    price = models.IntegerField("Цена квартиры", blank=True)
    about_apartment = models.TextField("О квартире", blank=True)
    apartment_images = ArrayField(models.CharField(max_length=1000))

    def __str__(self):
        return f' Информация о квартире пользователя {self.apartment_owner}'

    class Meta:
        verbose_name = "Информация о квартире"
        verbose_name_plural = "Информация о квартире"


class UserStatus(models.Model):  # Статус пользователя
    status_for_user = models.ForeignKey(UserGeneralInformation, on_delete=models.CASCADE)  # Для какого пользователя
    form_active = models.BooleanField("Активна ли анкета")
    user_intention = models.IntegerField("Соседа в квартиру(1) / Квартиру(2)")

    def __str__(self):
        return f' Статус пользователя {self.status_for_user}'

    class Meta:
        verbose_name = "Статус пользователя"
        verbose_name_plural = "Статус пользователя"


class UserCriteria(models.Model):  # Критерии для поиска определенного пользователя
    for_user = models.ForeignKey(UserGeneralInformation, on_delete=models.CASCADE)  # Для какого пользователя
    required_price = models.IntegerField("Какая цена квартиры устроит", blank=True, null=True)
    required_metro = models.CharField("Для совместного поиска: Рядом с какими метро хочет квартиру",
                                      blank=True, null=True, max_length=500)
    neighbor_gender = models.IntegerField("Важен ли пол соседа?")  # 1 - Важен, мужской  2 - Важен, женский  3 - Неважен
    neighbor_class = models.IntegerField("Важен ли курс соседа?")
    # 1 - Важен, 1-2
    # 2 - Важен, 3-4
    # 3 - Важен, 5-6
    # 4 - Важен, 1-4
    # 5 - Важен, выпускник
    # 6 - Неважен

    def __str__(self):
        return f' Критерии пользователя {self.for_user}'

    class Meta:
        verbose_name = "Критерии пользователя"
        verbose_name_plural = "Критерии пользователя"
