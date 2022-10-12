from bs4 import BeautifulSoup
import requests
from random import choice
from copy import copy

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

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
    port = 587  # 587 465-ssl
    smtp_server = 'smtp.gmail.com'
    mail_sender = 'pomocnicze.konto.pocztowe@gmail.com'
    password = 'hhjbzpgkbiqxincf'
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