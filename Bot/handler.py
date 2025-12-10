# bot/handlers.py

from aiogram import Router, F, types
from aiogram.filters import Command

from .quiz_data import quiz_data
from .keyboards import start_kb, options_kb
from .db import (
    init_db,
    set_quiz_state,
    get_quiz_state,
    reset_quiz_state,
    save_quiz_result,
    get_user_result,
    get_top_results,
)

router = Router()


# ---------- вспомогательные функции ----------

async def send_question(message: types.Message, user_id: int):
    question_index, score = await get_quiz_state(user_id)

    if question_index >= len(quiz_data):
        await message.answer("Квиз уже завершён. Используй /quiz, чтобы начать заново.")
        return

    q = quiz_data[question_index]
    kb = options_kb(q["options"])

    await message.answer(q["question"], reply_markup=kb)


async def finish_quiz(message: types.Message, user_id: int):
    question_index, score = await get_quiz_state(user_id)
    total = len(quiz_data)

    username = message.from_user.username or message.from_user.full_name

    await save_quiz_result(user_id, username, score, total)
    await reset_quiz_state(user_id)

    await message.answer(
        f"Квиз завершён! 🎉\n"
        f"Твой результат: {score} из {total}."
    )


# ---------- хендлеры сообщений ----------

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Добро пожаловать в квиз! Нажми 'Начать игру' 👇",
        reply_markup=start_kb(),
    )


@router.message(Command("quiz"))
@router.message(F.text == "Начать игру")
async def cmd_quiz(message: types.Message):
    user_id = message.from_user.id
    await reset_quiz_state(user_id)
    await message.answer("Давайте начнём квиз! 🎮")
    await send_question(message, user_id)


@router.message(Command("stats"))
async def cmd_stats(message: types.Message):
    user_id = message.from_user.id
    last_result = await get_user_result(user_id)
    top = await get_top_results()

    text = []

    if last_result:
        username, score, total, updated_at = last_result
        text.append(
            f"Твой последний результат:\n"
            f"- {score} из {total}\n"
            f"- обновлено: {updated_at}\n"
        )
    else:
        text.append("Ты ещё не проходил(а) квиз.\n")

    if top:
        text.append("Топ игроков:\n")
        for i, (uname, score, total, updated_at) in enumerate(top, start=1):
            text.append(f"{i}. {uname}: {score}/{total}")
    else:
        text.append("Пока нет результатов у других игроков.")

    await message.answer("\n".join(text))


# ---------- хендлер ответов (callback) ----------

@router.callback_query(F.data.startswith("answer:"))
async def process_answer(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    data = callback.data  # "answer:<index>"
    _, index_str = data.split(":", 1)
    chosen_index = int(index_str)

    question_index, score = await get_quiz_state(user_id)

    if question_index >= len(quiz_data):
        await callback.answer("Квиз уже завершён.", show_alert=True)
        return

    q = quiz_data[question_index]
    options = q["options"]
    correct_index = q["correct_option"]

    user_answer_text = options[chosen_index]
    correct_answer_text = options[correct_index]

    # 1) удаляем кнопки и добавляем в текст выбранный ответ
    new_text = f"{callback.message.text}\n\nТвой ответ: {user_answer_text}"
    await callback.message.edit_text(new_text)

    # 2) отвечаем — правильно или нет
    if chosen_index == correct_index:
        score += 1
        await callback.message.answer("✅ Правильно!")
    else:
        await callback.message.answer(
            f"❌ Неправильно.\nПравильный ответ: {correct_answer_text}"
        )

    # 3) обновляем состояние
    question_index += 1
    await set_quiz_state(user_id, question_index, score)

    # 4) если вопросы закончились → завершаем квиз
    if question_index >= len(quiz_data):
        await finish_quiz(callback.message, user_id)
    else:
        # показываем следующий вопрос
        await send_question(callback.message, user_id)

    # 5) убираем "часики" на кнопке
    await callback.answer()
