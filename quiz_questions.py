import os
import re
import random


def make_questions_answers(folder):
    folder = os.path.join(os.path.dirname(__file__), folder)
    questions_answers = {}
    for filename in os.listdir(folder):
        with open(os.path.join(folder, filename), 'rt', encoding='KOI8-R') as file:
            contents = file.read().split('\n\n')
        questions = []
        answers = []
        for content in contents:
            sentence = (content.replace('\n', '', 1)).replace('\n', ' ')
            if sentence.startswith('Вопрос'):
                questions.append(' '.join(sentence.split(':')[1:]))
            elif sentence.startswith('Ответ'):
                answers.append(' '.join(sentence.split(':')[1:]))

        compilation = dict(zip(questions, answers))
        questions_answers.update(compilation)

    return questions_answers


def multi_split(delimiters, string, maxsplit=0):
    regex_pattern = '|'.join(map(re.escape, delimiters))
    return re.split(regex_pattern, string, maxsplit)[0]


def get_random_key(questions_answers):
    question = random.choice(list(questions_answers.keys()))

    return question
