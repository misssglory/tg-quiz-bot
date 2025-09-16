from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
import db
from aiogram import types

async def new_quiz(message):
    # получаем id пользователя, отправившего сообщение
    user_id = message.from_user.id
    # сбрасываем значение текущего индекса вопроса квиза в 0
    current_question_index = 0
    await db.update_quiz_index(user_id, current_question_index)

    # запрашиваем новый вопрос для квиза
    await get_question(message, user_id)


async def get_question(message, user_id):

    # Запрашиваем из базы текущий индекс для вопроса
    current_question_index = await db.get_quiz_index(user_id)
    # Получаем индекс правильного ответа для текущего вопроса
    correct_index = db.quiz_data[current_question_index]['correct_option']
    # Получаем список вариантов ответа для текущего вопроса
    opts = db.quiz_data[current_question_index]['options']

    # Функция генерации кнопок для текущего вопроса квиза
    # В качестве аргументов передаем варианты ответов и значение правильного ответа (не индекс!)
    kb = generate_options_keyboard(opts, opts[correct_index])
    # Отправляем в чат сообщение с вопросом, прикрепляем сгенерированные кнопки
    await message.answer(f"{db.quiz_data[current_question_index]['question']}", reply_markup=kb)

def generate_options_keyboard(answer_options, right_answer):
  # Создаем сборщика клавиатур типа Inline
    builder = InlineKeyboardBuilder()

    # В цикле создаем 4 Inline кнопки, а точнее Callback-кнопки
    for option in answer_options:
        builder.add(types.InlineKeyboardButton(
            # Текст на кнопках соответствует вариантам ответов
            text=option,
            # Присваиваем данные для колбэк запроса.
            # Если ответ верный сформируется колбэк-запрос с данными 'right_answer'
            # Если ответ неверный сформируется колбэк-запрос с данными 'wrong_answer'
            callback_data="right_answer" if option == right_answer else "wrong_answer")
        )

    # Выводим по одной кнопке в столбик
    builder.adjust(1)
    return builder.as_markup()


