import os
import re

import requests
from bs4 import BeautifulSoup
import urllib.parse
from dotenv import load_dotenv

# Конфигурационные параметры
load_dotenv()

# Создаем сессию
session = requests.Session()

phpmyadmin_url = os.getenv("phpmyadmin_url")
login = os.getenv("login")
password = os.getenv("password")
database = os.getenv("database")
table = os.getenv("table")

# 1. Авторизация в phpMyAdmin
def login_to_phpmyadmin():
    # Первый запрос для получения токена и cookies
    response = session.get(phpmyadmin_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the login token
    token_input = soup.find('input', {'name': 'token'})
    if not token_input:
        raise Exception("Не удалось получить токен авторизации")
    token = token_input.get('value')

    # Формируем данные для авторизации
    auth_data = {
        'pma_username': login,
        'pma_password': password,
        'server': '1',
        'token': token
    }

    # Отправляем POST-запрос для авторизации
    auth_response = session.post(phpmyadmin_url, data=auth_data)

    # Проверяем успешность авторизации
    if "pma_navigation" not in auth_response.text:
        raise Exception("Ошибка авторизации в phpMyAdmin")


# 2. Переход в базу данных testDB и извлечение таблицы users
def fetch_table_data():
    # Получаем страницу таблиц
    browse_url = f"{phpmyadmin_url}index.php?route=/sql&db={urllib.parse.quote(database)}&table={urllib.parse.quote(table)}&pos=0"
    print(f"Accessing table URL: {browse_url}")
    response = session.get(browse_url)

    if f"Table: {table}" not in re.sub(r"\s+", " ", response.text):
        raise Exception(f"Не удалось получить доступ к таблице {table}")

    print("Парсим данные...")
    soup = BeautifulSoup(response.text, 'html.parser')

    # Try to find the table with results
    result_table = soup.find('table', {'class': 'table_results'})

    if not result_table:
        # Check if table is empty
        empty_msg = soup.find('div', {'class': 'message'})
        if empty_msg and "No rows selected" in empty_msg.text:
            print("В таблице нет данных")
            return
        raise Exception("Не удалось найти данные таблицы, возможно, у таблицы другая структура.")

    if not result_table:
        raise Exception("В таблице нет данных")

    # Extract headers
    headers = [th.a.contents[0].strip() for th in result_table.find('thead').find_all('th', attrs={"data-column": True})]

    # Extract rows
    rows = []
    for tr in result_table.find('tbody').find_all('tr'):
        row = [td.get_text(strip=True) for td in tr.find_all('td', attrs={"data-type": True})]
        if row:
            rows.append(row)

    column_widths = [2, 10]
    # Создаем строку формата для выравнивания
    format_str = " | ".join([f"{{:<{width}}}" for width in column_widths])

    # Выводим заголовки
    print("\nTable contents:")
    print(format_str.format(*headers))

    # Выводим строки таблицы
    for row in rows:
        print(format_str.format(*row))

# Основной код
try:
    print("Attempting to login...")
    login_to_phpmyadmin()
    print("Login successful!")

    fetch_table_data()

except Exception as e:
    print(f"Ошибка: {e}")