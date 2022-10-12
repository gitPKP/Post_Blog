from django.shortcuts import render, redirect
from django.contrib.auth.models import User, auth
from django.contrib import messages
from django.db.models import Q, Count
from django.http import HttpResponse

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from random import randint
from datetime import datetime, timedelta
from pytz import timezone

from .models import *
from .functions import gain_quote, send_mail, create_content, get_comments

# SZYFROWNIE PODWOJNE HASEŁ BO W UTC WIDAĆ HASŁA

# Create your views here.
@csrf_exempt
def test(request):
    x = Post.objects.prefetch_related('Likes', 'Comments').all()

    print(x)


    from django.db.models import Count
    #user = User.objects.get(id=1)

    #x = Likes.objects.filter(author=user, value=1).values('post').annotate(counter=Count('post'))
    #return dict
    #print(x.post.author.username)


    #a = {'title':'a2', 'description':'b2', 'author':user}
    #post = Post.objects.create(title='bnm', **a)

    #new_post = PostUnfinished.objects.create(**post.__dict__)



    #posts = PostUnfinished.objects.all()
    #posts.delete()

    #posts = PostUnfinished.objects.filter(description='qwe').update(description='qwerty')

    #person = UserToConfirm.objects.get(login='op')

    #user = UserToConfirm.objects.get(id=7)
    #user.delete()

    #user = User.objects.create_user(username=request.POST['username'],
    #                                email=request.POST['email'],
    #                                password=request.POST['password'])
    #user.save();
    return JsonResponse({"message": "ok"}, safe=False)


#def base(request):
#    return JsonResponse({"messages": "Base page"}, safe=False)


def login(request):
    posts_menu = Post.objects.order_by('-created').all()
    # Button service
    if request.method == 'POST':
        if 'login_button' in request.POST.keys():
            username = request.POST['username']
            password = request.POST['password']

            # User authentication
            user = auth.authenticate(username=username, password=password)
            if user is not None:
                auth.login(request, user)
                #Author.objects.filter(author=username).update(seen=datetime.datetime.now())
                return redirect('/')
            else:
                messages.info(request, 'Błędne dane logowania.')
                return render(request, 'login_page.html')

        elif 'register_button' in request.POST.keys():
            username = request.POST['username']
            email = request.POST['email']
            password = request.POST['password']
            confirm_password = request.POST['confirm_password']

            # Checking correct values
            erro = []
            if User.objects.filter(username=username).exists():
                erro.append('Użytkownik o tym nicku już istnieje.')
                username = ''
            if User.objects.filter(email=email).exists():
                erro.append('Na podany adres email jest już zarejestrowany użytkownik.')
                email = ''
            if password != confirm_password:
                erro.append("Hasła nie są identyczne.")

            # Sending information about errors to page
            if erro:
                messages.info(request, erro)
                return render(request, 'login_page.html', {'content': {'posts_menu': posts_menu,
                                                                       'email': email,
                                                                       'username': username}})
            # Registration with sending code
            else:
                if UserToConfirm.objects.filter(email=email).exists():
                    messages.info(request, 'Twoje konto oczekuje na potwierdzenie. Sprawdź email.')
                    return render(request, 'login_page.html')
                elif UserToConfirm.objects.filter(login=username).exists():
                    messages.info(request, 'Konto o danym nicku oczekuje na potwierdzenie. Sprawdź email.')
                    return render(request, 'login_page.html', {'content': {'posts_menu': posts_menu, 'email': email}})
                else:
                    code = randint(1000, 9999)

                    UserToConfirm.objects.create(login=username,
                                                 email=email,
                                                 password=password,
                                                 code=code,
                                                 valid_time=(datetime.now() + timedelta(minutes=15)))
                    url = 'confirm/'+username
                    send_mail(email, username, code, 'http://' + request.META['HTTP_HOST'] + '/confirm/' + login)
                    return redirect(url)

    messages.info(request, '')
    return render(request, 'login_page.html', {'content': {'posts_menu': posts_menu, 'email': ''}})


def confirm(request, login):
    posts_menu = Post.objects.order_by('-created').all()
    if request.method == 'POST':
        if UserToConfirm.objects.filter(login=login).exists():
            person = UserToConfirm.objects.get(login=login)
            if 'confirm_button' in request.POST.keys():
                print(person.valid_time, ' xxx ', timezone("Europe/Warsaw").localize(datetime.now()))
                if person.valid_time > timezone("Europe/Warsaw").localize(datetime.now()):
                    if int(request.POST['code']) == person.code:
                        user = User.objects.create_user(username=person.login,
                                                        email=person.email,
                                                        password=person.password)
                        user.save();
                        UserToConfirm.objects.filter(login=login).delete()
                        #Author.objects.create(author=person.username)
                        messages.info(request, 'Potwierdzono rejestrację konta.')
                        return redirect('login')

                else:
                    messages.info(request, 'Czas na potwierdzenie rejestracji minął. '
                                           'Wyślij kod ponownie lub dokonaj rejestracji od początku')
                    return redirect('/confirm/' + login)

            elif 'resend_button' in request.POST.keys():
                code = randint(1000, 9999)
                UserToConfirm.objects.filter(login=login).update(
                    valid_time=timezone("Europe/Warsaw").localize((datetime.now() + timedelta(minutes=15))), code=code)
                send_mail(person.email, login, code, 'http://' + request.META['HTTP_HOST'] + '/confirm/' + login)
                messages.info(request, 'Wysłano nowy kod aktywacyjny')
                return redirect('/confirm/' + login)
        else:
            messages.info(request, 'Twoja prośba o rejestrację została usunięta z powodu zbyt długiej zwłoki z '
                                   'potwierdzeniem. Proszę wrócić do formularza rejestracyjnego')
            return redirect('/confirm/' + login)

    return render(request, 'confirm_page.html', {'content': {'posts_menu': posts_menu, 'login': login}})


def logout(request):
    auth.logout(request)
    return redirect('/')


def start(request):
    user = auth.get_user(request)
    posts_menu = Post.objects.order_by('-created').all()

    if user.username:
        new_messages = len(Messages.objects.filter(reciver=user, seen=False))
    else:
        new_messages = False

    last_3 = posts_menu[:3]
    quote = gain_quote()
    best_3_likes = Likes.objects.filter(value='+1').values('post').annotate(plus_likes=Count('post')).order_by(
        '-plus_likes').all()[:3]
    best_3 = []
    for post in best_3_likes:
        best_3.append({'post': Post.objects.filter(id=post['post']).first(), 'plus_likes': post['plus_likes']})

    content = {'user': user, 'posts_menu': posts_menu, 'new_messages': new_messages, 'last_3': last_3, 'best_3': best_3, 'quote': quote}
    return render(request, 'start_page.html', {'content': content})


def create_post(request):
    user = auth.get_user(request)
    if user.username:
        unfinished_posts = PostUnfinished.objects.filter(author=user).all()
        if len(unfinished_posts) <= 5:
            new_post = PostUnfinished.objects.create(author=user)
            return redirect('edit_post/unfinished/' + str(new_post.id))
        else:
            messages.info(request, 'Osiągnołeś maksymalną liczbę roboczych postów.')
            return redirect('author/' + str(user.id))
    else:
        messages.info(request, 'Ta opcja wymaga zalogowanego użytkownika')
        return redirect('/')


def edit_post(request, post_type, post_id):
    user = auth.get_user(request)
    post_id = int(post_id)
    posts_menu = Post.objects.order_by('-created').all()

    if user.username:
        new_messages = len(Messages.objects.filter(reciver=user, seen=False))
    else:
        new_messages = False

# MOVE POST AND PARAGRAPHS FROM FINISHED TO UNFINISHED TABLE
    if post_type == 'finished':
        if Post.objects.filter(id=post_id).exists():
            post = Post.objects.get(id=post_id)
            if Paragraph.objects.filter(post=post).exists():
                paragraphs = Paragraph.objects.filter(post=post_id)
            else:
                paragraphs = []

            new_post = PostUnfinished.objects.create(title=post.title, description=post.description, author=post.author,
                                                     created=post.created, id=post.id)

            for paragraph in paragraphs:
                new_paragraph = ParagraphUnfinished.objects.create(post=new_post,
                                                                   paragraph_number=paragraph.paragraph_number,
                                                                   paragraph_type=paragraph.paragraph_type,
                                                                   paragraph_style_txt=paragraph.paragraph_style_txt,
                                                                   paragraph_style_img=paragraph.paragraph_style_img,
                                                                   url=paragraph.url,
                                                                   paragraph_content=paragraph.paragraph_content)

            Comments.objects.filter(post=post).update(post=new_post)
            Likes.objects.filter(post=post).update(post=new_post)

            post.delete()
            #return JsonResponse({"message": "ok"}, safe=False)
            return redirect('/edit_post/unfinished/' + str(new_post.id))

    elif post_type != 'unfinished':
        return redirect('/')

    if PostUnfinished.objects.filter(id=post_id).exists():
        post = PostUnfinished.objects.get(id=post_id)
        if ParagraphUnfinished.objects.filter(post=post).exists():
            paragraphs = ParagraphUnfinished.objects.filter(post=post).order_by('paragraph_number')
        else:
            paragraphs = []

# FONTS, SIZES AND POSITION TABLE
        fonts = [{'font_name': 'FONT1', 'font_code': 'FONT1'},
                 {'font_name': 'FONT2', 'font_code': 'FONT2'}]
        sizes = [{'size_name': '8', 'size_code': 'font-size: 8px'},
                 {'size_name': '10', 'size_code': 'font-size: 10px'},
                 {'size_name': '12', 'size_code': 'font-size: 12px'},
                 {'size_name': '14', 'size_code': 'font-size: 14px'},
                 {'size_name': '16', 'size_code': 'font-size: 16px'},
                 {'size_name': '18', 'size_code': 'font-size: 18px'},
                 {'size_name': '20', 'size_code': 'font-size: 20px'},
                 {'size_name': '22', 'size_code': 'font-size: 22px'}]
        img_positions = [{'position_name': 'Lewo', 'position_code': 'margin:0 auto 0 0;display:block'},
                         {'position_name': 'Środek', 'position_code': 'margin:0 auto;display:block'},
                         {'position_name': 'Prawo', 'position_code': 'margin:0 0 0 auto;display:block'}]

# SWITCH BUTTONS
        if request.method == 'POST':
            if 'reject_changes_in_paragraph' not in request.POST.keys():
                print('Keys: ', request.POST.keys())
                if 'TXT_type_paragraph_button' in request.POST.keys() and request.POST['TXT_type_paragraph_button']:
                    to_edit = request.POST['paragraph_number']
                    paragraphs[int(to_edit)-1].update(temp_paragraph_type='TXT')

                    style = paragraphs[int(to_edit) - 1].temp_paragraph_style_txt
                    style = style.split('; ')
                    style[5] = style[5][-7:]
                elif 'IMG_type_paragraph_button' in request.POST.keys() and request.POST['IMG_type_paragraph_button']:
                    to_edit = request.POST['paragraph_number']
                    paragraphs[int(to_edit)-1].update(temp_paragraph_type='IMG')

                    style = paragraphs[int(to_edit) - 1].temp_paragraph_style_img
                    style = style.split('; ')
                    style[0] = style[0][8:-2]
                    style[1] = style[1][7:-2]

                else:
                    if 'TXT_style_form' in request.POST.keys():
                        to_edit = int(request.POST['paragraph_number'])
                        style = paragraphs[to_edit-1].temp_paragraph_style_txt
                        style = style.split('; ')

                        keys = ['bold_TXT_button', 'underline_TXT_button', 'italic_TXT_button']
                        for n, key in enumerate(keys):
                            if key in request.POST.keys():
                                style[n] = request.POST[key]

                        style[3] = request.POST['font']
                        style[4] = request.POST['font_size']
                        style[5] = 'color: ' + request.POST['font_color']

                        paragraph_to_edit = paragraphs[to_edit-1]
                        paragraph_to_edit.update(temp_paragraph_style_txt='; '.join(style))
                        style[5] = request.POST['font_color']

                    elif 'IMG_style_form' in request.POST.keys():
                        to_edit = int(request.POST['paragraph_number'])
                        paragraph_to_edit = paragraphs[to_edit - 1]
                        style = paragraph_to_edit.temp_paragraph_style_img
                        style = style.split('; ')

                        style[0] = 'height: ' + request.POST['height_IMG'] + 'px'
                        style[1] = 'width: ' + request.POST['width_IMG'] + 'px'
                        style[2] = request.POST['position_IMG']

                        paragraph_to_edit.update(temp_paragraph_style_img='; '.join(style))

                        style[0] = request.POST['height_IMG']
                        style[1] = request.POST['width_IMG']


                        """to_edit = int(request.POST['paragraph_number'])
                        style = ''
                        keys = ['bold_TXT_button', 'underline_TXT_button', 'italic_TXT_button']
                        for key in keys:
                            if key in request.POST.keys():
                                if request.POST[key + '_hidden']:
                                    style += '; '
                                else:
                                    style += request.POST[key] + '; '
                            else:
                                style += request.POST[key + '_hidden'] + '; '

                        style += 'color: ' + request.POST['font_color'] + '; '"""





                        """if 'bold_TXT_button' not in tab: tab['bold_TXT_button'] = ''
                        if 'underline_TXT_button' not in tab: tab['underline_TXT_button'] = ''
                        if 'italic_TXT_button' not in tab: tab['italic_TXT_button'] = ''
    
                        style = [tab['bold_TXT_button'], tab['underline_TXT_button'], tab['italic_TXT_button'],
                                 tab['font_color']
                                 #,request.POST['font'], request.POST['font_size']
                                 ,'']
                        style = '; '.join(style)"""
                        #paragraphs[int(to_edit) - 1].update(temp_paragraph_style=style)

            if 'accept_title_form_button' in request.POST.keys():
                post.title = request.POST['title']
                post.description = request.POST['description']
                post.background_image = request.POST['background_image']
                post.save()

            elif 'edit_paragraph_button' in request.POST.keys():
                to_edit = request.POST['edit_paragraph_button']
                paragraph_to_edit = paragraphs[int(to_edit) - 1]
                paragraph_to_edit.update(temp_paragraph_type=paragraph_to_edit.paragraph_type,
                                         temp_paragraph_style_txt=paragraph_to_edit.paragraph_style_txt,
                                         temp_paragraph_style_img=paragraph_to_edit.paragraph_style_img,
                                         temp_url=paragraph_to_edit.url,
                                         temp_paragraph_content=paragraph_to_edit.paragraph_content)
                if paragraph_to_edit.temp_paragraph_type == 'TXT':
                    style = paragraph_to_edit.temp_paragraph_style_txt
                    style = style.split('; ')
                    style[5] = style[5][-7:]
                elif paragraph_to_edit.temp_paragraph_type == 'IMG':
                    style = paragraph_to_edit.temp_paragraph_style_img
                    style = style.split('; ')
                    style[0] = style[0][8:-2]
                    style[1] = style[1][7:-2]

            elif 'save_changes_in_paragraph' in request.POST.keys():
                paragraph_to_edit = paragraphs[int(request.POST['paragraph_number']) - 1]
                if 'paragraph_new_content' in request.POST.keys():
                    new_content = request.POST['paragraph_new_content']
                else:
                    new_content = paragraph_to_edit.temp_paragraph_content
                if 'paragraph_new_url' in request.POST.keys():
                    new_url = request.POST['paragraph_new_url']
                else:
                    new_url = paragraph_to_edit.temp_paragraph_content

                paragraphs[int(request.POST['paragraph_number']) - 1].update(
                    paragraph_type=paragraph_to_edit.temp_paragraph_type,
                    paragraph_style_txt=paragraph_to_edit.temp_paragraph_style_txt,
                    paragraph_style_img=paragraph_to_edit.temp_paragraph_style_img,
                    url=new_url,
                    paragraph_content=new_content)
                if 'to_edit' in locals():
                    del to_edit

            elif 'add_paragraph_button' in request.POST.keys():
                style = ['', '', '', fonts[0]['font_code'], sizes[0]['size_code'], 'color: #000000', '']
                style_img = ['100', '100', '', '', '']
                parameters = {'post': post, 'paragraph_number': len(paragraphs) + 1, 'temp_paragraph_type': 'TXT',
                              'temp_paragraph_style_txt': '; '.join(style), 'temp_paragraph_style_img': style_img}

                new_paragraph = ParagraphUnfinished.objects.create(**parameters)
                new_paragraph.save()
                paragraphs = ParagraphUnfinished.objects.filter(post=post).order_by('paragraph_number')

                to_edit = new_paragraph.paragraph_number
                #style = ['', '', '', fonts[0]['font_code'], sizes[0]['size_code'], 'color: #000000', '']
                #return redirect('/edit_post/unfinished/' + str(post_id))

            elif 'delete_paragraph_button' in request.POST.keys():
                for paragraph in paragraphs:
                    if paragraph.paragraph_number == int(request.POST['delete_paragraph_button']):
                        paragraph.delete()
                    elif paragraph.paragraph_number > int(request.POST['delete_paragraph_button']):
                        paragraph.paragraph_number += -1
                        paragraph.save()
                return redirect('/edit_post/unfinished/' + str(post_id))

            elif 'move_up_paragraph_button' in request.POST.keys():
                number = int(request.POST['move_up_paragraph_button'])
                if request.POST['move_up_paragraph_button'] != '1':
                    paragraphs[number - 1].update(paragraph_number=number - 1)
                    paragraphs[number - 2].update(paragraph_number=number)
                return redirect('/edit_post/unfinished/' + str(post_id))

            elif 'move_down_paragraph_button' in request.POST.keys():
                number = int(request.POST['move_down_paragraph_button'])
                if request.POST['move_down_paragraph_button'] != str(len(paragraphs)):
                    paragraphs[number - 1].update(paragraph_number=number + 1)
                    paragraphs[number].update(paragraph_number=number)
                return redirect('/edit_post/unfinished/' + str(post_id))

            elif 'show_button' in request.POST.keys():
                return redirect('/post/unfinished/' + str(post_id))

            elif 'publish_button' in request.POST.keys():
                if post.created:
                    new_post = Post.objects.create(title=post.title, description=post.description, author=post.author,
                                                   created=post.created, id=post.id)
                    new_post.edited = datetime.now()

                else:
                    new_post = Post.objects.create(title=post.title, description=post.description, author=post.author,
                                                   created=datetime.now(), id=post.id)
                new_post.save()

                for paragraph in paragraphs:
                    new_paragraph = Paragraph.objects.create(post=new_post,
                                                             paragraph_number=paragraph.paragraph_number,
                                                             paragraph_type=paragraph.paragraph_type,
                                                             paragraph_style_txt=paragraph.paragraph_style_txt,
                                                             paragraph_style_img=paragraph.paragraph_style_img,
                                                             url=paragraph.url,
                                                             paragraph_content=paragraph.paragraph_content)

                Comments.objects.filter(post=post.id).update(post=new_post)
                Likes.objects.filter(post=post.id).update(post=new_post)

                post.delete()
                return redirect('/author/' + user.username)

            elif 'end_for_now_button' in request.POST.keys():
                return redirect('/')

        # Może będzie trzeba przekonwertować modele na słowniki
        content = {'username': user.username, 'posts_menu': posts_menu, 'new_messages': new_messages,
                   'fonts': fonts, 'sizes': sizes, 'img_positions': img_positions,
                   'post': post, 'paragraphs': paragraphs}

        if 'to_edit' in locals():
            content['to_edit'] = int(to_edit)
            content['styles'] = style

            """style = paragraphs[int(to_edit) - 1].temp_paragraph_style
            if style:
                style = style.split('; ')
            else:
                style = ['', '', '', 'color: #000000; ']
            style[3] = style[3][-7:]
            print(style)
            content['styles'] = style"""
        if 'style' in locals():
            print('Final stylesa: ', style)
        return render(request, 'edit_post_page.html', {'content': content})

    else:
        messages.info(request, f'Nie istnieje post o podanym id: {post_id}')
        return redirect('/')


def post(request, post_type, post_id):
    user = auth.get_user(request)
    post_id = int(post_id)
    posts_menu = Post.objects.order_by('-created').all()

    if user.username:
        new_messages = len(Messages.objects.filter(reciver=user, seen=False))
    else:
        new_messages = False

    if post_type == 'unfinished':
        post_model = PostUnfinished
        paragraph_model = ParagraphUnfinished
    elif post_type == 'finished':
        post_model = Post
        paragraph_model = Paragraph
    else:
        return redirect('/')

    if post_type == 'finished' and request.method == 'POST':
        # if user
# Post likes add
        if ('post_likes_plus_button' in request.POST.keys()) and user.username:
            if Likes.objects.filter(post=Post.objects.get(id=post_id), author=user).exists():
                if Likes.objects.filter(post=Post.objects.get(id=post_id), author=user).first().value == 1:
                    Likes.objects.filter(post=Post.objects.get(id=post_id), author=user).first().delete()
                else:
                    Likes.objects.filter(post=Post.objects.get(id=post_id), author=user).first().update(value='+1')
            else:
                Likes.objects.create(post=Post.objects.get(id=post_id), author=user, value='+1')

        elif ('post_likes_minus_button' in request.POST.keys()) and user.username:
            if Likes.objects.filter(post=Post.objects.get(id=post_id), author=user).exists():
                if Likes.objects.filter(post=Post.objects.get(id=post_id), author=user).first().value == -1:
                    Likes.objects.filter(post=Post.objects.get(id=post_id), author=user).first().delete()
                else:
                    Likes.objects.filter(post=Post.objects.get(id=post_id), author=user).first().update(value='-1')
            else:
                Likes.objects.create(post=Post.objects.get(id=post_id), author=user, value='-1')

# Comments likes add
        elif ('comment_likes_plus_button' in request.POST.keys()) and user.username:
            if Comments.objects.filter(id=int(request.POST['comment_likes_plus_button'])).exists():
                try:
                    if CommentsLikes.objects.filter(comment=Comments.objects.get(
                            id=int(request.POST['comment_likes_plus_button'])), author=user).first().value == 1:
                        CommentsLikes.objects.filter(comment=Comments.objects.get(
                            id=int(request.POST['comment_likes_plus_button'])), author=user).first().delete()
                    else:
                        CommentsLikes.objects.filter(comment=Comments.objects.get(
                            id=int(request.POST['comment_likes_plus_button'])), author=user).first().update(value='+1')
                except:
                    CommentsLikes.objects.create(comment=Comments.objects.get(
                        id=int(request.POST['comment_likes_plus_button'])), author=user, value='+1')

        elif ('comment_likes_minus_button' in request.POST.keys()) and user.username:
            if Comments.objects.filter(id=int(request.POST['comment_likes_minus_button'])).exists():
                try:
                    if CommentsLikes.objects.filter(comment=Comments.objects.get(
                            id=int(request.POST['comment_likes_minus_button'])), author=user).first().value == -1:
                        CommentsLikes.objects.filter(comment=Comments.objects.get(
                            id=int(request.POST['comment_likes_minus_button'])), author=user).first().delete()
                    else:
                        CommentsLikes.objects.filter(comment=Comments.objects.get(
                            id=int(request.POST['comment_likes_minus_button'])), author=user).first().update(value='-1')

                except:
                    CommentsLikes.objects.create(comment=Comments.objects.get(
                        id=int(request.POST['comment_likes_minus_button'])), author=user, value='-1')

# Adding comment
        elif 'accept_comment_button' in request.POST.keys() and user.username:
            # edit comment
            try:
                Comments.objects.filter(id=int(request.POST['accept_comment_button'])).update(
                    content=request.POST['comment_content'])
            except:
                # comment to comment
                if request.POST['accept_comment_button']:
                    Comments.objects.create(post=Post.objects.get(id=post_id), comment=Comments.objects.filter(
                        id=int(request.POST['accept_comment_button'])).first(), author=user,
                                            content=request.POST['comment_content'])
                # comment to post
                else:
                    Comments.objects.create(post=Post.objects.get(id=post_id), author=user,
                                            content=request.POST['comment_content'])
        elif 'add_comment_button' in request.POST.keys() and user.username:
            new_comment = Comments.objects.create(post=Post.objects.get(id=post_id), comment=Comments.objects.filter(
                id=request.POST['add_comment_button']).first(), author=user, content='', created=datetime.now())

            #request.POST['edit_comment_button'] = str(new_comment.id)
            to_edit = str(new_comment.id)

        elif 'edit_comment_button' in request.POST.keys() and user.username:
            to_edit = request.POST['edit_comment_button']

        elif 'delete_comment_button' in request.POST.keys() and user.username:
            Comments.objects.filter(id=int(request.POST['delete_comment_button'])).delete()

        else:
            messages.info(request, "Tylko zalogowani użytkownicy mogą komentować oraz likować posty oraz komentarze")

    if post_model.objects.filter(id=post_id).exists():
        post = post_model.objects.get(id=post_id)
        if paragraph_model.objects.filter(post=post).exists():
            paragraphs = paragraph_model.objects.filter(post=post).order_by('paragraph_number').all()
        else:
            paragraphs = []

        # mb here if POST
        if post_type == 'finished':
            if Likes.objects.filter(post=post, value='+1').exists():
                post_likes_plus = len(Likes.objects.filter(post=post, value='+1').all())
            else:
                post_likes_plus = 0
            if Likes.objects.filter(post=post, value='-1').exists():
                post_likes_minus = len(Likes.objects.filter(post=post, value='-1').all())
            else:
                post_likes_minus = 0

            if user.username:
                if Likes.objects.filter(post=post, author=user).exists():
                    post_my_like = Likes.objects.filter(post=post, author=user).first().value
                else:
                    post_my_like = 0
            else:
                post_my_like = 0

# Order_by ?a
            comments = []
            if Comments.objects.filter(post=post, comment=None).exists():
                for main_comment in Comments.objects.filter(post=post, comment=None).order_by('created').all():
                    if CommentsLikes.objects.filter(comment=main_comment, value='+1').exists():
                        comment_likes_plus = len(CommentsLikes.objects.filter(comment=main_comment, value='+1').all())
                    else:
                        comment_likes_plus = 0
                    if CommentsLikes.objects.filter(comment=main_comment, value='-1').exists():
                        comment_likes_minus = len(CommentsLikes.objects.filter(comment=main_comment, value='-1').all())
                    else:
                        comment_likes_minus = 0

                    if CommentsLikes.objects.filter(comment=main_comment, author=user).exists():
                        comment_my_like = CommentsLikes.objects.filter(comment=main_comment, author=user).first().value
                    else:
                        comment_my_like = 0

                    comments_to_comment = []
                    if Comments.objects.filter(post=post, comment=main_comment).exists():
                        for comment_to_comment in Comments.objects.filter(post=post, comment=main_comment).order_by(
                                'created').all():
                            if CommentsLikes.objects.filter(comment=comment_to_comment, value='+1').exists():
                                comment_to_comment_likes_plus = len(CommentsLikes.objects.filter(
                                    comment=comment_to_comment, value='+1').all())
                            else:
                                comment_to_comment_likes_plus = 0
                            if CommentsLikes.objects.filter(comment=comment_to_comment, value='-1').exists():
                                comment_to_comment_likes_minus = len(CommentsLikes.objects.filter(
                                    comment=comment_to_comment, value='-1').all())
                            else:
                                comment_to_comment_likes_minus = 0

                            if CommentsLikes.objects.filter(comment=comment_to_comment, author=user).exists():
                                comment_to_comment_my_like = CommentsLikes.objects.filter(comment=comment_to_comment,
                                                                                          author=user).first().value
                            else:
                                comment_to_comment_my_like = 0

                            comments_to_comment.append({'comment_to_comment': comment_to_comment,
                                                        'comment_to_comment_likes_plus': comment_to_comment_likes_plus,
                                                        'comment_to_comment_likes_minus': comment_to_comment_likes_minus,
                                                        'comment_to_comment_my_like': comment_to_comment_my_like})

                    comments.append({'comment': main_comment, 'comment_likes_plus': comment_likes_plus,
                                     'comment_likes_minus': comment_likes_minus, 'comment_my_like': comment_my_like,
                                     'comments_to_comment': comments_to_comment})

            content = {'user': user, 'posts_menu': posts_menu, 'new_messages': new_messages,
                       'post': post, 'paragraphs': paragraphs, 'post_type': post_type,
                       'comments': comments, 'post_my_like': post_my_like,
                       'post_likes_plus': post_likes_plus, 'post_likes_minus': post_likes_minus}
            if 'to_edit' in locals():
                content['to_edit'] = int(to_edit)
        else:
            content = {'user': user, 'posts_menu': posts_menu, 'new_messagers': new_messages,
                       'post': post, 'paragraphs': paragraphs,
                       'post_type': post_type, 'comments': [], 'post_my_like': 0,
                       'post_likes_plus': 0, 'post_likes_minus': 0}

        return render(request, 'post_page.html', {'content': content})

    else:
        messages.info(request, 'Post o podanym id nie istnieje1')
        return redirect('/')


def posts(request):
    user = auth.get_user(request)
    posts_menu = Post.objects.order_by('-created').all()

    if user.username:
        new_messages = len(Messages.objects.filter(reciver=user, seen=False))
    else:
        new_messages = False

    #post_keys = [key.name for key in Post._meta.get_fields()]
    filters = {}
    if request.method == 'POST':
        for key in request.POST.keys():
            if request.POST[key]:
                if key == 'author':
                    author_list = User.objects.filter(username__contains=request.POST[key])
                    filters[key + '__in'] = author_list
                elif key == 'created_after':
                    filters['created__gt'] = request.POST['created_after']
                elif key == 'created_before':
                    filters['created__lt'] = request.POST['created_before']
                elif key == 'id':
                    filters['id'] = request.POST['id']
                elif key in ['title', 'description']:
                    filters[key + '__contains'] = request.POST[key]
                else:
                    pass
############################## IMPORT SORTING NUMBERS WITH TEXT MECHANICS
    order_by = '-created'
    if 'order_by' in request.POST.keys():
        if request.POST['order_by'] not in ['likes', 'comments', '-likes', '-comments']:
            order_by = request.POST['order_by']

    posts = Post.objects.filter(**filters).order_by(order_by).all()

    posts_extended = []
    for post in posts:
        dictionary = {'post_model': post, 'comments': len(Comments.objects.filter(post=post).all()),
                      'likes': len(Likes.objects.filter(post=post, value=1).all())}
        posts_extended.append(dictionary)

    if 'order_by' in request.POST.keys():
        order_by = request.POST['order_by']
        if request.POST['order_by'] == 'likes':
            posts_extended = sorted(posts_extended, key=lambda k: k['likes'])
        elif request.POST['order_by'] == '-likes':
            posts_extended = sorted(posts_extended, key=lambda k: k['likes'], reverse=True)
        elif request.POST['order_by'] == 'comments':
            posts_extended = sorted(posts_extended, key=lambda k: k['comments'])
        elif request.POST['order_by'] == '-comments':
            posts_extended = sorted(posts_extended, key=lambda k: k['comments'], reverse=True)

    column_names = ['id', 'title', 'description', 'author', 'likes', 'comments', 'created']
    if 'author' in request.POST.keys():
        filters['author__in'] = request.POST['author']
    content = {'user': user, 'posts_menu': posts_menu, 'new_messages': new_messages,
               'filters': filters, 'order_by': order_by, 'column_names': column_names,
               'posts': posts_extended}
    return render(request, 'posts_page.html', {'content': content})


def msgs(request):
    user = auth.get_user(request)
    posts_menu = Post.objects.order_by('-created').all()

    if user.username:
        new_messages = len(Messages.objects.filter(reciver=user, seen=False))
    else:
        new_messages = False

    if user.username:
        messages_list = [[message.reciver, message.seen, message.created, message.content, message.sender]
                         if message.sender.id == user.id else
                         [message.sender, message.seen, message.created, message.content, message.sender]
                         for message in Messages.objects.filter(Q(reciver=user) | Q(sender=user)).order_by('-created')]

        messagers = []
        persons = []
        for message in messages_list:
            if not message[0] in persons:
                persons.append(message[0])
                messagers.append({'author': message[0], 'seen': message[1], 'created': message[2],
                                  'content': message[3], 'message_sender': message[4]})

        content = {'user': user, 'posts_menu': posts_menu, 'new_messages': new_messages, 'messagers': messagers}
        return render(request, 'messages_page.html', {'content': content})

    else:
        messages.info(request, 'Ta opcja wymaga zalogowanego użytkownika')
        return redirect(request, '/')


def send_message(request, author):
    user = auth.get_user(request)
    posts_menu = Post.objects.order_by('-created').all()

    if user.username:
        new_messages = len(Messages.objects.filter(reciver=user, seen=False))
    else:
        new_messages = False

    if user.username:
        author_object = User.objects.get(username=author)
        if user != author_object:
            if request.method == 'POST':
                if 'send_message_button' in request.POST.keys():
                    Messages.objects.create(sender=user, reciver=author_object, content=request.POST['message_content'],
                                            created=datetime.now())


            # messages = [{'sender': message['sender'], 'reciver':message['reciver'], 'content':message['content'], 'seen':message['seen'], 'created':message['created']} for message in Messages.objects.filter(Q(reciver=user) & Q(sender=author_object) | Q(sender=user) & Q(reciver=author_object).order_by('created').values('sender', 'reciver', 'seen', 'created', content)
            messages_between = Messages.objects.filter(Q(sender=user) & Q(reciver=author_object) |
                                                       Q(sender=author_object) & Q(reciver=user)).order_by('created')

            content = {'user': user, 'posts_menu': posts_menu, 'new_messages': new_messages,
                       'messages': messages_between}

            messages_between.filter(reciver=user).update(seen=True)
            return render(request, 'send_message_page.html', {'content': content})

        else:
            messages.info(request, 'Nie możesz wysłać wiadomości sam do siebie')
            return redirect('/')
    else:
        messages.info(request, 'Ta opcja wymaga zalogowanego użytkownika')
        return redirect('/')


def authors(request):
    user = auth.get_user(request)
    posts_menu = Post.objects.order_by('-created').all()

    if user.username:
        new_messages = len(Messages.objects.filter(reciver=user, seen=False))
    else:
        new_messages = False

    authors_list = []
    author_list = User.objects.order_by('username').all()

    if request.method == 'POST':
        if 'search_author_button' in request.POST:
            author_list = User.objects.filter(username__contains=request.POST['search_author']).order_by(
                'username').all()

    for user_from_list in author_list:
        authors_list.append({'user': user_from_list, 'post_count': len(Post.objects.filter(author=user_from_list)),
                            'comments_count': len(Comments.objects.filter(author=user_from_list))})

    content = {'user': user, 'posts_menu': posts_menu, 'new_messages': new_messages, 'users': authors_list}
    return render(request, 'authors_page.html', {'content': content})


def author(request, username):
    user = auth.get_user(request)
    posts_menu = Post.objects.order_by('-created').all()

    if user.username:
        new_messages = len(Messages.objects.filter(reciver=user, seen=False))
    else:
        new_messages = False

    if request.method == 'POST':
        if 'delete_unfinished_post_button' in request.POST.keys():
            PostUnfinished.objects.filter(id=request.POST['delete_unfinished_post_button']).delete()

        elif 'delete_finished_post_button' in request.POST.keys():
            Post.objects.filter(id=request.POST['delete_finished_post_button']).delete()

    if not User.objects.filter(username=username).exists():
        messages.info(request, 'Nie istnieje użytkownik o wpisanej nazwie')
        #return render(request, 'author_page.html', {'content': 'content'})
        return redirect('/authors')

    author = User.objects.filter(username=username).first()
    content = {'user': user, 'posts_menu': posts_menu, 'new_messages': new_messages,
               'author': author, 'post_count': len(Post.objects.filter(author=author)),
               'comments_count': len(Comments.objects.filter(author=author))}

    if user == author:
        unfinishedposts = PostUnfinished.objects.filter(author=author)
        content['unfinished_posts'] = unfinishedposts

    posts = []
    post_list = Post.objects.filter(author=author)
    for post in post_list:
        posts.append({'post': post, 'comments_count': len(Comments.objects.filter(post=post)), 'likes_plus': len(Likes.objects.filter(post=post, value='+1')), 'likes_minus': len(Likes.objects.filter(post=post, value='-1'))})
    content['posts'] = posts

    return render(request, 'author_page.html', {'content': content})

