from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from Store import views
# from Store.forms import CustomSetPasswordForm
from django.contrib.auth import views as auth_views
from django.contrib.sitemaps.views import sitemap
from Store.sitemaps import ProductSitemap, CategorySitemap, StaticViewSitemap, ProjectSitemap, HomeSitemap

sitemaps = {
    'home': HomeSitemap,
    'products': ProductSitemap,
    'projects': ProjectSitemap,
    'categories': CategorySitemap,
    'static': StaticViewSitemap,
}

urlpatterns = [
      path('admin/', admin.site.urls),
      path("",views.home,name="home"),
      path("Register/",views.Register,name="register"),
      path("login/",views.Login,name="login"),
      path('password_reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),  # ✅ Use this one only
      path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
          template_name='registration/password_reset_done.html',
      ), name='password_reset_done'),

   path('reset/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(  
        template_name='registration/password_reset_confirm.html',
    ), name='password_reset_confirm'),
    
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html',
    ), name='password_reset_complete'),
    path('ajax-login/', views.ajax_login, name='ajax_login'),
    path('ajax-register/', views.ajax_register, name='ajax_register'),
    path("logout/",views.Logout,name="logout"),
    path("reset_verify_otp/", views.reset_verify_otp, name="reset_verify_otp"),
  # path("reset-new-password/", views.reset_new_password, name="reset_new_password"),
    path("forgot/",views.forgot,name="forgot"),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path("home/",views.home,name="home"),
    path("checkout/",views.checkout,name="checkout"),
    path("detail/<slug:slug>/",views.productDetail,name="product_detail"),
    path("product/",views.product,name="product"),
    path("project/",views.project,name="project"),
    path('category/<slug:category_slug>/', views.category_products, name='category_products'),
    path('add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('get-cart/', views.get_cart, name='get_cart'),
    path('update-cart/', views.update_cart, name='update_cart'),
    path('remove-from-cart/', views.remove_from_cart, name='remove_from_cart'),
    # Other URLs, e.g., for product detail
    path('detail/<slug:slug>/', views.productDetail, name='product_detail'),
    #   path("product_Show Mores",views.product_Show Mores,name="product_Show Mores"),
    path("cart/",views.cart,name="cart"),
    path('contact/', views.contact, name='contact'),
    path('contact/success/', views.contact_success, name='contact_success'),
    path('place-order/', views.place_order, name='place_order'),
    path('order-confirmation/', views.order_confirmation, name='order_confirmation'),
    path('order-history/', views.order_history, name='order_history'),
    path("cart-count/", views.cart_count, name="cart_count"),
    path('toggle-like/<int:product_id>/', views.toggle_like, name='toggle_like'),
    path('share-product/<int:product_id>/', views.share_product, name='share_product'),
    path('submit-review/<int:product_id>/', views.submit_review, name='submit_review'),
    path('track-whatsapp-order/<int:product_id>/', views.track_whatsapp_order, name='track_whatsapp_order'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps, 'template_name': 'custom_sitemap.xml'}, name='django.contrib.sitemaps.views.sitemap'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
