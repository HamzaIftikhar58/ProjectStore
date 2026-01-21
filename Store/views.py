import logging
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView
from django.core.files.storage import FileSystemStorage
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Avg, Prefetch, Q

from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.urls import reverse, reverse_lazy
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST

from .forms import (
    LoginForm,
    RegisterForm,
    ContactForm,
    CustomPasswordResetForm,
    CustomSetPasswordForm,
)
from .models import (
    Cart,
    CartItem,
    Order,
    OrderItem,
    Product,
    Category,
    ProductReview,
    ProductVariant,
    UserProfile,
    ContactMessage,
)
from .isol_functions import create_verification_code, send_order_email_admin, send_order_email_customer, send_verification_code
    # Set up logging
logger = logging.getLogger(__name__)

User = get_user_model()
class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'registration/password_reset_confirm.html'
    form_class = CustomSetPasswordForm
    success_url = '/reset/done/'
class CustomPasswordResetView(PasswordResetView):
    template_name = 'registration/password_reset_form.html'
    form_class = CustomPasswordResetForm

    def form_valid(self, form):
        email = form.cleaned_data['email'].strip().lower()
        user = User.objects.filter(email__iexact=email).first()
        if user:
            try:
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                reset_link = self.request.build_absolute_uri(
                    reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
                )

                # render email template
                subject = "Password Reset Request"
                message = render_to_string('registration/password_reset_email.html', {
                    'user': user,
                    'reset_link': reset_link,
                })

                # send email
                send_mail(
                    subject,
                    message,
                    settings.EMAIL_HOST_USER,  # sender
                    [email],                   # recipient
                    fail_silently=False,
                )
                
                messages.success(self.request, "Mail is sent. Check your mail.")
                return render(self.request, self.template_name, {
                    'form': form,
                    'email_sent': True  # Context variable to disable the field
                })

            except Exception as e:
                logger.error(f"Failed to send password reset email: {str(e)}")
                messages.error(self.request, "Mail cannot be sent. Please try again later.")
                return render(self.request, self.template_name, {'form': form})

        # User not found
        messages.error(self.request, "Mail cannot be sent. No user found with this email.")
        return render(self.request, self.template_name, {'form': form})

    


 

def prehome(request):
         if request.user.is_authenticated:
             return redirect('home')
         return render(request, 'prehome.html')

def Register(request):
         Rform = RegisterForm()
         if request.method == 'POST':
             PostData = request.POST.copy()
             logger.info(f"POST data received: {PostData}")
             if PostData['password'] == PostData['confirmpassword']:
                 Rform = RegisterForm(PostData)
                 if Rform.is_valid():
                     # Store form data in session and send OTP
                     # Convert QueryDict to standard dict for safe session serialization
                     request.session['temp_user_data'] = PostData.dict()
                     verification_code = create_verification_code()
                     request.session['verification_code'] = verification_code
                     request.session.modified = True  # Ensure session is saved
                     logger.info(f"Session data stored: temp_user_data={PostData.dict()}, verification_code={verification_code}")
                     try:
                         send_verification_code(request, PostData['username'], PostData['email'], verification_code)
                         logger.info(f"Verification code sent to {PostData['email']}: {verification_code}")
                        #  messages.success(request, 'OTP sent to your email.')
                         return redirect('verify_otp')  # Redirect to OTP verification page
                     except Exception as e:
                         logger.error(f"Failed to send verification code to {PostData['email']}: {str(e)}")
                         messages.error(request, 'Failed to send verification code. Please try again.', extra_tags='danger')
                 else:
                     for field, errors in Rform.errors.items():
                         messages.error(request, errors, extra_tags='danger')
                         logger.error(f"Form errors: {field}: {errors}")
             else:
                 messages.error(request, 'Password and Confirm Password Fields Do Not Match', extra_tags='danger')
                 logger.error("Password and Confirm Password do not match")

         logger.info(f"Session contents: {request.session.items()}")
         context = {'Rform': Rform}
         return render(request, "register.html", context)

def verify_otp(request):
         if request.method == 'POST':
             entered_otp = request.POST.get('otp')
             stored_otp = request.session.get('verification_code')
             temp_user_data = request.session.get('temp_user_data')

             logger.info(f"Verifying OTP: Entered={entered_otp}, Stored={stored_otp}, Temp User Data={temp_user_data}")

             if not temp_user_data:
                 messages.error(request, 'Session expired or invalid. Please try again.', extra_tags='danger')
                 logger.error("Session expired: temp_user_data not found")
                 return redirect('register')

             # Compare as strings to avoid Type Errors (int vs str)
             if str(entered_otp).strip() == str(stored_otp).strip():
                 # OTP is correct, proceed to save user
                 Rform = RegisterForm(temp_user_data)
                 if Rform.is_valid():
                     user = Rform.save(commit=False)
                     user.username = user.username.lower()
                     user.set_password(temp_user_data['password'])
                     user.save()
                     logger.info(f"User created: {user.username}")

                     # Save phone number in profile
                     phone = temp_user_data.get('phone')
                     if phone:
                         UserProfile.objects.create(user=user, phone=phone)
                         logger.info(f"UserProfile created for {user.username} with phone {phone}")

                     # Authenticate and log the user in
                     user = authenticate(
                         request,
                         username=temp_user_data['username'].lower(),
                         password=temp_user_data['password']
                     )
                     if user is not None:
                         login(request, user)
                         # Clear session data
                         request.session.pop('verification_code', None)
                         request.session.pop('temp_user_data', None)
                         messages.success(request, 'Registered Successfully')
                         logger.info(f"User {user.username} logged in successfully")
                         return HttpResponseRedirect('/home/')
                     else:
                         messages.error(request, 'Authentication failed. Please try again.', extra_tags='danger')
                         logger.error(f"Authentication failed for {temp_user_data['username']}")
                 else:
                     # If valid during register but invalid now (e.g. username taken), inform user
                     messages.error(request, 'Registration failed (Username/Email may have been taken). Please register again.', extra_tags='danger')
                     logger.error(f"Form errors during saving: {Rform.errors}")
                     return redirect('register')
             else:
                 messages.error(request, 'Invalid OTP. Please try again.', extra_tags='danger')
                 logger.error(f"Invalid OTP: Entered={entered_otp}, Stored={stored_otp}")

         logger.info(f"Session contents: {request.session.items()}")
         return render(request, 'verify_otp.html')

def Login(request):
         if request.user.is_authenticated:
             return redirect('home')
         form = LoginForm(request.POST or None)

         if request.method == 'POST':
             if form.is_valid():
                 username = form.cleaned_data['username'].lower()
                 password = form.cleaned_data['password']
                 user = authenticate(request, username=username, password=password)
                 if user:
                     login(request, user)
                     return HttpResponseRedirect('/home/')
                 else:
                     messages.error(request, "Username and password did not match!", extra_tags='danger')
                     logger.error(f"Login failed for username: {username}")
             else:
                 for errors in form.errors.values():
                     for error in errors:
                         messages.error(request, error, extra_tags='danger')
                         logger.error(f"Login form errors: {error}")

         return render(request, "login.html", {'form': form})
def Logout(request):
         logout(request)
         return redirect('/')

def forgot(request):
    
    return render(request, "forgot.html",)


def reset_verify_otp(request):
    if request.method == "POST":
        entered_otp = request.POST.get("otp")
        stored_otp = request.session.get("reset_verification_code")
        user_id = request.session.get("reset_user_id")

        if entered_otp == stored_otp and user_id:
            return redirect("reset_new_password")  # go to set new password
        else:
            messages.error(request, "Invalid OTP, try again")
    return render(request, "reset_verify_otp.html")



def home(request):
         return render(request, 'home_new.html')


@require_http_methods(["GET", "POST"])
def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact_message = form.save()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Your message has been sent successfully!'
                })
            return redirect('contact_success')
        
        # Form is not valid
        errors = {field: error.get_json_data()[0]['message'] for field, error in form.errors.items()}
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'Please correct the errors below.',
                'errors': errors
            }, status=400)
    
    # GET request - show empty form
    form = ContactForm()
    return render(request, 'contact.html', {'form': form})

def contact_success(request):
    return render(request, 'contact_success.html')
def checkout(request):
    return render(request, 'checkout.html')

def category_products(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)
    # Optimized query to avoid N+1 problem in template
    products_list = category.products.select_related('category').all()  # related_name="products"
    paginator = Paginator(products_list, 12)  # Show 12 products per page
    page = request.GET.get('page')
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)

    return render(request, 'category_products.html', {
        'category': category,
        'products': products
    })




def productDetail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    reviews = ProductReview.objects.filter(product=product)

    # Calculate average rating
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    avg_rating = round(avg_rating, 1)

    full_stars = int(avg_rating)
    half_star = (avg_rating - full_stars) >= 0.5
    empty_stars = 5 - full_stars - (1 if half_star else 0)

    context = {
        'product': product,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'full_stars': range(full_stars),
        'half_star': half_star,
        'empty_stars': range(empty_stars),

        # 👇 Extra context for breadcrumb / dynamic UI
        'is_project': product.is_project,
        'page_title': product.name,
        'is_liked': product.liked_by.filter(id=request.user.id).exists() if request.user.is_authenticated else False,
    }

    return render(request, 'detail.html', context)



from django.db.models import Prefetch

def product(request):
    from django.db.models import Q
    import operator
    from functools import reduce

    query = request.GET.get('q')

    if query:
        # Split query into terms to handle "Ambulance Detection" finding "AI Ambulance Detection"
        terms = query.split()
        
        # Create a Q object for each term (search in name OR descriptions)
        search_rules = []
        for term in terms:
            search_rules.append(
                Q(name__icontains=term) | 
                Q(short_description__icontains=term) | 
                Q(description__icontains=term)
            )
        
        # Combine all rules with AND (product must contain ALL terms)
        if search_rules:
            combined_filter = reduce(operator.and_, search_rules)
            products = Product.objects.filter(is_active=True).filter(combined_filter)
        else:
            products = Product.objects.none()

        # Pagination for Search Results
        paginator = Paginator(products, 12)  # Show 12 items per page
        page = request.GET.get('page')
        try:
            products_paginated = paginator.page(page)
        except PageNotAnInteger:
            products_paginated = paginator.page(1)
        except EmptyPage:
            products_paginated = paginator.page(paginator.num_pages)

        class MockCategory:
            def __init__(self, name, products):
                self.name = name
                self.slug = 'search-results'
                self.only_products = products
        
        # If no products found, we still pass the empty list so the template handles "No products available"
        categories = [MockCategory(f"Search Results for '{query}'", products_paginated)]
        
        context = {
            'categories': categories,
            'is_project': False,
            'page_title': f"Search: {query}",
            'products_paginated': products_paginated, # Pass directly for accessing pagination info
            'search_query': query 
        }
    else:
        categories = Category.objects.filter(products__is_project=False).distinct()

        # Prefetch only products (not projects)
        categories = categories.prefetch_related(
            Prefetch(
                'products',
                queryset=Product.objects.filter(is_project=False, is_active=True),
                to_attr='only_products'
            )
        )

        context = {
            'categories': categories,
            'is_project': False,        # 👈 breadcrumb helper
            'page_title': 'Products'    # 👈 optional (for breadcrumb active text)
        }
    return render(request, 'product.html', context)


def project(request):
    categories = Category.objects.prefetch_related(
        Prefetch(
            'products',
            queryset=Product.objects.filter(is_project=True, is_active=True),
            to_attr='only_projects'
        )
    ).filter(products__is_project=True).distinct()

    context = {
        'categories': categories,
        'is_project': True,         # 👈 breadcrumb helper
        'page_title': 'Projects'    # 👈 optional (for breadcrumb active text)
    }
    return render(request, 'project.html', context)




def AIpage(request):
    category = get_object_or_404(Category, name='AI')
    products = Product.objects.filter(category__name='AI').select_related('category')
    context = {
        'products': products,
        'category': category
    }
    return render(request, 'AIpage.html', context)

def hardwarepage(request):
    category = get_object_or_404(Category, name='Hardware')
    products = Product.objects.filter(category__name='Hardware').select_related('category')
    context = {
        'products': products,
        'category': category
    }
    return render(request, 'hardwarepage.html', context)

def cart(request):
    """
    View to display the full shopping cart page.
    """
    # Get or create cart for user/session
    if request.user.is_authenticated:
        cart_obj, created = Cart.objects.get_or_create(user=request.user)
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        cart_obj, created = Cart.objects.get_or_create(session_key=session_key)

    items = cart_obj.items.all().select_related('product', 'variant')
    total = sum(item.price * item.quantity for item in items)

    context = {
        'cart': cart_obj,
        'items': items,
        'total': total,
        'page_title': 'Your Shopping Cart'
    }
    return render(request, 'cart.html', context)



@require_POST
def submit_review(request, product_id):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'You must be logged in to submit a review'}, status=403)
    
    product = get_object_or_404(Product, id=product_id)
    reviewer_name = request.POST.get('reviewer_name')
    rating = request.POST.get('rating')
    review_text = request.POST.get('review')
    
    # Validate data
    if not all([reviewer_name, rating, review_text]):
        return JsonResponse({'success': False, 'message': 'All fields are required'}, status=400)
    
    try:
        ProductReview.objects.create(
            product=product,
            reviewer_name=reviewer_name,
            rating=int(rating),
            review=review_text
        )
        return JsonResponse({'success': True, 'message': 'Review submitted successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

def softwarepage(request):
    category = get_object_or_404(Category, name='Software')
    products = Product.objects.filter(category__name='Software').select_related('category')
    context = {
        'products': products,
        'category': category
    }
    return render(request, 'softwarepage.html', context)

def Robotspage(request):
    category = get_object_or_404(Category, name='Robot')
    products = Product.objects.filter(category__name='Robot').select_related('category')
    context = {
        'products': products,
        'category': category
    }
    return render(request, 'Robotspage.html', context)

def Electronicspage(request):
    category = get_object_or_404(Category, name='Electronics')
    products = Product.objects.filter(category__name='Electronics').select_related('category')
    context = {
        'products': products,
        'category': category
    }
    return render(request, 'Electronicspage.html', context)

@require_POST
def add_to_cart(request):
    """
    Add an item to the cart via AJAX with discount support.
    """
    product_id = request.POST.get('product_id')
    quantity = int(request.POST.get('quantity', 1))
    variant_id = request.POST.get('variant_id')

    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(
        user=request.user if request.user.is_authenticated else None
    )

    if variant_id:
        variant = get_object_or_404(ProductVariant, id=variant_id)
        # Use variant price (if variants don’t have discount logic, keep it as is)
        final_price = float(variant.price)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            variant=variant,
            defaults={'quantity': quantity, 'price': final_price}
        )
    else:
        # Use product.final_price (with discount applied automatically)
        final_price = float(product.final_price)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity, 'price': final_price}
        )

    if not created:
        cart_item.quantity += quantity
        cart_item.save()

    return JsonResponse({
        'success': True,
        'message': 'Item added to cart',
        'final_price': final_price,
        'discount_percentage': product.discount_percentage if not variant_id else None
    })

def get_cart(request):
    """
    Retrieve the current cart items via AJAX with discount prices.
    """
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_key=session_key)
    items = []
    for item in cart.items.all().select_related('product', 'variant'):
        items.append({
            'id': item.id,
            'name': item.product.name,
            'price': float(item.price),  # already discounted when added
            'quantity': item.quantity,
            'image': item.variant.image.url if item.variant else item.product.main_image.url
        })
    return JsonResponse({'items': items})
@require_POST
def update_cart(request):
    """
    Update the quantity of a cart item via AJAX.
    """
    item_id = request.POST.get('item_id')
    change = int(request.POST.get('change'))
    cart_item = get_object_or_404(CartItem, id=item_id)

    new_quantity = cart_item.quantity + change
    if new_quantity < 1:
        cart_item.delete()
        return JsonResponse({'success': True, 'message': 'Item removed'})

    cart_item.quantity = new_quantity
    cart_item.save()

    return JsonResponse({
        'success': True,
        'message': 'Quantity updated',
        'final_price': float(cart_item.price),
        'total_item_price': float(cart_item.price) * cart_item.quantity
    })

@require_POST
def remove_from_cart(request):
    """
    Remove an item from the cart via AJAX.
    """
    item_id = request.POST.get('item_id')
    cart_item = get_object_or_404(CartItem, id=item_id)
    cart_item.delete()
    return JsonResponse({'success': True, 'message': 'Item removed'})


def cart_count(request):
    count = 0
    if request.user.is_authenticated:
        count = CartItem.objects.filter(cart__user=request.user).count()
    else:
        session_key = request.session.session_key
        if session_key:
            count = CartItem.objects.filter(cart__session_key=session_key).count()
    return JsonResponse({'count': count})



@login_required
@require_POST
def toggle_like(request, product_id):
    product = Product.objects.get(id=product_id)
    if product.liked_by.filter(id=request.user.id).exists():
        product.liked_by.remove(request.user)
        liked = False
    else:
        product.liked_by.add(request.user)
        liked = True
    return JsonResponse({
        'liked': liked,
        'count': product.like_count
    })

def share_product(request, product_id):
    product = Product.objects.get(id=product_id)
    # You can implement actual sharing logic here (email, social media, etc.)
    return JsonResponse({
        'success': True,
        'message': 'Product shared successfully'
    })


@require_POST
def place_order(request):
    try:
  
        email = request.POST.get('email')
        payment_method = request.POST.get('payment_method')
        country = request.POST.get('country')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        address = request.POST.get('address')
        apartment = request.POST.get('apartment')
        city = request.POST.get('city')
        state = request.POST.get('state')
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get('phone')
        save_info = request.POST.get('save_info') == 'on'
        text_offers = request.POST.get('text_offers') == 'on'

 
        if not all([email, payment_method, country, last_name, address, city, state, zip_code, phone]):
            return JsonResponse({"success": False, "message": "Please fill all required fields."}, status=400)

        payment_slip_url = None
        if payment_method == "online_payment":
            if "payment_slip" not in request.FILES:
                return JsonResponse({"success": False, "message": "Payment slip required."}, status=400)

            slip = request.FILES["payment_slip"]
            fs = FileSystemStorage()
            file_path = fs.save(f"payment_slips/{slip.name}", slip)
            payment_slip_url = file_path

     
        if request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=request.user)
        else:
            session_key = request.session.session_key
            if not session_key:
                request.session.create()
            cart, created = Cart.objects.get_or_create(session_key=request.session.session_key)

        cart_items = cart.items.select_related('product', 'variant').all()

        if not cart_items:
            return JsonResponse({"success": False, "message": "Your cart is empty."}, status=400)

        # Calculate total
        total_price = sum(item.price * item.quantity for item in cart_items)

      
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            session_key=None if request.user.is_authenticated else request.session.session_key,
            email=email,
            payment_method=payment_method,
            payment_slip=payment_slip_url,
            country=country,
            first_name=first_name,
            last_name=last_name,
            address=address,
            apartment=apartment,
            city=city,
            state=state,
            zip_code=zip_code,
            phone=phone,
            save_info=save_info,
            text_offers=text_offers,
            total=total_price   
        )

       
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                variant=item.variant,
                quantity=item.quantity,
                price=item.price
            )

       
        send_order_email_admin(order, cart_items)
        send_order_email_customer(order)
        
        cart_items.delete()

        if not request.user.is_authenticated:
            cart.delete()

      
        return JsonResponse({
            "success": True,
            "message": "Order placed successfully!",
            "redirect_url": "/order-confirmation/"
        })

    except Exception as e:
        print("ORDER ERROR:", e)
        return JsonResponse({"success": False, "message": str(e)}, status=400)




def order_confirmation(request):
    # Get the most recent order for the user or session
    if request.user.is_authenticated:
        order = Order.objects.filter(user=request.user).order_by('-created_at').first()
    else:
        # For anonymous users, use session_key if available
        session_key = request.session.session_key
        order = Order.objects.filter(session_key=session_key).order_by('-created_at').first() if session_key else None

    if not order:
        # Redirect to home or show an error if no order is found
        messages.error(request, "No order found.", extra_tags='danger')
        return redirect('home')

    context = {
        'order': order,
    }
    return render(request, 'order_confirmation.html', context)

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at').prefetch_related('items__product', 'items__variant')
    context = {
        'orders': orders
    }
    return render(request, 'order_history.html', context)






@csrf_exempt
def track_whatsapp_order(request, product_id):
    if request.method == 'POST':
        try:
            # Verify the product exists
            product = Product.objects.get(id=product_id)
            
            # Example tracking logic: Log to console or database
            logger.info(f"WhatsApp order tracked for product ID {product_id}: {product.name}")
            
            # Optionally, save tracking data to a model (you'll need to create this model)
            # Example model: WhatsAppOrderTrack
            """
            WhatsAppOrderTrack.objects.create(
                product=product,
                user=request.user if request.user.is_authenticated else None,
                timestamp=timezone.now()
            )
            """
            
            return JsonResponse({
                'success': True,
                'message': 'WhatsApp order tracked successfully'
            })
        except Product.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Product not found'
            }, status=404)
        except Exception as e:
            logger.error(f"Error tracking WhatsApp order for product ID {product_id}: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            }, status=500)
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    }, status=400)
@csrf_protect
@require_POST
def ajax_login(request):
    """
    Handle AJAX login requests using request.POST (for FormData).
    """
    try:
        username = request.POST.get('username', '').lower().strip()
        password = request.POST.get('password', '').strip()
        
        # Optional: Handle 'remember' checkbox (e.g., set session expiry)
        remember = request.POST.get('remember') == 'on'
        if remember:
            request.session.set_expiry(1209600)  # 2 weeks
        else:
            request.session.set_expiry(0)  # Browser session
        
        # Authenticate user
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return JsonResponse({
                'success': True,
                'message': 'Login successful!'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Invalid username or password',
                'errors': {
                    'username': 'Invalid credentials',
                    'password': 'Invalid credentials'
                }
            }, status=400)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

@csrf_protect
@require_POST
def ajax_register(request):
    """
    Handle AJAX registration requests using request.POST (for FormData).
    Supports optional phone field from UserProfile model.
    """
    try:
        # Extract form data
        username = request.POST.get('username', '').lower().strip()
        email = request.POST.get('email', '').lower().strip()
        password = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        phone = request.POST.get('phone', '').strip()  # Optional phone from form
        
        errors = {}
        
        # Validate passwords match
        if password != confirm_password:
            errors['confirm_password'] = 'Passwords do not match'
        
        # Check if username already exists
        if User.objects.filter(username__iexact=username).exists():
            errors['username'] = 'Username already exists'
        
        # Check if email already exists
        if User.objects.filter(email__iexact=email).exists():
            errors['email'] = 'Email already exists'
        
        # Validate password strength
        if len(password) < 8:
            errors['password'] = 'Password must be at least 8 characters'
        
        # Optional: Validate phone if provided (basic check)
        if phone and len(phone) > 15:
            errors['phone'] = 'Phone number too long (max 15 characters)'
        
        # If errors
        if errors:
            return JsonResponse({
                'success': False,
                'message': 'Please correct the errors below',
                'errors': errors
            }, status=400)
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        
        # Auto login after registration
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            
            # Create or update user profile with optional phone
            UserProfile.objects.update_or_create(
                user=user,
                defaults={'phone': phone}
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Registration successful!'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Registration successful but auto-login failed'
            }, status=400)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)