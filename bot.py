import logging
import requests
from math import radians, cos, sin, asin, sqrt
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

import os
BOT_TOKEN = os.getenv("BOT_TOKEN")

TEXTS = {
    "ua": {
        "choose_lang": "Оберіть мову / Choose language / Wybierz język:",
        "welcome": "Привіт! Я допоможу знайти лікаря поруч і розібратися зі страховкою.\n\nЩо хочеш зробити?",
        "find_doctor": "🔍 Знайти лікарів поруч",
        "how_to_book": "📋 Як записатися",
        "insurance": "🛡️ Страховка / NFZ",
        "emergency": "🚨 Екстрені номери",
        "pesel": "🆔 Як отримати PESEL",
        "telemed": "💻 Телемедицина",
        "links": "🔗 Корисні посилання",
        "change_lang": "🌐 Змінити мову",
        "back": "🔙 Назад",
        "back_menu": "🔙 Назад у меню",
        "choose_spec": "Оберіть спеціальність:",
        "send_location": "Надішліть геолокацію",
        "searching": "Шукаю... ⏳",
        "spec_selected": "Спеціальність обрано. Надішли геолокацію:",
        "instructions": "📋 <b>Як записатися:</b>\n\n1. Зайдіть на <a href='https://www.znanylekarz.pl/'>ZnanyLekarz.pl</a>\n2. Оберіть спеціальність і місто\n3. Запишіться онлайн\n\nДля NFZ потрібен PESEL.",
        "insurance_text": "🛡️ <b>Страховка</b>\n\nДля державної медицини (NFZ) потрібен PESEL.\nЯкщо працюєш офіційно — страхує роботодавець.\n\n<a href='https://www.nfz.gov.pl/'>Сайт NFZ</a>",
        "emergency_text": "🚨 <b>Екстрені номери</b>\n\n112 — екстрена допомога\n999 — швидка\n998 — пожежна\n997 — поліція",
        "pesel_text": "🆔 <b>Як отримати PESEL</b>\n\nЗвернися в Urząd Miasta / Urząd Gminy з паспортом.\n\nНадішли геолокацію — покажу найближчі Urząd.",
        "telemed_text": "💻 Багато лікарів приймають онлайн на <a href='https://www.znanylekarz.pl/'>ZnanyLekarz</a>",
        "links_text": "🔗 <a href='https://www.znanylekarz.pl/'>ZnanyLekarz</a>\n<a href='https://www.nfz.gov.pl/'>NFZ</a>\n<a href='https://www.patient.gov.pl/'>Internetowe Konto Pacjenta</a>",
    },
    "pl": {
        "choose_lang": "Wybierz język / Оберіть мову / Choose language:",
        "welcome": "Cześć! Pomogę znaleźć lekarza i ogarnąć ubezpieczenie.\n\nCo chcesz zrobić?",
        "find_doctor": "🔍 Znajdź lekarzy w pobliżu",
        "how_to_book": "📋 Jak się umówić",
        "insurance": "🛡️ Ubezpieczenie / NFZ",
        "emergency": "🚨 Numery alarmowe",
        "pesel": "🆔 Jak dostać PESEL",
        "telemed": "💻 Telemedycyna",
        "links": "🔗 Przydatne linki",
        "change_lang": "🌐 Zmień język",
        "back": "🔙 Wstecz",
        "back_menu": "🔙 Powrót do menu",
        "choose_spec": "Wybierz specjalizację:",
        "send_location": "Wyślij lokalizację",
        "searching": "Szukam... ⏳",
        "spec_selected": "Specjalizacja wybrana. Wyślij lokalizację:",
        "instructions": "📋 Wejdź na <a href='https://www.znanylekarz.pl/'>ZnanyLekarz.pl</a>, wybierz specjalizację i miasto.",
        "insurance_text": "🛡️ Do NFZ potrzebny PESEL.\n<a href='https://www.nfz.gov.pl/'>NFZ</a>",
        "emergency_text": "🚨 112 — alarmowy\n999 — pogotowie\n998 — straż\n997 — policja",
        "pesel_text": "🆔 PESEL wyrabia się w Urzędzie. Wyślij lokalizację, pokażę najbliższe.",
        "telemed_text": "💻 Wizyty online na <a href='https://www.znanylekarz.pl/'>ZnanyLekarz</a>",
        "links_text": "🔗 <a href='https://www.znanylekarz.pl/'>ZnanyLekarz</a>\n<a href='https://www.nfz.gov.pl/'>NFZ</a>",
    },
    "en": {
        "choose_lang": "Choose language:",
        "welcome": "Hi! I'll help you find a doctor.\n\nWhat do you want?",
        "find_doctor": "🔍 Find doctors nearby",
        "how_to_book": "📋 How to book",
        "insurance": "🛡️ Insurance / NFZ",
        "emergency": "🚨 Emergency numbers",
        "pesel": "🆔 How to get PESEL",
        "telemed": "💻 Telemedicine",
        "links": "🔗 Useful links",
        "change_lang": "🌐 Change language",
        "back": "🔙 Back",
        "back_menu": "🔙 Back to menu",
        "choose_spec": "Choose specialty:",
        "send_location": "Send location",
        "searching": "Searching... ⏳",
        "spec_selected": "Specialty selected. Send location:",
        "instructions": "📋 Book on <a href='https://www.znanylekarz.pl/'>ZnanyLekarz.pl</a>",
        "insurance_text": "🛡️ PESEL needed for NFZ.",
        "emergency_text": "🚨 112 — emergency\n999 — ambulance",
        "pesel_text": "🆔 Apply at city office. Send location.",
        "telemed_text": "💻 Online visits on ZnanyLekarz.",
        "links_text": "🔗 <a href='https://www.znanylekarz.pl/'>ZnanyLekarz</a>",
    }
}

def t(ud, key):
    return TEXTS.get(ud.get("lang", "ua"), TEXTS["ua"]).get(key, key)

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return 2 * R * asin(sqrt(a))

def get_city_name(lat, lon):
    try:
        r = requests.get(f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json",
                         headers={"User-Agent": "DoctorBot"}, timeout=8)
        addr = r.json().get("address", {})
        return addr.get("city") or addr.get("town") or addr.get("village") or ""
    except:
        return ""

def find_nearby(lat, lon, lang="ua", radius=12000):
    query = f'[out:json][timeout:25];(node["amenity"~"clinic|doctors|hospital|dentist"](around:{radius},{lat},{lon});node["healthcare"](around:{radius},{lat},{lon});way["amenity"~"clinic|doctors|hospital"](around:{radius},{lat},{lon}););out center;'
    try:
        r = requests.post("https://overpass-api.de/api/interpreter", data={"data": query}, timeout=20)
        elements = r.json().get("elements", [])
        results = []
        for el in elements:
            tags = el.get("tags", {})
            if lang == "pl":
                name = tags.get("name:pl") or tags.get("name") or "Placówka medyczna"
            elif lang == "en":
                name = tags.get("name:en") or tags.get("name") or "Medical facility"
            else:
                name = tags.get("name:uk") or tags.get("name") or "Медичний заклад"
            if "center" in el:
                elat, elon = el["center"]["lat"], el["center"]["lon"]
            else:
                elat, elon = el.get("lat"), el.get("lon")
            if not elat:
                continue
            results.append({
                "name": name,
                "lat": elat,
                "lon": elon,
                "distance": round(haversine(lat, lon, elat, elon), 1)
            })
        results.sort(key=lambda x: x["distance"])
        return results[:8]
    except:
        return []

def main_menu_keyboard(ud):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t(ud, "find_doctor"), callback_data="find")],
        [InlineKeyboardButton(t(ud, "how_to_book"), callback_data="howto")],
        [InlineKeyboardButton(t(ud, "insurance"), callback_data="insurance")],
        [InlineKeyboardButton(t(ud, "emergency"), callback_data="emergency")],
        [InlineKeyboardButton(t(ud, "pesel"), callback_data="pesel")],
        [InlineKeyboardButton(t(ud, "telemed"), callback_data="telemed")],
        [InlineKeyboardButton(t(ud, "links"), callback_data="links")],
        [InlineKeyboardButton(t(ud, "change_lang"), callback_data="changelang")],
    ])

def back_keyboard(ud):
    return InlineKeyboardMarkup([[InlineKeyboardButton(t(ud, "back_menu"), callback_data="back_menu")]])

async def show_main_menu(message, context):
    await message.reply_text(t(context.user_data, "welcome"), reply_markup=main_menu_keyboard(context.user_data))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("🇺🇦 Українська", callback_data="lang_ua")],
        [InlineKeyboardButton("🇵🇱 Polski", callback_data="lang_pl")],
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
    ]
    await update.message.reply_text(TEXTS["ua"]["choose_lang"], reply_markup=InlineKeyboardMarkup(kb))

async def lang_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["lang"] = query.data.split("_")[1]
    await query.message.reply_text(t(context.user_data, "welcome"), reply_markup=main_menu_keyboard(context.user_data))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    ud = context.user_data

    if data == "find":
        lang = ud.get("lang", "ua")
        if lang == "pl":
            specs = [
                ("🧑‍⚕️ Internista", "internista"),
                ("🦴 Ortopeda", "ortopeda"),
                ("👩‍⚕️ Ginekolog", "ginekolog"),
                ("👶 Pediatra", "pediatra"),
                ("🦷 Stomatolog", "stomatolog"),
                ("👁️ Okulista", "okulista"),
                ("❤️ Kardiolog", "kardiolog"),
            ]
        elif lang == "en":
            specs = [
                ("🧑‍⚕️ GP", "internista"),
                ("🦴 Orthopedist", "ortopeda"),
                ("👩‍⚕️ Gynecologist", "ginekolog"),
                ("👶 Pediatrician", "pediatra"),
                ("🦷 Dentist", "stomatolog"),
                ("👁️ Ophthalmologist", "okulista"),
                ("❤️ Cardiologist", "kardiolog"),
            ]
        else:
            specs = [
                ("🧑‍⚕️ Терапевт", "internista"),
                ("🦴 Ортопед", "ortopeda"),
                ("👩‍⚕️ Гінеколог", "ginekolog"),
                ("👶 Педіатр", "pediatra"),
                ("🦷 Стоматолог", "stomatolog"),
                ("👁️ Окуліст", "okulista"),
                ("❤️ Кардіолог", "kardiolog"),
            ]
        kb = [[InlineKeyboardButton(name, callback_data=f"spec_{code}")] for name, code in specs]
        kb.append([InlineKeyboardButton(t(ud, "back"), callback_data="back_menu")])
        await query.message.reply_text(t(ud, "choose_spec"), reply_markup=InlineKeyboardMarkup(kb))

    elif data.startswith("spec_"):
        ud["specialty"] = data.split("_", 1)[1]
        ud["waiting_for"] = "doctor"
        btn = KeyboardButton("📍 " + t(ud, "send_location"), request_location=True)
        await query.message.reply_text(t(ud, "spec_selected"), reply_markup=ReplyKeyboardMarkup([[btn]], resize_keyboard=True, one_time_keyboard=True))

    elif data == "back_menu":
        await show_main_menu(query.message, context)

    elif data == "howto":
        await query.message.reply_text(t(ud, "instructions"), parse_mode="HTML", reply_markup=back_keyboard(ud), disable_web_page_preview=True)

    elif data == "insurance":
        await query.message.reply_text(t(ud, "insurance_text"), parse_mode="HTML", reply_markup=back_keyboard(ud), disable_web_page_preview=True)

    elif data == "emergency":
        await query.message.reply_text(t(ud, "emergency_text"), parse_mode="HTML", reply_markup=back_keyboard(ud))

    elif data == "pesel":
        ud["waiting_for"] = "pesel"
        await query.message.reply_text(t(ud, "pesel_text"), parse_mode="HTML", reply_markup=back_keyboard(ud))
        btn = KeyboardButton("📍 " + t(ud, "send_location"), request_location=True)
        await query.message.reply_text("👇", reply_markup=ReplyKeyboardMarkup([[btn]], resize_keyboard=True, one_time_keyboard=True))

    elif data == "telemed":
        await query.message.reply_text(t(ud, "telemed_text"), parse_mode="HTML", reply_markup=back_keyboard(ud), disable_web_page_preview=True)

    elif data == "links":
        await query.message.reply_text(t(ud, "links_text"), parse_mode="HTML", reply_markup=back_keyboard(ud), disable_web_page_preview=True)

    elif data == "changelang":
        await start(update, context)

async def location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loc = update.message.location
    ud = context.user_data
    waiting = ud.get("waiting_for")
    lang = ud.get("lang", "ua")

    await update.message.reply_text(t(ud, "searching"), reply_markup=ReplyKeyboardRemove())

    if waiting == "pesel":
        g = f"https://www.google.com/maps/search/Urząd+Miasta/@{loc.latitude},{loc.longitude},14z"
        a = f"https://maps.apple.com/?q=Urząd&ll={loc.latitude},{loc.longitude}"
        await update.message.reply_text(f"🗺 <a href='{g}'>Google Maps</a>\n🍎 <a href='{a}'>Apple Maps</a>",
                                        parse_mode="HTML", reply_markup=back_keyboard(ud), disable_web_page_preview=True)
        ud.pop("waiting_for", None)
        return

    results = find_nearby(loc.latitude, loc.longitude, lang)
    city = get_city_name(loc.latitude, loc.longitude)
    specialty = ud.get("specialty", "")

    if lang == "pl":
        header, not_found, on_map, km = "<b>Najbliższe placówki:</b>\n\n", "Nic nie znaleziono.\n\n", "Na mapie", "km"
    elif lang == "en":
        header, not_found, on_map, km = "<b>Nearest:</b>\n\n", "Nothing found.\n\n", "On map", "km"
    else:
        header, not_found, on_map, km = "<b>Найближчі:</b>\n\n", "Нічого не знайдено.\n\n", "На карті", "км"

    text = header if results else not_found
    for i, r in enumerate(results, 1):
        maps = f"https://www.google.com/maps/search/?api=1&query={r['lat']},{r['lon']}"
        text += f"{i}. <b>{r['name']}</b>\n📏 {r['distance']} {km}\n<a href='{maps}'>{on_map}</a>\n\n"

    if specialty and city:
        text += f"<a href='https://www.znanylekarz.pl/szukaj?q={specialty}&loc={city}'>📅 ZnanyLekarz</a>"
    elif city:
        text += f"<a href='https://www.znanylekarz.pl/szukaj?loc={city}'>📅 ZnanyLekarz</a>"
    else:
        text += "<a href='https://www.znanylekarz.pl/'>📅 ZnanyLekarz</a>"

    await update.message.reply_text(text, parse_mode="HTML", reply_markup=back_keyboard(ud), disable_web_page_preview=True)
    ud.pop("waiting_for", None)
    ud.pop("specialty", None)

async def any_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "lang" not in context.user_data:
        await start(update, context)
    else:
        await show_main_menu(update.message, context)

def main():
    logging.basicConfig(level=logging.INFO)
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(lang_callback, pattern="^lang_"))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.LOCATION, location_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, any_message))
    print("Бот запущено!")
    app.run_polling()

if __name__ == "__main__":
    main()