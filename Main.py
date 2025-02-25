import requests
import logging
import time
import hashlib
import hmac
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from collections import deque
import telebot
from telebot import types
import sqlite3
import random
import threading
import string
import asyncio

API_KEY = "YOUR MEXC API KEY"  # Замініть на свій API-ключ
SECRET_KEY = "YOUR MEXC SECRET KEY"  # Замініть на свій секретний ключ
MEXC_API_URL = "https://api.mexc.com/api/v3"
DEX_API_URL = "https://api.dexscreener.com"

bot = telebot.TeleBot("TG API KEY")

ADMIN_ID = # Admin id telegram
global show_massage
def create_signature(query_string, secret_key):
    return hmac.new(secret_key.encode(), query_string.encode(), hashlib.sha256).hexdigest()

def get_contract_addresses():
    timestamp = str(int(time.time() * 1000))
    query_string = f"timestamp={timestamp}"
    signature = create_signature(query_string, SECRET_KEY)
    headers = {"X-MEXC-APIKEY": API_KEY}
    url = f"{MEXC_API_URL}/capital/config/getall?{query_string}&signature={signature}"

    response = requests.get(url, headers=headers)

    # Перелік мереж, які ми хочемо обробляти
    valid_networks = {
        "Solana(SOL)": "solana",
        "BNB Smart Chain(BEP20)": "bsc",
    }
 #
  #"Toncoin(TON)": "ton",         "Polygon(MATIC)": "polygon",

    if response.status_code == 200:
        data = response.json()
        contract_list = []
        for token in data:
            coin = token.get("coin")
            for network in token.get("networkList", []):
                contract = network.get("contract")
                network_name = network.get("network")
                if network_name in valid_networks:
                    withdraw_fee = network.get("withdrawFee", 0)
                    withdraw_min = network.get("withdrawMin", "N/A")
                    withdraw_max = network.get("withdrawMax", "N/A")
                    deposit_enable = network.get("depositEnable", False)
                    withdraw_enable = network.get("withdrawEnable", False)


                    contract_list.append({
                        "symbol": coin,
                        "contract_address": contract,
                        "network": valid_networks[network_name],
                        "withdraw_fee": withdraw_fee,
                        "withdraw_min": withdraw_min,
                        "withdraw_max": withdraw_max,
                        "deposit_enable": deposit_enable,
                        "withdraw_enable": withdraw_enable
                    })
        return contract_list
    else:
        print("❌ Помилка отримання контрактів:", response.status_code, response.text)
        return []

def get_dexscreener_price(chain_id, contract_address):
    try:
        url = f"{DEX_API_URL}/token-pairs/v1/{chain_id}/{contract_address}"
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        data = response.json()
        if isinstance(data, list):
            pairs = data
        elif isinstance(data, dict) and 'pairs' in data:
            pairs = data['pairs']
        else:
            return None

        for pair in pairs:
            liquidity = pair.get('liquidity')
            if liquidity:
                liquidity_usd = liquidity.get('usd')
                if liquidity_usd and liquidity_usd < 300:
                    print(f"🔴 Liquidity USD too low ({liquidity_usd}). Skipping...")
                    continue

                price_usd = pair.get('priceUsd')
                if price_usd:
                    return float(price_usd)
        return None
    except requests.exceptions.RequestException as e:
        #print(f"❌ Помилка при запиті до DexScreener: {e}")
        return None


# Функція для отримання глибини ринку
def get_order_book(symbol):
    symbol += "USDT"
    url = f"{MEXC_API_URL}/depth"
    params = {'symbol': symbol, 'limit': 40}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        #print(f"❌ Помилка при запиті до MEXC для {symbol}: {response.status_code}")
        return None

def get_mexc_price(symbol):
    url = f"{MEXC_API_URL}/ticker/price?symbol={symbol}USDT"
    try:
        response = requests.get(url).json()
        if 'price' in response:
            price = float(response['price'])
            return price
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Помилка при запиті до MEXC для {symbol}: {e}")
        return None

def get_mexc_sell_price(symbol, target_amount=20):
    """Отримує середню ціну ордерів на продаж на суму $20 для пари символ-USDT."""

    # Отримуємо глибину ринку (ордери на продаж)
    order_book = get_order_book(symbol)

    if not order_book:
        return None

    total_price = 0
    total_quantity = 0
    total_value = 0


    for ask in order_book['asks']:
        price = float(ask[0])
        quantity = float(ask[1])
        value = price * quantity


        if total_value < target_amount:
            total_price += price * quantity
            total_quantity += quantity
            total_value += value


        if total_value >= target_amount:
            break

    if total_quantity == 0:
        return None


    average_price = total_price / total_quantity


    return round(average_price, 8)

def get_mexc_buy_price(symbol, target_amount=20):


    order_book = get_order_book(symbol)

    if not order_book:
        return None

    total_price = 0
    total_quantity = 0
    total_value = 0


    for bid in order_book['bids']:
        price = float(bid[0])
        quantity = float(bid[1])
        value = price * quantity

        if total_value < target_amount:
            total_price += price * quantity
            total_quantity += quantity
            total_value += value

        if total_value >= target_amount:
            break

    if total_quantity == 0:
        return None


    average_price = total_price / total_quantity


    return round(average_price, 8)



def check_price_difference():
    contracts = get_contract_addresses()
    if not contracts:
        return

    print("✅ Start check spread...")

    for contract in contracts:
        symbol = contract["symbol"]
        contract_address = contract["contract_address"]
        network = contract["network"]


        try:
            withdraw_fee = float(contract["withdraw_fee"]) if contract["withdraw_fee"] != "N/A" else 0.0
        except ValueError:
            withdraw_fee = 0.0
        with open("ignore.txt", "r", encoding="utf-8") as file:
            ignore_list = file.read().splitlines()

        if symbol in ignore_list:
            continue




        mexc_price_buy = get_mexc_buy_price(symbol, target_amount=20)
        mexc_price_sell = get_mexc_sell_price(symbol, target_amount=20)

        if mexc_price_buy is None:
            continue
        if mexc_price_sell is None:
            continue



        mexc_price = get_mexc_price(symbol)
        if mexc_price is None:
            continue

        # Отримуємо ціну з DexScreener
        dex_price = get_dexscreener_price(network, contract_address)
        if dex_price is None:
            continue
        spread_without_fee = ((mexc_price - dex_price) / dex_price) * 100
        if abs(spread_without_fee) <= 5 or abs(spread_without_fee) > 300:
            continue

        spread_withdraw = 0.0
        mexc_link = f"https://www.mexc.com/ru-RU/exchange/{symbol}_USDT"
        dex_link = f"https://dexscreener.com/{network}/{contract_address}"
        difference = ((mexc_price - dex_price) / dex_price) * 100
        difference_buy = ((mexc_price_buy - dex_price) / dex_price) * 100
        difference_sell = ((mexc_price_sell - dex_price) / dex_price) * 100

        global show_massage
        if show_massage:
            if abs(difference) > 799:
                continue
            elif difference_buy >= 4:
                min_amount = (spread_withdraw / abs(difference_buy)) * (100 + abs(difference))
                if mexc_price > dex_price:
                    if contract["deposit_enable"]:
                        message = (
                            f"📈 Network! {network}\n"
                            f"📈 Arbitrage is possible!\n\n"
                            f"🔹 **Coin**: {symbol}\n"
                            f"💵 **MEXC**: ${mexc_price:.15f} | [MEXC pair]({mexc_link})\n"
                            f"📉 **DexScreener**: ${dex_price:.15f} | [DexScreener pair]({dex_link})\n"
                            f"📊 **Difference**: {difference_buy:.2f}%\n"
                            f"💰 **MEXC fee**: {spread_withdraw:.2f}$\n"
                            f"🔑 **Deposit enabled on MEXC**: {'Yes' if contract['deposit_enable'] else 'No'}"
                        )
                        bot.send_message(ADMIN_ID, message)

                elif difference_sell <= -4:
                    min_amount = (spread_withdraw / abs(difference_sell)) * (100 + abs(difference))
                    if contract["withdraw_enable"]:
                        message = (
                            f"📈 Network! {network}\n"
                            f"📈 Arbitrage is possible!\n\n"
                            f"🔹 **Coin**: {symbol}\n"
                            f"💵 **MEXC**: ${mexc_price:.15f} | [MEXC pair]({mexc_link})\n"
                            f"📉 **DexScreener**: ${dex_price:.15f} | [DexScreener pair]({dex_link})\n"
                            f"📊 **Difference**: {difference_sell:.2f}%\n"
                            f"💰 **Withdrawal fee**: {spread_withdraw:.10f} $\n"
                            f"📊 **USDT needed to break even on fees**: {min_amount:.10f} $\n"
                            f"🔑 **Withdrawal enabled on DexScreener**: {'Yes' if contract['withdraw_enable'] else 'No'}"
                        )
                        bot.send_message(ADMIN_ID, message)



@bot.message_handler(commands=["start_checking"])
def start_checking(message):
    if message.from_user.id == ADMIN_ID:
        bot.reply_to(message, "✅ Spread checker started!")
        while True:
            check_price_difference()
            time.sleep(60)  # Перевірка кожні 60 секунд
    else:
        bot.reply_to(message, "❌ No  admin.")


is_checking_active = False


def start_price_checking():
    global is_checking_active
    is_checking_active = True
    while is_checking_active:
        check_price_difference()
        time.sleep(60)


def stop_price_checking():
    global is_checking_active
    is_checking_active = False


@bot.message_handler(commands=["start"])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    start_button = types.KeyboardButton("Start")
    stop_button = types.KeyboardButton("Stop showing")
    markup.add(start_button, stop_button)
    bot.send_message(message.chat.id, "Chose action:", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "Start")
def start_checking(message):
    if message.from_user.id == ADMIN_ID:
        if not is_checking_active:
            bot.reply_to(message, "✅ Spread checker started!")

            checking_thread = threading.Thread(target=start_price_checking)
            global show_massage
            show_massage = True
            checking_thread.start()
        else:
            bot.reply_to(message, "❌ Перевірка вже активна.")
    else:
        bot.reply_to(message, "❌ У вас немає прав для старту перевірки.")


@bot.message_handler(func=lambda message: message.text == "Stop showing")
def stop_checking(message):
    if message.from_user.id == ADMIN_ID:
        if is_checking_active:
            stop_price_checking()
            bot.reply_to(message, "⛔ Stop showing .")
            global show_massage
            show_massage = False
        else:
            bot.reply_to(message, "❌ Перевірка не була запущена.")
    else:
        bot.reply_to(message, "❌ У вас немає прав для зупинки перевірки.")


@bot.message_handler(commands=["info"])
def info(message):
    bot.reply_to(message, "add to ignore /add_ignore")


@bot.message_handler(commands=["add_ignore"])
def add_ignore(message):
    if message.from_user.id == ADMIN_ID:
        try:
            symbol = message.text.split(maxsplit=1)[1]
        except IndexError:
            bot.reply_to(message, "Помилка: Where coin name?.")
            return

        with open("ignore.txt", "r", encoding="utf-8") as file:
            ignore_list = file.read().splitlines()

        if symbol in ignore_list:
            bot.reply_to(message, f"Символ '{symbol}' already exists.")
        else:
            with open("ignore.txt", "a", encoding="utf-8") as file:
                file.write(symbol + "\n")

            bot.reply_to(message, f"Символ '{symbol}' added to ignore list.")


if __name__ == "__main__":
    bot.polling(none_stop=True)
