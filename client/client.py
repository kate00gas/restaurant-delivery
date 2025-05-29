import requests
import json
import uuid
from decimal import Decimal
import os
from dotenv import load_dotenv
from rich import print
from rich.table import Table
from rich.prompt import Prompt

# Загружаем переменные окружения
load_dotenv()
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")

# Глобальные переменные для хранения токена и имени пользователя
access_token = None
current_username = None


# ----- Функции для взаимодействия с API -----

def login():
    """Аутентификация пользователя."""
    global access_token, current_username
    username = Prompt.ask("Enter username")
    password = input("Enter password: ")  # Use input() to avoid GetPassWarning
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/login",
            data={"username": username, "password": password},
            timeout=5
        )
        response.raise_for_status()
        token_data = response.json()
        access_token = token_data["access_token"]
        current_username = username
        print(f"[green]Login successful! Username set to: {current_username}[/green]")
        return True
    except requests.exceptions.RequestException as e:
        print(f"[bold red]Login failed: {e}[/bold red]")
        if e.response is not None:
            try:
                print(f"Server response: {e.response.json()}")
            except json.JSONDecodeError:
                print(f"Server response (non-JSON): {e.response.text}")
        access_token = None
        current_username = None
        print("[yellow]Username reset to None due to login failure.[/yellow]")
        return False


def logout():
    """Выход из аккаунта."""
    global access_token, current_username
    if not access_token:
        print("[bold red]Not logged in. Cannot logout.[/bold red]")
        return
    access_token = None
    current_username = None
    print("[green]Logged out successfully![/green]")


def register():
    """Регистрация нового пользователя."""
    global access_token, current_username
    if access_token:
        print("[bold red]Cannot register a new user while logged in. Please logout first.[/bold red]")
        return
    username = Prompt.ask("Enter username")
    password = input("Enter password: ")  # Use input() to avoid GetPassWarning
    phone_number = Prompt.ask("Enter phone number")
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/users/",
            json={"username": username, "password": password, "role": "user", "phone_number": phone_number},
            timeout=5
        )
        response.raise_for_status()
        print("[green]User registered successfully![/green]")
        print("You can now login with your new credentials.")
    except requests.exceptions.RequestException as e:
        print(f"[bold red]Registration failed: {e}[/bold red]")
        if e.response is not None:
            try:
                print(f"Server response: {e.response.json()}")
            except json.JSONDecodeError:
                print(f"Server response (non-JSON): {e.response.text}")


def get_headers():
    """Возвращает заголовки с токеном, если пользователь аутентифицирован."""
    if access_token:
        return {"Authorization": f"Bearer {access_token}"}
    return {}


def get_restaurants():
    """Получает список ресторанов с API (без аутентификации)."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/restaurants/",
            timeout=5
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[bold red]Ошибка подключения:[/bold red] Сервер не отвечает по адресу {API_BASE_URL}")
        print("Проверьте что:")
        print("1. Сервер FastAPI запущен (docker-compose up -d)")
        print("2. Порт 8000 не занят другим приложением")
        print(f"3. URL {API_BASE_URL} правильный")
        return None


def get_restaurant_menu(restaurant_id: str):
    """Получает меню конкретного ресторана (без аутентификации)."""
    try:
        response = requests.get(f"{API_BASE_URL}/restaurants/{restaurant_id}", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[bold red]Error fetching menu for restaurant {restaurant_id}:[/bold red] {e}")
        return None
    except json.JSONDecodeError:
        print(f"[bold red]Error decoding JSON response for restaurant {restaurant_id}.[/bold red]")
        return None


def create_order(restaurant_id: str, items: list, delivery_address: str):
    """Создает новый заказ (требуется аутентификация)."""
    if not access_token:
        print("[yellow]Please log in to create an order.[/yellow]")
        if not login():
            return None
    order_data = {
        "restaurant_id": restaurant_id,
        "delivery_address": delivery_address,
        "items": items
    }
    try:
        response = requests.post(
            f"{API_BASE_URL}/orders/",
            json=order_data,
            headers=get_headers(),
            timeout=5
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[bold red]Error creating order:[/bold red] {e}")
        if e.response is not None:
            try:
                print(f"Server response: {e.response.json()}")
            except json.JSONDecodeError:
                print(f"Server response (non-JSON): {e.response.text}")
        return None
    except json.JSONDecodeError:
        print("[bold red]Error decoding JSON response after creating order.[/bold red]")
        return None


# ----- Функции для отображения данных -----

def display_restaurants(restaurants):
    """Красиво отображает список ресторанов в таблице."""
    if not restaurants:
        print("[yellow]No restaurants found.[/yellow]")
        return

    table = Table(title="Available Restaurants")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="magenta")
    table.add_column("Address", style="green")
    table.add_column("Phone", style="blue")

    for r in restaurants:
        table.add_row(
            r.get('restaurant_id', 'N/A'),
            r.get('name', 'N/A'),
            r.get('address', 'N/A'),
            r.get('phone_number', 'N/A')
        )
    print(table)


def display_menu(restaurant_data):
    """Красиво отображает меню ресторана."""
    if not restaurant_data:
        print("[yellow]Could not fetch restaurant data.[/yellow]")
        return

    print(f"\n[bold magenta]Menu for: {restaurant_data.get('name', 'Unknown Restaurant')}[/bold magenta]")
    print(f"Address: {restaurant_data.get('address', 'N/A')}")

    menu_items = restaurant_data.get('menu_items', [])
    if not menu_items:
        print("[yellow]No menu items available for this restaurant.[/yellow]")
        return

    table = Table(title="Menu")
    table.add_column("Item ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="magenta")
    table.add_column("Description", style="white")
    table.add_column("Price", style="green")
    table.add_column("Category", style="blue")

    for item in menu_items:
        price = item.get('price', 'N/A')
        try:
            price_str = f"${Decimal(price):.2f}"
        except (ValueError, TypeError):
            price_str = str(price)

        table.add_row(
            item.get('item_id', 'N/A'),
            item.get('name', 'N/A'),
            item.get('description', 'N/A'),
            price_str,
            item.get('category', 'N/A')
        )
    print(table)


# ----- Основной цикл CLI -----

def main_cli():
    """Главная функция для интерактивного клиента."""
    global access_token, current_username
    while True:
        # Отображаем текущего пользователя или "Not logged in"
        print(
            f"\n[bold yellow]Restaurant Delivery CLI (Logged in as: {current_username if current_username else 'Not logged in'})[/bold yellow]")

        # Динамическое меню в зависимости от состояния авторизации
        if access_token:
            print("1. List Restaurants")
            print("2. View Restaurant Menu")
            print("3. Create Order")
            print("4. Logout")
            print("0. Exit")
        else:
            print("1. List Restaurants")
            print("2. View Restaurant Menu")
            print("3. Create Order")
            print("4. Login")
            print("5. Register")
            print("0. Exit")

        choice = input("Enter your choice: ")

        if choice == '1':
            restaurants = get_restaurants()
            display_restaurants(restaurants)
        elif choice == '2':
            restaurant_id = input("Enter Restaurant ID to view menu: ")
            try:
                uuid.UUID(restaurant_id)
                menu_data = get_restaurant_menu(restaurant_id)
                display_menu(menu_data)
            except ValueError:
                print("[bold red]Invalid Restaurant ID format.[/bold red]")
        elif choice == '3':
            restaurant_id = input("Enter Restaurant ID for the order: ")
            try:
                uuid.UUID(restaurant_id)
                menu_data = get_restaurant_menu(restaurant_id)
                if not menu_data:
                    continue
                display_menu(menu_data)

                order_items = []
                while True:
                    item_id = input("Enter Item ID to add (or 'done' to finish): ")
                    if item_id.lower() == 'done':
                        break
                    try:
                        uuid.UUID(item_id)
                        if not any(item['item_id'] == item_id for item in menu_data.get('menu_items', [])):
                            print(
                                "[yellow]Warning: Item ID not found in the displayed menu. Ensure it's correct.[/yellow]")
                        quantity = int(input(f"Enter quantity for item {item_id}: "))
                        if quantity > 0:
                            order_items.append({"item_id": item_id, "quantity": quantity})
                        else:
                            print("[bold red]Quantity must be positive.[/bold red]")
                    except ValueError:
                        print("[bold red]Invalid Item ID format or quantity.[/bold red]")
                    except TypeError:
                        print("[bold red]Error processing input.[/bold red]")

                if not order_items:
                    print("[yellow]No items added to the order.[/yellow]")
                    continue

                delivery_address = input("Enter delivery address: ")
                if not delivery_address:
                    print("[bold red]Delivery address cannot be empty.[/bold red]")
                    continue
                if len(delivery_address) < 5:
                    print("[bold red]Delivery address must be at least 5 characters.[/bold red]")
                    continue

                print("\nCreating order...")
                created_order = create_order(restaurant_id, order_items, delivery_address)

                if created_order:
                    print("[green]Order created successfully![/green]")
                    print(json.dumps(created_order, indent=2, default=str))
                else:
                    print("[bold red]Failed to create order.[/bold red]")

            except ValueError:
                print("[bold red]Invalid Restaurant ID format.[/bold red]")
        elif choice == '4':
            if access_token:
                logout()
            else:
                login()
        elif choice == '5' and not access_token:
            register()
        elif choice == '5' and access_token:
            print("[bold red]Cannot register a new user while logged in. Please logout first.[/bold red]")
        elif choice == '0':
            print("Exiting.")
            break
        else:
            print("[bold red]Invalid choice. Please try again.[/bold red]")


if __name__ == "__main__":
    print(f"Connecting to API at: {API_BASE_URL}")
    main_cli()


#
# # Файл client.py
# import requests
# import json
# import uuid
# from decimal import Decimal
# import os
# from dotenv import load_dotenv
# # from api_client import (
# #     get_restaurants,
# #     get_restaurant_menu,
# #     display_restaurants,
# #     display_menu
# # )
# # Используем rich для красивого вывода
# try:
#     from rich import print
#     from rich.table import Table
# except ImportError:
#     print("Rich library not found, using standard print.")
#     print("Install it using: pip install rich")
#
# # Загружаем переменные окружения (API_BASE_URL)
# load_dotenv()
# API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
#
# # ----- Функции для взаимодействия с API -----
#
# def get_restaurants():
#     """Получает список ресторанов с API."""
#     try:
#         response = requests.get(
#             f"{API_BASE_URL}/restaurants/",
#             timeout=5  # Добавляем таймаут
#         )
#         response.raise_for_status()
#         return response.json()
#     except requests.exceptions.RequestException as e:
#         print(f"[bold red]Ошибка подключения:[/bold red] Сервер не отвечает по адресу {API_BASE_URL}")
#         print("Проверьте что:")
#         print("1. Сервер FastAPI запущен (docker-compose up -d)")
#         print("2. Порт 8000 не занят другим приложением")
#         print(f"3. URL {API_BASE_URL} правильный")
#         return None
#
# def get_restaurant_menu(restaurant_id: str):
#     """Получает меню конкретного ресторана."""
#     try:
#         response = requests.get(f"{API_BASE_URL}/restaurants/{restaurant_id}")
#         response.raise_for_status()
#         return response.json()
#     except requests.exceptions.RequestException as e:
#         print(f"[bold red]Error fetching menu for restaurant {restaurant_id}:[/bold red] {e}")
#         return None
#     except json.JSONDecodeError:
#         print(f"[bold red]Error decoding JSON response for restaurant {restaurant_id}.[/bold red]")
#         return None
#
# def create_order(restaurant_id: str, items: list, delivery_address: str):
#     """Создает новый заказ."""
#     order_data = {
#         "restaurant_id": restaurant_id,
#         "delivery_address": delivery_address,
#         "items": items # items должен быть списком словарей вида [{"item_id": "...", "quantity": N}]
#     }
#     try:
#         response = requests.post(f"{API_BASE_URL}/orders/", json=order_data)
#         response.raise_for_status()
#         return response.json()
#     except requests.exceptions.RequestException as e:
#         print(f"[bold red]Error creating order:[/bold red] {e}")
#         if e.response is not None:
#             try:
#                 print(f"Server response: {e.response.json()}")
#             except json.JSONDecodeError:
#                 print(f"Server response (non-JSON): {e.response.text}")
#         return None
#     except json.JSONDecodeError:
#          print("[bold red]Error decoding JSON response after creating order.[/bold red]")
#          return None
#
# # ----- Функции для отображения данных -----
#
# def display_restaurants(restaurants):
#     """Красиво отображает список ресторанов в таблице."""
#     if not restaurants:
#         print("[yellow]No restaurants found.[/yellow]")
#         return
#
#     table = Table(title="Available Restaurants")
#     table.add_column("ID", style="cyan", no_wrap=True)
#     table.add_column("Name", style="magenta")
#     table.add_column("Address", style="green")
#     table.add_column("Phone", style="blue")
#
#     for r in restaurants:
#         table.add_row(
#             r.get('restaurant_id', 'N/A'),
#             r.get('name', 'N/A'),
#             r.get('address', 'N/A'),
#             r.get('phone_number', 'N/A')
#         )
#     print(table)
#
# def display_menu(restaurant_data):
#     """Красиво отображает меню ресторана."""
#     if not restaurant_data:
#         print("[yellow]Could not fetch restaurant data.[/yellow]")
#         return
#
#     print(f"\n[bold magenta]Menu for: {restaurant_data.get('name', 'Unknown Restaurant')}[/bold magenta]")
#     print(f"Address: {restaurant_data.get('address', 'N/A')}")
#
#     menu_items = restaurant_data.get('menu_items', [])
#     if not menu_items:
#         print("[yellow]No menu items available for this restaurant.[/yellow]")
#         return
#
#     table = Table(title="Menu")
#     table.add_column("Item ID", style="cyan", no_wrap=True)
#     table.add_column("Name", style="magenta")
#     table.add_column("Description", style="white")
#     table.add_column("Price", style="green")
#     table.add_column("Category", style="blue")
#
#     for item in menu_items:
#         # Убедимся, что цена - строка для отображения
#         price = item.get('price', 'N/A')
#         try:
#             # Попытка форматировать как валюту
#             price_str = f"${Decimal(price):.2f}"
#         except (ValueError, TypeError):
#              price_str = str(price)
#
#         table.add_row(
#             item.get('item_id', 'N/A'),
#             item.get('name', 'N/A'),
#             item.get('description', 'N/A'),
#             price_str,
#             item.get('category', 'N/A')
#         )
#     print(table)
#
#
# # ----- Основной цикл CLI -----
#
# def main_cli():
#     """Главная функция для интерактивного клиента."""
#     while True:
#         print("\n[bold yellow]Restaurant Delivery CLI[/bold yellow]")
#         print("1. List Restaurants")
#         print("2. View Restaurant Menu")
#         print("3. Create Order")
#         print("0. Exit")
#         choice = input("Enter your choice: ")
#
#         if choice == '1':
#             restaurants = get_restaurants()
#             display_restaurants(restaurants)
#         elif choice == '2':
#             restaurant_id = input("Enter Restaurant ID to view menu: ")
#             try:
#                 uuid.UUID(restaurant_id) # Простая валидация формата UUID
#                 menu_data = get_restaurant_menu(restaurant_id)
#                 display_menu(menu_data)
#             except ValueError:
#                 print("[bold red]Invalid Restaurant ID format.[/bold red]")
#         elif choice == '3':
#             restaurant_id = input("Enter Restaurant ID for the order: ")
#             try:
#                 uuid.UUID(restaurant_id)
#                 # Сначала покажем меню для удобства выбора ID блюд
#                 menu_data = get_restaurant_menu(restaurant_id)
#                 if not menu_data:
#                     continue # Не продолжаем, если меню не загрузилось
#                 display_menu(menu_data)
#
#                 order_items = []
#                 while True:
#                     item_id = input("Enter Item ID to add (or 'done' to finish): ")
#                     if item_id.lower() == 'done':
#                         break
#                     try:
#                          uuid.UUID(item_id)
#                          # Проверим, есть ли такое блюдо в показанном меню
#                          if not any(item['item_id'] == item_id for item in menu_data.get('menu_items',[])):
#                               print("[yellow]Warning: Item ID not found in the displayed menu. Ensure it's correct.[/yellow]")
#
#                          quantity = int(input(f"Enter quantity for item {item_id}: "))
#                          if quantity > 0:
#                              order_items.append({"item_id": item_id, "quantity": quantity})
#                          else:
#                              print("[bold red]Quantity must be positive.[/bold red]")
#                     except ValueError:
#                          print("[bold red]Invalid Item ID format or quantity.[/bold red]")
#                     except TypeError:
#                          print("[bold red]Error processing input.[/bold red]")
#
#
#                 if not order_items:
#                     print("[yellow]No items added to the order.[/yellow]")
#                     continue
#
#                 delivery_address = input("Enter delivery address: ")
#                 if not delivery_address:
#                      print("[bold red]Delivery address cannot be empty.[/bold red]")
#                      continue
#
#                 print("\nCreating order...")
#                 created_order = create_order(restaurant_id, order_items, delivery_address)
#
#                 if created_order:
#                     print("[bold green]Order created successfully![/bold green]")
#                     # Отображаем созданный заказ (можно сделать красивее)
#                     print(json.dumps(created_order, indent=2, default=str)) # default=str для UUID/Decimal
#                 else:
#                     print("[bold red]Failed to create order.[/bold red]")
#
#             except ValueError:
#                 print("[bold red]Invalid Restaurant ID format.[/bold red]")
#         elif choice == '0':
#             print("Exiting.")
#             break
#         else:
#             print("[bold red]Invalid choice. Please try again.[/bold red]")
#
# if __name__ == "__main__":
#     print(f"Connecting to API at: {API_BASE_URL}")
#     main_cli()
