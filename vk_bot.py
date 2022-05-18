from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from dotenv import load_dotenv
from log_handler import LogsHandler
from telegram import Bot
from redis import StrictRedis
from random import randint
from quiz_questions import make_questions_answers, multi_split

import os
import vk_api as vk
import logging


logger = logging.getLogger(__file__)


def get_answer(id_user, redis_session, questions_answers):
    question = redis_session.get(id_user)
    answer = multi_split(
        ['.', '('], questions_answers.get(question, '')
    )
    return answer


def handle_new_question_request(event, vk_api, redis_session, questions_answers, keyboard) -> None:
    id_user = event.user_id
    list_keys = list(questions_answers.keys())
    random_item = randint(0, len(list_keys) - 1)
    key_question = list_keys[random_item]

    redis_session.set(id_user, key_question)
    question = redis_session.get(id_user)

    vk_api.messages.send(
        user_id=id_user,
        random_id=get_random_id(),
        keyboard=keyboard.get_keyboard(),
        message=f'Новый вопрос: \n {question}'
    )


def handle_solution_attempt(event, vk_api, redis_session, questions_answers, keyboard) -> None:
    user_id = event.user_id
    answer = get_answer(user_id, redis_session, questions_answers)
    text_answer = event.text
    if text_answer.upper().strip() == answer.upper().strip():
        reply_text = 'Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»'
    else:
        reply_text = f'Неправильно… Верный ответ "{answer}". Попробуешь ещё раз?'
    vk_api.messages.send(
        user_id=user_id,
        random_id=get_random_id(),
        keyboard=keyboard.get_keyboard(),
        message=reply_text
    )


def handle_surrender_request(event, vk_api, redis_session, questions_answers, keyboard):
    user_id = event.user_id
    answer = get_answer(user_id, redis_session, questions_answers)
    reply_text = f'Верный ответ "{answer}"'
    vk_api.messages.send(
        user_id=user_id,
        random_id=get_random_id(),
        keyboard=keyboard.get_keyboard(),
        message=reply_text
    )


def handle_score(event, vk_bot, keyboard):
    user_id = event.user_id
    vk_bot.messages.send(
        user_id=user_id,
        random_id=get_random_id(),
        message='TODO Показать счёт...',
        keyboard=keyboard.get_keyboard()
    )


def done(event, vk_api, keyboard) -> None:
    keyboard.keyboard['buttons'] = []
    vk_api.messages.send(
        user_id=event.user_id,
        random_id=get_random_id(),
        keyboard=keyboard.get_keyboard(),
        message='Счастливо!'
    )


def process_vk_message(event, vk_api, redis_session, questions_answers):
    keyboard = VkKeyboard()
    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('Мой счёт', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Выйти', color=VkKeyboardColor.NEGATIVE)

    if 'Новый вопрос' in event.text:
        handle_new_question_request(
            event, vk_api, redis_session, questions_answers, keyboard)
    elif 'Сдаться' in event.text:
        handle_surrender_request(event, vk_api, redis_session, questions_answers, keyboard)
    elif 'Мой счёт' in event.text:
        handle_score(event, vk_api, keyboard)
    elif 'Выйти' in event.text:
        done(event, vk_api, keyboard)
    else:
        handle_solution_attempt(
            event, vk_api, redis_session, questions_answers, keyboard)


def main():
    load_dotenv()
    vk_token = os.environ['VK_TOKEN']
    tgm_token = os.environ['TGM_TOKEN']
    session_id = os.environ['SESSION_ID']
    quiz_files_folder = os.environ['QUIZ_FILES_FOLDER']
    redis_host = os.environ['REDIS_HOST']
    redis_port = os.environ['REDIS_PORT']
    redis_psw = os.environ['REDIS_PSW']
    redis_session = StrictRedis(
        host=redis_host,
        port=redis_port,
        password=redis_psw,
        decode_responses=True,
        db=0
    )

    questions_answers = make_questions_answers(quiz_files_folder)

    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
    )
    logger.setLevel(logging.WARNING)
    logger.addHandler(LogsHandler(Bot(token=tgm_token), session_id))
    logger.info('VK bot running...')

    try:
        vk_session = vk.VkApi(token=vk_token)
        vk_api = vk_session.get_api()
        longpoll = VkLongPoll(vk_session)
        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                process_vk_message(event, vk_api, redis_session, questions_answers)
    except Exception as exp:
        logger.error(f'VK bot error {exp}')


if __name__ == '__main__':
    main()
