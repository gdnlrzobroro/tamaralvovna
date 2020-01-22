import copy
from nltk.corpus import stopwords
import pandas as pd
import pyLDAvis
import pymorphy2
import requests
from dawg_python import Dictionary
from gensim.models import LdaModel
from gensim.corpora.dictionary import Dictionary
import pyLDAvis.gensim




def get_wall(
    owner_id: str='',
    domain: str='',
    offset: int=0,
    count: int=10,
    filter: str='owner',
    extended: int=0,
    fields: str='',
    v: str='5.103'
) -> pd.DataFrame:
    """
    Возвращает список записей со стены пользователя или сообщества.

    @see: https://vk.com/dev/wall.get

    :param owner_id: Идентификатор пользователя или сообщества, со стены которого необходимо получить записи.
    :param domain: Короткий адрес пользователя или сообщества.
    :param offset: Смещение, необходимое для выборки определенного подмножества записей.
    :param count: Количество записей, которое необходимо получить (0 - все записи).
    :param filter: Определяет, какие типы записей на стене необходимо получить.
    :param extended: 1 — в ответе будут возвращены дополнительные поля profiles и groups, содержащие информацию о пользователях и сообществах.
    :param fields: Список дополнительных полей для профилей и сообществ, которые необходимо вернуть.
    :param v: Версия API.
    """
    code = {
        "owner_id": owner_id,
        "domain": domain,
        "offset": offset,
        "count": count,
        "filter": filter,
        "extended": extended,
        "fields": fields,
        "v": v
    }

    response = requests.post(
        url="https://api.vk.com/method/execute",
        data={
            "code": f'return API.wall.get({code});',
            "access_token": "d27a459fb783a36b9d558c8aebcbbb0786b9cf3c4fa6798f2d904e8943a08f8a59015d3df51a18d2acdd1",
            "v": v
        }
    )

    wall = response.json()
    return wall


def prepare_txt(wall, count):

    text = ''
    for i in range(count):
        try:
            text += wall['response']['items'][i]['text']
            text += ' '
        except IndexError:
            break

    #удаляем ссылки
    new_text = copy.copy(text.split())
    for word in new_text:
        if 'http' or '#' or '.ru' or '.com' in word:
            new_text.remove(word)
    text = ' '.join(new_text)


    #удаляем символы
    new_text = ''
    for el in text:
        if el.isalpha() is True or el == ' ':
            new_text += el
        if el == '\n':
            new_text += ' '
    text = new_text

    # Проведем нормализацию
    morph = pymorphy2.MorphAnalyzer()
    new_text = text.split()
    for i in range(len(new_text)):
        new_text[i] = morph.parse(new_text[i])[0].normal_form


    # Удалим стоп слова
    sort_text = copy.copy(new_text)
    for el in new_text:
        if el in (stopwords.words('russian') + stopwords.words('english')):
            sort_text.remove(el)

    return sort_text


def topic_model(clean_txt: list, num_count: int):
    """Визуализация тематической модели"""
    clean_txt = [clean_txt]
    common_dictionary = Dictionary(clean_txt)
    common_corpus = [common_dictionary.doc2bow(text) for text in clean_txt]
    lda = LdaModel(common_corpus, num_topics=num_count)

    vis = pyLDAvis.gensim.prepare(lda, common_corpus, common_dictionary)
    pyLDAvis.save_html(vis, 'LDA.html')
    pyLDAvis.show(data=vis, open_browser=True)


wall_1 = get_wall(domain='countryballs_re', count=500)
wall_2 = get_wall(domain='itmoru', count=500)
txt_1 = prepare_txt(wall_1, 500)
txt_2 = prepare_txt(wall_2, 500)
all_txt = txt_1 + txt_2
topic_model(all_txt, 2)
