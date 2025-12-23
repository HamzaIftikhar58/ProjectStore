from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

from django.contrib.auth import get_user_model

from django import forms
from .models import ContactMessage

from django.contrib.auth.forms import SetPasswordForm

from django.contrib.auth.forms import SetPasswordForm, PasswordResetForm
from .isol_functions import create_verification_code, send_verification_code
class CustomSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label="New Password",
        strip=False,
        widget=forms.PasswordInput(attrs={
            "autocomplete": "new-password",
            "class": "form-control",
            "placeholder": "Enter new password"
        }),
    )
    new_password2 = forms.CharField(
        label="Confirm Password",  # ✅ Custom label
        strip=False,
        widget=forms.PasswordInput(attrs={
            "autocomplete": "new-password",
            "class": "form-control",
            "placeholder": "Confirm new password"
        }),
    )
class CustomPasswordResetForm(forms.Form):
    email = forms.EmailField(
        label="Email",
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        })
    )


def send_reset_code(self, request):
        """Send OTP for password reset"""
        email = self.cleaned_data['email']
        user = User.objects.get(email=email)

        # Create and save OTP in session
        verification_code = create_verification_code()
        request.session['reset_verification_code'] = verification_code
        request.session['reset_user_id'] = user.id
        request.session.modified = True

        # Send via your existing email function
        send_verification_code(request, user.username, email, verification_code)
        return True
from django import forms


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Email'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Subject'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Your message...'
            }),
        }
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if len(name) < 2:
            raise forms.ValidationError("Name must be at least 2 characters long.")
        return name
    
    def clean_message(self):
        message = self.cleaned_data.get('message')
        if len(message) < 2:
            raise forms.ValidationError("Message must be at least 2 characters long.")
        return message

def check_user(user_name):
    try:
        user_name=user_name.lower()
        user=User.objects.get(username=user_name)
    except:
        raise forms.ValidationError('User Not Found')

def check_password(password):
    if len(password) >= 8:
        pass
    else:
        raise forms.ValidationError('Password is too short')
    pass

def register_email(_email):
    try:
        _user=User.objects.get(email=_email)
    except:
        return
    raise forms.ValidationError('User with same email address already exist!')

class RegisterForm(forms.ModelForm):
    email = forms.EmailField(validators=[register_email],widget=forms.EmailInput(attrs={'class':"form-control"}))
    password = forms.CharField(validators=[validate_password],widget=forms.PasswordInput(attrs={'class':"form-control"}))
    username = forms.CharField(widget=forms.TextInput(attrs={'class':"form-control"}))
    profile_image = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': "form-control"}))  # Added profile image field
   
    class Meta:
        model=User
        fields =('username', 'email' , 'password','profile_image')

class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'class':"form-control form-control-lg"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class':"form-control form-control-lg"}))


