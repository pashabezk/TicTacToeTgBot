import os
import random
import sys

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters

import strings as st


# поиск токена для телеграмма
def getToken():
    token = ''
    if os.path.isfile(st.BOT_TOKEN_FILENAME):
        f = open(st.BOT_TOKEN_FILENAME, "r")
        token = f.read()
        f.close()
    else:
        print("Пожалуйста, создайте в папке проекта файл 'token.txt' и поместите туда токен для работы телеграм бота  и запустите скрипт заново")
        sys.exit()  # завершить работу скрипта
    return token


# проверка на выигрыш
# проверяет нет ли победной комбинации в строчках, столбцах или по диагонали
# arr - массив
# who - кого надо проверить: нужно передать значение 'х' или '0'
def isWin(arr, who):
    if (((arr[0] == who) and (arr[4] == who) and (arr[8] == who)) or
            ((arr[2] == who) and (arr[4] == who) and (arr[6] == who)) or
            ((arr[0] == who) and (arr[1] == who) and (arr[2] == who)) or
            ((arr[3] == who) and (arr[4] == who) and (arr[5] == who)) or
            ((arr[6] == who) and (arr[7] == who) and (arr[8] == who)) or
            ((arr[0] == who) and (arr[3] == who) and (arr[6] == who)) or
            ((arr[1] == who) and (arr[4] == who) and (arr[7] == who)) or
            ((arr[2] == who) and (arr[5] == who) and (arr[8] == who))):
        return True
    return False


# возвращает количество неопределенных ячеек (т.е. количество ячеек, в которые можно сходить)
# cellArray - массив данных из callBackData, полученных после нажатия на callBack-кнопку
def countUndefinedCells(cellArray):
    counter = 0
    for i in cellArray:
        if i == st.SYMBOL_UNDEF:
            counter += 1
    return counter


# callBackData формат:
# n????????? - общее описание
# n - номер кнопки
# ? - один из вариантов значения клетки: смотри модуль strings, раздел "символы, которые используются"
# пример: 5❌❌⭕⭕❌❌◻◻❌
# означает, что была нажата пятая кнопка, и текущий вид поля:
# ❌❌⭕
# ⭕❌❌
# ◻◻❌
# данные обо всем состоянии поля необходимо помещать в кнопку, т.к. бот имеет доступ к информации только из текущего сообщения

# игра: проверка возможности хода крестиком, проверка победы крестика, ход бота (ноликом), проверка победы ботом
# возвращает:
# message - сообщение, которое надо отправить
# callBackData - данные для формирования callBack данных обновленного игрового поля
def game(callBackData):
    # -------------------------------------------------- global message  # использование глобальной переменной message
    message = st.ANSW_YOUR_TURN  # сообщение, которое вернется
    alert = None

    buttonNumber = int(callBackData[0])  # считывание нажатой кнопки, преобразуя ее из строки в число
    if not buttonNumber == 9:  # цифра 9 передается в первый раз в качестве заглушки. Т.е. если передана цифра 9, то клавиатура для сообщения создается впервые
        charList = list(callBackData)  # строчка callBackData разбивается на посимвольный список "123" -> ['1', '2', '3']
        charList.pop(0)  # удаление из списка первого элемента: который отвечает за выбор кнопки
        if charList[buttonNumber] == st.SYMBOL_UNDEF:  # проверка: если в нажатой кнопке не выбран крестик/нолик, то можно туда сходить крестику
            charList[buttonNumber] = st.SYMBOL_X  # эмуляция хода крестика
            if isWin(charList, st.SYMBOL_X):  # проверка: выиграл ли крестик после своего хода
                message = st.ANSW_YOU_WIN
            else:  # если крестик не выиграл, то может сходит бот, т.е. нолик
                if countUndefinedCells(charList) != 0:  # проверка: есть ли свободные ячейки для хода
                    # если есть, то ходит бот (нолик)
                    isCycleContinue = True
                    # запуск бесконечного цикла т.к. необходимо, чтобы бот походил в свободную клетку, а клетка выбирается случайным образом
                    while (isCycleContinue):
                        rand = random.randint(0, 8)  # генерация случайного числа - клетки, в которую сходит бот
                        if charList[rand] == st.SYMBOL_UNDEF:  # если клетка неопределенна, то ходит бот
                            charList[rand] = st.SYMBOL_O
                            isCycleContinue = False  # смена значения переменной для остановки цикла
                            if isWin(charList, st.SYMBOL_O):  # проверка: выиграл ли бот после своего кода
                                message = st.ANSW_BOT_WIN

        # если клетка, в которую хотел походить пользователь уже занята:
        else:
            alert = st.ALERT_CANNOT_MOVE_TO_THIS_CELL

        # проверка: остались ли свободные ячейки для хода и что изначальное сообщение не поменялось (означает, что победителя нет, и что это был не ошибочный ход)
        if countUndefinedCells(charList) == 0 and message == st.ANSW_YOUR_TURN:
            message = st.ANSW_DRAW

        # формирование новой строчки callBackData на основе сделанного хода
        callBackData = ''
        for c in charList:
            callBackData += c

    # проверка, что игра закончилась (message равно одному из трех вариантов: победил Х, 0 или ничья):
    if message == st.ANSW_YOU_WIN or message == st.ANSW_BOT_WIN or message == st.ANSW_DRAW:
        message += '\n'
        for i in range(0, 3):
            message += '\n | '
            for j in range(0, 3):
                message += callBackData[j + i * 3] + ' | '
        callBackData = None  # обнуление callBackData

    return message, callBackData, alert


# Формат объекта клавиатуры
# в этом примере описана клавиатура из трех строчек кнопок
# в первой строчке две кнопки
# во 2-ой и 3-ей строчке по одной
# keyboard = [
#     # строчка из кнопок:
#     [
#         # собственно кнопки
#         InlineKeyboardButton("Кнопка 1", callback_data='1'),
#         InlineKeyboardButton("Кнопка 2", callback_data='2'),
#     ],
#     [InlineKeyboardButton("Кнопка 3", callback_data='3')],
#     [InlineKeyboardButton("Кнопка 4", callback_data='4')],
# ]
# для формирования объекта клавиатуры, необходимо выполнить следующую команду:
# InlineKeyboardMarkup(keyboard)

# возвращает клавиатуру для бота
# на вход получает callBackData - данные с callBack-кнопки
def getKeyboard(callBackData):
    keyboard = [[], [], []]  # заготовка объекта клавиатуры, которая вернется

    if callBackData != None:  # если
        # формирование объекта клавиатуры
        for i in range(0, 3):
            for j in range(0, 3):
                keyboard[i].append(InlineKeyboardButton(callBackData[j + i * 3], callback_data=str(j + i * 3) + callBackData))

    return keyboard


def newGame(update, _):
    # сформировать callBack данные для первой игры, то есть строку, состояющую из 9 неопределенных символов
    data = ''
    for i in range(0, 9):
        data += st.SYMBOL_UNDEF

    # отправить сообщение для начала игры
    update.message.reply_text(st.ANSW_YOUR_TURN, reply_markup=InlineKeyboardMarkup(getKeyboard(data)))


def button(update, _):
    query = update.callback_query
    callbackData = query.data  # получение callbackData, скрытых в кнопке

    message, callbackData, alert = game(callbackData)  # игра
    if alert is None:  # если не получен сигнал тревоги (alert==None), то редактируем сообщение и меняем клавиатуру
        query.answer()  # обязательно нужно что-то отправить в ответ, иначе могут возникнуть проблемы с ботом
        query.edit_message_text(text=message, reply_markup=InlineKeyboardMarkup(getKeyboard(callbackData)))
    else:  # если получен сигнал тревоги (alert!=None), то отобразить сообщение о тревоге
        query.answer(text=alert, show_alert=True)


def help_command(update, _):
    update.message.reply_text(st.ANSW_HELP)


if __name__ == '__main__':
    updater = Updater(getToken())  # получения токена из файла 'token.txt' и инициализация updater

    # добавление обработчиков
    updater.dispatcher.add_handler(CommandHandler('start', newGame))
    updater.dispatcher.add_handler(CommandHandler('new_game', newGame))
    updater.dispatcher.add_handler(CommandHandler('help', help_command))
    updater.dispatcher.add_handler(MessageHandler(Filters.text, help_command))  # обработчик на любое текстовое сообщение
    updater.dispatcher.add_handler(CallbackQueryHandler(button))  # добавление обработчика на CallBack кнопки

    # Запуск бота
    updater.start_polling()
    updater.idle()
