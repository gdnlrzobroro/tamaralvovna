import telebot
from telebot import apihelper

# Создание бота с указанным токеном доступа
access_token = "937796779:AAG__nXnZAdew5mBeJEcsglmxFO1evzrrYQ"
bot = telebot.TeleBot(access_token)
apihelper.proxy = {'https': 'https://213.183.51.172:3128'}

# Бот будет отвечать только на текстовые сообщения
@bot.message_handler(content_types=['text'])
def echo(message: str) -> None:
    bot.send_message(message.chat.id, message.text)


if __name__ == '__main__':
    bot.polling()