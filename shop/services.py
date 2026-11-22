from decimal import Decimal

from django.db import transaction
from rest_framework.exceptions import ValidationError

from .models import Order, OrderItem, Product


@transaction.atomic
def place_order(user, items):
    """Create an order, check stock, calculate the total and reduce stock.
    Everything runs in one transaction: if any step fails, nothing is saved.
    """
    product_ids = [item['product'].id for item in items]
    products = Product.objects.select_for_update().filter(id__in=product_ids)
    products_by_id = {product.id: product for product in products}

    order = Order.objects.create(user=user)
    total = Decimal('0.00')

    for item in items:
        product = products_by_id[item['product'].id]
        quantity = item['quantity']

        if product.stock < quantity:
            raise ValidationError({
                'detail': f'Not enough stock for "{product.name}". '
                          f'Available: {product.stock}.'
            })

        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=quantity,
            price_at_purchase=product.price,
        )
        product.stock -= quantity
        product.save(update_fields=['stock', 'updated_at'])
        total += product.price * quantity

    order.total_amount = total
    order.save(update_fields=['total_amount'])
    return order