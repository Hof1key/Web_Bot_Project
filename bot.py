import datetime
import json
import sqlite3

import vk_api
from vk_api.keyboard import VkKeyboardColor, VkKeyboard
from vk_api.longpoll import VkLongPoll, VkEventType
import random

db_name = 'data/chat_trecking_bot1.db'
kb1_name = 'data/keyboard.json'
kb2_name = 'data/game.json'

game_n = {}
game_bool = {}

muted_users = {}

bad_words = ['chat_trecking', '@all', '...']


def write_msg(chat_id, message):
    rnd_id = random.randint(0, 2 ** 64)
    vk.method('messages.send', {'chat_id': chat_id,
                                'message': message,
                                'random_id': rnd_id})


def write_message(user_id, message, keyboard=json.dumps({"buttons": [], "one_time": True})):
    vk_api = vk.get_api()

    vk_api.messages.send(user_id=user_id,
                         message=message,
                         keyboard=keyboard,
                         random_id=random.randint(0, 2 ** 64))


def mute_user(chat_id, user_id, hours, reason):

    time = datetime.datetime.today()

    time += datetime.timedelta(hours=hours)

    str_time = time.strftime('%d/%m/%Y %H:%M:%S')



    write_msg(chat_id=chat_id,
              message=f'''Пользователь @id{user_id} замучен на {hours} часов (-а). \n
                      Причина: {reason}. 
                      При попытке обойти наказание вы будете выгнаны из беседы!!!
                      Мут истекает в {str_time}.''')

    muted_users[user_id] = time


def statistics_new_user(database, user_id):
    db = sqlite3.connect(database)
    cur = db.cursor()

    cur.execute(f'''INSERT INTO messages VALUES ({user_id}, 0, 0, 1, 100, 0)''')

    db.commit()
    db.close()


def statistics(database, user_id, row, value):
    db = sqlite3.connect(database)
    cur = db.cursor()

    cur.execute(f"""UPDATE messages
                    SET {row} = {row} + {value}
                    WHERE user_id = {user_id}""")

    db.commit()

    if row == 'messages':
        res = cur.execute(f'''SELECT messages, lvl_up_pt FROM messages
                        WHERE user_id = {user_id}''').fetchone()

        if res[0] > res[1]:
            statistics(database, user_id, 'level', 1)
            statistics(database, user_id, 'lvl_up_pt', int(res[1] * 1.3))

    db.close()


def get_statistics(database, user_id):
    db = sqlite3.connect(database)
    cur = db.cursor()

    res = cur.execute(f'''SELECT * FROM messages
                            WHERE user_id = {user_id}''').fetchone()

    return f'''Уровень пользователя в чате: {res[3]}
               Отправленных сообщений: {res[1]}
               Всего написано символов: {res[2]}
               Заработано очков в мини-игре: {res[5]}'''


# API-ключ созданный ранее
token = "455abef9e5a275893cf3edf18701cc8f77b92896c0803aafc210fc1a58d2393f96916a58df187fbf21bc1"

# Авторизуемся как сообщество
vk = vk_api.VkApi(token=token)

# Работа с сообщениями
longpoll = VkLongPoll(vk)

# Основной цикл
for event in longpoll.listen():

    # Если пришло новое сообщение

    if event.type == VkEventType.MESSAGE_NEW:

        if hasattr(event, 'source_act') and event.source_act == 'chat_invite_user':
            user = event.source_mid

            statistics_new_user(db_name, user)

            continue

        if event.from_chat:

            txt = str(event.text)

            if not event.to_me and not txt[0] == '!':
                continue

            if txt.startswith('!'):

                cmd = txt[1:].split(' ')

                if cmd[0] in ['kick', 'кик', 'ban', 'бан']:

                    id = cmd[1]

                    user_id = event.user_id

                    ans = ''

                    if id[0] == '@':
                        id = id[1:]

                    if id[:2] == 'id':
                        id = id[2:]

                    vk_api = vk.get_api()

                    try:
                        session_api = vk.get_api()

                        members = session_api.messages.getConversationMembers(peer_id=event.object.peer_id)

                        for i in members["items"]:

                            if i["member_id"] == user_id:
                                admin = i.get('is_admin', False)

                            if admin == True:
                                ans = vk_api.messages.removeChatUser(chat_id=event.chat_id,
                                                                     member_id=id)
                            else:
                                ans = 'Вы не являетесь администратором сообщества!'

                    except Exception as ex:
                        ans = f'Возникла ошибка {ex.__class__.__name__}.'

                    if ans == 1:

                        user_from = event.user_id
                        write_msg(chat_id=event.chat_id,
                                  message=f'Пользователь @id{id} успешно выгнан из беседы!')

                    else:
                        write_msg(chat_id=event.chat_id,
                                  message=ans)

                elif cmd[0] in ['stata', 'state', 'statistics', 'стата', 'статистика']:

                    user = event.user_id

                    write_msg(chat_id=event.chat_id, message=f'@id{user}\n' + get_statistics(db_name, user))

                elif cmd[0] in ['unmute', 'размут', 'анмут']:

                    session_api = vk.get_api()

                    members = session_api.messages.getConversationMembers(peer_id=event.object.peer_id)

                    for i in members["items"]:

                        if i["member_id"] == user_id:
                            admin = i.get('is_admin', False)

                        if admin == True:

                            id = cmd[1]

                            user_id = event.user_id

                            ans = ''

                            if id[0] == '@':
                                id = id[1:]

                            if id[:2] == 'id':
                                id = id[2:]

                            del muted_users[id]

                        else:
                            ans = 'Вы не являетесь администратором сообщества!'

            else:

                user = event.user_id

                if user in muted_users.keys():

                    time_now = datetime.datetime.now()

                    if muted_users[user] > time_now:

                        write_msg(chat_id=event.chat_id,
                                  message=f'!kick @id{user}')

                    else:

                        del muted_users[user]

                else:

                    m = txt.split()

                    if any([i in bad_words for i in m]):

                        mute_user(chat_id=event.chat_id, user_id=user,
                                  hours=3, reason='Вы использовали запретные слова в своем сообщении!')

                    else:

                        statistics(db_name, user, 'messages', 1)

                        statistics(db_name, user, 'symbols', len(txt))

            # write_msg(event.chat_id, txt)

        elif event.from_user:

            if not event.to_me:
                continue

            txt = event.text.lower()

            user = event.user_id

            if not user in game_bool.keys():
                game_bool[user] = False

            vk_api = vk.get_api()

            if game_bool[user]:

                if txt == 'четное':

                    if game_n[user] % 2 == 0:
                        write_message(user_id=user,
                                      message=f'Было загадано число {game_n[user]} (четное). Вы выиграли!')

                    else:
                        write_message(user_id=user,
                                      message=f'Было загадано число {game_n[user]} (четное). Вы проиграли.')

                elif txt == 'нечетное':

                    if game_n[user] % 2 == 1:
                        write_message(user_id=user,
                                      message=f'Было загадано число {game_n[user]} (нечетное). Вы выиграли!')

                    else:
                        write_message(user_id=user,
                                      message=f'Было загадано число {game_n[user]} (четное). Вы проиграли.')

                game_bool[user] = False

                write_message(user_id=user,
                              message='Хотите сыграть снова?',
                              keyboard=open(kb1_name, "r",
                                            encoding="UTF-8").read())

            else:

                if txt == "да":

                    # global game_n, game_bool

                    game_n[user] = random.randint(1, 100)
                    game_bool[user] = True

                    write_message(user_id=user,
                                  message='Число загадано. Выберите, ЧЕТНОЕ оно или НЕЧЕТНОЕ?',
                                  keyboard=open(kb2_name, "r",
                                                encoding="UTF-8").read())

                elif txt == 'нет':

                    write_message(
                        user_id=event.user_id,
                        message='Оставили вас без игры.')



                elif txt == 'вернуться назад':

                    write_message(user_id=event.user_id,
                                  message='Вы вышли из игры.',
                                  keyboard=open(kb1_name, "r",
                                                encoding="UTF-8").read()
                                  )

                elif txt in ['привет', 'hi', 'игра', '!игра']:

                    write_message(user_id=event.user_id,
                                  message='Сыграем в Чет/Нечет?',
                                  keyboard=open(kb1_name, "r",
                                                encoding="UTF-8").read())
                else:
                    pass
