import random
import string
from django.contrib import messages
from smtplib import SMTPException
from django.core.mail import send_mail

#Creat Verification Code
def create_verification_code():
    verification_code=''.join(random.choices(string.digits, k=6))
    return verification_code

#Send Verification Code through Email
def send_verification_code(request,username,email,verification_code):
    subject='Verify Your Email Address'
    e_message=''
    message=f'''<h2 style="color:black;">Dear {username},</h2>  
    <p style="color:black;font-size:large;">
    Thank you for signing up with ProjectStore! We're excited to have you onboard.
    <br>
    To complete your registration, please verify your email address your verification code is below:
    <br>
    </p>
    <h2>{verification_code}</h2>
    <p style="color:black;font-size:large;">
    If you have any questions or concerns, please don't hesitate to reach out to us.
    <br>
    Best regards,<br>
    ProjectStore Team </p>'''
    try:
        send_mail(subject,e_message,'register@projectstore.pk',[email],html_message=message,fail_silently=False)
        messages.success(request, 'Verification Code Sent to Your Email')
    except SMTPException as e:
        messages.error(request,
                        'We were unable to send a verification code to your email. Please try again later or contact support for assistance.',
                        extra_tags='danger')
                        
                        
def send_order_email_admin(order, items):
    subject = f"New Order Received | Order #{order.id}"
    html_msg = f"""
    <h2>New Order Received</h2>
    <p><strong>Name:</strong> {order.first_name} {order.last_name}</p>
    <p><strong>Email:</strong> {order.email}</p>
    <p><strong>Phone:</strong> {order.phone}</p>
    <p><strong>Address:</strong> {order.address}, {order.city}, {order.state}</p>
    <h3>Order Details:</h3>
    <ul>
    """

    for item in items:
        html_msg += f"<li>{item.product.name} — {item.quantity} × Rs {item.price}</li>"

    html_msg += f"""
    </ul>
    <h3>Total Amount: Rs {order.total}</h3>
    """

    try:
        send_mail(
            subject,
            "",
            "register@projectstore.pk",
            ["register@projectstore.pk"],  # ✅ RECEIVES ADMIN EMAIL
            html_message=html_msg
        )
    except SMTPException:
        print("❌ Failed to send admin order email")


# ✅ Email To CUSTOMER
def send_order_email_customer(order):
    subject = f"Order Confirmation | ProjectStore | Order #{order.id}"
    message = f"""
    <h2>Hello {order.first_name},</h2>
    <p>Thank you for your order at ProjectStore!</p>
    <p>Your order has been received and is being processed.</p>

    <h3>Order Total: Rs {order.total}</h3>

    <p>We will contact you soon.</p>
    <p>– ProjectStore Team</p>
    """

    try:
        send_mail(
            subject,
            "",
            "register@projectstore.pk",
            [order.email],
            html_message=message
        )
    except SMTPException:
        print("❌ Failed to send customer order email")