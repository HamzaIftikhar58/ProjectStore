import json
import secrets
from decimal import Decimal
from django.conf import settings
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from Store.models import (
    Product, Category, ProductSpecification, ProductFeature,
    ProductVariant, ProductImage
)


def _verify_token(request):
    """
    Validate the incoming request token against settings.PROJECTSTORE_MCP_TOKEN.
    Accepts:
      - Header 'X-ProjectStore-Token'
      - Header 'Authorization: Bearer <token>' or 'Authorization: <token>'
    """
    expected_token = getattr(settings, 'PROJECTSTORE_MCP_TOKEN', None)
    if not expected_token:
        return False

    auth_header = request.headers.get('X-ProjectStore-Token') or request.META.get('HTTP_X_PROJECTSTORE_TOKEN')
    if not auth_header:
        auth_raw = request.headers.get('Authorization') or request.META.get('HTTP_AUTHORIZATION', '')
        if auth_raw.startswith('Bearer '):
            auth_header = auth_raw[7:].strip()
        else:
            auth_header = auth_raw.strip()

    if not auth_header:
        return False

    return secrets.compare_digest(auth_header, expected_token)


def _find_product(identifier):
    """Locate a product by ID, SKU, or slug."""
    if not identifier:
        return None
    if isinstance(identifier, int) or (isinstance(identifier, str) and identifier.isdigit()):
        p = Product.objects.filter(id=int(identifier)).first()
        if p:
            return p
    p = Product.objects.filter(sku=str(identifier).strip()).first()
    if p:
        return p
    return Product.objects.filter(slug=str(identifier).strip()).first()


def _calculate_product_health(product):
    """Calculate completeness score (0-100%) and identify missing elements."""
    issues = []
    score = 100

    # Description check
    word_count = len(product.description.split()) if product.description else 0
    if not product.description or word_count == 0:
        issues.append("missing_description")
        score -= 25
    elif word_count < 40:
        issues.append("thin_description")
        score -= 10

    if not product.short_description:
        issues.append("missing_short_description")
        score -= 10

    # SEO checks
    if not product.meta_description:
        issues.append("missing_meta_description")
        score -= 15
    elif len(product.meta_description) > 160:
        issues.append("meta_description_too_long")
        score -= 5

    if not product.meta_keywords:
        issues.append("missing_meta_keywords")
        score -= 5

    # Alt text
    if not product.alt_text:
        issues.append("missing_alt_text")
        score -= 10

    # Specifications
    specs_count = product.specifications.count()
    if specs_count == 0:
        issues.append("missing_specifications")
        score -= 15

    # Package includes
    if not product.package_includes:
        issues.append("missing_package_includes")
        score -= 10

    # Stock vs Active
    if product.is_active and product.stock == 0:
        issues.append("out_of_stock_active")
        score -= 5

    score = max(0, min(100, score))
    return {
        "score": score,
        "word_count": word_count,
        "specs_count": specs_count,
        "issues": issues,
    }


@csrf_exempt
def mcp_endpoint(request):
    """Main dispatch endpoint for all MCP operations."""
    if request.method != 'POST':
        return JsonResponse({"status": "error", "message": "Method not allowed. POST required."}, status=405)

    if not _verify_token(request):
        return JsonResponse({"status": "error", "message": "Unauthorized. Invalid or missing MCP token."}, status=403)

    try:
        data = json.loads(request.body.decode('utf-8')) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON body."}, status=400)

    action = data.get("action")
    if not action:
        return JsonResponse({"status": "error", "message": "Missing 'action' parameter in request."}, status=400)

    # 1. Health check
    if action == "health_check":
        return JsonResponse({
            "status": "success",
            "message": "ProjectStore MCP Bridge is online and authenticated.",
            "data": {
                "total_products": Product.objects.count(),
                "active_products": Product.objects.filter(is_active=True).count(),
                "categories_count": Category.objects.count(),
                "specifications_count": ProductSpecification.objects.count(),
                "features_count": ProductFeature.objects.count(),
                "variants_count": ProductVariant.objects.count(),
            }
        })

    # 2. Audit Catalog
    elif action == "audit_catalog":
        category_slug = data.get("category_slug")
        limit = int(data.get("limit", 50))
        offset = int(data.get("offset", 0))

        qs = Product.objects.all().select_related('category').prefetch_related('specifications')
        if category_slug:
            qs = qs.filter(category__slug=category_slug)

        total_matching = qs.count()
        products = qs.order_by('id')[offset:offset + limit]

        audited_list = []
        total_score = 0
        issue_counts = {
            "missing_description": 0,
            "thin_description": 0,
            "missing_short_description": 0,
            "missing_meta_description": 0,
            "missing_meta_keywords": 0,
            "missing_alt_text": 0,
            "missing_specifications": 0,
            "missing_package_includes": 0,
            "out_of_stock_active": 0,
        }

        for p in products:
            health = _calculate_product_health(p)
            total_score += health["score"]
            for issue in health["issues"]:
                if issue in issue_counts:
                    issue_counts[issue] += 1

            audited_list.append({
                "id": p.id,
                "name": p.name,
                "sku": p.sku,
                "slug": p.slug,
                "category": p.category.name,
                "price": str(p.price),
                "stock": p.stock,
                "is_active": p.is_active,
                "is_project": p.is_project,
                "health_score": health["score"],
                "word_count": health["word_count"],
                "specs_count": health["specs_count"],
                "issues": health["issues"],
            })

        # Sort audited products by lowest health score first (prioritize items needing work)
        audited_list.sort(key=lambda x: x["health_score"])

        avg_score = round(total_score / len(audited_list), 1) if audited_list else 100

        return JsonResponse({
            "status": "success",
            "data": {
                "total_matching": total_matching,
                "returned_count": len(audited_list),
                "average_health_score": avg_score,
                "issue_summary": issue_counts,
                "products": audited_list,
            }
        })

    # 3. List Products
    elif action == "list_products":
        query = data.get("query", "").strip()
        category_slug = data.get("category_slug", "").strip()
        is_active = data.get("is_active")
        is_project = data.get("is_project")
        limit = min(int(data.get("limit", 20)), 100)
        offset = int(data.get("offset", 0))

        qs = Product.objects.all().select_related('category')
        if query:
            qs = qs.filter(name__icontains=query) | qs.filter(sku__icontains=query)
        if category_slug:
            qs = qs.filter(category__slug=category_slug)
        if is_active is not None:
            qs = qs.filter(is_active=bool(is_active))
        if is_project is not None:
            qs = qs.filter(is_project=bool(is_project))

        total_count = qs.count()
        products = qs.order_by('-updated_at')[offset:offset + limit]

        results = [{
            "id": p.id,
            "name": p.name,
            "sku": p.sku,
            "slug": p.slug,
            "category": p.category.name,
            "price": str(p.price),
            "discount_percentage": p.discount_percentage,
            "final_price": str(p.final_price),
            "stock": p.stock,
            "is_active": p.is_active,
            "is_project": p.is_project,
            "short_description": p.short_description,
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        } for p in products]

        return JsonResponse({
            "status": "success",
            "data": {
                "total_count": total_count,
                "limit": limit,
                "offset": offset,
                "products": results,
            }
        })

    # 4. Get Product Details
    elif action == "get_product":
        identifier = data.get("identifier")
        p = _find_product(identifier)
        if not p:
            return JsonResponse({"status": "error", "message": f"Product '{identifier}' not found."}, status=404)

        specs = [{"id": s.id, "key": s.key, "value": s.value} for s in p.specifications.all()]
        features = [{"id": f.id, "title": f.title, "feature": f.feature} for f in p.features.all()]
        variants = [{
            "id": v.id,
            "title": v.title,
            "price": str(v.price),
            "is_active": v.is_active,
            "alt_text": v.alt_text,
            "image": v.image.url if v.image else None
        } for v in p.variants.all()]
        images = [{
            "id": img.id,
            "image": img.image.url if img.image else None,
            "alt_text": img.alt_text
        } for img in p.images.all()]
        related = [{
            "id": r.id,
            "name": r.name,
            "slug": r.slug,
            "sku": r.sku,
            "price": str(r.price)
        } for r in p.related_products.all()]

        health = _calculate_product_health(p)

        return JsonResponse({
            "status": "success",
            "data": {
                "id": p.id,
                "name": p.name,
                "slug": p.slug,
                "sku": p.sku,
                "category": {
                    "id": p.category.id,
                    "name": p.category.name,
                    "slug": p.category.slug,
                },
                "price": str(p.price),
                "discount_percentage": p.discount_percentage,
                "final_price": str(p.final_price),
                "stock": p.stock,
                "availability": p.availability,
                "is_active": p.is_active,
                "is_project": p.is_project,
                "short_description": p.short_description,
                "description": p.description,
                "main_image": p.main_image.url if p.main_image else None,
                "alt_text": p.alt_text,
                "youtube_video_url": p.youtube_video_url,
                "meta_description": p.meta_description,
                "meta_keywords": p.meta_keywords,
                "package_includes": p.package_includes,
                "package_includes_list": p.get_package_includes_list(),
                "guarantee_text": p.guarantee_text,
                "specifications": specs,
                "features": features,
                "variants": variants,
                "gallery_images": images,
                "related_products": related,
                "health": health,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None,
            }
        })

    # 5. Update Product
    elif action == "update_product":
        identifier = data.get("identifier")
        p = _find_product(identifier)
        if not p:
            return JsonResponse({"status": "error", "message": f"Product '{identifier}' not found."}, status=404)

        updates = data.get("updates", {})
        dry_run = bool(data.get("dry_run", False))

        allowed_fields = [
            'name', 'short_description', 'description', 'meta_description',
            'meta_keywords', 'alt_text', 'package_includes', 'guarantee_text',
            'youtube_video_url', 'stock', 'availability', 'is_active', 'is_project'
        ]
        decimal_fields = ['price', 'discount_percentage']

        diff = {}
        for field in allowed_fields:
            if field in updates:
                old_val = getattr(p, field)
                new_val = updates[field]
                if old_val != new_val:
                    diff[field] = {"old": old_val, "new": new_val}

        for field in decimal_fields:
            if field in updates:
                old_val = getattr(p, field)
                new_val = Decimal(str(updates[field]))
                if old_val != new_val:
                    diff[field] = {"old": str(old_val), "new": str(new_val)}

        if not diff:
            return JsonResponse({
                "status": "success",
                "message": "No changes detected.",
                "data": {"diff": {}, "dry_run": dry_run}
            })

        if dry_run:
            return JsonResponse({
                "status": "success",
                "message": f"Dry run: {len(diff)} field(s) would be updated for '{p.name}'.",
                "data": {"diff": diff, "dry_run": True}
            })

        # Apply changes atomically
        with transaction.atomic():
            for field in allowed_fields:
                if field in updates:
                    setattr(p, field, updates[field])
            for field in decimal_fields:
                if field in updates:
                    setattr(p, field, Decimal(str(updates[field])))
            p.save()

        return JsonResponse({
            "status": "success",
            "message": f"Successfully updated '{p.name}'.",
            "data": {"diff": diff, "dry_run": False}
        })

    # 6. Update Specifications
    elif action == "update_specifications":
        identifier = data.get("identifier")
        p = _find_product(identifier)
        if not p:
            return JsonResponse({"status": "error", "message": f"Product '{identifier}' not found."}, status=404)

        specs_input = data.get("specifications", [])
        mode = data.get("mode", "merge")  # "merge" or "replace"
        dry_run = bool(data.get("dry_run", False))

        # Convert dict to list if needed: {"Key": "Val"} -> [{"key": "Key", "value": "Val"}]
        if isinstance(specs_input, dict):
            specs_list = [{"key": k, "value": str(v)} for k, v in specs_input.items()]
        else:
            specs_list = specs_input

        if dry_run:
            return JsonResponse({
                "status": "success",
                "message": f"Dry run: Would apply {len(specs_list)} specifications to '{p.name}' in '{mode}' mode.",
                "data": {
                    "dry_run": True,
                    "mode": mode,
                    "target_specifications": specs_list,
                }
            })

        with transaction.atomic():
            if mode == "replace":
                p.specifications.all().delete()

            applied = []
            for item in specs_list:
                k = str(item.get("key", "")).strip()
                v = str(item.get("value", "")).strip()
                if not k:
                    continue
                spec_obj, _ = ProductSpecification.objects.update_or_create(
                    product=p,
                    key=k,
                    defaults={"value": v}
                )
                applied.append({"key": spec_obj.key, "value": spec_obj.value})

        return JsonResponse({
            "status": "success",
            "message": f"Applied {len(applied)} specifications to '{p.name}'.",
            "data": {
                "dry_run": False,
                "applied_specifications": applied,
            }
        })

    # 7. Update Features
    elif action == "update_features":
        identifier = data.get("identifier")
        p = _find_product(identifier)
        if not p:
            return JsonResponse({"status": "error", "message": f"Product '{identifier}' not found."}, status=404)

        features_input = data.get("features", [])
        mode = data.get("mode", "merge")  # "merge" or "replace"
        dry_run = bool(data.get("dry_run", False))

        if dry_run:
            return JsonResponse({
                "status": "success",
                "message": f"Dry run: Would apply {len(features_input)} features to '{p.name}' in '{mode}' mode.",
                "data": {
                    "dry_run": True,
                    "mode": mode,
                    "target_features": features_input,
                }
            })

        with transaction.atomic():
            if mode == "replace":
                p.features.all().delete()

            applied = []
            for item in features_input:
                title = str(item.get("title", "")).strip()
                desc = str(item.get("feature", "")).strip()
                if not title:
                    continue
                feat_obj, _ = ProductFeature.objects.update_or_create(
                    product=p,
                    title=title,
                    defaults={"feature": desc}
                )
                applied.append({"title": feat_obj.title, "feature": feat_obj.feature})

        return JsonResponse({
            "status": "success",
            "message": f"Applied {len(applied)} features to '{p.name}'.",
            "data": {
                "dry_run": False,
                "applied_features": applied,
            }
        })

    return JsonResponse({"status": "error", "message": f"Unknown action '{action}'."}, status=400)
