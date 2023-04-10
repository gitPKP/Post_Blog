from bs4 import BeautifulSoup
import requests
from random import choice
from copy import copy
from re import split as re_split

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


from django_app.settings import env


url = 'https://lubimyczytac.pl/cytaty?page=1&listId=quoteListFull&tab=All&phrase=&sortBy=new&paginatorType=Standard'


class Quote():
    def __init__(self, text, author):
        self.text = text
        self.author = author


def gain_quote(url='https://lubimyczytac.pl/cytaty?page=1&listId=quoteListFull&tab=All&phrase=&sortBy=new&paginatorType=Standard'):
    cnt = []
    response = requests.get(url)
    content = response.content
    soup = BeautifulSoup(content, 'html.parser')
    for tag in soup.find_all('div', attrs={'class': 'quotes__singleText'}):
        txt = tag.text.split('\n')
        txt = [part for part in txt if part]

        auth = txt[-2][:-9]
        quot = '\n'.join(txt[:-2])

        cnt.append({'quote': quot, 'author': auth, 'url': url})

    return choice(cnt)


def send_mail(email, username, code, url):
    port = int(env('MAIL_PORT'))  # 587 465-ssl
    smtp_server = env('MAIL_SMTP_SERVER')
    mail_sender = env('MAIL_SENDER')
    password = env('MAIL_PASSWORD')
    mail_reciver = email

    print(url)
    content = '<h1>Witaj ' + username + '<h1>\n'
    content += '<h3>Twoje konto oczekuje na potwierdzenie rejestracji pod poniższym adresem:</h3>\n'
    content += '<a href="' + url + '">Potwierdź rejestrację</a>\n'
    content += '<h3>Twój kod potwierdzający ważny przez 15 minut:</h3>\n'
    content += '<h1>' + str(code) + '</h1>\n'
    content += '<h3>Pozdrowienia od ekipy Radke</h3>\n'
    content += '<p>Jest to wiadomość wysłana automatycznie, prosimy na nią nie odpowiadać.</p>\n'
    content += '<p>Jeśli nie przeprowadzałeś rejestracji, prosimy o zignorowanie tej wiadomości.</p>\n'

    msg = MIMEMultipart()
    msg['Subject'] = 'Rejestracja na portalu Radke'
    msg['From'] = mail_sender
    msg['To'] = mail_reciver
    msg.attach(MIMEText(content, 'html'))

    server = smtplib.SMTP(smtp_server, port)
    server.set_debuglevel(1)
    server.ehlo()
    server.starttls()
    server.login(mail_sender, password)
    server.sendmail(mail_sender, mail_reciver, msg.as_string())

    server.quit()


def create_content(Temp_Post):
    content = {
        'title': Temp_Post.title,
        'description': Temp_Post.description,
        'text': Temp_Post.text,
        'image': Temp_Post.img,
        'post_content': [],
        'author': Temp_Post.author,
        'views': Temp_Post.views,
        'date': Temp_Post.date
    }

    if content['text']:
        txt = content['text'].split('\n')
        img = content['image'].split('\n')

        content['text'] = txt
        content['image'] = copy(img)

        """if 'edit' in content.keys():
            if content['edit'][2] == 1:
                if txt[-2] == '--[IMG]--':
                    img.pop(-2)
                    Temp_Posts.objects.filter(author=nick).update(img='\n'.join(img))
                txt.pop(-2)
                Temp_Posts.objects.filter(author=nick).update(text='\n'.join(txt))"""

        content['post_counter'] = []
        for i, t in enumerate(txt):
            if t != '--[IMG]--':
                content['post_content'].append([i, '', t])
            else:
                content['post_content'].append([i, '', t, img.pop(0)])
            # content['post_counter'].append([i, ''])
        content['post_content'][0][1] = 'First'
        content['post_content'][-2][1] = 'Last'
        content['post_content'][-1][1] = 'Pass'

        # content['post_counter'] = {'post_content': content['post_content'], 'counter': content['post_counter']}
        #print('con in  end fun', content)

    return content


def get_comments(id_post, content, Posts, Comment, Comment_to_Comment):
    comments = Comment.objects.filter(post=Posts.objects.get(id=id_post)).order_by('-date')
    comment_to_comments = Comment_to_Comment.objects.filter(post=Posts.objects.get(id=id_post)).order_by('-date')
    content['comments'] = {}
    content['comments']['comment'] = []
    data = [[], [], [], [], []]

    for c in comment_to_comments:
        data[0].append(c.text)
        data[1].append(c.author)
        data[2].append(c.date)
        data[3].append(c.id)  # id własne
        data[4].append(c.comment.id)  # id

    for i, com in enumerate(comments):
        content['comments']['comment'].append({'text': com.text, 'author': com.author, 'date': com.date, 'num': i,
                                    'inside_comment': [], 'com_id': com.id})
        n = 0

        while com.id in data[4]:
            x = data[4].index(com.id)
            content['comments']['comment'][i]['inside_comment'].append({
                'text': data[0].pop(x), 'author': data[1].pop(x), 'date': data[2].pop(x), 'num': n,
                'com_id': data[3].pop(x)})
            data[4].pop(x)
            n += 1

    return content


# New sorting including alfanumerical sort
def my_sort(sort_var, sorting_list, prefix=''):
    '''
    New sorting including alfanumerical sort
    :param sort_var: '-parametr' (transformed from sort_way and sort_by -> see first if)
    :param sorting_list: list of dicts with models and extended parameters
    :param prefix: dict key of model if we sort by it (Optional)
    :return:
    '''
    # Transform '-parametr' into sort_way=ASC/DESC and sort_by=parametr
    if sort_var[0] == '-':
        sort_way = 'DESC'
        sort_by = sort_var[1:]
    else:
        sort_way = 'ASC'
        sort_by = sort_var

    if sort_by and sort_way:
        new_list = []
        sort_words = []
        lengths = []

        # Creating list of alfababetical and numerical parts ['AB', '12', 'ERT', '34', ' tyu ']
        for list_line in sorting_list:
            if prefix:
                sort_word = re_split(r'(\d+)', str(list_line[prefix].__getattribute__(sort_by)))
            else:
                sort_word = re_split(r'(\d+)', str(list_line[sort_by]))
            sort_word = list(filter(''.__ne__, sort_word))
            sort_words.append(sort_word)

            # Extending lengths list to length equal the longest sort_word
            while len(sort_word) > len(lengths):
                lengths.append(0)

            # Update lengths list if any part is longer then earlier longest
            for n, part in enumerate(sort_word):
                if len(part) > lengths[n]:
                    lengths[n] = len(part)

        # Adding paces (' ') to sort_words (to numbers on left, to letters on right)
        for i, sort_word in enumerate(sort_words):
            for n, word in enumerate(sort_word):
                try:
                    int(word)
                    while len(word) < lengths[n]:
                        word = ' ' + word
                    sort_words[i][n] = word
                except:
                    while len(word) < lengths[n]:
                        word = word + ' '
                    sort_words[i][n] = word

            # Creating list of dicts to sort by 'sort' key. 'model' contains model.User object
            new_list.append({'list_line': sorting_list[i], 'sort': ''.join(sort_words[i])})

        # Sort with direction
        if sort_way == 'ASC':
            new_list = sorted(new_list, key=lambda k: k['sort'])
        elif sort_way == 'DESC':
            new_list = sorted(new_list, key=lambda k: k['sort'], reverse=True)

        # Create sorted list to return
        return_list = []
        for element in new_list:
            return_list.append(element['list_line'])

    return return_list
