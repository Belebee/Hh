
import os
import sys
import subprocess

def install_if_missing(package):
    try:
        __import__(package)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install_if_missing("pip")

packages = [
    "requests==2.31.0",
    "python-telegram-bot==20.3", 

]

for package in packages:
    install_if_missing(package)

os.system("clear")


import requests
import time
import hashlib
import hmac
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackContext,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)
import asyncio

API_KEY = 'mx0vglX75gG0MdTDB3'
SECRET_KEY = 'abebe1640bc14bf2b9b278b31225c13f'
MEXC_API_URL = "https://api.mexc.com/api/v3"
DEX_API_URL = "https://api.dexscreener.com"

ADMIN_ID = 5244655536
show_massage = True
is_checking_active = True

# روابط المنصات اللامركزية
DEX_SWAP_LINKS = {
    "bsc": "https://pancakeswap.finance/swap?outputCurrency={contract}",
    "ethereum": "https://app.uniswap.org/#/swap?outputCurrency={contract}",
    "solana": "https://raydium.io/swap/?inputCurrency=USDC&outputCurrency={contract}",
    "arbitrum": "https://app.uniswap.org/#/swap?chain=arbitrum&outputCurrency={contract}",
    "polygon": "https://quickswap.exchange/#/swap?outputCurrency={contract}",
    "avalanche": "https://traderjoexyz.com/avalanche/trade?outputCurrency={contract}",
    "optimism": "https://app.uniswap.org/#/swap?chain=optimism&outputCurrency={contract}",
    "fantom": "https://spookyswap.finance/swap?outputCurrency={contract}",
    "cronos": "https://mm.finance/swap?outputCurrency={contract}",
    "aptos": "https://liquidswap.com/#/swap?outputCurrency={contract}",
    "sui": "https://suiswap.app/swap?outputCurrency={contract}",
    "near": "https://app.ref.finance/swap?outputCurrency={contract}",
    "cosmos": "https://app.osmosis.zone/?outputCurrency={contract}",
    "klaytn": "https://klayswap.com/exchange/swap?outputCurrency={contract}",
    "aurora": "https://app.trisolaris.io/swap?outputCurrency={contract}",
    "zksync": "https://syncswap.xyz/?outputCurrency={contract}",
    "base": "https://baseswap.fi/bswap?outputCurrency={contract}",
    "linea": "https://kyberswap.com/swap/linea?outputCurrency={contract}",
    "mantle": "https://app.fusionx.finance/swap?outputCurrency={contract}",
    "metis": "https://netswap.io/#/swap?outputCurrency={contract}",
    "moonbeam": "https://stellaswap.com/swap?outputCurrency={contract}",
    "moonriver": "https://solarbeam.io/exchange/swap?outputCurrency={contract}",
    "harmony": "https://app.sushi.com/swap?chainId=1666600000&outputCurrency={contract}",
    "celo": "https://ubeswap.org/#/swap?outputCurrency={contract}",
    "gnosis": "https://app.honeyswap.org/#/swap?outputCurrency={contract}",
    "kava": "https://equilibrefinance.com/swap?outputCurrency={contract}",
    "okc": "https://www.joyswap.org/#/swap?outputCurrency={contract}"
}

def create_signature(query_string, secret_key):
    return hmac.new(secret_key.encode(), query_string.encode(), hashlib.sha256).hexdigest()

def get_contract_addresses():
    timestamp = str(int(time.time() * 1000))
    query_string = f"timestamp={timestamp}"
    signature = create_signature(query_string, SECRET_KEY)
    headers = {"X-MEXC-APIKEY": API_KEY}
    url = f"{MEXC_API_URL}/capital/config/getall?{query_string}&signature={signature}"

    response = requests.get(url, headers=headers)

    valid_networks = {
        "Solana(SOL)": "solana",
        "BNB Smart Chain(BEP20)": "bsc",
        "Ethereum(ERC20)": "ethereum",
        "Polygon(MATIC)": "polygon",
        "Avalanche C-Chain": "avalanche",
        "Arbitrum One": "arbitrum",
        "Optimism": "optimism",
        "Fantom": "fantom",
        "Cronos": "cronos",
        "Aptos": "aptos",
        "Sui": "sui",
        "Near Protocol": "near",
        "Cosmos": "cosmos",
        "Klaytn": "klaytn",
        "Aurora": "aurora",
        "zkSync Era": "zksync",
        "Base": "base",
        "Linea": "linea",
        "Mantle": "mantle",
        "Metis": "metis",
        "Moonbeam": "moonbeam",
        "Moonriver": "moonriver",
        "Harmony": "harmony",
        "Celo": "celo",
        "Gnosis": "gnosis",
        "Kava": "kava",
        "OKX Chain": "okc",
    }

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
        print("❌ Error getting contracts:", response.status_code, response.text)
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
                if liquidity_usd and liquidity_usd < 50:
                    print(f"🔴 Low liquidity USD ({liquidity_usd}). Skipping...")
                    continue

                price_usd = pair.get('priceUsd')
                if price_usd:
                    return float(price_usd)
        return None
    except requests.exceptions.RequestException as e:
        return None

def get_order_book(symbol):
    symbol += "USDT"
    url = f"{MEXC_API_URL}/depth"
    params = {'symbol': symbol, 'limit': 40}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
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
        print(f"❌ MEXC request error for {symbol}: {e}")
        return None

def get_mexc_sell_price(symbol, target_amount=20):
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

async def check_price_difference(context: CallbackContext):
    contracts = get_contract_addresses()
    if not contracts:
        return

    print("✅ Starting spread check...")

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

        if mexc_price_buy is None or mexc_price_sell is None:
            continue

        mexc_price = get_mexc_price(symbol)
        if mexc_price is None:
            continue

        dex_price = get_dexscreener_price(network, contract_address)
        if dex_price is None:
            continue

        spread_without_fee = ((mexc_price - dex_price) / dex_price) * 100
        if abs(spread_without_fee) <= 5 or abs(spread_without_fee) > 100:
            continue

        mexc_link = f"https://www.mexc.com/ru-RU/exchange/{symbol}_USDT"
        dex_link = f"https://dexscreener.com/{network}/{contract_address}"
        dex_swap_link = DEX_SWAP_LINKS.get(network, "").format(contract=contract_address)
        
        # حساب الفروقات والرسوم
        difference_buy = ((dex_price - mexc_price_buy) / mexc_price_buy) * 100  # ربح عند الشراء من MEXC والبيع على DEX
        difference_sell = ((mexc_price_sell - dex_price) / dex_price) * 100  # ربح عند الشراء من DEX والبيع على MEXC
        
        # حساب رسوم السحب كنسبة مئوية
        if dex_price > 0:
            withdraw_fee_percentage = (withdraw_fee * dex_price / mexc_price_buy) * 100 if mexc_price_buy > 0 else 0
        else:
            withdraw_fee_percentage = 0
        
        global show_massage
        if show_massage:
            if abs(difference_buy) > 799 or abs(difference_sell) > 799:
                continue
            elif difference_buy >= 10:  # فرصة الشراء من MEXC والبيع على DEX
                net_profit = difference_buy - withdraw_fee_percentage
                if contract["withdraw_enable"] and net_profit > 0:
                    message = (
                        f"📈 **Network**: {network}\n"
                        f"🔄 **Opportunity**: Buy on MEXC → Sell on DEX\n\n"
                        f"🔹 **Coin**: {symbol}\n"
                        f"💵 **MEXC Buy Price**: ${mexc_price_buy:.8f} | [MEXC Link]({mexc_link})\n"
                        f"📉 **DEX Sell Price**: ${dex_price:.8f} | [DexScreener]({dex_link})\n"
                        f"🔗 **Swap on DEX**: [Sell {symbol} here]({dex_swap_link})\n"
                        f"📊 **Gross Profit**: +{difference_buy:.2f}%\n"
                        f"💸 **Withdrawal Fee**: {withdraw_fee} {symbol} (~{withdraw_fee_percentage:.2f}%)\n"
                        f"💰 **Net Profit**: +{net_profit:.2f}%\n"
                        f"🔑 **Withdrawal enabled**: {'✅' if contract['withdraw_enable'] else '❌'}"
                    )
                    await context.bot.send_message(chat_id=ADMIN_ID, text=message, parse_mode='Markdown')

            elif difference_sell >= 10:  # فرصة الشراء من DEX والبيع على MEXC
                net_profit = difference_sell - withdraw_fee_percentage
                if contract["deposit_enable"] and net_profit > 0:
                    message = (
                        f"📈 **Network**: {network}\n"
                        f"🔄 **Opportunity**: Buy on DEX → Sell on MEXC\n\n"
                        f"🔹 **Coin**: {symbol}\n"
                        f"💵 **DEX Buy Price**: ${dex_price:.8f} | [DexScreener]({dex_link})\n"
                        f"📉 **MEXC Sell Price**: ${mexc_price_sell:.8f} | [MEXC Link]({mexc_link})\n"
                        f"🔗 **Swap on DEX**: [Buy {symbol} here]({dex_swap_link})\n"
                        f"📊 **Gross Profit**: +{difference_sell:.2f}%\n"
                        f"💸 **Withdrawal Fee**: {withdraw_fee} {symbol} (~{withdraw_fee_percentage:.2f}%)\n"
                        f"💰 **Net Profit**: +{net_profit:.2f}%\n"
                        f"🔑 **Deposit enabled**: {'✅' if contract['deposit_enable'] else '❌'}"
                    )
                    await context.bot.send_message(chat_id=ADMIN_ID, text=message, parse_mode='Markdown')

async def start_checking_job(context: CallbackContext):
    global is_checking_active
    is_checking_active = True
    while is_checking_active:
        await check_price_difference(context)
        await asyncio.sleep(60)

async def stop_checking_job():
    global is_checking_active
    is_checking_active = False

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text('✅ Bot is running automatically with 10% spread threshold.')

async def button(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    global show_massage

    if query.data == 'start_checking':
        if update.effective_user.id == ADMIN_ID:
            if not is_checking_active:
                await query.edit_message_text(text="✅ Spread checker started!")
                show_massage = True
                context.job_queue.run_repeating(
                    check_price_difference,
                    interval=60.0,
                    first=0.0,
                    chat_id=ADMIN_ID
                )
            else:
                await query.edit_message_text(text="❌ Checking is already active.")
        else:
            await query.edit_message_text(text="❌ You don't have permission to start checking.")

    elif query.data == 'stop_showing':
        if update.effective_user.id == ADMIN_ID:
            if is_checking_active:
                await stop_checking_job()
                show_massage = False
                await query.edit_message_text(text="⛔ Stopped showing messages.")
            else:
                await query.edit_message_text(text="❌ Checking wasn't started.")
        else:
            await query.edit_message_text(text="❌ You don't have permission to stop checking.")

async def info(update: Update, context: CallbackContext):
    await update.message.reply_text("Add to ignore: /add_ignore [symbol]")

async def add_ignore(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You don't have permission.")
        return

    try:
        symbol = context.args[0].upper()
    except IndexError:
        await update.message.reply_text("Error: Please provide a coin symbol.")
        return

    with open("ignore.txt", "r", encoding="utf-8") as file:
        ignore_list = file.read().splitlines()

    if symbol in ignore_list:
        await update.message.reply_text(f"Symbol '{symbol}' already exists.")
    else:
        with open("ignore.txt", "a", encoding="utf-8") as file:
            file.write(symbol + "\n")

        await update.message.reply_text(f"Symbol '{symbol}' added to ignore list.")

def main():
    application = Application.builder().token("7887167602:AAEmpIny8aLfno4D-LbmEaP4hAjENKDdaoA").build()

    # بدء الفحص تلقائيًا عند التشغيل
    application.job_queue.run_repeating(
        check_price_difference,
        interval=60.0,
        first=0.0,
        chat_id=ADMIN_ID
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("info", info))
    application.add_handler(CommandHandler("add_ignore", add_ignore))
    application.add_handler(CallbackQueryHandler(button))

    application.run_polling()

if __name__ == "__main__":
    main()
