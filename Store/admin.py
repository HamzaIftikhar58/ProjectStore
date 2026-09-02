from django.contrib import admin
from django.utils import timezone
from .models import Cart, CartItem, Category, ContactMessage, Order, OrderItem, Product, ProductVariant, ProductImage, ProductSpecification , ProductReview, ProductFeature, UserProfile, SiteSetting, SiteConfiguration, BlogPost, ItemQuestion

# ... rest of registrations ...


admin.site.register(SiteConfiguration)


admin.site.register(UserProfile)
admin.site.register(SiteSetting)
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
    list_filter = ('category', 'availability', 'is_project')
    ordering = ('-created_at',)
    filter_horizontal = ('related_products',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'category', 'sku', 'is_project', 'price', 'discount_percentage', 'stock', 'availability', 'is_active')
        }),
        ('Media & Links', {
            'fields': ('main_image', 'alt_text', 'youtube_video_url')
        }),
        ('Descriptions & Details', {
            'fields': ('short_description', 'description')
        }),
        ('Content Enrichment & E-E-A-T Options', {
            'fields': ('package_includes', 'guarantee_text', 'related_products'),
            'description': 'Configure Package Includes list (one item per line), Buyer Guarantee, and Related Product cross-links.'
        }),
        ('SEO & Metadata', {
            'fields': ('meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
    )
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


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'author', 'reading_time', 'is_featured', 'is_published', 'views_count', 'created_at')
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'content', 'excerpt', 'meta_keywords')
    list_filter = ('category', 'is_featured', 'is_published', 'created_at')
    ordering = ('-is_featured', '-created_at')
    filter_horizontal = ('related_products',)

    fieldsets = (
        ('Article Content', {
            'fields': ('title', 'slug', 'category', 'author', 'reading_time', 'featured_image', 'excerpt', 'content')
        }),
        ('Publication & E-Commerce Linkage', {
            'fields': ('is_featured', 'is_published', 'related_products'),
            'description': 'Select related products/kits to automatically embed 1-click buy cards inside this tutorial.'
        }),
        ('SEO & OpenGraph Metadata', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ItemQuestion)
class ItemQuestionAdmin(admin.ModelAdmin):
    list_display = ('question_preview', 'target_item', 'user', 'has_answer', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'answered_at', 'created_at')
    search_fields = ('question', 'answer', 'user__username', 'product__name', 'blog_post__title')
    list_editable = ('is_approved',)
    readonly_fields = ('user', 'product', 'blog_post', 'created_at', 'answered_at')
    
    fieldsets = (
        ('Question Details', {
            'fields': ('user', 'product', 'blog_post', 'question', 'is_approved', 'created_at')
        }),
        ('Official Answer', {
            'fields': ('answer', 'answered_by', 'answered_at'),
            'description': 'Answer this customer question. Once answered and approved, it will appear publicly and get fed into Google AI Overviews.'
        }),
    )

    def question_preview(self, obj):
        return obj.question[:50] + ("..." if len(obj.question) > 50 else "")
    question_preview.short_description = "Customer Question"

    def target_item(self, obj):
        if obj.product:
            return f"Product: {obj.product.name[:30]}"
        elif obj.blog_post:
            return f"Tutorial: {obj.blog_post.title[:30]}"
        return "General"
    target_item.short_description = "Asked On"

    def has_answer(self, obj):
        return bool(obj.answer)
    has_answer.boolean = True
    has_answer.short_description = "Answered?"

    def save_model(self, request, obj, form, change):
        if obj.answer and not obj.answered_by:
            obj.answered_by = request.user
            obj.answered_at = timezone.now()
        super().save_model(request, obj, form, change)

