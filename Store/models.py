from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from django.utils import timezone
from django.urls import reverse
from django.contrib.sites.models import Site


class UserProfile(models.Model):
    """
    User profile model to store additional user information.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=15, blank=True, null=True)  # Store phone number

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def __str__(self):
        return f"Profile of {self.user.username}"


class SiteSetting(models.Model):
    """Singleton model for global site settings, including social media links and contact info."""
    facebook_url = models.URLField(max_length=255, blank=True, null=True, help_text="e.g. https://www.facebook.com/IsolPaki")
    instagram_url = models.URLField(max_length=255, blank=True, null=True, help_text="e.g. https://www.instagram.com/yourpage")
    youtube_url = models.URLField(max_length=255, blank=True, null=True, help_text="e.g. https://www.youtube.com/@Isol_pk")
    whatsapp_number = models.CharField(max_length=20, blank=True, null=True, help_text="e.g. 923104505008 (Include country code without +)")
    twitter_url = models.URLField(max_length=255, blank=True, null=True, help_text="X/Twitter Profile URL")
    linkedin_url = models.URLField(max_length=255, blank=True, null=True, help_text="LinkedIn Profile URL")
    
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Site Setting"
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return "Global Site Settings"
    
    def save(self, *args, **kwargs):
        """Ensure only one instance exists"""
        if not self.pk and SiteSetting.objects.exists():
            return
        return super(SiteSetting, self).save(*args, **kwargs)


class Category(models.Model):
    """
    Model for product categories.
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('category_products', args=[self.slug])

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Product(models.Model):
    """
    Main model for products and projects.
    """
    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    slug = models.SlugField(max_length=120, unique=True)
    sku = models.CharField(max_length=100, unique=True)
    short_description = models.CharField(max_length=255)
    description = models.TextField()
    main_image = models.ImageField(upload_to='products/main/')
    alt_text = models.CharField(max_length=255, blank=True, null=True, help_text="Alt text for the main image.")
    youtube_video_url = models.URLField(max_length=500, blank=True, null=True)

    def get_alt_text(self):
        if self.alt_text:
            return self.alt_text
        return f"{self.name} - Professional Engineering Grade Hardware"

    liked_by = models.ManyToManyField(User, related_name='liked_products', blank=True)

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    discount_percentage = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Enter discount percentage (0–100)."
    )
    stock = models.PositiveIntegerField(validators=[MinValueValidator(0)])
    availability = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    
    # ✅ New field to distinguish project or product
    is_project = models.BooleanField(default=False, help_text="Check if this is a project; leave unchecked if it's a product.")
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    # ✅ SEO Fields
    meta_description = models.CharField(
        max_length=160,
        blank=True,
        null=True,
        help_text="Meta description for SEO (recommended max 160 characters)."
    )
    meta_keywords = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Comma-separated keywords for SEO."
    )

    # ✅ Content Enrichment Fields
    package_includes = models.TextField(
        blank=True,
        null=True,
        help_text="Items included in the box (one item per line, e.g. 1x ESP32 Board\n1x Pinout Guide)."
    )
    guarantee_text = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        default="Pre-tested & Quality Checked before dispatch across Pakistan. 100% Genuine Guaranteed.",
        help_text="Custom buyer quality assurance callout."
    )
    related_products = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=False,
        help_text="Select related products or accessories for cross-linking."
    )

    def get_package_includes_list(self):
        if not self.package_includes:
            return []
        return [item.strip() for item in self.package_includes.splitlines() if item.strip()]

    def is_liked_by_user(self, user):
        """Check if the product is liked by a specific user"""
        return self.liked_by.filter(id=user.id).exists() if user.is_authenticated else False

    @property
    def like_count(self):
        """Count of users who liked this product"""
        return self.liked_by.count()

    @property
    def final_price(self):
        """Price after applying discount"""
        if self.discount_percentage > 0:
            discount_amount = (self.price * Decimal(self.discount_percentage)) / Decimal(100)
            return self.price - discount_amount
        return self.price

    class Meta:
        ordering = ['name']
        verbose_name = "Product"
        verbose_name_plural = "Products"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('product_detail', args=[self.slug])

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)




class ProductVariant(models.Model):
    """
    Model for product variants (e.g., different colors or sizes).
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    title = models.CharField(max_length=100)
    image = models.ImageField(upload_to='products/variants/')
    alt_text = models.CharField(max_length=255, blank=True, null=True, help_text="Alt text for the variant image.")

    def get_alt_text(self):
        if self.alt_text:
            return self.alt_text
        return f"{self.product.name} - {self.title} - Professional Engineering Grade Hardware"

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']
        verbose_name = "Product Variant"
        verbose_name_plural = "Product Variants"
        constraints = [
            models.UniqueConstraint(fields=['product', 'title'], name='unique_product_variant')
        ]

    def __str__(self):
        return f"{self.product.name} - {self.title}"

class ProductImage(models.Model):
    """
    Model for additional product gallery images.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/gallery/')
    alt_text = models.CharField(max_length=255, blank=True, null=True, help_text="Alt text for the gallery image.")

    def get_alt_text(self):
        if self.alt_text:
            return self.alt_text
        return f"{self.product.name} - Professional Engineering Grade Hardware"

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['id']
        verbose_name = "Product Image"
        verbose_name_plural = "Product Images"

    def __str__(self):
        return f"Image for {self.product.name}"

class ProductFeature(models.Model):
    """
    Model for product features.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='features')
    title = models.CharField(max_length=100)
    feature = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']
        verbose_name = "Product Feature"
        verbose_name_plural = "Product Features"

    def __str__(self):
        return f"{self.title} - {self.product.name}"

class ProductSpecification(models.Model):
    """
    Model for product specifications.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='specifications')
    key = models.CharField(max_length=100)
    value = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['key']
        verbose_name = "Product Specification"
        verbose_name_plural = "Product Specifications"
        constraints = [
            models.UniqueConstraint(fields=['product', 'key'], name='unique_product_specification')
        ]

    def __str__(self):
        return f"{self.key}: {self.value} ({self.product.name})"

class ProductReview(models.Model):
    """
    Model for product reviews.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    reviewer_name = models.CharField(max_length=100)
    rating = models.IntegerField(choices=[(i, f'{i} Star') for i in range(1, 6)])
    review = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)  # Changed to DateTimeField for consistency
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Product Review"
        verbose_name_plural = "Product Reviews"

    def __str__(self):
        return f"Review by {self.reviewer_name} - {self.rating} Stars"

class Cart(models.Model):
    """
    Model for shopping cart, supporting both authenticated and anonymous users.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='carts')
    session_key = models.CharField(max_length=40, null=True, blank=True)  # For anonymous users
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Cart"
        verbose_name_plural = "Carts"

    def __str__(self):
        return f"Cart {'for ' + str(self.user) if self.user else 'anonymous: ' + str(self.session_key)}"

class CartItem(models.Model):
    """
    Model for items in a cart.
    """
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cart_items')
    variant = models.ForeignKey(ProductVariant, null=True, blank=True, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    @property
    def total_price(self):
        return self.price * self.quantity

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Cart Item"
        verbose_name_plural = "Cart Items"
        constraints = [
            models.UniqueConstraint(fields=['cart', 'product', 'variant'], name='unique_cart_item')
        ]

    def __str__(self):
        return f"{self.quantity} x {self.product.name} ({self.variant.title if self.variant else 'No Variant'})"
    
from django.db import models
from django.contrib.auth.models import User

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    session_key = models.CharField(max_length=32, null=True, blank=True)
    email = models.EmailField()
    payment_method = models.CharField(max_length=50, choices=[('online_payment', 'Online Payment'), ('cash_on_delivery', 'Cash on Delivery')])
    payment_slip = models.FileField(upload_to='payment_slips/', null=True, blank=True)
    country = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100)
    address = models.TextField()
    apartment = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    phone = models.CharField(max_length=20)
    save_info = models.BooleanField(default=False)
    text_offers = models.BooleanField(default=False)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} by {self.email}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey('Product', on_delete=models.SET_NULL, null=True)
    variant = models.ForeignKey('ProductVariant', on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} (Order {self.order.id})"

    @property
    def total_price(self):
        return self.price * self.quantity

from django.db import models

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Message from {self.name} - {self.subject}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Contact Message'
        verbose_name_plural = 'Contact Messages'

# class WhatsAppOrderTrack(models.Model):
#     product = models.ForeignKey('Product', on_delete=models.CASCADE)
#     user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
#     timestamp = models.DateTimeField(default=timezone.now)

#     def __str__(self):
#         return f"WhatsApp order for {self.product.name} at {self.timestamp}"


class SiteConfiguration(models.Model):
    """
    Configuration model for site-specific settings like Meta Pixel ID.
    Extends the Django Sites framework.
    """
    site = models.OneToOneField(Site, on_delete=models.CASCADE, related_name='configuration')
    meta_pixel_id = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        help_text="Enter the Meta Pixel ID for this site (e.g. 1664993358009540)"
    )

    class Meta:
        verbose_name = "Site Configuration"
        verbose_name_plural = "Site Configurations"

    def __str__(self):
        return f"Configuration for {self.site.domain}"


class BlogPost(models.Model):
    """
    Project Guides, Tutorials, and Engineering Blog Posts designed to capture
    high-intent organic search queries and funnel readers to buy kits & codes.
    """
    CATEGORY_CHOICES = [
        ('ai-ml', 'AI & Machine Learning'),
        ('iot-embedded', 'IoT & Embedded Systems'),
        ('robotics-hardware', 'Robotics & Hardware'),
        ('fyp-guides', 'Final Year Project (FYP) Guides'),
        ('tutorials', 'DIY Tutorials & How-To'),
    ]

    title = models.CharField(max_length=255, verbose_name="Article Title")
    slug = models.SlugField(max_length=280, unique=True, help_text="Unique URL slug")
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='tutorials')
    featured_image = models.ImageField(upload_to='blog/images/', blank=True, null=True)
    excerpt = models.TextField(max_length=500, help_text="Short summary for article cards and meta description")
    content = models.TextField(help_text="Full article content in HTML or Markdown")
    author = models.CharField(max_length=100, default="ISOL Engineering Team")
    reading_time = models.CharField(max_length=20, default="5 min read")
    is_featured = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)
    views_count = models.PositiveIntegerField(default=0)
    
    # SEO fields
    meta_title = models.CharField(max_length=200, blank=True, null=True)
    meta_description = models.TextField(max_length=300, blank=True, null=True)
    meta_keywords = models.CharField(max_length=255, blank=True, null=True)
    
    # Related products embedded in this tutorial
    related_products = models.ManyToManyField(
        'Product', 
        blank=True, 
        related_name='blog_posts', 
        help_text="Products/kits mentioned in this tutorial for 1-click buying"
    )
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_featured', '-created_at']
        verbose_name = "Blog & Tutorial Post"
        verbose_name_plural = "Blog & Tutorial Posts"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('blog_detail', kwargs={'slug': self.slug})


class ItemQuestion(models.Model):
    """
    Community Q&A for Products, Projects, and Blog Tutorials.
    Empowers AEO/GEO indexing by capturing long-tail user queries and providing verified answers.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='item_questions')
    product = models.ForeignKey('Product', on_delete=models.CASCADE, null=True, blank=True, related_name='questions')
    blog_post = models.ForeignKey('BlogPost', on_delete=models.CASCADE, null=True, blank=True, related_name='questions')
    question = models.TextField(verbose_name="Question")
    answer = models.TextField(blank=True, null=True, verbose_name="Official Answer")
    answered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='answered_questions')
    answered_at = models.DateTimeField(null=True, blank=True)
    is_approved = models.BooleanField(default=True, help_text="Approved questions are visible to all visitors")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Community Question"
        verbose_name_plural = "Community Questions"

    def __str__(self):
        target = self.product.name if self.product else (self.blog_post.title if self.blog_post else "General")
        return f"{self.user.username}: {self.question[:40]} ({target})"