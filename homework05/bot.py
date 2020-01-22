import datetime
import requests
import telebot
from bs4 import BeautifulSoup
from typing import List, Tuple
from telebot import apihelper

NUMBER_DAY = {
    'monday': 1,
    'tuesday': 2,
    'wednesday': 3,
    'thursday': 4,
    'friday': 5,
    'saturday': 6,
    'sunday': 7
}

RUSSIAN_DAY = ['', 'Понедельник', 'Вторник', 'Среда', 'Четверг',
               'Пятница', 'Суббота', 'Воскресенье']

access_token = '937796779:AAG__nXnZAdew5mBeJEcsglmxFO1evzrrYQ'
telebot.apihelper.proxy = {'https': 'https://213.183.51.172:3128'}
bot = telebot.TeleBot(access_token)


def parse_command(message: str) -> Tuple[int, int, str]:
    info = message.text.split()
    try:
        return NUMBER_DAY[info[0][1:]], int(info[1]), info[2]
    except:
        return NUMBER_DAY[info[0][1:]], 0, info[1]


def get_page(group: str, week: int = 0) -> str:
    if week:
        week = str(week % 2 + 1) + '/'  # 1 - нечётная, 2 - чётная
    url = f'http://www.ifmo.ru/ru/schedule/0/{group}/{week}raspisanie_zanyatiy_{group}.htm'
    try:
        with open('cache.html', 'r') as f:
            date = int(f.readline())
            string = f.readline().strip()
    except FileNotFoundError:
        with open('cache.html', 'w') as f:  # создадим файл, если его ещё нет
            string = ""

    now = datetime.date.today().isocalendar()[1]
    if string == url and now != date:
        with open('cache.html', 'r') as f:
            return f.read()
    response = requests.get(url)
    web_page = response.text
    with open('cache.html', 'w') as f:
        f.write(f'{now}\n{url}\n{web_page[50000:]}')
    return web_page[50000:]


def parse_schedule(web_page: str, day: int) -> Tuple[List[str], List[str], List[str], List[str]]:
    soup = BeautifulSoup(web_page, "html5lib")

    # Получаем таблицу с расписанием
    schedule_table = soup.find("table", attrs={"id": f"{day}day"})
    if (schedule_table is None):
        return (['Целый день'], ['занятий у группы нет'],
                ['\nне забудь посетить индивидуальные'], [''])

    # Время проведения занятий
    times_list = schedule_table.find_all("td", attrs={"class": "time"})
    times_list = [time.span.text for time in times_list]

    # Место проведения занятий
    locations_list = schedule_table.find_all("td", attrs={"class": "room"})
    locations_list = [room.span.text for room in locations_list]

    # Аудитория
    rooms_list = schedule_table.find_all("td", attrs={"class": "room"})
    rooms_list = [room.dd.text for room in rooms_list]

    # Название дисциплин и имена преподавателей
    lessons_list = schedule_table.find_all("td", attrs={"class": "lesson"})
    lessons_list = [lesson.text.split('\n\n') for lesson in lessons_list]
    lessons_list = [', '.join([info for info in lesson_info if info]) for lesson_info in lessons_list]

    return times_list, locations_list, rooms_list, lessons_list


@bot.message_handler(commands=['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'])
def get_schedule(message: str) -> None:
    """ Получить расписание на указанный день """

    try:
        day, week, group = parse_command(message)
    except:
        bot.send_message(message.chat.id, '<b>Используйте:</b> /weekday [week=0] [group]\n' +
                         '2 - чётная неделя, 1 - нечётная, 0 - обе', parse_mode='HTML')
        return

    get_timetable(message, day, week, group)


def get_timetable(message: str, day: int, week: int, group: str) -> None:
    if len(group) < 5 or not group[0].isalpha() or not group[1:5].isdigit():
        bot.send_message(message.chat.id, '<b>Используйте:</b> /weekday [week=0] [group]\n' +
                         '2 - чётная неделя, 1 - нечётная, 0 - обе', parse_mode='HTML')
        return

    web_page = get_page(group, week)
    times_lst, locations_lst, rooms_lst, lessons_lst = parse_schedule(web_page, day)
    resp = "<b>{}</b>\n\n".format(RUSSIAN_DAY[day])
    for time, location, room, lesson in zip(times_lst, locations_lst, rooms_lst, lessons_lst):
        resp += '<i>{}:</i>  {}, {} {}\n'.format(time, location, room, lesson)
    bot.send_message(message.chat.id, resp, parse_mode='HTML')


@bot.message_handler(commands=['near'])
def get_near_lesson(message: str) -> None:
    """ Получить ближайшее занятие """

    try:
        _, group = message.text.split()
    except:
        bot.send_message(message.chat.id, '<b>Используйте:</b> /near [group]',
                         parse_mode='HTML')
        return
    if len(group) < 5 or not group[0].isalpha() or not group[1:5].isdigit():
        bot.send_message(message.chat.id, '<b>Используйте:</b> /near [group]',
                         parse_mode='HTML')
        return

    week = (datetime.date.today().isocalendar()[1] - 35) % 2
    if not week:
        week += 2
    now_day = datetime.date.today().isocalendar()[2]
    day = now_day
    now = datetime.datetime.now()
    hour = now.hour
    minute = now.minute
    time_now = hour*60 + minute
    web_page = get_page(group, week)
    flag = 1
    times_lst, locations_lst, rooms_lst, lessons_lst = parse_schedule(web_page, day)
    num = 0
    while flag:
        for time in times_lst:
            if not time[0].isalpha():
                time_class = int(time[0:2])*60 + int(time[3:5])
                if time_class > time_now or now_day < day:
                    flag = 0
                    break
                num += 1
        else:
            day += 1
            if day > 7:
                day = 1
            if day == now_day:
                bot.send_message(message.chat.id, 'У этой группы занятий нет\n' +
                                 'Проверьте правильность ввода номера группы', parse_mode='HTML')
                return
            num = 0
            times_lst, locations_lst, rooms_lst, lessons_lst = parse_schedule(web_page, day)
    resp = "<b>{}</b>\n\n".format(RUSSIAN_DAY[day])
    resp += '<i>{}:</i>  {}, {} {}\n'.format(times_lst[num], locations_lst[num],
                                             rooms_lst[num], lessons_lst[num])
    bot.send_message(message.chat.id, resp, parse_mode='HTML')


@bot.message_handler(commands=['tomorrow'])
def get_tomorrow(message: str) -> None:
    """ Получить расписание на следующий день """

    try:
        _, group = message.text.split()
    except:
        bot.send_message(message.chat.id, '<b>Используйте:</b> /tomorrow [group]',
                         parse_mode='HTML')
        return
    _, group = message.text.split()
    if len(group) < 5 or not group[0].isalpha() or not group[1:5].isdigit():
        bot.send_message(message.chat.id, '<b>Используйте:</b> /tomorrow [group]',
                         parse_mode='HTML')
        return

    week = (datetime.date.today().isocalendar()[1] - 35) % 2
    day = datetime.date.today().isocalendar()[2] + 1
    if day > 7:
        day = 1
        week += 1
    elif not week:
        week += 2
    web_page = get_page(group, week)
    times_lst, locations_lst, rooms_lst, lessons_lst = parse_schedule(web_page, day)
    resp = "<b>{}</b>\n\n".format(RUSSIAN_DAY[day])
    for time, location, room, lesson in zip(times_lst, locations_lst, rooms_lst, lessons_lst):
        resp += '<i>{}:</i>  {}, {} {}\n'.format(time, location, room, lesson)
    bot.send_message(message.chat.id, resp, parse_mode='HTML')


@bot.message_handler(commands=['all'])
def get_all_schedule(message: str) -> None:
    """ Получить расписание на всю неделю для указанной группы """

    info = message.text.split()
    if len(info) == 3:
        week = info[1]
        group = info[2]
    elif len(info) == 2:
        week = 0
        group = info[1]
    else:
        bot.send_message(message.chat.id, '<b>Используйте:</b> /all [week=0] [group]\n' +
                         '2 - чётная неделя, 1 - нечётная, 0 - обе', parse_mode='HTML')
        return
    if len(group) < 5 or not group[0].isalpha() or not group[1:5].isdigit():
        bot.send_message(message.chat.id, '<b>Используйте:</b> /all [week=0] [group]\n' +
                         '2 - чётная неделя, 1 - нечётная, 0 - обе', parse_mode='HTML')
        return

    for i in range(1, 8):
        get_timetable(message, i, int(week), group)


if __name__ == '__main__':
    bot.polling()