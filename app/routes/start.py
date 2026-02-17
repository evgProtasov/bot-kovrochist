from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, FSInputFile, InputMediaPhoto
from app.states.state import OrderInfo
from app.bot.bot_commands import set_bot_commands
from app.bot.bot import bot
import app.keyboards.inline_keyboards as ikb
import app.keyboards.replykeyboards as rkb
from app.utils.googledoc import write_order_to_sheet, check_user
import re
import os

router = Router()

def get_color_image_paths(color_name: str, rug_type: str) -> list[str]:
    """Возвращает список путей к картинкам цвета (обычная и full версия) для указанного типа ковра"""
    base_path = "app/image"
    images = []
    
    # Определяем префикс в зависимости от типа ковра
    prefix = "wool" if rug_type == "Ворсовый ковёр" else "eva"
    
    # Маппинг названий цветов на имена файлов
    color_file_mapping = {
        "Чёрный": "black",
        "Серый": "grey",
        "Бежевый": "beige",
        "Коричневый": "brown"
    }
    
    color_code = color_file_mapping.get(color_name)
    if color_code:
        # Обычная версия
        filename = f"{prefix}_{color_code}.jpeg"
        file_path = os.path.join(base_path, filename)
        if os.path.exists(file_path):
            images.append(file_path)
        
        # Full версия
        filename_full = f"{prefix}_{color_code}_full.jpeg"
        file_path_full = os.path.join(base_path, filename_full)
        if os.path.exists(file_path_full):
            images.append(file_path_full)
    
    return images

def get_edging_image_paths(rug_type: str) -> list[str]:
    """Возвращает список путей к картинкам окантовки для ворсовых ковров"""
    if rug_type != "Ворсовый ковёр":
        return []
    
    base_path = "app/image"
    images = []
    
    # Для ворсовых ковров отправляем enging_1, enging_2, enging_3
    for i in range(1, 4):
        filename = f"enging_{i}.jpeg"
        file_path = os.path.join(base_path, filename)
        if os.path.exists(file_path):
            images.append(file_path)
    
    return images

@router.message(Command("start"))
async def start(message: Message, state: FSMContext):
    username = message.from_user.username
    user_exists = await check_user(username=username)
    if user_exists:
        await message.answer("Вы уже заказали ковер!")
        return
    else:
        await message.answer("Добро пожаловать в бот для заказа ковров!", reply_markup=ikb.get_main_menu_keyboard())
        
        await state.set_state(OrderInfo.type_rug)
    # print(tg_nickname)

@router.callback_query(F.data == "order_rug")
async def order_rug(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Выберите тип ковра", reply_markup=ikb.get_type_rug_keyboard())
    await state.set_state(OrderInfo.type_rug)

@router.callback_query(F.data.startswith("type_rug:"))
async def select_type_rug(callback: CallbackQuery, state: FSMContext):
    type_mapping = {
        "type_rug:eva": "ЭВА ковёр",
        "type_rug:wool": "Ворсовый ковёр"
    }
    tg_nickname = callback.from_user.username
    await state.update_data(tg_nickname=tg_nickname)
    type_rug = type_mapping.get(callback.data)
    await state.update_data(type_rug=type_rug)
    await state.set_state(OrderInfo.color_rug)
    data = await state.get_data()
    print(data)
    await callback.message.edit_text("Выберите цвет ковра", reply_markup=ikb.get_color_eva_rug_keyboard() if callback.data == "type_rug:eva" else ikb.get_color_wool_rug_keyboard())

@router.callback_query(F.data.startswith("color_rug_eva:") | F.data.startswith("color_rug_wool:"))
async def select_color_rug(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    type_rug = data.get("type_rug")

    if type_rug == "ЭВА ковёр":
        color_mapping = {
            "color_rug_eva:black": "Чёрный",
            "color_rug_eva:gray": "Серый",
            "color_rug_eva:beige": "Бежевый",
            "color_rug_eva:brown": "Коричневый"
        }
        color_rug = color_mapping.get(callback.data)
        await state.update_data(color_rug=color_rug)
        
        # Удаляем сообщение с клавиатурой
        try:
            await callback.message.delete()
        except:
            pass
        
        # Отправляем обе картинки выбранного цвета в одном сообщении (медиа-группа)
        image_paths = get_color_image_paths(color_rug, type_rug)
        if image_paths:
            media_group = []
            for i, image_path in enumerate(image_paths):
                photo = FSInputFile(image_path)
                caption = f"Выбран цвет: {color_rug}" if i == 0 else None
                media_group.append(InputMediaPhoto(media=photo, caption=caption))
            
            # Отправляем медиа-группу и сохраняем ID сообщений
            sent_messages = await bot.send_media_group(chat_id=callback.message.chat.id, media=media_group)
            color_image_ids = [msg.message_id for msg in sent_messages]
            await state.update_data(color_image_ids=color_image_ids)
        
        # Для ЭВА ковров пропускаем окантовку, записываем None
        await state.update_data(edging_rug=None)
        await state.set_state(OrderInfo.size_rug)
        data = await state.get_data()
        print(data)
        
        # Переходим к запросу размера
        size_message = await bot.send_message(chat_id=callback.message.chat.id, text="Укажите размер ковра (ширина и длина в метрах)\nФормат: 0.5x0.8\nРазмер ковра должен быть не более 2х квадратных метров\nВведите размер ниже⬇️", reply_markup=rkb.back_keyboard())
        await state.update_data(size_rug_message_id=size_message.message_id)
        await callback.answer()
    
    else:
        # Ворсовый ковёр
        color_mapping = {
            "color_rug_wool:black": "Чёрный",
            "color_rug_wool:brown": "Коричневый",
            "color_rug_wool:grey": "Серый"
        }
        color_rug = color_mapping.get(callback.data)
        await state.update_data(color_rug=color_rug)
        
        # Удаляем сообщение с клавиатурой
        try:
            await callback.message.delete()
        except:
            pass
        
        # Отправляем обе картинки выбранного цвета в одном сообщении (медиа-группа)
        image_paths = get_color_image_paths(color_rug, type_rug)
        if image_paths:
            media_group = []
            for i, image_path in enumerate(image_paths):
                photo = FSInputFile(image_path)
                caption = f"Выбран цвет: {color_rug}" if i == 0 else None
                media_group.append(InputMediaPhoto(media=photo, caption=caption))
            
            # Отправляем медиа-группу и сохраняем ID сообщений
            sent_messages = await bot.send_media_group(chat_id=callback.message.chat.id, media=media_group)
            color_image_ids = [msg.message_id for msg in sent_messages]
            await state.update_data(color_image_ids=color_image_ids)
        
        # Отправляем картинки примеров окантовки (enging_1, enging_2, enging_3)
        edging_image_paths = get_edging_image_paths(type_rug)
        if edging_image_paths:
            media_group = []
            for i, image_path in enumerate(edging_image_paths):
                photo = FSInputFile(image_path)
                caption = "Примеры окантовки" if i == 0 else None
                media_group.append(InputMediaPhoto(media=photo, caption=caption))
            
            # Отправляем медиа-группу и сохраняем ID сообщений
            sent_messages = await bot.send_media_group(chat_id=callback.message.chat.id, media=media_group)
            edging_image_ids = [msg.message_id for msg in sent_messages]
            await state.update_data(edging_image_ids=edging_image_ids)
        
        await state.set_state(OrderInfo.edging_rug)
        data = await state.get_data()
        print(data)
        await bot.send_message(chat_id=callback.message.chat.id, text="Выберите окантовку ковра", reply_markup=ikb.get_edging_rug_keyboard())
        await callback.answer()

@router.callback_query(F.data.startswith("rug_edging:"))
async def select_edging_rug(callback: CallbackQuery, state: FSMContext):
    edging_mapping = {
        "rug_edging:black_strap": "Стропа чёрная",
        "rug_edging:brown_strap": "Стропа коричневая",
        "rug_edging:thread_overlock": "Оверлок нитками",
        "rug_edging:no_edging": "Без окантовки"
    }
    edging_rug = edging_mapping.get(callback.data)
    await state.update_data(edging_rug=edging_rug)
    
    # Удаляем сообщение с клавиатурой
    try:
        await callback.message.delete()
    except:
        pass
    
    # Картинки окантовки уже отправлены при выборе цвета для ворсовых ковров
    # Просто переходим к следующему шагу
    await state.set_state(OrderInfo.size_rug)
    data = await state.get_data()
    print(data)

    await callback.answer()
    size_message = await bot.send_message(chat_id=callback.message.chat.id, text="Укажите размер ковра (ширина и длина в метрах)\nФормат: 0.5x0.8\nРазмер ковра должен быть не более 2х квадратных метров\nВведите размер ниже⬇️", reply_markup=rkb.back_keyboard())
    await state.update_data(size_rug_message_id=size_message.message_id)

    # await state.update_data(size_rug_message=callback.message.text)
    # await callback.message.delete()
    # await callback.message.answer(f"Укажите размер ковра (ширина и длина в метрах)\nФормат: 1.5x2.5", reply_markup=rkb.back_keyboard())


@router.message(OrderInfo.size_rug, F.text == "⬅️ Назад")
async def back_from_size_rug(message: Message, state: FSMContext):
    data = await state.get_data()
    size_message_id = data.get("size_rug_message_id")
    type_rug = data.get("type_rug")
    
    # Удаляем сообщение с запросом размера
    if size_message_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=size_message_id)
        except:
            pass
    
    # Удаляем сообщение "Назад" пользователя
    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except:
        pass
    
    # Удаляем размер из state
    data.pop("size_rug", None)
    data.pop("size_rug_message_id", None)
    
    # В зависимости от типа ковра возвращаемся к нужному шагу
    if type_rug == "ЭВА ковёр":
        # Для ЭВА ковров удаляем картинки цвета
        color_image_ids = data.get("color_image_ids", [])
        if color_image_ids:
            for msg_id in color_image_ids:
                try:
                    await bot.delete_message(chat_id=message.chat.id, message_id=msg_id)
                except:
                    pass
        
        # Удаляем цвет из state
        data.pop("color_rug", None)
        data.pop("color_image_ids", None)
        await state.set_data(data)
        
        # Возвращаемся к выбору цвета
        keyboard = ikb.get_color_eva_rug_keyboard()
        await message.answer("Выберите цвет ковра", reply_markup=keyboard)
        await state.set_state(OrderInfo.color_rug)
    else:
        # Для ворсовых ковров возвращаемся к выбору окантовки
        await message.answer("Выберите окантовку ковра", reply_markup=ikb.get_edging_rug_keyboard())
        await state.set_state(OrderInfo.edging_rug)

@router.message(OrderInfo.size_rug)
async def select_size_rug(message: Message, state: FSMContext):
    # Пропускаем кнопку "Назад" - она обрабатывается отдельным обработчиком выше
    if message.text == "⬅️ Назад":
        return
    
    data = await state.get_data()
    size_message_id = data.get("size_rug_message_id")
    
    # Удаляем сообщение с запросом размера
    if size_message_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=size_message_id)
        except:
            pass
    
    # Удаляем сообщение "Назад" пользователя
    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except:
        pass
    
    size_rug = message.text
    await state.update_data(size_rug=size_rug)
    data = await state.get_data()
    print(data)

    await state.set_state(OrderInfo.phone)
    
    # Отправляем сообщение с запросом контакта
    contact_message = await message.answer("Поделитесь контактом для связи", reply_markup=rkb.contact_keyboard())
    await state.update_data(contact_message_id=contact_message.message_id)
    
@router.message(OrderInfo.phone, F.text == "⬅️ Назад")
async def back_from_phone(message: Message, state: FSMContext):
    data = await state.get_data()
    contact_message_id = data.get("contact_message_id")
    
    # Удаляем сообщение с запросом контакта
    if contact_message_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=contact_message_id)
        except:
            pass
    
    # Удаляем сообщение "Назад" пользователя
    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except:
        pass
    
    # Удаляем размер и контакт из state
    data.pop("size_rug", None)
    data.pop("size_rug_message_id", None)
    data.pop("contact_message_id", None)
    await state.set_data(data)
    
    # Возвращаемся к запросу размера
    await state.set_state(OrderInfo.size_rug)
    size_message = await message.answer("Укажите размер ковра (ширина и длина в метрах)\nФормат: 0.5x0.8\nРазмер ковра должен быть не более 2х квадратных метров\nВведите размер ниже⬇️", reply_markup=rkb.back_keyboard())
    await state.update_data(size_rug_message_id=size_message.message_id)

@router.message(OrderInfo.phone, F.contact)
async def get_phone_from_contact(message: Message, state: FSMContext):
    data = await state.get_data()
    contact_message_id = data.get("contact_message_id")
    
    # Удаляем сообщение с запросом контакта
    if contact_message_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=contact_message_id)
        except:
            pass
    
    # Удаляем сообщение пользователя с контактом
    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except:
        pass
    
    phone = message.contact.phone_number
    await state.update_data(phone=phone)
    data = await state.get_data()
    print(data)
    
    # Переходим к запросу ФИО
    await state.set_state(OrderInfo.name)
    name_message = await message.answer("Введите ваше ФИО", reply_markup=ReplyKeyboardRemove())
    await state.update_data(name_message_id=name_message.message_id)

@router.message(OrderInfo.phone)
async def get_phone_text(message: Message, state: FSMContext):
    # Пропускаем кнопку "Назад" - она обрабатывается отдельным обработчиком выше
    if message.text == "⬅️ Назад":
        return
    
    data = await state.get_data()
    contact_message_id = data.get("contact_message_id")
    
    # Удаляем сообщение с запросом контакта
    if contact_message_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=contact_message_id)
        except:
            pass
    
    # Удаляем сообщение пользователя с номером
    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except:
        pass
    
    # Если пользователь ввел номер текстом вместо кнопки
    phone = message.text.strip()
    # Простая валидация номера
    if not re.match(r'^\+?\d{10,15}$', phone.replace(' ', '').replace('-', '')):
        await message.answer("Неверный формат номера. Пожалуйста, используйте кнопку 'Поделиться контактом' или введите номер в формате: +79991234567")
        return
    
    await state.update_data(phone=phone)
    data = await state.get_data()
    print(data)
    
    # Переходим к запросу ФИО
    await state.set_state(OrderInfo.name)
    name_message = await message.answer("Введите ваше ФИО", reply_markup=ReplyKeyboardRemove())
    await state.update_data(name_message_id=name_message.message_id)

@router.message(OrderInfo.name)
async def get_name(message: Message, state: FSMContext):
    data = await state.get_data()
    name_message_id = data.get("name_message_id")
    
    # Удаляем сообщение с запросом ФИО
    if name_message_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=name_message_id)
        except:
            pass
    
    # Удаляем сообщение пользователя с ФИО
    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except:
        pass
    
    name = message.text.strip()
    await state.update_data(name=name)
    data = await state.get_data()
    print(data)
    
    # Записываем заказ в Google таблицу
    try:
        order_written = await write_order_to_sheet(data)
        if order_written:
            ilya_id = 1177005836
            notify_message = await bot.send_message(chat_id=ilya_id, text=f"Новый заказ на ковер:\n{data.get('name')}\n{data.get('phone')}")
            await bot.send_message(chat_id=message.chat.id, text=f"Спасибо! Ваш заказ принят! Мы свяжемся с вами в ближайшее время.", reply_markup=ReplyKeyboardRemove())
        
    except Exception as e:
        print(f"Error writing order to sheet: {e}")
        return
    
    # Отправляем финальное сообщение
    # await message.answer("Спасибо! Ваш заказ принят. Мы свяжемся с вами в ближайшее время.", reply_markup=ReplyKeyboardRemove())
    
    await state.clear()

@router.callback_query(F.data == "back_to_type_rug")
async def back_to_type_rug(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    # Удаляем сообщения с картинками цвета
    color_image_ids = data.get("color_image_ids", [])
    if color_image_ids:
        for msg_id in color_image_ids:
            try:
                await bot.delete_message(chat_id=callback.message.chat.id, message_id=msg_id)
            except:
                pass
    
    # Удаляем сообщения с картинками окантовки (для ворсовых ковров)
    edging_image_ids = data.get("edging_image_ids", [])
    if edging_image_ids:
        for msg_id in edging_image_ids:
            try:
                await bot.delete_message(chat_id=callback.message.chat.id, message_id=msg_id)
            except:
                pass
    
    # Удаляем поля, связанные с выбором типа, цвета и окантовки
    data.pop("type_rug", None)
    data.pop("color_rug", None)
    data.pop("edging_rug", None)
    data.pop("color_image_ids", None)
    data.pop("edging_image_ids", None)
    await state.set_data(data)
    await callback.message.edit_text("Выберите тип ковра", reply_markup=ikb.get_type_rug_keyboard())
    await state.set_state(OrderInfo.type_rug)
    await callback.answer()

@router.callback_query(F.data == "back_to_color_rug")
async def back_to_color_rug(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    type_rug = data.get("type_rug")
    
    # Удаляем сообщения с картинками цвета
    color_image_ids = data.get("color_image_ids", [])
    if color_image_ids:
        for msg_id in color_image_ids:
            try:
                await bot.delete_message(chat_id=callback.message.chat.id, message_id=msg_id)
            except:
                pass
    
    # Для ворсовых ковров удаляем картинки окантовки
    if type_rug == "Ворсовый ковёр":
        edging_image_ids = data.get("edging_image_ids", [])
        if edging_image_ids:
            for msg_id in edging_image_ids:
                try:
                    await bot.delete_message(chat_id=callback.message.chat.id, message_id=msg_id)
                except:
                    pass
    
    # Удаляем поля цвета и окантовки
    data.pop("color_rug", None)
    data.pop("edging_rug", None)
    data.pop("color_image_ids", None)
    data.pop("edging_image_ids", None)
    await state.set_data(data)
    
    # Определяем клавиатуру на основе сохраненного типа ковра
    keyboard = ikb.get_color_eva_rug_keyboard() if type_rug == "ЭВА ковёр" else ikb.get_color_wool_rug_keyboard()
    await callback.message.edit_text("Выберите цвет ковра", reply_markup=keyboard)
    await state.set_state(OrderInfo.color_rug)
    await callback.answer()

@router.callback_query(F.data == "back_to_edging_rug")
async def back_to_edging_rug(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    type_rug = data.get("type_rug")
    
    # Удаляем сообщения с картинками окантовки (для ворсовых ковров)
    if type_rug == "Ворсовый ковёр":
        edging_image_ids = data.get("edging_image_ids", [])
        if edging_image_ids:
            for msg_id in edging_image_ids:
                try:
                    await bot.delete_message(chat_id=callback.message.chat.id, message_id=msg_id)
                except:
                    pass
    
    # Удаляем только окантовку
    data.pop("edging_rug", None)
    data.pop("edging_image_ids", None)
    await state.set_data(data)
    await callback.message.edit_text("Выберите окантовку ковра", reply_markup=ikb.get_edging_rug_keyboard())
    await state.set_state(OrderInfo.edging_rug)
    await callback.answer()