import gspread_asyncio
from google.oauth2.service_account import Credentials
import os
from app.config.settings import GOOGLE_SHEETS_CREDENTIALS, SPREADSHEET_ID
import json


def get_creds():
    """Создает credentials для Google Sheets API"""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds_dict = json.loads(GOOGLE_SHEETS_CREDENTIALS)

    return Credentials.from_service_account_info(
        creds_dict,
        scopes=scopes
    )

async def write_order_to_sheet(order_data: dict, spreadsheet_id: str = None):
    """
    Записывает данные заказа в Google таблицу
    
    Args:
        order_data: словарь с данными заказа:
            - tg_nickname: username пользователя
            - type_rug: тип ковра
            - color_rug: цвет ковра
            - edging_rug: окантовка (может быть None для ЭВА)
            - size_rug: размер ковра
            - phone: телефон
            - name: ФИО
        spreadsheet_id: ID Google таблицы (можно указать в .env как GOOGLE_SHEET_ID)
    
    Returns:
        True если успешно, False если ошибка
    """
    try:
        spreadsheet_id = spreadsheet_id or SPREADSHEET_ID
        if not spreadsheet_id:
            print("Ошибка: не указан GOOGLE_SHEET_ID")
            return False
        
        # Создаем клиент
        agc = gspread_asyncio.AsyncioGspreadClientManager(get_creds)
        agc_instance = await agc.authorize()
        spreadsheet = await agc_instance.open_by_key(spreadsheet_id)
        
        # Получаем первый лист (или создаем новый если нет)
        try:
            worksheet = await spreadsheet.get_worksheet(0)
        except:
            worksheet = await spreadsheet.add_worksheet(title="Заказы", rows=1000, cols=10)
        
        # Подготавливаем строку данных
        row_data = [
            order_data.get("tg_nickname", ""),
            order_data.get("type_rug", ""),
            order_data.get("color_rug", ""),
            order_data.get("edging_rug", "") if order_data.get("edging_rug") else "Без окантовки",
            order_data.get("size_rug", ""),
            order_data.get("phone", ""),
            order_data.get("name", ""),
        ]
        
        # Добавляем строку в конец таблицы
        await worksheet.append_row(row_data)
        
        print(f"Заказ успешно записан в таблицу.")
        return True
        
    except Exception as e:
        print(f"Ошибка при записи в Google таблицу: {e}")
        return False

async def init_sheet_headers(spreadsheet_id: str = None):
    """
    Инициализирует заголовки в таблице (если таблица пустая)
    
    Args:
        spreadsheet_id: ID Google таблицы
    """
    try:
        spreadsheet_id = spreadsheet_id or SPREADSHEET_ID
        if not spreadsheet_id:
            return False
        
        agc = gspread_asyncio.AsyncioGspreadClientManager(get_creds)
        agc_instance = await agc.authorize()
        spreadsheet = await agc_instance.open_by_key(spreadsheet_id)
        
        worksheet = await spreadsheet.get_worksheet(0)
        
        # Проверяем есть ли заголовки
        existing_headers = await worksheet.row_values(1)
        if existing_headers:
            return True  # Заголовки уже есть
        
        # Добавляем заголовки
        headers = ["Telegram", "Тип ковра", "Цвет", "Окантовка", "Размер", "Телефон", "ФИО"]
        await worksheet.append_row(headers)
        
        print("Заголовки успешно добавлены в таблицу")
        return True
        
    except Exception as e:
        print(f"Ошибка при инициализации заголовков: {e}")
        return False

async def check_user(username: str) -> bool:
    try:
        agc = gspread_asyncio.AsyncioGspreadClientManager(get_creds)
        agc_instance = await agc.authorize()

        spreadsheet = await agc_instance.open_by_key(SPREADSHEET_ID)
        worksheet = await spreadsheet.get_worksheet(0)

        records = await worksheet.get_all_records()

        for record in records:
            if str(record.get("Telegram")) == str(username):
                return True

        return False

    except Exception as e:
        print(f"Error checking user: {e}")
        raise