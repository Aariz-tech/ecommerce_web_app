from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import *
import json
import datetime
from . utils import cookieCart, cartData, guestOrder
from django.http import HttpResponse
from django.contrib.auth.hashers import make_password, check_password

# Create your views here.

def store(request):
	data = cartData(request)
	cartItems = data['cartItems']
	
	products = Product.objects.all()
	context = {
		'products':products,
		'cartItems':cartItems
	}
	return render(request, 'store/store.html', context)

def cart(request):
	data = cartData(request)
	cartItems = data['cartItems']
	order = data['order'] 
	items = data['items']

	context = {'items':items, 'order':order, 'cartItems':cartItems}
	return render(request, 'store/cart.html', context)


from django.views.decorators.csrf import csrf_exempt
@csrf_exempt
def checkout(request):
	
	data = cartData(request)
	cartItems = data['cartItems']
	order = data['order'] 
	items = data['items'] 

	context = {'items':items, 'order':order, 'cartItems':cartItems}
	return render(request, 'store/checkout.html', context)

def updateItem(request):
	data = json.loads(request.body)
	productId = data['productId']
	action = data['action']
	print('Action:', action)
	print('productId', productId)

	customer = request.user.customer 
	product = Product.objects.get(id=productId)
	order, created = Order.objects.get_or_create(customer=customer,complete=False)
	orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)
	if action == 'add':
		orderItem.quantity = (orderItem.quantity + 1)
	elif action == 'remove':
		orderItem.quantity = (orderItem.quantity - 1)
	orderItem.save()
	if orderItem.quantity <= 0:
		orderItem.delete()

	return JsonResponse('Item was Added', safe=False)


def processOrder(request):
	transaction_id = datetime.datetime.now().timestamp()
	data = json.loads(request.body)

	if request.user.is_authenticated:
		customer = request.user.customer 
		order, created = Order.objects.get_or_create(customer=customer,complete=False)
		
		


	else:
		customer, order = guestOrder(request,data)
		

	total = float(data['form']['total'])
	order.transaction_id = transaction_id

	if total == float(order.get_cart_total):
		order.complete = True 

	order.save()

	if order.shipping == True:
		ShippingAddress.objects.create(
			customer = customer,
			order = order,
			address = data['shipping']['address'],
			city = data['shipping']['city'],
			state = data['shipping']['state'],
			zipcode = data['shipping']['zipcode'],
				

			)

	return JsonResponse('Payment Submitted..', safe=False)




def validateCustomer(customer):
	error_message = None
	if(not customer.first_name):
			error_message = 'First Name Required!!'
	elif not customer.last_name:
		error_message = 'Last Name Required!!'

	elif not customer.phone:
		error_message = 'Phone Number Required!!'

		
	elif customer.isExists():
		error_message = "Email Address Already Registered!"

	return error_message



def registerUser(request):

	postData = request.POST 
	first_name = postData.get('firstname')
	last_name = postData.get('lastname')
	phone = postData.get('phone') 
	email = postData.get('email')
	password = postData.get('password')
		#Validation 

	value = {
		'first_name':first_name,
		'last_name':last_name,
		'phone':phone, 
		'email':email
	}
	error_message = None
	customer = CustomerInfo(first_name=first_name, last_name=last_name,
			phone=phone,
			email=email,
			password=password

			)
		
		

		#Saving
	error_message = validateCustomer(customer)
	if not error_message:
		customer.password = make_password(customer.password)
			
		customer.register()
		return redirect("store")
	else:
		data = {
			'error':error_message,
			'value':value
		}
		return render(request, 'store/signup.html', data)



def signup(request):
	if request.method == "GET":
		return render(request,'store/signup.html')
	else:
		return registerUser(request)

def login(request):
	if request.method == 'GET':
		return render(request, 'store/login.html')
	else:
		email = request.POST.get('email')
		password = request.POST.get('password')
		customer = CustomerInfo.get_customer_by_email(email)
		error_message = None 
		if customer:
			flag = check_password(password, customer.password) 
			if flag:
				return redirect("store") 
			else:
				error_message = 'Email or Password Invalid!!!'
		else:
			error_message = 'Email or Password Invalid!!!'
		return render(request, 'store/login.html', {'error':error_message})

		
def aboutus(request):
	return render(request, "store/aboutus.html")