from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
from dotenv import load_dotenv
# from handle_intent import detect_intent_texts
from log_handler import LogsHandler
from telegram import Bot

import os
import vk_api as vk
import logging

logger = logging.getLogger(__file__)


def process_vk_message(event, vk_bot):
    # response = detect_intent_texts(
    #     project_id=project_id,
    #     session_id=event.user_id,
    #     text=event.text,
    #     language_code='ru-RU'
    # )
    # if not response.query_result.intent.is_fallback:
    vk_bot.messages.send(
        user_id=event.user_id,
        random_id=get_random_id(),
        # message=response.query_result.fulfillment_text
        message=event.text
    )


def main():
    load_dotenv()
    vk_token = os.environ['VK_TOKEN']
    # project_id = os.environ['PROJECT_ID']
    tgm_token = os.environ['TGM_TOKEN']
    session_id = os.environ['SESSION_ID']

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
                process_vk_message(event, vk_api)
    except Exception as exp:
        logger.error(f'VK bot error {exp}')


if __name__ == '__main__':
    main()