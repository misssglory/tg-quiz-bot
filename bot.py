import asyncio
import logging
from aiogram import Bot, Dispatcher, types
import os
from aiogram.filters.command import Command
from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram import F
import db
import quiz
import quiz_data

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)

# Замените "YOUR_BOT_TOKEN" на токен, который вы получили от BotFather
API_TOKEN = os.environ.get('YOUR_BOT_TOKEN', '')


# Объект бота
bot = Bot(token=API_TOKEN)
# Диспетчер
dp = Dispatcher()



# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Создаем сборщика клавиатур типа Reply
    builder = ReplyKeyboardBuilder()
    # Добавляем в сборщик одну кнопку
    builder.add(types.KeyboardButton(text="Начать игру"))
    # Прикрепляем кнопки к сообщению
    await message.answer("Добро пожаловать в квиз!", reply_markup=builder.as_markup(resize_keyboard=True))


# Хэндлер на команды /quiz
@dp.message(F.text=="Начать игру")
@dp.message(Command("quiz"))
async def cmd_quiz(message: types.Message):
    # Отправляем новое сообщение без кнопок
    await message.answer(f"Давайте начнем квиз!")
    # Запускаем новый квиз
    await quiz.new_quiz(message)


@dp.callback_query(quiz.ButtonCallback.filter())
async def process_answer(callback: types.CallbackQuery, callback_data: quiz.ButtonCallback):
    await callback.bot.edit_message_reply_markup(
        chat_id=callback.from_user.id,
        message_id=callback.message.message_id,
        reply_markup=None
    )

    # Получение текущего вопроса из словаря состояний пользователя
    current_question_index = await db.get_quiz_index(callback.from_user.id)
    correct_option = quiz_data.quiz_data[current_question_index]['correct_option'] 
    await callback.message.answer(f"Ваш ответ: {callback_data.text}")
    ans = callback_data.action == "right_answer"
    ans_text = "Верно" if ans else "Неверно"
    await callback.message.answer(ans_text)
    if not ans:
        await callback.message.answer(f"Правильный ответ: {quiz_data.quiz_data[current_question_index]['options'][correct_option]}")
    
    # Обновление номера текущего вопроса в базе данных
    current_question_index += 1
    await db.update_quiz_index(callback.from_user.id, current_question_index)


    if current_question_index < len(quiz_data.quiz_data):
        await quiz.get_question(callback.message, callback.from_user.id)
    else:
        await callback.message.answer("Это был последний вопрос. Квиз завершен!")



# Запуск процесса поллинга новых апдейтов
async def main():
    await db.create_table()    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())