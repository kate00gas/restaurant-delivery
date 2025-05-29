import requests
import json
import uuid
from decimal import Decimal
import os
from dotenv import load_dotenv
from app.models.order import OrderStatusEnum

try:
    from rich import print
except ImportError:
    print("Rich library not found, using standard print.")

load_dotenv()
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")

# Global variable to store the access token
access_token = None

# ----- Authentication Functions -----
def login():
    """Prompt for username and password and get access token."""
    global access_token
    username = input("Enter username: ")
    password = input("Enter password: ")
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/login",
            data={"username": username, "password": password}
        )
        response.raise_for_status()
        token_data = response.json()
        access_token = token_data["access_token"]
        print("[green]Login successful![/green]")
        return True
    except requests.exceptions.RequestException as e:
        print(f"[red]Login failed: {e}[/red]")
        return False

# ----- Modified API Functions to Include Token -----
def get_headers():
    """Return headers with Authorization token if available."""
    headers = {}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    return headers

def get_all_orders():
    try:
        response = requests.get(f"{API_BASE_URL}/admin/orders/", headers=get_headers())
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[Error fetching orders]: {e}")
        return None

def get_order_details(order_id: str):
    try:
        response = requests.get(f"{API_BASE_URL}/admin/orders/{order_id}", headers=get_headers())
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[Error fetching order details]: {e}")
        return None

def update_order_status(order_id: str, status: str):
    try:
        response = requests.patch(
            f"{API_BASE_URL}/admin/orders/{order_id}",
            json={"status": status},
            headers=get_headers()
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[Error updating order]: {e}")
        return None

def get_all_restaurants():
    try:
        response = requests.get(f"{API_BASE_URL}/admin/restaurants/", headers=get_headers())
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[Error fetching restaurants]: {e}")
        return None

def get_all_restaurant_menu(restaurant_id: str):
    try:
        response = requests.get(f"{API_BASE_URL}/admin/restaurants/{restaurant_id}/menu/", headers=get_headers())
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[Error fetching menu]: {e}")
        return None

def delete_restaurant(restaurant_id: str):
    try:
        response = requests.delete(f"{API_BASE_URL}/admin/restaurants/{restaurant_id}", headers=get_headers())
        response.raise_for_status()
        return response.status_code == 204
    except requests.exceptions.RequestException as e:
        print(f"[Error deleting restaurant]: {e}")
        return False

def delete_menu_item(item_id: str):
    try:
        response = requests.delete(f"{API_BASE_URL}/admin/menu-items/{item_id}", headers=get_headers())
        response.raise_for_status()
        return response.status_code == 204
    except requests.exceptions.RequestException as e:
        print(f"[Error deleting menu item]: {e}")
        return False

def create_restaurant(name: str, description: str, address: str, phone_number: str, email: str, latitude: float, longitude: float):
    try:
        response = requests.post(
            f"{API_BASE_URL}/admin/restaurants/",
            json={
                "name": name,
                "description": description,
                "address": address,
                "phone_number": phone_number,
                "email": email,
                "latitude": latitude,
                "longitude": longitude,
                "is_active": False
            },
            headers=get_headers()
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[Error creating restaurant]: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"[Response details]: {e.response.text}")
        return None

def create_menu_item(restaurant_id: str, name: str, description: str, price: float, category: str, is_available: bool):
    try:
        response = requests.post(
            f"{API_BASE_URL}/admin/menu-items/",
            json={
                "restaurant_id": restaurant_id,
                "name": name,
                "description": description,
                "price": price,
                "category": category,
                "is_available": is_available
            },
            headers=get_headers()
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[Error creating menu item]: {e}")
        return None

def get_all_users():
    try:
        response = requests.get(f"{API_BASE_URL}/admin/users/", headers=get_headers())
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[Error fetching users]: {e}")
        return None

# ----- Display Functions -----
def display_orders(orders):
    if not orders:
        print("No orders found")
        return
    print("\nAll Orders:")
    print("=" * 80)
    for order in orders:
        restaurant = order.get('restaurant', {})
        print(f"Order ID: {order.get('order_id', 'N/A')}")
        print(f"User ID: {order.get('user_id', 'N/A')}")
        print(f"Restaurant ID: {order.get('restaurant_id', 'N/A')}")
        print(f"Restaurant Name: {restaurant.get('name', 'N/A')}")
        print(f"Status: {order.get('status', 'N/A')}")
        print(f"Total Amount: {order.get('total_amount', '0.00')}")
        print(f"Delivery Address: {order.get('delivery_address', 'N/A')}")
        print(f"Created At: {order.get('created_at', 'N/A')}")
        print(f"Updated At: {order.get('updated_at', 'N/A')}")
        print("Items:")
        for item in order.get('items', []):
            item_name = item.get('menu_item', {}).get('name', 'N/A')
            print(f"  - Item ID: {item.get('item_id', 'N/A')}")
            print(f"    Name: {item_name}")
            print(f"    Quantity: {item.get('quantity', 0)}")
            print(f"    Price per Item: {item.get('price_per_item', '0.00')}")
            print(f"    Total: {Decimal(str(item.get('price_per_item', 0))) * item.get('quantity', 0)}")
        print("-" * 80)

def display_restaurants(restaurants):
    if not restaurants:
        print("No restaurants found")
        return
    print("\nAll Restaurants:")
    print("=" * 80)
    for restaurant in restaurants:
        print(f"Restaurant ID: {restaurant.get('restaurant_id', 'N/A')}")
        print(f"Name: {restaurant.get('name', 'N/A')}")
        print(f"Description: {restaurant.get('description', 'N/A')}")
        print(f"Address: {restaurant.get('address', 'N/A')}")
        print(f"Phone Number: {restaurant.get('phone_number', 'N/A')}")
        print(f"Email: {restaurant.get('email', 'N/A')}")
        print(f"Is Active: {restaurant.get('is_active', False)}")
        print(f"Latitude: {restaurant.get('latitude', 'N/A')}")
        print(f"Longitude: {restaurant.get('longitude', 'N/A')}")
        print(f"Created At: {restaurant.get('created_at', 'N/A')}")
        print(f"Updated At: {restaurant.get('updated_at', 'N/A')}")
        print("-" * 80)

def display_menu(menu_items):
    if not menu_items:
        print("No menu items found")
        return
    print("\nAll Menu Items:")
    print("=" * 80)
    for item in menu_items:
        print(f"Item ID: {item.get('item_id', 'N/A')}")
        print(f"Restaurant ID: {item.get('restaurant_id', 'N/A')}")
        print(f"Name: {item.get('name', 'N/A')}")
        print(f"Description: {item.get('description', 'N/A')}")
        print(f"Price: {item.get('price', '0.00')}")
        print(f"Category: {item.get('category', 'N/A')}")
        print(f"Is Available: {item.get('is_available', True)}")
        print(f"Created At: {item.get('created_at', 'N/A')}")
        print(f"Updated At: {item.get('updated_at', 'N/A')}")
        print("-" * 80)

def display_order_details(order):
    if not order:
        print("Order not found")
        return
    print("\nOrder Details:")
    print("=" * 80)
    print(f"Order ID: {order.get('order_id', 'N/A')}")
    print(f"User ID: {order.get('user_id', 'N/A')}")
    print(f"Restaurant ID: {order.get('restaurant_id', 'N/A')}")
    print(f"Restaurant Name: {order.get('restaurant', {}).get('name', 'N/A')}")
    print(f"Status: {order.get('status', 'N/A')}")
    print(f"Total Amount: {order.get('total_amount', '0.00')}")
    print(f"Delivery Address: {order.get('delivery_address', 'N/A')}")
    print(f"Created At: {order.get('created_at', 'N/A')}")
    print(f"Updated At: {order.get('updated_at', 'N/A')}")
    print("Items:")
    for item in order.get('items', []):
        item_name = item.get('menu_item', {}).get('name', 'N/A')
        print(f"  - Item ID: {item.get('item_id', 'N/A')}")
        print(f"    Name: {item_name}")
        print(f"    Quantity: {item.get('quantity', 0)}")
        print(f"    Price per Item: {item.get('price_per_item', '0.00')}")
        print(f"    Total: {Decimal(str(item.get('price_per_item', 0))) * item.get('quantity', 0)}")
    print("-" * 80)

def display_users(users):
    if not users:
        print("No users found")
        return
    print("\nAll Users:")
    print("=" * 80)
    for user in users:
        print(f"User ID: {user.get('user_id', 'N/A')}")
        print(f"Username: {user.get('username', 'N/A')}")
        print(f"Role: {user.get('role', 'N/A')}")
        print(f"Phone Number: {user.get('phone_number', 'N/A')}")
        print(f"Is Active: {user.get('is_active', False)}")
        print(f"Created At: {user.get('created_at', 'N/A')}")
        print(f"Updated At: {user.get('updated_at', 'N/A')}")
        print("-" * 80)

# ----- Updated Main Menu -----
def admin_cli():
    global access_token
    # Require login before accessing the admin panel
    print("\n[bold yellow]Admin Login Required[/bold yellow]")
    if not login():
        print("Exiting due to failed login.")
        return

    while True:
        print("\n[Admin Panel]")
        print("1. List Restaurants")
        print("2. View Restaurant Menu")
        print("3. List All Orders")
        print("4. Update Order Status")
        print("5. Delete Restaurant")
        print("6. Delete Menu Item")
        print("7. View Order Details")
        print("8. Create Restaurant")
        print("9. Create Menu Item")
        print("10. List All Users")
        print("0. Exit")

        choice = input("Enter your choice: ")

        if choice == '1':
            restaurants = get_all_restaurants()
            display_restaurants(restaurants)

        elif choice == '2':
            restaurant_id = input("Enter Restaurant ID: ")
            try:
                uuid.UUID(restaurant_id)
                menu_data = get_all_restaurant_menu(restaurant_id)
                display_menu(menu_data)
            except ValueError:
                print("[Error] Invalid Restaurant ID format. Must be a valid UUID.")

        elif choice == '3':
            orders = get_all_orders()
            display_orders(orders)

        elif choice == '4':
            order_id = input("Enter Order ID: ")
            try:
                uuid.UUID(order_id)
                print("Available statuses: pending_confirmation, confirmed, preparing, ready_for_pickup, delivered, cancelled")
                status = input("Enter new status: ")
                if status not in [e.value for e in OrderStatusEnum]:
                    print(f"[Error] Invalid status. Must be one of: {[e.value for e in OrderStatusEnum]}")
                    continue
                result = update_order_status(order_id, status)
                if result:
                    print("Status updated successfully!")
                else:
                    print("[Error] Failed to update status.")
            except ValueError:
                print("[Error] Invalid Order ID format. Must be a valid UUID.")

        elif choice == '5':
            restaurant_id = input("Enter Restaurant ID to delete: ")
            try:
                uuid.UUID(restaurant_id)
                if delete_restaurant(restaurant_id):
                    print("Restaurant deleted successfully!")
                else:
                    print("[Error] Failed to delete restaurant.")
            except ValueError:
                print("[Error] Invalid Restaurant ID format. Must be a valid UUID.")

        elif choice == '6':
            item_id = input("Enter Menu Item ID to delete: ")
            try:
                uuid.UUID(item_id)
                if delete_menu_item(item_id):
                    print("Menu item deleted successfully!")
                else:
                    print("[Error] Failed to delete menu item.")
            except ValueError:
                print("[Error] Invalid Menu Item ID format. Must be a valid UUID.")

        elif choice == '7':
            order_id = input("Enter Order ID: ")
            try:
                uuid.UUID(order_id)
                order = get_order_details(order_id)
                display_order_details(order)
            except ValueError:
                print("[Error] Invalid Order ID format. Must be a valid UUID.")

        elif choice == '8':
            name = input("Enter Restaurant Name: ")
            description = input("Enter Description (or press Enter to skip): ") or None
            address = input("Enter Address: ")
            phone_number = input("Enter Phone Number (or press Enter to skip): ") or None
            email = input("Enter Email (or press Enter to skip): ") or None
            latitude = input("Enter latitude (or press Enter for None): ")
            longitude = input("Enter longitude (or press Enter for None): ")
            try:
                latitude = float(latitude) if latitude else None
                longitude = float(longitude) if longitude else None
                result = create_restaurant(name, description, address, phone_number, email, latitude, longitude)
                if result:
                    print(f"Restaurant created successfully: {result['restaurant_id']}")
                else:
                    print("[Error] Failed to create restaurant.")
            except ValueError:
                print("[Error] Invalid latitude or longitude format.")

        elif choice == '9':
            restaurant_id = input("Enter Restaurant ID: ")
            try:
                uuid.UUID(restaurant_id)
                name = input("Enter Menu Item Name: ")
                description = input("Enter Description (or press Enter to skip): ") or None
                price = input("Enter Price: ")
                category = input("Enter Category (or press Enter to skip): ") or None
                is_available = input("Is Available? (y/n, default y): ").lower() in ('y', '')
                try:
                    price = float(price)
                    result = create_menu_item(restaurant_id, name, description, price, category, is_available)
                    if result:
                        print(f"Menu item created successfully: {result['item_id']}")
                    else:
                        print("[Error] Failed to create menu item.")
                except ValueError:
                    print("[Error] Invalid Price format.")
            except ValueError:
                print("[Error] Invalid Restaurant ID format. Must be a valid UUID.")

        elif choice == '10':
            users = get_all_users()
            display_users(users)

        elif choice == '0':
            print("Exiting admin panel.")
            break

        else:
            print("Invalid choice, try again.")

if __name__ == "__main__":
    admin_cli()



# import requests
# import json
# import uuid
# from decimal import Decimal
# import os
# from dotenv import load_dotenv
# from client import (
#     get_restaurants,
#     get_restaurant_menu,
#     display_restaurants,
#     display_menu
# )
#
# from app.models.order import OrderStatusEnum
#
# try:
#     from rich import print
#     from rich.table import Table
# except ImportError:
#     print("Rich library not found, using standard print.")
#
# load_dotenv()
# API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
#
#
# # ----- Расширенные API-функции для админа -----
# def get_all_orders():
#     """Получить все заказы"""
#     try:
#         response = requests.get(f"{API_BASE_URL}/admin/orders/")
#         response.raise_for_status()
#         return response.json()
#     except requests.exceptions.RequestException as e:
#         print(f"[Error fetching orders]: {e}")
#         return None
#
#
# def update_order_status(order_id: str, status: str):
#     """Обновить статус заказа"""
#     try:
#         response = requests.patch(
#             f"{API_BASE_URL}/admin/orders/{order_id}",
#             json={"status": status}
#         )
#         response.raise_for_status()
#         return response.json()
#     except requests.exceptions.RequestException as e:
#         print(f"[Error updating order]: {e}")
#         return None
#
#
# def delete_restaurant(restaurant_id: str):
#     """Удалить ресторан"""
#     try:
#         response = requests.delete(f"{API_BASE_URL}/admin/restaurants/{restaurant_id}")
#         response.raise_for_status()
#         return response.status_code == 204
#     except requests.exceptions.RequestException as e:
#         print(f"[Error deleting restaurant]: {e}")
#         return False
#
#
# def delete_menu_item(item_id: str):
#     """Удалить пункт меню"""
#     try:
#         response = requests.delete(f"{API_BASE_URL}/admin/menu-items/{item_id}")
#         response.raise_for_status()
#         return response.status_code == 204
#     except requests.exceptions.RequestException as e:
#         print(f"[Error deleting menu item]: {e}")
#         return False
#
#
# # ----- Функции отображения -----
# def display_orders(orders):
#     """Отобразить заказы"""
#     if not orders:
#         print("No orders found")
#         return
#
#     table = Table(title="All Orders")
#     table.add_column("Order ID", style="cyan")
#     table.add_column("Status", style="magenta")
#     table.add_column("Total", style="green")
#     table.add_column("Restaurant", style="blue")
#
#     for order in orders:
#         table.add_row(
#             order.get('order_id'),
#             order.get('status'),
#             str(order.get('total_amount', 0)),
#             order.get('restaurant', {}).get('name', 'N/A')
#         )
#     print(table)
#
#
# # ----- Главное меню -----
# def admin_cli():
#     while True:
#         print("\n[Admin Panel]")
#         print("1. List Restaurants")
#         print("2. View Restaurant Menu")
#         print("3. List All Orders")
#         print("4. Update Order Status")
#         print("5. Delete Restaurant")
#         print("6. Delete Menu Item")
#         print("0. Exit")
#
#         choice = input("Enter your choice: ")
#
#         if choice == '1':
#             restaurants = get_restaurants()  # Используем функцию из client.py
#             display_restaurants(restaurants)
#
#         elif choice == '2':
#             restaurant_id = input("Enter Restaurant ID: ")
#             menu_data = get_restaurant_menu(restaurant_id)  # Из client.py
#             display_menu(menu_data)
#
#         elif choice == '3':
#             orders = get_all_orders()
#             display_orders(orders)
#
#         # elif choice == '4':
#         #     order_id = input("Enter Order ID: ")
#         #     print("Available statuses: pending, preparing, ready, delivered, cancelled")
#         #     status = input("Enter new status: ")
#         #     result = update_order_status(order_id, status)
#         #     if result:
#         #         print("Status updated successfully!")
#
#         elif choice == '4':
#             order_id = input("Enter Order ID: ")
#             try:
#                 uuid.UUID(order_id)  # Validate UUID format
#                 print(
#                     "Available statuses: pending_confirmation, confirmed, preparing, ready_for_pickup, delivered, cancelled")
#                 status = input("Enter new status: ")
#                 if status not in [e.value for e in OrderStatusEnum]:
#                     print(f"[bold red]Invalid status. Must be one of: {[e.value for e in OrderStatusEnum]}[/bold red]")
#                     continue
#                 result = update_order_status(order_id, status)
#                 if result:
#                     print("Status updated successfully!")
#                 else:
#                     print("[bold red]Failed to update status.[/bold red]")
#             except ValueError:
#                 print("[bold red]Invalid Order ID format. Must be a valid UUID.[/bold red]")
#
#         # elif choice == '5':
#         #     restaurant_id = input("Enter Restaurant ID to delete: ")
#         #     if delete_restaurant(restaurant_id):
#         #         print("Restaurant deleted successfully!")
#
#         elif choice == '5':
#             restaurant_id = input("Enter Restaurant ID to delete: ")
#             try:
#                 uuid.UUID(restaurant_id)  # Validate UUID format
#                 if delete_restaurant(restaurant_id):
#                     print("Restaurant deleted successfully!")
#                 else:
#                     print("[bold red]Failed to delete restaurant.[/bold red]")
#             except ValueError:
#                 print("[bold red]Invalid Restaurant ID format. Must be a valid UUID.[/bold red]")
#
#         elif choice == '6':
#             item_id = input("Enter Menu Item ID to delete: ")
#             if delete_menu_item(item_id):
#                 print("Menu item deleted successfully!")
#
#         elif choice == '0':
#             print("Exiting admin panel.")
#             break
#
#         else:
#             print("Invalid choice, try again.")
#
#
# if __name__ == "__main__":
#     admin_cli()