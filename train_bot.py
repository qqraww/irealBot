import os
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Embedding, LSTM, Dense, TimeDistributed
from tensorflow.keras.utils import to_categorical
import numpy as np

MODEL_PATH = 'chatbot_model.h5'

# Расширенный датасет вопросов и ответов
questions = [
    'привет', 'здравствуй', 'добрый день', 'как дела', 'что делаешь',
    'как тебя зовут', 'пока', 'спасибо', 'какой сегодня день', 'чем занимаешься',
    'ты кто', 'что нового', 'как погода', 'ты умеешь шутить', 'расскажи анекдот',
    'что любишь', 'где живёшь', 'ты человек?', 'что делаешь сейчас', 'какие планы',
    'ты можешь помочь?', 'как настроение', 'что ты думаешь о жизни?', 'расскажи о себе'
]

answers = [
    'привет!', 'приветствую!', 'добрый день!', 'всё хорошо, а у тебя?', 'просто думаю',
    'меня зовут бот', 'пока!', 'пожалуйста', 'сегодня отличный день', 'учусь программировать',
    'я бот', 'ничего нового', 'сейчас солнечно', 'иногда шучу', 'лучше не надо',
    'люблю помогать', 'живу в интернете', 'нет, я ИИ', 'сейчас отвечаю тебе', 'планы большие',
    'конечно могу', 'отлично', 'жизнь — это удивительно', 'я простой бот, но стараюсь'
]

# Создаем токенизатор
tokenizer = Tokenizer(filters='!"#$%&()*+,-./:;<=>?@[\\]^_`{|}~\t\n')
tokenizer.fit_on_texts(questions + answers)
vocab_size = len(tokenizer.word_index) + 1

# Преобразуем в последовательности
input_seq = tokenizer.texts_to_sequences(questions)
output_seq = tokenizer.texts_to_sequences(answers)

max_len_in = max(len(seq) for seq in input_seq)
max_len_out = max(len(seq) for seq in output_seq)
max_len = max(max_len_in, max_len_out)

input_padded = pad_sequences(input_seq, maxlen=max_len, padding='post')
output_padded = pad_sequences(output_seq, maxlen=max_len, padding='post')

output_categorical = to_categorical(output_padded, num_classes=vocab_size)

# Если модель уже обучена — загружаем, иначе создаём и тренируем
if os.path.exists(MODEL_PATH):
    model = load_model(MODEL_PATH)
    print("Модель загружена из файла.")
else:
    model = Sequential()
    model.add(Embedding(input_dim=vocab_size, output_dim=128, input_length=max_len))
    model.add(LSTM(128, return_sequences=True))
    model.add(TimeDistributed(Dense(vocab_size, activation='softmax')))

    model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

    print("Начинаем обучение...")
    model.fit(input_padded, output_categorical, epochs=300, verbose=1)
    print("Обучение завершено.")

    model.save(MODEL_PATH)
    print(f"Модель сохранена в {MODEL_PATH}")

# Функция генерации ответа
def respond(text):
    seq = tokenizer.texts_to_sequences([text])
    pad = pad_sequences(seq, maxlen=max_len, padding='post')
    preds = model.predict(pad)[0]
    words = []
    for word_probs in preds:
        idx = np.argmax(word_probs)
        if idx == 0:
            break
        words.append(tokenizer.index_word.get(idx, ''))
    return ' '.join(words) if words else '...'

print("Напиши 'выход' для завершения.")
while True:
    user_input = input("Ты: ")
    if user_input.lower() in ['выход', 'stop', 'quit']:
        print("Выход из программы.")
        break
    answer = respond(user_input)
    print("Бот:", answer)
