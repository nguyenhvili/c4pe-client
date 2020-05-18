from django.http import HttpResponse
from django.shortcuts import render, redirect
from .auth import get_user, authorized
from django.contrib import messages
from django.views.decorators.http import require_http_methods
import requests
import json
from datetime import datetime


def index(request, place_id):
    place = json.loads(requests.get('http://77.244.251.110/api/places/' + place_id).text)
    owners_id = place['owners']
    owners = []
    for i in owners_id:
        owners.append(json.loads(requests.get('http://77.244.251.110/api/users/' + str(i['userID'])).text))
    return render(request, 'owners/index.html',
                  {
                      'place': place,
                      'owners': owners,
                      'currentUser': get_user(request),
                  })


@require_http_methods(['POST'])
def create(request, place_id):
    username = request.POST.get('username')
    headers = {
        'content-type': 'application/json',
        'Authorization': 'Bearer ' + request.COOKIES['token']
    }
    data = {
        'username': username
    }
    response = requests.post('http://77.244.251.110/api/places/' + place_id + '/owner', data=data, headers=headers)

    if response.status_code == 200:
        messages.success(request, 'Owner added')
    else:
        messages.error(request, response)
    return redirect('owners')


@require_http_methods(['POST'])
def delete(request, place_id, user_id):
    headers = {
        'content-type': 'application/json',
        'Authorization': 'Bearer ' + request.COOKIES['token']
    }
    response = requests.delete('http://77.244.251.110/api/places/' + place_id + '/owner/' + user_id, headers=headers)

    if response.status_code == 200:
        messages.success(request, 'Owner removed')
    else:
        messages.error(request, response)
    return redirect('owners')