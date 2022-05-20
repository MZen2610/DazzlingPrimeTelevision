from random import randint

import os
import re


def make_questions_answers(folder):
    folder = os.path.join(os.path.dirname(__file__), folder)
    questions_answers = {}
    for filename in os.listdir(folder):
        with open(os.path.join(folder, filename), 'rt', encoding='KOI8-R') as file:
            contents = file.read().split('\n\n')
        questions = []
        answers = []
        for content in contents:
            if content.startswith('Вопрос'):
                questions.append(''.join(content.split('\n')[1:]))
            elif content.startswith('Ответ'):
                answers.append(''.join(content.split('\n')[1:]))

        compilation = dict(zip(questions, answers))
        questions_answers.update(compilation)
    return questions_answers

def multi_split(delimiters, string, maxsplit=0):
    regex_pattern = '|'.join(map(re.escape, delimiters))
    return re.split(regex_pattern, string, maxsplit)[0]

def get_random_key(keys):
    keys = list(keys.keys())
    random_item = randint(0, len(keys) - 1)
    key = keys[random_item]

    return key




