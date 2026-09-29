<div align="center">

# ⚡ Famwareta TS3 Blacklist Fixer (v1.2.0)
### The Ultimate TeamSpeak 3 Anti-Blacklist & VPN Bypass Engine
**حل قطعی، تضمینی و همیشگی ارور «This server is blacklisted» حتی با روشن بودن فیلترشکن (VPN)**

[![Version](https://img.shields.io/badge/version-1.2.0-blue.svg?style=for-the-badge&color=BB86FC)](https://github.com/iMysticisM/Famwareta-TS3-Blacklist-Fixer/releases)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%20%7C%2011-black.svg?style=for-the-badge&logo=windows)](https://github.com/iMysticisM/Famwareta-TS3-Blacklist-Fixer)
[![License](https://img.shields.io/badge/license-MIT-green.svg?style=for-the-badge)](LICENSE)
[![Telegram](https://img.shields.io/badge/Telegram-FamwaretaVPN-03DAC6.svg?style=for-the-badge&logo=telegram)](https://t.me/FamwaretaVPN)

---

[فارسی](#-راهنمای-فارسی) • [English](#-english-guide) • [ویژگی‌ها](#-ویژگی‌های-کلیدی--features) • [دانلود مستقیم](#-دانلود-و-نصب--download) • [حمایت مالی](#-حمایت-مالی--donate)

</div>

---

## 🌟 معرفی پروژه | Overview

آیا هنگام اتصال به سرورهای تیم‌اسپیک با ارور زیر مواجه می‌شوید؟
> **`<This server is blacklisted. Refusing to connect>`**  
> یا وقتی فیلترشکن (VPN مانند Hiddify / v2ray) روشن است، تیم‌اسپیک قطع شده یا بلک‌لیست می‌شوید؟

نرم‌افزار **Famwareta TS3 Blacklist Fixer (نسخه 1.2.0)** تنها ابزار فوق‌پیشرفته و هوشمند در ایران است که بدون نیاز به خاموش کردن فیلترشکن، هستهٔ اتصال تیم‌اسپیک را از فیلترشکن ایزوله کرده و دسترسی به تمامی سرورهای بلک‌لیست‌شده را به صورت ۱۰۰٪ تضمینی برای همیشه آزاد می‌کند!

---

## 🚀 ویژگی‌های کلیدی | Features

- ⚡ **حل ۱۰۰٪ تضمینی و همیشگی بلک‌لیست:** مسدودسازی سرورهای استعلام بلک‌لیست آلمان در سطح هستهٔ فایروال ویندوز (Windows Kernel Firewall).
- 🛡️ **خنثی‌سازی تأثیر VPN روی تیم‌اسپیک (VPN Bypass):** فیلترشکن شما روشن می‌ماند، اما ترافیک صوتی تیم‌اسپیک مستقیماً از اینترنت خانگی بدون افت پینگ عبور می‌کند!
- 🎨 **رابط کاربری مدرن نئومورفیسم (Neumorphism Soft UI):** طراحی اختصاصی، تاریک و چشم‌نواز بر پایه پالت رنگی Famwareta Community.
- 📦 **فوق‌العاده کم‌حجم و تک‌فایل (Single File):** بدون نیاز به نصب هرگونه پیشنیاز یا فایل‌های جانبی (فقط ۱۶ مگابایت).
- 🔄 **عملیات خودکار با ۱ کلیک:** بستن پروسه‌های معلق، پاکسازی کامل کش‌های آلوده و اتصال مستقیم به سرور تیم‌اسپیک.
- 🌐 **پشتیبانی از تمامی نسخه‌ها:** قابل استفاده روی نسخه‌های 3.1.10 تا جدیدترین نسخه یعنی **3.6.2** بدون هیچ محدودیت.

---

## 📥 دانلود و نصب | Download

برای دانلود آخرین نسخه آماده اجرا، از بخش **Releases** گیت‌هاب فایل را دریافت کنید:

👉 **[دانلود FamwaretaTS3Fixer.exe (v1.2.0)](https://github.com/iMysticisM/Famwareta-TS3-Blacklist-Fixer/releases/latest)**

### نحوه استفاده:
1. نرم‌افزار را اجرا کرده و دسترسی Administrator (UAC) را تأیید کنید.
2. روی دکمه بزرگ بنفش‌رنگ **`APPLY ULTIMATE FIX & CONNECT`** کلیک کنید.
3. در کمتر از ۳ ثانیه تمام اصلاحات اعمال شده و تیم‌اسپیک باز و متصل می‌شود!

---

## 🛠️ نحوه کارکرد فنی | How It Works

1. **فایروال ویندوز (Firewall Outbound Drop):** حتی با روشن بودن فیلترشکن‌های مدرن (TUN Mode)، فایروال ویندوز بسته‌های ارسالی تیم‌اسپیک به سمت آی‌پی‌های `46.105.112.65` و کلودفلر (`104.18.4.167`) و پورت ۴۱۱۴۴ را مسدود می‌کند؛ تیم‌اسپیک در صورت قطعی این سرورها فرآیند بلک‌لیست را رد کرده و متصل می‌شود.
2. **روتینگ مستقیم (Direct Network Routing):** رنج آی‌پی سرورهای گیمینگ ایرانی (`5.57.37.0/24`, `5.57.39.0/24`, `81.12.50.0/24` و...) مستقیماً به گیت‌وی کارت شبکه اصلی هدایت می‌شوند تا پینگ شما کمترین حالت ممکن بماند.
3. **پچ دامنه‌های Hosts:** تمامی دامنه‌های `blacklist2.teamspeak.com`، `accounting` و ساب‌دامنه‌ها در هر دو حالت IPv4 و IPv6 خنثی می‌شوند.

---

## 💖 حمایت مالی | Donate & Support

توسعه و به‌روزرسانی رایگان این ابزار با حمایت شما ادامه دارد:

- **Tether (USDT - TRC20):**  
  `TYDzsxdh5m3sHMvf8gKjP9vV8B59W9yZzQ`
- **کانال تلگرام ما:**  
  [![Telegram](https://img.shields.io/badge/Join-FamwaretaVPN-03DAC6.svg?style=flat-square&logo=telegram)](https://t.me/FamwaretaVPN)

---

<div align="center">

⭐ **اگر این پروژه مشکل شما را حل کرد، لطفاً به آن در گیت‌هاب ستاره (Star) بدهید!**  
Developed with ❤️ by **Famwareta Community**

</div>
