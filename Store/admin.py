from django.contrib import admin
from .models import Cart, CartItem, Category, ContactMessage, Order, OrderItem, Product, ProductVariant, ProductImage, ProductSpecification , ProductReview, ProductFeature, UserProfile


admin.site.register(UserProfile)
admin.site.register(ContactMessage)
admin.site.register(Cart)
admin.site.register(CartItem)
# admin.site.register(WhatsAppOrderTrack)
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'sku', 'price', 'stock', 'availability', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'sku')
    list_filter = ('category', 'availability')
    ordering = ('-created_at',)
@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'title', 'price')
    search_fields = ('product__name', 'title')
    list_filter = ('product',)
@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'image')
    search_fields = ('product__name',)
    list_filter = ('product',)
@admin.register(ProductSpecification)
class ProductSpecificationAdmin(admin.ModelAdmin):
    list_display = ('product', 'key', 'value')
    search_fields = ('product__name', 'key')
    list_filter = ('product',)

@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'reviewer_name', 'rating', 'created_at')
    search_fields = ('product__name', 'reviewer_name')
    list_filter = ('product',)
    
@admin.register(ProductFeature)
class ProductFeatureAdmin(admin.ModelAdmin):
    list_display = ('product', 'title', 'feature')
    search_fields = ('product__name', 'title')
    list_filter = ('product',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'email', 'payment_method', 'total', 'created_at']
    list_filter = ['payment_method', 'created_at']
    search_fields = ['email', 'first_name', 'last_name']

    def get_readonly_fields(self, request, obj=None):
        return ['payment_slip', 'created_at']

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'price']
    list_filter = ['order']

