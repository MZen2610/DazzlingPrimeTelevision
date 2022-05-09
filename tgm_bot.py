from telegram import Bot, ReplyKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from dotenv import load_dotenv
from quiz_questions import make_questions_answers
from log_handler import LogsHandler
from random import randint

import logging
import os

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


def start(update: Update, context: CallbackContext) -> None:
    custom_keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счёт']]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard)
    update.message.reply_text(text='Здравствуйте!', reply_markup=reply_markup)


def questions(update: Update, context: CallbackContext):
    text = update.message.text
    list_keys = list(context.bot_data['questions_answers'].keys())
    random_item = randint(0, len(list_keys)-1)
    key = list_keys[random_item]
    if text == 'Новый вопрос':
        update.message.reply_text(key)



def error(update: Update, context: CallbackContext) -> None:
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def main():
    load_dotenv()

    tgm_token = os.environ['TGM_TOKEN']
    session_id = os.environ['SESSION_ID']
    quiz_files_folder = os.environ['QUIZ_FILES_FOLDER']

    questions_answers = make_questions_answers(quiz_files_folder).copy()

    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
    )
    logger.setLevel(logging.WARNING)
    logger.addHandler(LogsHandler(Bot(token=tgm_token), session_id))
    logger.info('TG bot running...')

    updater = Updater(tgm_token)
    dispatcher = updater.dispatcher
    dispatcher.bot_data['questions_answers'] = questions_answers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text, questions))
    dispatcher.add_error_handler(error)

    try:
        updater.start_polling()
        updater.idle()
    except Exception as exp:
        logger.error(f'TGM bot error {exp}')


if __name__ == '__main__':
    main()
