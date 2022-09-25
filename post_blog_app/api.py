from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.forms.models import model_to_dict
from django.contrib.auth.models import User, auth
from random import randint
from datetime import datetime, timedelta

from json import loads, dumps

from post_blog_app import models


def models_to_dict(list_of_models):
    json = []
    for model in list_of_models:
        json.append(model_to_dict(model))
    return json


# My apis
@csrf_exempt
def user_to_confirm_post(request):
    if request.method == 'POST':
        response = request.POST.dict()
        code = randint(1000, 9999)
        response['code'] = code
        response['valid_time'] = datetime.now() + timedelta(hours=1)

        new_user = models.UserToConfirm(**response)
        new_user.save()
        return JsonResponse(response, safe=False, status=201)


@csrf_exempt
def user_to_confirm_get(request):
    if request.method == 'GET':
        parameters = loads(request.headers.get('parameters'))
        if models.UserToConfirm.objects.filter(**parameters).exists():
            user = models.UserToConfirm.objects.get(**parameters)

            data = model_to_dict(user)

            return JsonResponse(data, safe=False)
        else:
            return JsonResponse({'message': f'User with that parameters {parameters} does not exists'}, safe=False, status=404)


@csrf_exempt
def user_to_confirm_get_all(request):
    if request.method == 'GET':
        parameters = loads(request.headers.get('parameters'))
        users = models.UserToConfirm.objects
        if parameters:
            users = users.filter(**parameters)
        if request.headers.get('order_by'):
            users = users.order_by(request.headers.get('order_by'))
        """
        if request.headers.get('filter_by') != None and request.headers.get('filter') != None:
            f = {request.headers.get('filter_by'): request.headers.get('filter')}
            users = users.filter(**f)
        """
        users = users.all()

        if users:
            data = models_to_dict(users)
            return JsonResponse(data, safe=False)
        else:
            return JsonResponse({'message': f'There are not users with parameters: {parameters}'}, safe=False,
                                status=404)


@csrf_exempt
def user_to_confirm_delete(request):
    if request.method == 'DELETE':
        if models.UserToConfirm.objects.filter(login=request.headers.get('login')).exists():
            user = models.UserToConfirm.objects.get(login=request.headers.get('login'))
            user.delete()

            return JsonResponse({'message': f'Deleted {request.headers.get("login")} user'}, safe=False)
        else:
            return JsonResponse({'message': f'User {request.headers.get("login")} does not exists'}, safe=False, status=404)


@csrf_exempt
def user_to_confirm_update(request):
    if request.method == 'PATCH':
        if models.UserToConfirm.objects.filter(id=request.headers.get('id')).exists():
            user = models.UserToConfirm.objects.get(id=request.headers.get('id'))
            for key in ['login', 'email', 'code', 'valid_time']:
                if key in request.headers.keys():
                    user.__setattr__(key, request.headers.get(key))
            user.save()

            return JsonResponse(user, safe=False)
        else:
            return JsonResponse({'message': f'User with id {request.headers.get("id")} does not exists'}, safe=False)


# User
@csrf_exempt
def user_post(request):
    if request.method == 'POST':
        response = request.POST.dict()


        user = User.objects.create_user(username=response.login,
                                        email=response.email,
                                        password=response.password)
        user.save();

        return JsonResponse(user, safe=False, status=201)
