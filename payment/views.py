import json
import stripe
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse,HttpResponse
from django.views.decorators.csrf import csrf_exempt 
from django.views.generic import TemplateView,View
from .models import Product


# Get secret key from env
stripe.api_key = settings.STRIPE_SECRET_KEY

# Get webhook secret
endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

# Success page after successfull payment
class SuccessView(TemplateView):
    template_name = "success.html"

# Cancel page after cancel payment
class CancelView(TemplateView):
    template_name = "cancel.html"


#Payment checkout page
class ProductLandingPageView(TemplateView):
    template_name = "landing.html"
    # Send product object and stripe public key to html page
    def get_context_data(self, **kwargs):
        product = Product.objects.get(id=1)
        context = super(ProductLandingPageView, self).get_context_data(**kwargs)
        context.update({
            "product": product,
            "STRIPE_PUBLIC_KEY": settings.STRIPE_PUBLIC_KEY
        })
        return context


# for single button checkout and redirect to stripe
class CreateCheckoutSessionView(View):
    # restrict get method
    def get(self, request,*args,**kwargs):
       return HttpResponse('Get method not allowed')

    # create checkout session when checkout button clicked
    def post(self,request,*args,**kwargs):
        product_id = self.kwargs["pk"]
        product = Product.objects.get(id=product_id)
        YOUR_DOMAIN = 'http://localhost:8000'
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'inr',
                        'unit_amount': product.stripe_price(),
                        'product_data': {
                            'name': product.name,
                            'images': ['https://i.imgur.com/EHyR2nP.png'],
                        },
                    },
                    'quantity': 1,
                },
            ],
            metadata={
                "product_id": product.id
            },
            mode='payment',
            success_url=YOUR_DOMAIN + '/success/',
            cancel_url=YOUR_DOMAIN + '/cancel',
        )
        return JsonResponse({
            'id': checkout_session.id
            })
    

#stripe webhook to get event while payment
@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    #try to get event otherwise raise error
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    #if payment successful and checkout session completed send email to customer
    if event['type'] == 'checkout.session.completed':
        #grab session from event which was started by create-checkout-session
        session = event['data']['object']

        # Fulfill the purchase...
        # fulfill_order(session)
        #grab customer email from session
        customer_email = session['customer_details']['email']

        #grab product id from metadata of session which was sent by checkout page 
        product_id = session['metadata']['product_id']
        product = Product.objects.get(id=product_id)

        #send email to customer
        send_mail(
           subject="Thanks for purchase",
           message=f"Here is Your product, Product url is {product.get_url()}",
           recipient_list = [customer_email,],
           from_email="test@admin.com" 
        )
    elif event["type"] == "payment_intent.succeeded":
        #grab intent from event which was created by create-payment-intent
        intent = event['data']['object']

        #grab stripe customer from intent
        stripe_customer_id = intent['customer']
        stripe_customer = stripe.Customer.retrieve(stripe_customer_id)

        customer_email = stripe_customer['email']

        #grab product from metadata of intent which was sent by create-payment-intent view
        product_id = intent["metadata"]["product_id"]
        product = Product.objects.get(id=product_id)

        # send email to customer
        send_mail(
            subject="Here is your product",
            message=f"Thanks for your purchase. Here is the product you ordered. The URL is {product.get_url()}",
            recipient_list=[customer_email],
            from_email="matt@test.com"
        )

    # Passed signature verification
    return HttpResponse(status=200)

#define functionality for successful order after successful payment and call  it from webhook as send_email
def fulfill_order(session):
  # TODO: fill me in
  print("Fulfilling order")

#stripe intent view for custom form checkout
class StripeIntentView(View):    
    def post(self,request,*args,**kwargs):
        try:
            # get customer input
            req_json = json.loads(request.body)
            # create stripe customer
            customer = stripe.Customer.create(email=req_json['email'])
            product_id = self.kwargs["pk"]
            product = Product.objects.get(id=product_id)
            intent = stripe.PaymentIntent.create(
                amount=product.stripe_price(),
                currency='inr',
                customer=customer['id'],
                metadata={
                    "product_id": product.id
                }
            )
            return JsonResponse({
                'clientSecret': intent['client_secret']
                })
        except Exception as e:
            return JsonResponse({'error':str(e)})