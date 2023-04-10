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
from .functions import gain_quote, send_mail, my_sort, create_content, get_comments

# SZYFROWNIE PODWOJNE HASEŁ BO W UTC WIDAĆ HAS
print('11221x11231a2zz1224112235142222322aa1')

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


# Menu toolbar
@csrf_exempt
def menu(request):
    # Get logged user and all posts ordered by date
    user = auth.get_user(request)
    posts_menu = Post.objects.order_by('-created').all()

    # Check if user have new messages
    if user.username:
        new_messages = len(Messages.objects.filter(reciver=user, seen=False))
    else:
        new_messages = False

    # Create variable with 3 last posts, quote and 3 best posts to show in page
    last_3 = posts_menu[:3]
    quote = gain_quote()
    best_3_likes = Likes.objects.filter(value='+1').values('post').annotate(plus_likes=Count('post')).order_by(
        '-plus_likes').all()[:3]
    best_3 = []
    # Add to best posts number of likes (2 different tables)
    for post in best_3_likes:
        best_3.append({'post': Post.objects.filter(id=post['post']).first(), 'plus_likes': post['plus_likes']})

    # Content variable to render template
    content = {'user': user, 'posts_menu': posts_menu, 'new_messages': new_messages, 'last_3': last_3, 'best_3': best_3,
               'quote': quote}

    return render(request, 'base_page.html', {'content': content})


# LOGIN AND REGISTER PAGE
def login(request):
    # Get all posts
    posts_menu = Post.objects.order_by('-created').all()
    # Button service
    if request.method == 'POST':
        # Login button
        if 'login_button' in request.POST.keys():
            # Get username and password from HTML form
            username = request.POST['username']
            password = request.POST['password']

            # User authentication and login if user exists
            user = auth.authenticate(username=username, password=password)
            if user is not None:
                auth.login(request, user)
                return redirect('/')
            else:
                messages.info(request, 'Błędne dane logowania.')
                return render(request, 'login_page.html', {'content': {'posts_menu': posts_menu}})

        # Register button
        elif 'register_button' in request.POST.keys():
            # Get data from HTML form
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
                # Checking if account already waiting to confirm
                if UserToConfirm.objects.filter(email=email).exists():
                    messages.info(request, 'Twoje konto oczekuje na potwierdzenie. Sprawdź email.')
                    return render(request, 'login_page.html', {'content': {'posts_menu': posts_menu, 'email': email}})
                elif UserToConfirm.objects.filter(login=username).exists():
                    messages.info(request, 'Konto o danym nicku oczekuje na potwierdzenie. Sprawdź email.')
                    return render(request, 'login_page.html', {'content': {'posts_menu': posts_menu, 'email': email}})
                else:
                    # Generate confirm code
                    code = randint(1000, 9999)

                    # create user to confirm position in database
                    UserToConfirm.objects.create(login=username,
                                                 email=email,
                                                 password=password,
                                                 code=code,
                                                 valid_time=(datetime.now() + timedelta(minutes=15)))
                    # Send main with confirm code and redirect to user confirm page
                    url = 'confirm/'+username
                    send_mail(email, username, code, 'http://' + request.META['HTTP_HOST'] + '/confirm/' + login)
                    return redirect(url)

    messages.info(request, '')
    return render(request, 'login_page.html', {'content': {'posts_menu': posts_menu, 'email': ''}})


# CONFIRM PAGE
def confirm(request, login):
    # Get all posts
    posts_menu = Post.objects.order_by('-created').all()
    # Button service
    if request.method == 'POST':
        # Checking if user from url is waiting to confirm
        if UserToConfirm.objects.filter(login=login).exists():
            person = UserToConfirm.objects.get(login=login)
            # Confirm button
            if 'confirm_button' in request.POST.keys():
                # Checking confirm expire time
                if person.valid_time > timezone("Europe/Warsaw").localize(datetime.now()):
                    # Checking code from HTML form
                    if int(request.POST['code']) == person.code:
                        # creating new user and deleting him from waiting to confirm table
                        user = User.objects.create_user(username=person.login,
                                                        email=person.email,
                                                        password=person.password)
                        user.save();
                        UserToConfirm.objects.filter(login=login).delete()

                        messages.info(request, 'Potwierdzono rejestrację konta.')
                        return redirect('login')

                # Return message about expired confirm time
                else:
                    messages.info(request, 'Czas na potwierdzenie rejestracji minął. '
                                           'Wyślij kod ponownie.')
                    return redirect('/confirm/' + login)

            # Resend button
            elif 'resend_button' in request.POST.keys():
                # Generate new code and send it
                code = randint(1000, 9999)
                UserToConfirm.objects.filter(login=login).update(
                    valid_time=timezone("Europe/Warsaw").localize((datetime.now() + timedelta(minutes=15))), code=code)
                send_mail(person.email, login, code, 'http://' + request.META['HTTP_HOST'] + '/confirm/' + login)

                messages.info(request, 'Wysłano nowy kod aktywacyjny')
                return redirect('/confirm/' + login)
        # Register application was deleted
        else:
            messages.info(request, 'Twoja prośba o rejestrację została usunięta z powodu zbyt długiej zwłoki z '
                                   'potwierdzeniem. Proszę wrócić do formularza rejestracyjnego')
            return redirect('/confirm/' + login)

    return render(request, 'confirm_page.html', {'content': {'posts_menu': posts_menu, 'login': login}})


# Logout request
def logout(request):
    auth.logout(request)
    return redirect('/')


# MAIN PAGE
def start(request):
    # Get logged user and all posts ordered by date
    user = auth.get_user(request)
    posts_menu = Post.objects.order_by('-created').all()

    # Check if user have new messages
    if user.username:
        new_messages = len(Messages.objects.filter(reciver=user, seen=False))
    else:
        new_messages = False

    # Create variable with 3 last posts, quote and 3 best posts to show in page
    last_3 = posts_menu[:3]
    quote = gain_quote()
    best_3_likes = Likes.objects.filter(value='+1').values('post').annotate(plus_likes=Count('post')).order_by(
        '-plus_likes').all()[:3]
    best_3 = []
    # Add to best posts number of likes (2 different tables)
    for post in best_3_likes:
        best_3.append({'post': Post.objects.filter(id=post['post']).first(), 'plus_likes': post['plus_likes']})

    # Content variable to render template
    content = {'user': user, 'posts_menu': posts_menu, 'new_messages': new_messages, 'last_3': last_3, 'best_3': best_3,
               'quote': quote}

    return render(request, 'start_page.html', {'content': content})


# Create post request
def create_post(request):
    # Get logged user
    user = auth.get_user(request)
    # Checking if anyone user is logged
    if user.username:
        # Checking if user already have 5 unfinished posts and if not create new
        unfinished_posts = PostUnfinished.objects.filter(author=user).all()
        if len(unfinished_posts) <= 5:
            new_post = PostUnfinished.objects.create(author=user)
            return redirect('edit_post/unfinished/' + str(new_post.id))
        else:
            messages.info(request, 'Osiągnołeś maksymalną liczbę roboczych postów.')
            return redirect('author/' + str(user.id))
    # Unlogged user
    else:
        messages.info(request, 'Ta opcja wymaga zalogowanego użytkownika')
        return redirect('/')


# EDIT POST PAGE
def edit_post(request, post_type, post_id):
    # Get logged user and posts list
    user = auth.get_user(request)
    post_id = int(post_id)
    posts_menu = Post.objects.order_by('-created').all()

    print('qwe', request.POST)

    # Check if user have new messages
    if user.username:
        new_messages = len(Messages.objects.filter(reciver=user, seen=False))
    else:
        new_messages = False

    # MOVE POST AND PARAGRAPHS FROM FINISHED TO UNFINISHED TABLE (id don't change)
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

            return redirect('/edit_post/unfinished/' + str(new_post.id))

    # Redirect if unknown url
    elif post_type != 'unfinished':
        return redirect('/')

    # Get post with id from url if exists + paragraphs
    if PostUnfinished.objects.filter(id=post_id).exists():
        post = PostUnfinished.objects.get(id=post_id)
        if ParagraphUnfinished.objects.filter(post=post).exists():
            paragraphs = ParagraphUnfinished.objects.filter(post=post).order_by('paragraph_number')
        else:
            paragraphs = []


# FONTS, SIZES AND POSITION TABLE
        fonts = [{'font_name': 'Times New Roman', 'font_code': 'font-family: "Times New Roman", Times, serif'},
                 {'font_name': 'Arial', 'font_code': 'font-family: Arial, Helvetica, sans-serif'},
                 {'font_name': 'Lucilda Console', 'font_code': 'font-family: "Lucida Console", "Courier New", monospace'}]
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

        # Buttons service
        if request.method == 'POST':
            if 'reject_changes_in_paragraph' not in request.POST.keys():
                # TXT type button -> change paragraph type to TXT
                if 'TXT_type_paragraph_button' in request.POST.keys() and request.POST['TXT_type_paragraph_button']:
                    # Keep edited paragraph number
                    to_edit = request.POST['paragraph_number']
                    # Change temporary paragraph type
                    paragraphs[int(to_edit)-1].update(temp_paragraph_type='TXT')

                    # Create style variable for content
                    style = paragraphs[int(to_edit) - 1].temp_paragraph_style_txt
                    style = style.split('; ')
                    style[5] = style[5][-7:]

                # IMG type button -> change paragraph type to IMG
                elif 'IMG_type_paragraph_button' in request.POST.keys() and request.POST['IMG_type_paragraph_button']:
                    # Keep edited paragraph number
                    to_edit = request.POST['paragraph_number']
                    # Change temporary paragraph type
                    paragraphs[int(to_edit)-1].update(temp_paragraph_type='IMG')

                    # Create style variable for content
                    style = paragraphs[int(to_edit) - 1].temp_paragraph_style_img
                    style = style.split('; ')
                    style[0] = style[0][8:-2]
                    style[1] = style[1][7:-2]

                # Chcecking changes in style from HTML form
                else:
                    if 'TXT_style_form' in request.POST.keys():
                        # Keep edited paragraph number
                        to_edit = int(request.POST['paragraph_number'])
                        # Create style variable for content
                        style = paragraphs[to_edit-1].temp_paragraph_style_txt
                        style = style.split('; ')

                        # Get style data from HTML form
                        keys = ['bold_TXT_button', 'underline_TXT_button', 'italic_TXT_button']
                        for n, key in enumerate(keys):
                            if key in request.POST.keys():
                                style[n] = request.POST[key]

                        style[3] = request.POST['font']
                        style[4] = request.POST['font_size']
                        style[5] = 'color: ' + request.POST['font_color']

                        # Update temp style for edited paragraph
                        paragraph_to_edit = paragraphs[to_edit-1]
                        paragraph_to_edit.update(temp_paragraph_style_txt='; '.join(style),
                                                 temp_paragraph_content=request.POST['paragraph_new_content'])

                        # Change style data for content
                        style[5] = request.POST['font_color']

                    elif 'IMG_style_form' in request.POST.keys():
                        # Keep edited paragraph number
                        to_edit = int(request.POST['paragraph_number'])
                        # Create style variable for content
                        paragraph_to_edit = paragraphs[to_edit - 1]
                        style = paragraph_to_edit.temp_paragraph_style_img
                        style = style.split('; ')

                        # Get style data from HTML form
                        style[0] = 'height: ' + request.POST['height_IMG'] + 'px'
                        style[1] = 'width: ' + request.POST['width_IMG'] + 'px'
                        style[2] = request.POST['position_IMG']

                        # Update temp style for edited paragraph
                        paragraph_to_edit.update(temp_paragraph_style_img='; '.join(style),
                                                 temp_url=request.POST['paragraph_new_url'])

                        # Change style data for content
                        style[0] = request.POST['height_IMG']
                        style[1] = request.POST['width_IMG']

            # Accept title form button -> from HTML form get title, post description and background image
            if 'accept_title_form_button' in request.POST.keys():
                post.title = request.POST['title']
                post.description = request.POST['description']
                post.background_image = request.POST['background_image']
                post.save()

            # Edit paragraph button
            elif 'edit_paragraph_button' in request.POST.keys():
                # Keep edited paragraph number
                to_edit = request.POST['edit_paragraph_button']
                # Copy paragraph data to temp paragraph data
                paragraph_to_edit = paragraphs[int(to_edit) - 1]
                paragraph_to_edit.update(temp_paragraph_type=paragraph_to_edit.paragraph_type,
                                         temp_paragraph_style_txt=paragraph_to_edit.paragraph_style_txt,
                                         temp_paragraph_style_img=paragraph_to_edit.paragraph_style_img,
                                         temp_url=paragraph_to_edit.url,
                                         temp_paragraph_content=paragraph_to_edit.paragraph_content)

                # Create style variable for content
                if paragraph_to_edit.temp_paragraph_type == 'TXT':
                    style = paragraph_to_edit.temp_paragraph_style_txt
                    style = style.split('; ')
                    style[5] = style[5][-7:]
                elif paragraph_to_edit.temp_paragraph_type == 'IMG':
                    style = paragraph_to_edit.temp_paragraph_style_img
                    style = style.split('; ')
                    style[0] = style[0][8:-2]
                    style[1] = style[1][7:-2]

            # Save changes button
            elif 'save_changes_in_paragraph' in request.POST.keys():
                paragraph_to_edit = paragraphs[int(request.POST['paragraph_number']) - 1]
                # Save data from HTML from in paragraph or from temp value if HTML from is empty
                if 'paragraph_new_content' in request.POST.keys():
                    new_content = request.POST['paragraph_new_content']
                else:
                    new_content = paragraph_to_edit.temp_paragraph_content
                if 'paragraph_new_url' in request.POST.keys():
                    new_url = request.POST['paragraph_new_url']
                else:
                    new_url = paragraph_to_edit.temp_paragraph_content

                # Save data from paragraph temp value - temp values were updated in previous iterations
                paragraphs[int(request.POST['paragraph_number']) - 1].update(
                    paragraph_type=paragraph_to_edit.temp_paragraph_type,
                    paragraph_style_txt=paragraph_to_edit.temp_paragraph_style_txt,
                    paragraph_style_img=paragraph_to_edit.temp_paragraph_style_img,
                    url=new_url,
                    paragraph_content=new_content)

                # Ending editing paragraph
                if 'to_edit' in locals():
                    del to_edit

            # Add paragraph button
            elif 'add_paragraph_button' in request.POST.keys():
                # Create initial values for paragraph
                style = ['', '', '', fonts[0]['font_code'], sizes[4]['size_code'], 'color: #000000', '']
                style_img = ['100', '100', '', '', '']
                parameters = {'post': post, 'paragraph_number': len(paragraphs) + 1,
                              'paragraph_type': 'TXT', 'temp_paragraph_type': 'TXT',
                              'paragraph_style_txt': '; '.join(style), 'paragraph_style_img': '; '.join(style_img),
                              'temp_paragraph_style_txt': '; '.join(style),
                              'temp_paragraph_style_img': '; '.join(style_img)}

                # Create new paragraph with initial values
                new_paragraph = ParagraphUnfinished.objects.create(**parameters)
                new_paragraph.save()
                # Create new paragraph list for content
                paragraphs = ParagraphUnfinished.objects.filter(post=post).order_by('paragraph_number')

                # Set new paragraph number to edit
                to_edit = new_paragraph.paragraph_number

            # Delete paragraph button
            elif 'delete_paragraph_button' in request.POST.keys():
                for paragraph in paragraphs:
                    # Delete paragraph with specified number
                    if paragraph.paragraph_number == int(request.POST['delete_paragraph_button']):
                        paragraph.delete()
                    # Update paragraphs numbers for other paragraphs
                    elif paragraph.paragraph_number > int(request.POST['delete_paragraph_button']):
                        paragraph.paragraph_number += -1
                        paragraph.save()
                return redirect('/edit_post/unfinished/' + str(post_id))

            # Move up button -> swap paragraph number with higher paragraph
            elif 'move_up_paragraph_button' in request.POST.keys():
                number = int(request.POST['move_up_paragraph_button'])
                # Check if higher paragraph exists
                if request.POST['move_up_paragraph_button'] != '1':
                    print('imhere')
                    paragraphs[number - 1].update(paragraph_number=number - 1)
                    paragraphs[number - 2].update(paragraph_number=number)
                return redirect('/edit_post/unfinished/' + str(post_id))

            # Move down button -> swap paragraph number with lower paragraph
            elif 'move_down_paragraph_button' in request.POST.keys():
                number = int(request.POST['move_down_paragraph_button'])
                # Check if lower paragraph exists
                if request.POST['move_down_paragraph_button'] != str(len(paragraphs)):
                    paragraphs[number - 1].update(paragraph_number=number + 1)
                    paragraphs[number].update(paragraph_number=number)
                return redirect('/edit_post/unfinished/' + str(post_id))

            # Show button -> show post page for this post
            elif 'show_button' in request.POST.keys():
                return redirect('/post/unfinished/' + str(post_id))

            # Publish post -> move post form unfinished post table to post table
            elif 'publish_button' in request.POST.keys():
                # Adding edited variable if it isn't first publish of this post
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

            # End for now button -> finish work without publishing post
            elif 'end_for_now_button' in request.POST.keys():
                return redirect('/')

        # Convert positions 'None' from database to ''
        for paragraph in paragraphs:
            if not paragraph.paragraph_content:
                paragraph.paragraph_content = ''
            if not paragraph.url:
                paragraph.url = ''
            if not paragraph.temp_paragraph_content:
                paragraph.temp_paragraph_content = ''
            if not paragraph.temp_url:
                paragraph.temp_url = ''

        if 'y_scroll' in request.POST.keys():
            y_scroll = request.POST['y_scroll']
        else:
            y_scroll = 0



        # Content variable to render tamplate
        content = {'user': user, 'posts_menu': posts_menu, 'new_messages': new_messages, 'y_scroll': y_scroll,
                   'fonts': fonts, 'sizes': sizes, 'img_positions': img_positions,
                   'post': post, 'paragraphs': paragraphs}

        # Add to content edit paragraph options
        if 'to_edit' in locals():
            content['to_edit'] = int(to_edit)
            content['styles'] = style

        return render(request, 'edit_post_page.html', {'content': content})

    # Post with id from url don't exists
    else:
        messages.info(request, f'Nie istnieje post o podanym id: {post_id}')
        return redirect('/')


# POST PAGE
def post(request, post_type, post_id):
    # Get user and posts list
    user = auth.get_user(request)
    post_id = int(post_id)
    posts_menu = Post.objects.order_by('-created').all()

    # Check if user have new message
    if user.username:
        new_messages = len(Messages.objects.filter(reciver=user, seen=False))
    else:
        new_messages = False

    # Get post and paragraphs from table specified in url
    if post_type == 'unfinished':
        post_model = PostUnfinished
        paragraph_model = ParagraphUnfinished
    elif post_type == 'finished':
        post_model = Post
        paragraph_model = Paragraph
    else:
        return redirect('/')

    # If post is finished -> Button service
    if post_type == 'finished' and request.method == 'POST':
        # + button
        if ('post_likes_plus_button' in request.POST.keys()) and user.username:
            # Check if logged user like already exists
            if Likes.objects.filter(post=Post.objects.get(id=post_id), author=user).exists():
                if Likes.objects.filter(post=Post.objects.get(id=post_id), author=user).first().value == 1:
                    # If existing like is + -> delete it
                    Likes.objects.filter(post=Post.objects.get(id=post_id), author=user).first().delete()
                else:
                    # If existing like is - -> change it to +
                    Likes.objects.filter(post=Post.objects.get(id=post_id), author=user).first().update(value='+1')
            # If like don't exists add +
            else:
                Likes.objects.create(post=Post.objects.get(id=post_id), author=user, value='+1')

        # - button
        elif ('post_likes_minus_button' in request.POST.keys()) and user.username:
            # Check if logged user like already exists
            if Likes.objects.filter(post=Post.objects.get(id=post_id), author=user).exists():
                if Likes.objects.filter(post=Post.objects.get(id=post_id), author=user).first().value == -1:
                    # If existing like is - -> delete it
                    Likes.objects.filter(post=Post.objects.get(id=post_id), author=user).first().delete()
                else:
                    # If existing like is + -> change it to -
                    Likes.objects.filter(post=Post.objects.get(id=post_id), author=user).first().update(value='-1')
            # If like don't exists add -
            else:
                Likes.objects.create(post=Post.objects.get(id=post_id), author=user, value='-1')

        # Comments likes button +
        elif ('comment_likes_plus_button' in request.POST.keys()) and user.username:
            # Checking if comment exists
            if Comments.objects.filter(id=int(request.POST['comment_likes_plus_button'])).exists():
                try:
                    # If like to this comment is + -> delete it
                    if CommentsLikes.objects.filter(comment=Comments.objects.get(
                            id=int(request.POST['comment_likes_plus_button'])), author=user).first().value == 1:
                        CommentsLikes.objects.filter(comment=Comments.objects.get(
                            id=int(request.POST['comment_likes_plus_button'])), author=user).first().delete()

                    # If like to this comment is - -> change it to +
                    else:
                        CommentsLikes.objects.filter(comment=Comments.objects.get(
                            id=int(request.POST['comment_likes_plus_button'])), author=user).first().update(value='+1')
                # If like to this comment don't exists -> add +
                except:
                    CommentsLikes.objects.create(comment=Comments.objects.get(
                        id=int(request.POST['comment_likes_plus_button'])), author=user, value='+1')

        # Comments likes button +
        elif ('comment_likes_minus_button' in request.POST.keys()) and user.username:
            # Checking if comment exists
            if Comments.objects.filter(id=int(request.POST['comment_likes_minus_button'])).exists():
                try:
                    # If like to this comment is - -> delete it
                    if CommentsLikes.objects.filter(comment=Comments.objects.get(
                            id=int(request.POST['comment_likes_minus_button'])), author=user).first().value == -1:
                        CommentsLikes.objects.filter(comment=Comments.objects.get(
                            id=int(request.POST['comment_likes_minus_button'])), author=user).first().delete()

                    # If like to this comment is + -> change it to -
                    else:
                        CommentsLikes.objects.filter(comment=Comments.objects.get(
                            id=int(request.POST['comment_likes_minus_button'])), author=user).first().update(value='-1')

                # If like to this comment don't exists -> add -
                except:
                    CommentsLikes.objects.create(comment=Comments.objects.get(
                        id=int(request.POST['comment_likes_minus_button'])), author=user, value='-1')

        # Accept comment button
        elif 'accept_comment_button' in request.POST.keys() and user.username:
            # If comment already exists -> update it
            try:
                Comments.objects.filter(id=int(request.POST['accept_comment_button'])).update(
                    content=request.POST['comment_content'])
            except:
                # In request.POST['accept_comment_button'] is id of comment which user is commenting
                # Add new Comment to Comment
                if request.POST['accept_comment_button']:
                    Comments.objects.create(post=Post.objects.get(id=post_id), comment=Comments.objects.filter(
                        id=int(request.POST['accept_comment_button'])).first(), author=user,
                                            content=request.POST['comment_content'])
                # Add new Comment to post (bcs HTML form don't sent comment id in request.POST['accept_comment_button'])
                else:
                    Comments.objects.create(post=Post.objects.get(id=post_id), author=user,
                                            content=request.POST['comment_content'])

        # Add comment button -> create new empty comment and set it to edit in next iteration
        elif 'add_comment_button' in request.POST.keys() and user.username:
            new_comment = Comments.objects.create(post=Post.objects.get(id=post_id), comment=Comments.objects.filter(
                id=request.POST['add_comment_button']).first(), author=user, content='', created=datetime.now())

            to_edit = str(new_comment.id)

        # Edit comment button -> if it's user's comment set it to edit
        elif 'edit_comment_button' in request.POST.keys() and user.username:
            to_edit = request.POST['edit_comment_button']

        # Delete comment button -> if it's user's comment delete it
        elif 'delete_comment_button' in request.POST.keys() and user.username:
            Comments.objects.filter(id=int(request.POST['delete_comment_button'])).delete()

        # Unlogged users cannot comment or like
        else:
            messages.info(request, "Tylko zalogowani użytkownicy mogą komentować oraz likować posty oraz komentarze")

    # Generate post data for content
    if post_model.objects.filter(id=post_id).exists():
        post = post_model.objects.get(id=post_id)
        if paragraph_model.objects.filter(post=post).exists():
            paragraphs = paragraph_model.objects.filter(post=post).order_by('paragraph_number').all()
        else:
            paragraphs = []

        # post_type from url
        if post_type == 'finished':
            # Count likes +
            if Likes.objects.filter(post=post, value='+1').exists():
                post_likes_plus = len(Likes.objects.filter(post=post, value='+1').all())
            else:
                post_likes_plus = 0
                # Count likes -
            if Likes.objects.filter(post=post, value='-1').exists():
                post_likes_minus = len(Likes.objects.filter(post=post, value='-1').all())
            else:
                post_likes_minus = 0

            # If user liked post get user's like value
            if user.username:
                if Likes.objects.filter(post=post, author=user).exists():
                    post_my_like = Likes.objects.filter(post=post, author=user).first().value
                else:
                    post_my_like = 0
            else:
                post_my_like = 0

            # Get comments to post
            # Create comments variable for content [CommentModel, likes+, likes-, mylike, [comments_to_this_comment]]
            comments = []
            # Checking if comments to this post exists
            if Comments.objects.filter(post=post, comment=None).exists():
                for main_comment in Comments.objects.filter(post=post, comment=None).order_by('created').all():
                    # Get likes + to this comment
                    if CommentsLikes.objects.filter(comment=main_comment, value='+1').exists():
                        comment_likes_plus = len(CommentsLikes.objects.filter(comment=main_comment, value='+1').all())
                    else:
                        comment_likes_plus = 0
                    # Get likes - to this comment
                    if CommentsLikes.objects.filter(comment=main_comment, value='-1').exists():
                        comment_likes_minus = len(CommentsLikes.objects.filter(comment=main_comment, value='-1').all())
                    else:
                        comment_likes_minus = 0

                    # Get logged user like if it exists
                    comment_my_like = 0
                    if user.username:
                        if CommentsLikes.objects.filter(comment=main_comment, author=user).exists():
                            comment_my_like = CommentsLikes.objects.filter(comment=main_comment,
                                                                           author=user).first().value
                    # Get comments to this comment
                    # Create comments_to_comment variable for content [CommentModel, likes+, likes-, mylike]
                    comments_to_comment = []
                    # Checking if comments to this comment exists
                    if Comments.objects.filter(post=post, comment=main_comment).exists():
                        for comment_to_comment in Comments.objects.filter(post=post, comment=main_comment).order_by(
                                'created').all():
                            # Get likes + to this comment
                            if CommentsLikes.objects.filter(comment=comment_to_comment, value='+1').exists():
                                comment_to_comment_likes_plus = len(CommentsLikes.objects.filter(
                                    comment=comment_to_comment, value='+1').all())
                            else:
                                comment_to_comment_likes_plus = 0
                            # Get likes - to this comment
                            if CommentsLikes.objects.filter(comment=comment_to_comment, value='-1').exists():
                                comment_to_comment_likes_minus = len(CommentsLikes.objects.filter(
                                    comment=comment_to_comment, value='-1').all())
                            else:
                                comment_to_comment_likes_minus = 0

                            # Get logged user like if it exists
                            comment_to_comment_my_like = 0
                            if user.username:
                                if CommentsLikes.objects.filter(comment=comment_to_comment, author=user).exists():
                                    comment_to_comment_my_like = CommentsLikes.objects.filter(comment=comment_to_comment,
                                                                                              author=user).first().value
                            # Add actual comment to comments_to_comment variable
                            comments_to_comment.append({'comment_to_comment': comment_to_comment,
                                                        'comment_to_comment_likes_plus': comment_to_comment_likes_plus,
                                                        'comment_to_comment_likes_minus': comment_to_comment_likes_minus,
                                                        'comment_to_comment_my_like': comment_to_comment_my_like})

                    # Add actual comment to comments variable
                    comments.append({'comment': main_comment, 'comment_likes_plus': comment_likes_plus,
                                     'comment_likes_minus': comment_likes_minus, 'comment_my_like': comment_my_like,
                                     'comments_to_comment': comments_to_comment})

            # Create content variable for render template
            content = {'user': user, 'posts_menu': posts_menu, 'new_messages': new_messages,
                       'post': post, 'paragraphs': paragraphs, 'post_type': post_type,
                       'comments': comments, 'post_my_like': post_my_like,
                       'post_likes_plus': post_likes_plus, 'post_likes_minus': post_likes_minus}

            # Add edit option to content if exists
            if 'to_edit' in locals():
                content['to_edit'] = int(to_edit)

        # If post is unfinished create content variable without comments and likes
        else:
            content = {'user': user, 'posts_menu': posts_menu, 'new_messages': new_messages,
                       'post': post, 'paragraphs': paragraphs,
                       'post_type': post_type, 'comments': [], 'post_my_like': 0,
                       'post_likes_plus': 0, 'post_likes_minus': 0}

        return render(request, 'post_page.html', {'content': content})

    # Post with id from url don't exists
    else:
        messages.info(request, 'Post o podanym id nie istnieje')
        return redirect('/')


# POSTS PAGE
def posts(request):
    # Get user and posts list
    user = auth.get_user(request)
    posts_menu = Post.objects.order_by('-created').all()

    # Check if user have new messages
    if user.username:
        new_messages = len(Messages.objects.filter(reciver=user, seen=False))
    else:
        new_messages = False

    filters = {}
    # Buttons service
    if request.method == 'POST':
        for key in request.POST.keys():
            # Get filter options from HTML form. If its not empty modify iy and add to filters dict
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

    # Default sorting parameter
    order_by = '-created'
    '''# Get sorting parameter from HTML form ( sorting by likes and comments will be performed later)
    if 'order_by' in request.POST.keys():
        if request.POST['order_by'] not in ['likes', 'comments', '-likes', '-comments']:
            order_by = request.POST['order_by']'''

    # Get posts list with filters and ordered
    posts = Post.objects.filter(**filters).order_by(order_by).all()

    # Extend posts list by comments and likes count
    posts_extended = []
    for post in posts:
        dictionary = {'post_model': post, 'comments': len(Comments.objects.filter(post=post).all()),
                      'likes': len(Likes.objects.filter(post=post, value=1).all())}
        posts_extended.append(dictionary)

    """# Order by comments or likes
    if 'order_by' in request.POST.keys():
        order_by = request.POST['order_by']
        if request.POST['order_by'] == 'likes':
            posts_extended = sorted(posts_extended, key=lambda k: k['likes'])
        elif request.POST['order_by'] == '-likes':
            posts_extended = sorted(posts_extended, key=lambda k: k['likes'], reverse=True)
        elif request.POST['order_by'] == 'comments':
            posts_extended = sorted(posts_extended, key=lambda k: k['comments'])
        elif request.POST['order_by'] == '-comments':
            posts_extended = sorted(posts_extended, key=lambda k: k['comments'], reverse=True)"""

    # Updated sorting alfanumerical sorting method -> functions
    if 'order_by' in request.POST.keys():
        order_by = request.POST['order_by']
        if request.POST['order_by'] not in ['likes', 'comments', '-likes', '-comments']:
            posts_extended = my_sort(order_by, posts_extended, 'post_model')
        else:
            posts_extended = my_sort(order_by, posts_extended)

    # Create different filters['author_in'] display form to show in HTML form on site
    if 'author' in request.POST.keys():
        filters['author__in'] = request.POST['author']

    # Create content variable for render template
    column_names = ['id', 'title', 'description', 'author', 'likes', 'comments', 'created']
    content = {'user': user, 'posts_menu': posts_menu, 'new_messages': new_messages,
               'filters': filters, 'order_by': order_by, 'column_names': column_names,
               'posts': posts_extended}

    return render(request, 'posts_page.html', {'content': content})


# MESSAGES LIST PAGE
def msgs(request):
    # Get user and posts list
    user = auth.get_user(request)
    posts_menu = Post.objects.order_by('-created').all()

    # Check if user have new message
    if user.username:
        new_messages = len(Messages.objects.filter(reciver=user, seen=False))
    else:
        new_messages = False

    # If user is logged create list of authors which correspond with user
    if user.username:
        # Get list of all messages send or recived by user
        # messages_list [corresponding_person (not user), seen, date, content, who_send_it]
        messages_list = [[message.reciver, message.seen, message.created, message.content, message.sender]
                         if message.sender.id == user.id else
                         [message.sender, message.seen, message.created, message.content, message.sender]
                         for message in Messages.objects.filter(Q(reciver=user) | Q(sender=user)).order_by('-created')]

        messagers = []
        persons = []
        for message in messages_list:
            # Create list of uniqe corrensponding persons (list of contacts) with additional infos about last message
            if not message[0] in persons:
                persons.append(message[0])
                messagers.append({'author': message[0], 'seen': message[1], 'created': message[2],
                                  'content': message[3], 'message_sender': message[4]})

        # Create content variable to render template
        content = {'user': user, 'posts_menu': posts_menu, 'new_messages': new_messages, 'messagers': messagers}
        return render(request, 'messages_page.html', {'content': content})

    # Unlogged user
    else:
        messages.info(request, 'Ta opcja wymaga zalogowanego użytkownika')
        return redirect(request, '/')


# SEND MESSAGE PAGE - merged into MESSAGEs PAGE
def send_message(request, author):
    # Get user and posts list
    user = auth.get_user(request)
    posts_menu = Post.objects.order_by('-created').all()

    # Check if user have new messages
    if user.username:
        new_messages = len(Messages.objects.filter(reciver=user, seen=False))
    else:
        new_messages = False

    # Copy of code from msgs() bcs this page is merged into msgs page
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
        # End of copied code

        # Get corresponding author from url
        author_object = User.objects.get(username=author)
        # Corresponding author is different from logged user
        if user != author_object:
            # Button service
            if request.method == 'POST':
                # Create new message from user to author from url
                if 'send_message_button' in request.POST.keys():
                    Messages.objects.create(sender=user, reciver=author_object, content=request.POST['message_content'],
                                            created=datetime.now())

            # messages = [{'sender': message['sender'], 'reciver':message['reciver'], 'content':message['content'], 'seen':message['seen'], 'created':message['created']} for message in Messages.objects.filter(Q(reciver=user) & Q(sender=author_object) | Q(sender=user) & Q(reciver=author_object).order_by('created').values('sender', 'reciver', 'seen', 'created', content)

            # Get list of all messages between user and author from url ordered by date
            messages_between = Messages.objects.filter(Q(sender=user) & Q(reciver=author_object) |
                                                       Q(sender=author_object) & Q(reciver=user)).order_by('created')

            # Create content variable to render template
            content = {'user': user, 'posts_menu': posts_menu, 'new_messages': new_messages, 'messagers': messagers,
                       'messages': messages_between, 'author': author}

            messages_between.filter(reciver=user).update(seen=True)
            return render(request, 'send_message_page.html', {'content': content})

        # User tried send msgs to himself
        else:
            messages.info(request, 'Nie możesz wysłać wiadomości sam do siebie')
            return redirect('/')
    # Unlogged user
    else:
        messages.info(request, 'Ta opcja wymaga zalogowanego użytkownika')
        return redirect('/')


# AUTHORS PAGE
def authors(request):
    # Get user and posts list
    user = auth.get_user(request)
    posts_menu = Post.objects.order_by('-created').all()

    # Check if use have new messages
    if user.username:
        new_messages = len(Messages.objects.filter(reciver=user, seen=False))
    else:
        new_messages = False

    # Create list of all authors
    authors_list = []
    author_list = User.objects.order_by('username').all()

    # Buttons sservice
    if request.method == 'POST':
        # If search button is in HTML form modify authors list to authors names contain given string
        if 'search_author_button' in request.POST:
            author_list = User.objects.filter(username__contains=request.POST['search_author']).order_by(
                'username').all()

    # Extend author list with post and comments count
    for user_from_list in author_list:
        authors_list.append({'user': user_from_list, 'post_count': len(Post.objects.filter(author=user_from_list)),
                            'comments_count': len(Comments.objects.filter(author=user_from_list))})

    # Create content variable to render template
    content = {'user': user, 'posts_menu': posts_menu, 'new_messages': new_messages, 'users': authors_list}
    return render(request, 'authors_page.html', {'content': content})


# AUTHOR PAGE
def author(request, username):
    # get user and posts list
    user = auth.get_user(request)
    posts_menu = Post.objects.order_by('-created').all()

    # Check if user have new messages
    if user.username:
        new_messages = len(Messages.objects.filter(reciver=user, seen=False))
    else:
        new_messages = False

    # Button service
    if request.method == 'POST' and user.get_username() == username:
        # Deleting user's posts
        if 'delete_unfinished_post_button' in request.POST.keys():
            PostUnfinished.objects.filter(id=request.POST['delete_unfinished_post_button']).delete()

        elif 'delete_finished_post_button' in request.POST.keys():
            Post.objects.filter(id=request.POST['delete_finished_post_button']).delete()

    # Author with username from url does not exists
    if not User.objects.filter(username=username).exists():
        messages.info(request, 'Nie istnieje użytkownik o wpisanej nazwie')
        return redirect('/authors')

    # Create content variable to render template
    author = User.objects.filter(username=username).first()
    content = {'user': user, 'posts_menu': posts_menu, 'new_messages': new_messages,
               'author': author, 'post_count': len(Post.objects.filter(author=author)),
               'comments_count': len(Comments.objects.filter(author=author))}

    # If author from url is user -> show unfinished posts
    if user == author:
        unfinishedposts = PostUnfinished.objects.filter(author=author)
        content['unfinished_posts'] = unfinishedposts

    # Add author's from the url posts to content
    posts = []
    post_list = Post.objects.filter(author=author)
    # Extend posts list by comments and likes count
    for post in post_list:
        posts.append({'post': post, 'comments_count': len(Comments.objects.filter(post=post)), 'likes_plus': len(Likes.objects.filter(post=post, value='+1')), 'likes_minus': len(Likes.objects.filter(post=post, value='-1'))})
    content['posts'] = posts

    return render(request, 'author_page.html', {'content': content})

