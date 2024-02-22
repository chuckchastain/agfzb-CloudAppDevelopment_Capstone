from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
# from .models import related models
from .models import CarModel, CarMake, CarDealer, DealerReview
# from .restapis import related methods
from .restapis import get_dealers_from_cf, get_dealer_by_id_from_cf, get_dealer_reviews_from_cf, post_request, analyze_review_sentiments
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import datetime
import logging
import json

# Get an instance of a logger
logger = logging.getLogger(__name__)


# Create your views here.


# Create an `about` view to render a static about page
def about(request):
    context = [{}]
    if request.method == 'GET':
        return render(request, 'djangoapp/about.html', context)

# ...


# Create a `contact` view to return a static contact page
#def contact(request):
def contact(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'djangoapp/contact.html', context)


# Create a `login_request` view to handle sign in request
# def login_request(request):
# ...
def login_request(request):
    context = {}
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('djangoapp:index')
        else:
            return render(request, 'djangoapp/index.html', context)
    else:
        return render(request, 'djangoapp/index.html', context)


# Create a `logout_request` view to handle sign out request
# def logout_request(request):
# ...
def logout_request(request):
    if request.method == "GET":
        print("Logging out the user '{}'".format(request.user.username))
        logout(request)
    return redirect('djangoapp:index')

# Create a `registration_request` view to handle sign up request
# def registration_request(request):
# ...
def registration_request(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'djangoapp/registration.html', context)
    elif request.method == 'POST':
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            User.objects.get(username=username)
            user_exist = True
        except:
            logger.error("New user")
        if not user_exist:
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            user.is_superuser = True
            user.is_staff = True
            user.save()
            login(request, user)
            return redirect("/djangoapp:Index")
        else:
            context['message'] = "User already exists."
            return redirect('djangoapp:registration')

# Update the `get_dealerships` view to render the index page with a list of dealerships
#def get_dealerships(request):
#    context = {}
#    if request.method == "GET":
#        return render(request, 'djangoapp/index.html', context)
    
def get_dealerships(request):
    if request.method == "GET":
        context = {}
        url = "http://localhost:3000/dealerships/get"
        # Get dealers from the URL
        dealerships = get_dealers_from_cf(url)
        # Concat all dealer's short name
        #dealer_names = ' '.join([dealer.short_name for dealer in dealerships])
        # Return a list of dealer short name
        context["dealership_list"] = dealerships
        return render(request, 'djangoapp/index.html', context)

# Create a `get_dealer_details` view to render the reviews of a dealer
# def get_dealer_details(request, dealer_id):
# ...


def get_dealer_details(request, id):
    print("enter get_dealer_details")
    if request.method == "GET":
        context = {}
        print(f"get_dealer_details request is: {request}")
        print(f"id is: {id}")
        dealer_url = "http://localhost:3000/dealerships/get"
        print("calling get_dealer_by_id_from_cf")
        dealer = get_dealer_by_id_from_cf(dealer_url, id=id)
        print(f"Dealer is: {dealer}")
        context["dealer"] = dealer
    
        review_url = "http://localhost:5000/api/get_reviews"
        print("calling get_dealer_reviews from_cf")
        reviews = get_dealer_reviews_from_cf(review_url, id=id)
        print(f"Reviews list is: {reviews}")
        context["reviews"] = reviews
        print('context for dealer_details', context)
        return render(request, 'djangoapp/dealer_details.html', context)
    
    

# Create a `add_review` view to submit a review
# def add_review(request, dealer_id):
# ...
"""""
def add_review(request, id):
    context = {}
    url = "http://localhost:3000/dealerships/get"
    dealer = get_dealer_by_id_from_cf(url, id=id)
    context["dealer"] = dealer
    if request.method == 'GET':
        # Get cars for the dealer
        cars = CarModel.objects.all()
        print(cars)
        context["cars"] = cars
        
        return render(request, 'djangoapp/add_review.html', context)
    elif request.method == 'POST':
        if request.user.is_authenticated:
            username = request.user.username
            print(request.POST)
            payload = dict()
            car_id = request.POST["car"]
            car = CarModel.objects.get(pk=car_id)
            payload["time"] = datetime.utcnow().isoformat()
            payload["name"] = username
            payload["dealership"] = id
            payload["id"] = id
            payload["review"] = request.POST["content"]
            payload["purchase"] = False
            if "purchasecheck" in request.POST:
                if request.POST["purchasecheck"] == 'on':
                    payload["purchase"] = True
            payload["purchase_date"] = request.POST["purchasedate"]
            payload["car_make"] = car.car_make
            payload["car_model"] = car.name
            payload["car_year"] = int(car.year.strftime("%Y"))

            new_payload = {}
            new_payload["review"] = payload
            review_post_url = "http://localhost:5000/api/post_review"

            review = {
                "id":id,
                "time":datetime.utcnow().isoformat(),
                "name":request.user.username,  # Assuming you want to use the authenticated user's name
                "dealership" :id,                
                "review": request.POST["content"],  # Extract the review from the POST request
                "purchase": True,  # Extract purchase info from POST
                "purchase_date":request.POST["purchasedate"],  # Extract purchase date from POST
                "car_make": car.car_make,  # Extract car make from POST
                "car_model": car.name,  # Extract car model from POST
                "car_year": int(car.year.strftime("%Y")),  # Extract car year from POST
            }
            review=json.dumps(review,default=str)
            new_payload1 = {}
            new_payload1["review"] = review
            print("\nURL:", review_post_url)
            print("\nREVIEW:",review)
            print("\nID:",id)
            post_request(review_post_url, review, id = id)
        return redirect("djangoapp:dealer_details", id = id)
    
    """
@login_required
def add_review(request, id):
    context = {}
    url = "http://localhost:3000/dealerships/get"
    dealer = get_dealer_by_id_from_cf(url, id=id)
    context["dealer"] = dealer

    if request.method == 'GET':
        # Get cars for the dealer
        cars = CarModel.objects.all()
        print(cars)
        context["cars"] = cars
        return render(request, 'djangoapp/add_review.html', context)

    elif request.method == 'POST':
        if request.user.is_authenticated:
            username = request.user.username
            car_id = request.POST.get("car")
            car = CarModel.objects.get(pk=car_id)

            payload = {
                "time": datetime.utcnow().isoformat(),
                "name": username,
                "dealership": id,
                "id": id,
                "review": request.POST.get("content"),
                "purchase": request.POST.get("purchasecheck") == 'on',
                "purchase_date": request.POST.get("purchasedate"),
                "car_make": car.car_make,
                "car_model": car.name,
                "car_year": int(car.year.strftime("%Y")),
            }
            new_payload ={"review": payload}
            review_post_url = "http://localhost:5000/api/post_review"


            print("\nURL:", review_post_url)
            print("\nnew_payload:", new_payload)
            print("\nID:", id)

            post_request(review_post_url, new_payload, id=id)

        return redirect("djangoapp:dealer_details", id=id)

    