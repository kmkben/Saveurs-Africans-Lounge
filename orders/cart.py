from decimal import Decimal

from menu.models import Dish


class Cart:
    SESSION_KEY = "cart"

    def __init__(self, request):
        self.session = request.session

        cart = self.session.get(self.SESSION_KEY)

        if cart is None:
            cart = self.session[self.SESSION_KEY] = {}

        self.cart = cart

    def add(self, dish, quantity=1, override_quantity=False):
        dish_id = str(dish.pk)

        if dish_id not in self.cart:
            self.cart[dish_id] = {
                "quantity": 0,
                "price": str(dish.price),
            }

        if override_quantity:
            self.cart[dish_id]["quantity"] = quantity
        else:
            self.cart[dish_id]["quantity"] += quantity

        self.save()

    def remove(self, dish):
        dish_id = str(dish.pk)

        if dish_id in self.cart:
            del self.cart[dish_id]
            self.save()

    def save(self):
        self.session.modified = True

    def clear(self):
        self.session.pop(self.SESSION_KEY, None)
        self.session.modified = True

    def __len__(self):
        return sum(
            item["quantity"]
            for item in self.cart.values()
        )

    def __iter__(self):
        dish_ids = self.cart.keys()

        dishes = Dish.objects.filter(
            pk__in=dish_ids,
        )

        dishes_map = {
            str(dish.pk): dish
            for dish in dishes
        }

        for dish_id, stored_item in self.cart.items():
            dish = dishes_map.get(dish_id)

            if dish is None:
                continue

            # IMPORTANT:
            # copy the individual item so we never mutate
            # the dictionary stored inside the Django session.
            item = stored_item.copy()

            price = Decimal(item["price"])

            item["dish"] = dish
            item["price"] = price
            item["total_price"] = (
                price * item["quantity"]
            )

            yield item

    @property
    def subtotal(self):
        return sum(
            (
                Decimal(item["price"])
                * item["quantity"]
                for item in self.cart.values()
            ),
            Decimal("0.00"),
        )