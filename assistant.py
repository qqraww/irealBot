import json
import re
import logging
from typing import Dict, List, Optional
from openai import OpenAI
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters, CommandHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- КОНФИГУРАЦИЯ ---
API_KEY = "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"
MODEL_NAME = "google/gemini-flash-1.5-8b"
TELEGRAM_TOKEN = "7992173756:AAF96mu7hpiR6brqQmWRX81UoKLu6RYoIVI"
ADMIN_ID = 7341966376

client = OpenAI(api_key=API_KEY, base_url="https://openrouter.ai/api/v1")

# --- ДАННЫЕ ---
products = [
  {
    "model": "iphone 15 pro max",
    "variants": [
      {"memory": "256GB", "color": "белый-титановый", "price": 92000},
      {"memory": "256GB", "color": "серый-титановый", "price": 104000},
      {"memory": "256GB", "color": "синий-титановый", "price": 92000},
      {"memory": "256GB", "color": "черный-титановый", "price": 135000},
      {"memory": "512GB", "color": "белый-титановый", "price": 116000},
      {"memory": "512GB", "color": "серый-титановый", "price": 134000},
      {"memory": "512GB", "color": "синий-титановый", "price": 94000},
      {"memory": "512GB", "color": "черный-титановый", "price": 117000},
      {"memory": "1TB", "color": "белый-титановый", "price": 141000},
      {"memory": "1TB", "color": "серый-титановый", "price": 181000},
      {"memory": "1TB", "color": "синий-титановый", "price": 141000},
      {"memory": "1TB", "color": "черный-титановый", "price": 137000}
    ]
  },
  {
    "model": "iphone 16 pro max",
    "variants": [
      {"memory": "256GB", "color": "белый", "price": 112000},
      {"memory": "256GB", "color": "золотистый", "price": 112000},
      {"memory": "256GB", "color": "серебристый", "price": 127000},
      {"memory": "256GB", "color": "чёрный", "price": 114000},
      {"memory": "512GB", "color": "белый", "price": 131000},
      {"memory": "512GB", "color": "золотистый", "price": 133000},
      {"memory": "512GB", "color": "серебристый", "price": 138000},
      {"memory": "512GB", "color": "чёрный", "price": 134000},
      {"memory": "1TB", "color": "белый", "price": 146000},
      {"memory": "1TB", "color": "золотистый", "price": 139000},
      {"memory": "1TB", "color": "серебристый", "price": 152000},
      {"memory": "1TB", "color": "чёрный", "price": 147000}
    ]
  },
  {
    "model": "iphone 14",
    "variants": [
      {"memory": "128GB", "color": "чёрный (midnight)", "price": 55000},
      {"memory": "256GB", "color": "чёрный (midnight)", "price": 67000},
      {"memory": "128GB", "color": "жёлтый (yellow)", "price": 55000},
      {"memory": "256GB", "color": "белый (starlight)", "price": 57000}
    ]
  },
  {
    "model": "iphone 13",
    "variants": [
      {"memory": "128GB", "color": "белый (starlight)", "price": 52000},
      {"memory": "128GB", "color": "чёрный (midnight)", "price": 49000}
    ]
  },
  {
    "model": "iphone 11",
    "variants": [
      {"memory": "64GB", "color": "черный", "price": 40000},
      {"memory": "128GB", "color": "белый", "price": 45000}
    ]
  },
  {
    "model": "iphone x",
    "variants": [
      {"memory": "64GB", "color": "серебристый", "price": 38000},
      {"memory": "256GB", "color": "серебристый", "price": 50000}
    ]
  },
  {
    "model": "iphone 12 pro",
    "variants": [
      {"memory": "128GB", "color": "графитовый", "price": 60000},
      {"memory": "256GB", "color": "синий", "price": 65000}
    ]
  },
  {
    "model": "galaxy s24",
    "variants": [
      {"memory": "128GB", "color": "чёрный", "price": 51000}
    ]
  },
  {
    "model": "nothing phone 3a",
    "variants": [
      {"memory": "128GB", "color": "чёрный", "price": 37000},
      {"memory": "128GB", "color": "белый", "price": 40000}
    ]
  },
  {
    "model": "nothing phone 3a pro",
    "variants": [
      {"memory": "256GB", "color": "чёрный", "price": 49000},
      {"memory": "256GB", "color": "белый", "price": 53000}
    ]
  },
  {
    "model": "honor x7c",
    "variants": [
      {"memory": "128GB", "color": "белый", "price": 23000},
      {"memory": "128GB", "color": "чёрный", "price": 23000},
      {"memory": "128GB", "color": "зелёный", "price": 23000}
    ]
  }
]

# --- КОНТЕКСТ ПОЛЬЗОВАТЕЛЕЙ ---
user_contexts = {}

class UserContext:
    def __init__(self):
        self.state = "normal"  # normal, awaiting_phone
        self.wanted_model = None      # iphone 16 pro max
        self.wanted_memory = None     # 512GB  
        self.wanted_color = None      # белый
        self.current_selection = None # точный найденный товар
        self.order_data = {}

# --- ПРОВЕРКА НА ЗАПРОС АССОРТИМЕНТА ---
def is_catalog_request(text: str) -> bool:
    """Проверяет, просит ли пользователь показать каталог/ассортимент"""
    catalog_words = [
        'ассортимент', 'каталог', 'что есть', 'какие модели', 'покажи', 'список',
        'товары', 'телефоны', 'наличие', 'все модели'
    ]
    text_lower = text.lower()
    return any(word in text_lower for word in catalog_words)

def show_catalog() -> str:
    """Показывает весь каталог товаров"""
    catalog = "📱 <b>Наш ассортимент:</b>\n\n"
    
    for device in products:
        min_price = min(v['price'] for v in device['variants'])
        max_price = max(v['price'] for v in device['variants'])
        
        if min_price == max_price:
            price_text = f"{min_price:,} ₽"
        else:
            price_text = f"от {min_price:,} до {max_price:,} ₽"
            
        catalog += f"• <b>{device['model']}</b> — {price_text}\n"
    
    catalog += f"\n💬 Напишите модель, память и цвет для заказа!"
    return catalog

# --- УЛУЧШЕННЫЙ ПАРСИНГ ---
def extract_user_wants(text: str, context: UserContext):
    """Извлекает и обновляет желания пользователя"""
    text_lower = text.lower()
    
    # РАСШИРЕННЫЕ ВАРИАНТЫ МОДЕЛЕЙ
    model_patterns = {
        "iphone 16 pro max": [
            'iphone 16 pro max', '16 про макс', 'айфон 16 про макс', 
            '16 pro max', 'iphone16promax'
        ],
        "iphone 15 pro max": [
            'iphone 15 pro max', '15 про макс', 'айфон 15 про макс',
            '15 pro max', 'iphone15promax'
        ],
        "iphone 14": [
            'iphone 14', '14', 'айфон 14', 'iphone14'
        ],
        "iphone 13": [
            'iphone 13', '13', 'айфон 13', 'iphone13'
        ],
        "iphone 12 pro": [
            'iphone 12 pro', '12 про', 'айфон 12 про', 'iphone 12',
            '12 pro', 'iphone12pro', 'айфон 12'
        ],
        "iphone 11": [
            'iphone 11', '11', 'айфон 11', 'iphone11'
        ],
        "iphone x": [
            'iphone x', 'айфон х', 'iphonex', 'iphone х'
        ],
        "galaxy s24": [
            'galaxy s24', 's24', 'самсунг s24', 'samsung s24'
        ],
        "nothing phone 3a pro": [
            'nothing phone 3a pro', 'nothing 3a pro', 'носинг про 3а',
            'nothing pro 3a', 'nothing3apro', 'ничинг 3а про'
        ],
        "nothing phone 3a": [
            'nothing phone 3a', 'nothing 3a', 'носинг 3а',
            'nothing3a', 'ничинг 3а'
        ],
        "honor x7c": [
            'honor x7c', 'хонор x7c', 'honorx7c'
        ]
    }
    
    # Ищем модель
    for model_key, patterns in model_patterns.items():
        for pattern in patterns:
            if pattern in text_lower:
                context.wanted_model = model_key
                break
        if context.wanted_model:
            break
    
    # ПАМЯТЬ
    memory_match = re.search(r'(\d+)\s*(gb|гб|tb|тб)', text_lower)
    if memory_match:
        size, unit = memory_match.groups()
        if unit.lower() in ['tb', 'тб']:
            context.wanted_memory = f"{size}TB"
        else:
            context.wanted_memory = f"{size}GB"
    
    # ЦВЕТ (расширенный)
    color_patterns = {
        'белый': ['белый', 'white', 'бел'],
        'черный': ['черный', 'чёрный', 'black', 'чер'],
        'серый': ['серый', 'серебристый', 'silver', 'сер'],
        'синий': ['синий', 'blue', 'син'],
        'желтый': ['желтый', 'жёлтый', 'yellow', 'жел'],
        'зеленый': ['зеленый', 'зелёный', 'green', 'зел'],
        'золотой': ['золотой', 'золотистый', 'gold', 'зол']
    }
    
    for color_key, patterns in color_patterns.items():
        if any(pattern in text_lower for pattern in patterns):
            context.wanted_color = color_key
            break

def find_exact_device(context: UserContext):
    """Ищет точное совпадение по желаниям пользователя"""
    if not context.wanted_model:
        return None
    
    # Карта соответствия цветов
    color_map = {
        'белый': ['белый', 'белый-титановый', 'starlight'],
        'черный': ['чёрный', 'черный', 'черный-титановый', 'midnight'],
        'серый': ['серый-титановый', 'серебристый', 'графитовый'],
        'синий': ['синий', 'синий-титановый'],
        'желтый': ['жёлтый', 'yellow'],
        'зеленый': ['зелёный'],
        'золотой': ['золотистый']
    }
    
    for device in products:
        if device['model'] == context.wanted_model:
            for variant in device['variants']:
                # Проверка памяти
                memory_match = not context.wanted_memory or variant['memory'] == context.wanted_memory
                
                # Проверка цвета
                color_match = True
                if context.wanted_color:
                    variant_color = variant['color'].lower()
                    wanted_colors = color_map.get(context.wanted_color, [context.wanted_color])
                    color_match = any(color in variant_color for color in wanted_colors)
                
                if memory_match and color_match:
                    return {
                        'model': device['model'],
                        'memory': variant['memory'],
                        'color': variant['color'],
                        'price': variant['price']
                    }
    
    return None

def is_order_intent(text: str) -> bool:
    """Проверяет намерение заказать"""
    order_words = ['хочу', 'нужен', 'беру', 'заказать', 'оформить', 'купить']
    return any(word in text.lower() for word in order_words)

def is_confirmation(text: str) -> bool:
    """Проверяет подтверждение"""
    text_clean = text.lower().strip()
    confirm_words = ['да', 'ок', 'согласен', 'беру', 'оформляем', 'давайте', '+', 'yes']
    return text_clean in confirm_words

def get_missing_info(context: UserContext) -> List[str]:
    """Возвращает список недостающей информации"""
    missing = []
    if not context.wanted_model:
        missing.append("модель")
    if not context.wanted_memory:
        missing.append("память")
    if not context.wanted_color:
        missing.append("цвет")
    return missing

def clear_context(context: UserContext):
    """Очищает контекст пользователя"""
    context.wanted_model = None
    context.wanted_memory = None
    context.wanted_color = None
    context.current_selection = None

# --- TELEGRAM HANDLERS ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_contexts:
        user_contexts[user_id] = UserContext()
    
    catalog = show_catalog()
    await update.message.reply_text(catalog, parse_mode='HTML')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.full_name
    user_text = update.message.text.strip()
    
    if user_id not in user_contexts:
        user_contexts[user_id] = UserContext()
    
    user_ctx = user_contexts[user_id]
    await update.message.chat.send_action("typing")
    
    try:
        # === ОБРАБОТКА ВВОДА ТЕЛЕФОНА ===
        if user_ctx.state == "awaiting_phone":
            phone_match = re.search(r'[\+]?[78]?[\s\-\(\)]?(\d[\s\-\(\)]?){10,14}', user_text)
            
            if phone_match:
                phone = re.sub(r'[\s\-\(\)]', '', phone_match.group(0))
                order = user_ctx.order_data
                
                # Отправка админу
                admin_msg = (
                    f"🛒 <b>НОВЫЙ ЗАКАЗ</b>\n\n"
                    f"👤 @{username}\n"
                    f"📱 <b>{order['model']}</b>\n"
                    f"💾 {order['memory']}\n"
                    f"🎨 {order['color']}\n"
                    f"💰 <b>{order['price']:,} ₽</b>\n"
                    f"📞 <code>{phone}</code>"
                )
                
                try:
                    await context.bot.send_message(ADMIN_ID, admin_msg, parse_mode='HTML')
                    await update.message.reply_text(
                        f"✅ <b>Заказ принят!</b>\n\nМенеджер свяжется с вами в ближайшее время.\n📞 {phone}",
                        parse_mode='HTML'
                    )
                except:
                    await update.message.reply_text("Ошибка отправки заказа. Попробуйте ещё раз.")
                
                # Полный сброс
                user_ctx.state = "normal"
                clear_context(user_ctx)
                user_ctx.order_data = {}
                
            else:
                await update.message.reply_text("Введите корректный номер телефона (например: +79998887766)")
            return
        
        # === ПРОВЕРКА НА ЗАПРОС КАТАЛОГА ===
        if is_catalog_request(user_text):
            clear_context(user_ctx)  # Сбрасываем предыдущий выбор
            catalog = show_catalog()
            await update.message.reply_text(catalog, parse_mode='HTML')
            return
        
        # === ПОДТВЕРЖДЕНИЕ ЗАКАЗА ===
        if user_ctx.current_selection and is_confirmation(user_text):
            user_ctx.state = "awaiting_phone"
            user_ctx.order_data = user_ctx.current_selection
            device = user_ctx.current_selection
            
            await update.message.reply_text(
                f"✅ <b>Отлично! Оформляем заказ:</b>\n\n"
                f"📱 <b>{device['model']}</b>\n"
                f"💾 {device['memory']}\n"
                f"🎨 {device['color']}\n"
                f"💰 <b>{device['price']:,} ₽</b>\n\n"
                f"Напишите ваш номер телефона 📞",
                parse_mode='HTML'
            )
            return
        
        # === ИЗВЛЕЧЕНИЕ ЖЕЛАНИЙ ПОЛЬЗОВАТЕЛЯ ===
        extract_user_wants(user_text, user_ctx)
        
        # === ПОИСК ТОЧНОГО СОВПАДЕНИЯ ===
        exact_device = find_exact_device(user_ctx)
        
        if exact_device:
            user_ctx.current_selection = exact_device
            
            # Если пользователь явно хочет заказать - сразу оформляем
            if is_order_intent(user_text):
                user_ctx.state = "awaiting_phone"
                user_ctx.order_data = exact_device
                
                await update.message.reply_text(
                    f"✅ <b>Есть в наличии!</b>\n\n"
                    f"📱 <b>{exact_device['model']}</b>\n"
                    f"💾 {exact_device['memory']}\n"
                    f"🎨 {exact_device['color']}\n"
                    f"💰 <b>{exact_device['price']:,} ₽</b>\n\n"
                    f"Напишите ваш номер телефона для оформления заказа 📞",
                    parse_mode='HTML'
                )
            else:
                # Показываем товар и спрашиваем
                await update.message.reply_text(
                    f"📱 <b>{exact_device['model']}</b>\n"
                    f"💾 {exact_device['memory']}\n"
                    f"🎨 {exact_device['color']}\n"
                    f"💰 <b>{exact_device['price']:,} ₽</b>\n\n"
                    f"✅ В наличии! <b>Оформляем заказ?</b>",
                    parse_mode='HTML'
                )
        else:
            # === ЕСЛИ НЕ НАЙДЕНО - УТОЧНЯЕМ ===
            missing = get_missing_info(user_ctx)
            
            if missing:
                # Показываем что уже выбрано и что нужно уточнить
                selected_info = []
                if user_ctx.wanted_model:
                    selected_info.append(f"📱 Модель: <b>{user_ctx.wanted_model}</b>")
                if user_ctx.wanted_memory:
                    selected_info.append(f"💾 Память: <b>{user_ctx.wanted_memory}</b>")
                if user_ctx.wanted_color:
                    selected_info.append(f"🎨 Цвет: <b>{user_ctx.wanted_color}</b>")
                
                response = ""
                if selected_info:
                    response += "Выбрано:\n" + "\n".join(selected_info) + "\n\n"
                
                if len(missing) == 1:
                    response += f"Уточните <b>{missing[0]}</b>:"
                else:
                    response += f"Уточните <b>{' и '.join(missing)}</b>:"
                
                await update.message.reply_text(response, parse_mode='HTML')
            else:
                # Вся информация есть, но товар не найден
                await update.message.reply_text(
                    f"❌ К сожалению, <b>{user_ctx.wanted_model}</b> {user_ctx.wanted_memory} {user_ctx.wanted_color} нет в наличии.\n\n"
                    f"Напишите <i>«ассортимент»</i> чтобы посмотреть доступные модели.",
                    parse_mode='HTML'
                )
                clear_context(user_ctx)  # Сбрасываем после неудачного поиска
        
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка. Напишите <i>«ассортимент»</i> чтобы начать заново.",
            parse_mode='HTML'
        )

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("🚀 ИДЕАЛЬНЫЙ бот iReal запущен!")
    print("✅ Все проблемы решены!")
    app.run_polling()

if __name__ == "__main__":
    main()