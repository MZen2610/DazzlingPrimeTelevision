from telegram import Bot, ReplyKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from dotenv import load_dotenv
from quiz_questions import make_questions_answers, multi_split
from log_handler import LogsHandler
from random import randint
from redis import StrictRedis

import logging
import os

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


def start(update: Update, context: CallbackContext) -> None:
    custom_keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счёт']]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard)
    update.message.reply_text(text='Здравствуйте!', reply_markup=reply_markup)


def new_questions(update: Update, context: CallbackContext):
    id_user = update.message.chat_id
    text = update.message.text
    list_keys = list(context.bot_data['questions_answers'].keys())
    random_item = randint(0, len(list_keys) - 1)
    key_question = list_keys[random_item]

    redis_session = context.bot_data['redis_session']
    redis_session.set(id_user, key_question)
    question = redis_session.get(id_user)

    if text == 'Новый вопрос':
        update.message.reply_text(question)


def answers_on_questions(update: Update, context: CallbackContext):
    id_user = update.message.chat_id
    redis_session = context.bot_data['redis_session']
    question = redis_session.get(id_user)
    answer = multi_split(
        ['.', '('], context.bot_data['questions_answers'].get(question, '')
    )
    text_answer = update.message.text
    if text_answer.upper().strip() == answer.upper().strip():
        reply_text = 'Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»'
    else:
        reply_text = 'Неправильно… Попробуешь ещё раз?'
    update.message.reply_text(text=reply_text)


def error(update: Update, context: CallbackContext) -> None:
    logger.warning('Update "%s" caused error "%s"', update, error)


def main():
    load_dotenv()

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
    logger.info('TG bot running...')

    updater = Updater(tgm_token)
    dispatcher = updater.dispatcher
    dispatcher.bot_data['redis_session'] = redis_session
    dispatcher.bot_data['questions_answers'] = questions_answers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.regex('^Новый вопрос$'), new_questions))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, answers_on_questions))
    dispatcher.add_error_handler(error)

    try:
        updater.start_polling()
        updater.idle()
    except Exception as exp:
        logger.error(f'TGM bot error {exp}')


if __name__ == '__main__':
    main()
