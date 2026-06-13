"""English interface strings for GGSelCardinal."""
from __future__ import annotations

STRINGS = {
    # --- Core ---
    "init_start": "Initializing GGSelCardinal core…",
    "init_done": "Initialization complete. Plugins loaded: {0}.",
    "plugin_loaded": "Plugin loaded: {0} v{1}",
    "run_start": "Main event loop started.",
    "shutdown": "Core stopped. See you!",
    # --- Notifications ---
    "notify_autoresponse": "🤖 Auto-reply triggered.\nBuyer: {0}\nMessage: {1}",
    "notify_new_order": "🛒 New order #{0}\nItem: {1}\nTotal: {2:.2f} {3}\nBuyer: {4}",
    "notify_dispute": "⚠️ Dispute opened on order #{0} (buyer: {1}).",
    "notify_refund": "↩️ Refund issued for order #{0}.",
    "notify_delivered": "✅ Order #{0} delivered: {1}",
    # --- Telegram panel ---
    "tg_access_denied": "⛔ Access denied. You are not in the admin list.",
    "tg_welcome": "👋 Hi, {0}!\nThis is the GGSelCardinal control panel.",
    "tg_menu_title": "🏠 GGSelCardinal main menu",
    "tg_status": "📊 Status\n\nAccount: {0}\nPlugins loaded: {1}\nAuto-reply: {2}\nAuto-delivery: {3}",
    "tg_plugins_title": "🧩 Plugins (tap to toggle):",
    "tg_plugins_empty": "No plugins found",
    "tg_closed": "Menu closed.",
    "state_on": "on ✅",
    "state_off": "off ❌",
    "btn_status": "📊 Status",
    "btn_plugins": "🧩 Plugins",
    "btn_autoresponse": "🤖 Auto-reply",
    "btn_autodelivery": "📦 Auto-delivery",
    "btn_back": "⬅️ Back",
    "btn_close": "✖️ Close",
}
