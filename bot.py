import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
import random


def write_msg(chat_id, message):
    rnd_id = random.randint(0, 2 ** 64)
    vk.method('messages.send', {'chat_id': chat_id,
                                'message': message,
                                'random_id': rnd_id})


def write_message(user_id, message):
    vk.messages.send(user_id=event.obj.message['from_id'],
                     message="Спасибо, что написали нам. Мы обязательно ответим",
                     random_id=random.randint(0, 2 ** 64))


# API-ключ созданный ранее
token = "455abef9e5a275893cf3edf18701cc8f77b92896c0803aafc210fc1a58d2393f96916a58df187fbf21bc1"

# Авторизуемся как сообщество
vk = vk_api.VkApi(token=token)

# Работа с сообщениями
longpoll = VkLongPoll(vk)

# Основной цикл
for event in longpoll.listen():

    # Если пришло новое сообщение
    '''if event.type == VkEventType.MESSAGE_NEW:


        # Если оно имеет метку для меня( то есть бота)
        if event.to_me:

            if event.from_chat:

                txt = event.text

                print(txt + '1')

                write_msg(event.chat_id, txt)


        if event.from_user:

            txt = event.text

            print(txt + '2')

            write_msg(event.user_id, txt)'''

    if event.from_chat:

        txt = str(event.text)

        if txt.startswith('!'):

            cmd = txt[1:].split(' ')

            if cmd[0] in ['kick', 'кик', 'ban', 'бан']:

                id = cmd[1]

                ans = vk.method('messages.removeChatUser', chat_id=event.chat_id,
                          user_id=id)

                if ans == 1:

                    user_from = event.user_id
                    write_msg(chat_id=event.chat_id,
                              message='Пользователь успешно выгнан из беседы!')

                else:
                    write_msg(chat_id=event.chat_id,
                              message=ans)

        user = event.from_user

        write_msg(event.chat_id, txt)

    elif event.from_user:

        txt = event.text

        write_message(event.user_id, 'Спасибо, что написали нам. '
                                     'Ваше сообщение передано администрации.')

