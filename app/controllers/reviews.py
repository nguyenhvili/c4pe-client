from django.http import HttpResponse
from django.shortcuts import render, redirect
from .auth import get_user, authorized
import requests
import json
from datetime import datetime


def index(request, id):
    place = json.loads(requests.get('http://77.244.251.110/api/places/' + id).text)
    reviews = json.loads(requests.get('http://77.244.251.110/api/places/' + id + '/Reviews').text)

    positive = 0
    negative = 0
    verified = 0
    for review in reviews:
        if review['rating'] < 3:
            negative = negative + 1
        elif review['rating'] > 2:
            positive = positive + 1
        if review['user']['isVerified']:
            verified = verified + 1
    return render(request, 'reviews/index.html',
                  {
                      'place': place,
                      'reviews': reviews,
                      'positive': positive,
                      'negative': negative,
                      'verified': verified,
                      'currentUser': get_user(request)
                  })


def create(request, id):
    if request.method == 'GET':
        return render(request, 'reviews/create.html',
                      {
                          'currentUser': get_user(request)
                      })
    elif request.method == 'POST':
        data = {
            'rating': int(request.POST.get('rating')),
            'text': str(request.POST.get('text'))
        }
        headers = {
            'content-type': 'application/json',
            'Authorization': 'Bearer ' + request.COOKIES['token']
        }
        response = requests.post('http://77.244.251.110/api/places/' + id + '/Reviews', data=json.dumps(data),
                                 headers=headers)
        if response.status_code == 201:
            return redirect('reviews', id=id)  # TODO: review added
        else:
            return render(request, 'reviews/create.html',  # TODO: form validation error
                          {
                              'currentUser': get_user(request)
                          })


def edit(request, place_id, id):
    if request.method == 'GET':
        review = json.loads(requests.get('http://77.244.251.110/api/places/' + place_id + '/Reviews/' + id).text)
        return render(request, 'reviews/edit.html',
                      {
                          'review': review,
                          'currentUser': get_user(request)
                      })
    elif request.method == 'POST':
        data = {
            'rating': int(request.POST.get('rating')),
            'text': str(request.POST.get('text')),
        }
        headers = {
            'content-type': 'application/json',
            'Authorization': 'Bearer ' + request.COOKIES['token']
        }
        response = requests.put('http://77.244.251.110/api/places/' + place_id + '/Reviews/' + id, data=json.dumps(data), headers=headers)
        if response.status_code == 201:
            return redirect('reviews', id=place_id)  # TODO: review edited
        else:
            return render(request, 'reviews/edit.html',  # TODO: form validation error
                          {
                              'currentUser': get_user(request)
                          })
