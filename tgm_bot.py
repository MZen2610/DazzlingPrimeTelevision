from telegram import Bot, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, CallbackContext,
                          ConversationHandler, RegexHandler)
from dotenv import load_dotenv
from quiz_questions import make_questions_answers, multi_split, get_random_key
from log_handler import LogsHandler
from redis import StrictRedis

import logging
import os


logger = logging.getLogger(__file__)

CHOOSING = range(4)


def get_answer(update, context):
    user_id = update.message.chat_id
    redis_session = context.bot_data['redis_session']
    question = redis_session.get(user_id)
    answer = multi_split(
        ['.', '('], context.bot_data['questions_answers'].get(question, '')
    )
    return answer


def start(update: Update, context: CallbackContext) -> None:
    custom_keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счёт', 'Выйти']]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard)
    update.message.reply_text(text='Здравствуйте!', reply_markup=reply_markup)
    return CHOOSING


def handle_new_question_request(update: Update, context: CallbackContext) -> None:
    user_id = update.message.chat_id
    key_question = get_random_key(context.bot_data['questions_answers'])

    redis_session = context.bot_data['redis_session']
    redis_session.set(user_id, key_question)

    update.message.reply_text(f'Новый вопрос: \n {key_question}')
    return CHOOSING


def handle_solution_attempt(update: Update, context: CallbackContext) -> None:
    answer = get_answer(update, context)
    text_answer = update.message.text
    if text_answer.upper().strip() == answer.upper().strip():
        reply_text = 'Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»'
    else:
        reply_text = f'Неправильно… Верный ответ "{answer}". Попробуешь ещё раз?'
    update.message.reply_text(text=reply_text)
    return CHOOSING


def handle_surrender_request(update: Update, context: CallbackContext):
    answer = get_answer(update, context)
    reply_text = f'Верный ответ "{answer}"'
    update.message.reply_text(text=reply_text)


def handle_score(update: Update, context: CallbackContext) -> None:
    user = update.message.chat_id
    update.message.reply_text(text='TODO Показать счёт...')


def execute_exit(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        'Счастливо!',
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


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
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [
                MessageHandler(Filters.regex('^Новый вопрос$'), handle_new_question_request),
                MessageHandler(Filters.regex('^Сдаться$'), handle_surrender_request),
                MessageHandler(Filters.regex('^Мой счёт$'), handle_score),
                MessageHandler(Filters.regex('^Выйти$'), execute_exit),
                MessageHandler(Filters.text & ~Filters.command, handle_solution_attempt)],

        },
        fallbacks=[CommandHandler('stop', execute_exit)],
        allow_reentry=True,
    )
    dispatcher.add_handler(conv_handler)
    dispatcher.add_error_handler(error)

    try:
        updater.start_polling()
        updater.idle()
    except Exception as exp:
        logger.error(f'TGM bot error {exp}')


if __name__ == '__main__':
    main()
