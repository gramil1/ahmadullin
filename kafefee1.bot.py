import logging, os, telebot 
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ConversationHandler
from dotenv import load_dotenv

load_dotenv()
bot = telebot.TeleBot(os.getenv('TOKEN'))


CHOOSING, CATEGORY, ITEM, QUANTITY, CONFIRMATION = range(5)

menu = {
  "Пицца": {
    "Маргарита": {"price": 350},
    "Пепперони": {"price": 400}
  },
  "Супы": {
    "Борщ": {"price": 300},
    "Томатный": {"price": 400}
  },
  "Салаты": {
    "Цезарь": {"price": 150},
    "Греческий": {"price": 200}
  },
  "Напитки": {
    "Кофе": {"price": 150},
    "Чай": {"price": 100}
  }
}

def build_menu_keyboard(buttons):
  keyboard = [buttons]
  return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)


def build_item_keyboard(category):
  buttons = [[InlineKeyboardButton(item, callback_data=f"{category}:{item}")] for item in menu[category]]
  return InlineKeyboardMarkup(buttons)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  await update.message.reply_text(
    "Добро пожаловать в наше кафе! Выберите категорию:",
    reply_markup=build_menu_keyboard(list(menu.keys()))
  )
  return CHOOSING


async def choose_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
  context.user_data['category'] = update.message.text
  await update.message.reply_text(
    f"Меню - {context.user_data['category']}:",
    reply_markup=build_item_keyboard(context.user_data['category'])
  )
  return ITEM


async def choose_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
  query = update.callback_query
  category, item = query.data.split(":")
  context.user_data['item'] = item
  await query.answer()
  await query.edit_message_text(
    f"Вы выбрали: {item}\nЦена: {menu[category][item]['price']:.2f} ₽\nВведите количество:"
  )
  return QUANTITY


async def choose_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
  try:
    quantity = int(update.message.text)
    if quantity > 0:
      context.user_data['quantity'] = quantity
      total_price = menu[context.user_data['category']][context.user_data['item']]['price'] * quantity
      await update.message.reply_text(
                f"Ваш заказ:\n{context.user_data['item']} x {quantity} = {total_price:.2f} ₽\nПодтвердить?",
        reply_markup=ReplyKeyboardMarkup([["Да", "Нет"]], resize_keyboard=True, one_time_keyboard=True)
      )
      return CONFIRMATION
    else:
      await update.message.reply_text("Количество должно быть больше 0.")
      return QUANTITY
  except ValueError:
    await update.message.reply_text("Неверное количество. Попробуйте снова.")
    return QUANTITY


async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if update.message.text == "Да":
    await update.message.reply_text("Ваш заказ принят! Спасибо!")
  else:
    await update.message.reply_text("Заказ отменен.")
  return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
  await update.message.reply_text("До свидания!", reply_markup=ReplyKeyboardRemove())
  return ConversationHandler.END


if __name__ == '__main__':
  application = ApplicationBuilder().token(os.getenv('TOKEN')).build()

  conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
      CHOOSING: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_category)],
      ITEM: [CallbackQueryHandler(choose_item)],
      QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_quantity)],
      CONFIRMATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_order)]
    },
    fallbacks=[CommandHandler('cancel', cancel)]
  )

  application.add_handler(conv_handler)
  application.run_polling()