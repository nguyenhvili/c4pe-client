from django.http import HttpResponse
from django.shortcuts import render, redirect
from .auth import get_user, authorized
import requests
import json
from datetime import datetime

# Create your views here.


def index(request):
    page = request.GET.get('page')
    if page is None:
        page = '1'
    response = requests.get('http://77.244.251.110/api/places?PageNumber=' + page)
    types = json.loads(requests.get('http://77.244.251.110/api/placetypes').text)
    places = json.loads(response.text)
    current = json.loads(response.headers['X-Pagination'])['CurrentPage']
    last = json.loads(response.headers['X-Pagination'])['TotalPages']
    pages = {}
    pages['current'] = int(current)

    current_hour = int(datetime.now().hour)
    current_minute = int(datetime.now().minute)

    """
    SOMEHOW THIS SHIT WORKS
    It appends new index to dict which tells if restaurant is opening/closing/opened/closed
    """
    for place in places:
        for time in place['openingTimes']:
            place['open'] = {}
            open_minute = int(time['open'][3:5])
            open_hour = int(time['open'][0:2])
            close_minute = int(time['close'][3:5])
            close_hour = int(time['close'][0:2])

            if int(time['day']) == int(datetime.today().weekday()):
                if open_hour < current_hour < close_hour:
                    place['open']['state'] = 1
                    if 0 <= close_hour - current_hour < 2:
                        place['open']['state'] = 2
                        place['open']['time'] = time['close'][0:5]
                elif open_hour == current_hour:
                    if open_minute < current_minute:
                        place['open']['state'] = 1
                        if 0 <= close_hour - current_hour < 2:
                            place['open']['state'] = 2
                            place['open']['time'] = time['close'][0:5]
                    else:
                        place['open']['state'] = 4
                        if 0 <= open_hour - current_hour < 2:
                            place['open']['state'] = 3
                            place['open']['time'] = time['open'][0:5]
                elif close_hour == current_hour:
                    if close_minute > current_minute:
                        place['open']['state'] = 1
                        if 0 <= close_hour - current_hour < 2:
                            place['open']['state'] = 2
                            place['open']['time'] = time['close'][0:5]
                    else:
                        place['open']['state'] = 4
                        if 0 <= open_hour - current_hour < 2:
                            place['open']['state'] = 3
                            place['open']['time'] = time['open'][0:5]
                elif open_hour > current_hour or close_hour < current_hour:
                    place['open']['state'] = 4
                    if 0 <= open_hour - current_hour < 2:
                        place['open']['state'] = 3
                        place['open']['time'] = time['open'][0:5]
                break

    #  pagination
    if current == 1:
        pages['content'] = [1, 2, 3]
        pages['first'] = True
    elif current == last:
        pages['content'] = [last - 2, last - 1, last]
        pages['last'] = True
    else:
        pages['content'] = [current - 1, current, current + 1]
    #  pagination

    return render(request, 'places/index.html',
                  {
                      'places': places,
                      'pages': pages,
                      'types': types,
                      'currentUser': get_user(request)
                  })


def profile(request, id):
    place = json.loads(requests.get('http://77.244.251.110/api/places/' + id).text)
    reviews = json.loads(requests.get('http://77.244.251.110/api/places/' + id + '/Reviews').text)

    if len(reviews) > 5:
        reviews = reviews[len(reviews) - 6:len(reviews) - 1]

    return render(request, 'places/profile.html',
                  {
                      'place': place,
                      'reviews': reviews,
                      'currentUser': get_user(request)
                  })


def create(request):
    if request.method == 'GET':
        types = json.loads(requests.get('http://77.244.251.110/api/placetypes').text)
        return render(request, 'places/create.html',
                      {
                          'types': types,
                          'currentUser': get_user(request)
                      })
    elif request.method == 'POST':
        headers = {
            'content-type': 'application/json',
            'Authorization': 'Bearer ' + request.COOKIES['token']
        }
        data = {
            "street": request.POST.get("street"),
            "city": request.POST.get("city"),
            "zipCode": request.POST.get("zipCode"),  # TODO: not required
            "country": request.POST.get("country"),
            "name": request.POST.get("name"),
            "placeTypeID": int(request.POST.get("type"))
        }
        response = requests.post('http://77.244.251.110/api/places', data=json.dumps(data), headers=headers)
        if response.status_code == 201:
            return redirect('places')  # TODO: message - place created
        else:
            types = json.loads(requests.get('http://77.244.251.110/api/placetypes').text)
            return render(request, 'places/create.html',
                      {
                          'types': types,
                          'currentUser': get_user(request)  # TODO: form validation error
                      })


def edit(request, id):
    if request.method == 'GET':
        types = json.loads(requests.get('http://77.244.251.110/api/placetypes').text)
        place = json.loads(requests.get('http://77.244.251.110/api/places/' + id).text)
        return render(request, 'places/edit.html',
                      {
                          'types': types,
                          'place': place,
                          'currentUser': get_user(request)
                      })
    elif request.method == 'POST':
        headers = {
            'content-type': 'application/json',
            'Authorization': 'Bearer ' + request.COOKIES['token']
        }
        data = {
            "street": request.POST.get("street"),
            "city": request.POST.get("city"),
            "zipCode": request.POST.get("zipCode"),
            "country": request.POST.get("country"),
            "name": request.POST.get("name"),
            "placeTypeID": int(request.POST.get("type"))
        }
        response = requests.put('http://77.244.251.110/api/places/' + id, data=json.dumps(data), headers=headers)
        if response.status_code == 201:
            return redirect('places')  # TODO: message - place edited/saved
        else:
            types = json.loads(requests.get('http://77.244.251.110/api/placetypes').text)
            return render(request, 'places/edit.html',
                          {
                              'types': types,
                              'currentUser': get_user(request)  # TODO: form validation error
                          })


def get_json_reviews(request, id, type):
    reviews = json.loads(requests.get('http://77.244.251.110/api/places/' + id + '/Reviews').text)
    response_reviews = []
    for review in reviews:
        if int(type) == 1:  # all
            return HttpResponse(json.dumps(reviews))
        elif int(type) == 2:  # positive
            if review['rating'] > 2:
                response_reviews.append(review)
        elif int(type) == 3:  # negative
            if review['rating'] < 3:
                response_reviews.append(review)
        elif int(type) == 4:  # verified
            if review['user']['isVerified']:
                response_reviews.append(review)
    return HttpResponse(json.dumps(response_reviews))  # REQUIRED TO BE HTTP RESPONSE
