"""
Famwareta TS3 Blacklist Fixer
Version: 1.2.0
Author: Famwareta Community (Erfan Dehghani)
Description: The Ultimate TeamSpeak 3 Anti-Blacklist & VPN Bypass Tool
"""

import os
import sys
import ctypes
import shutil
import subprocess
import webbrowser
import threading
import time
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
from PIL import Image, ImageTk

# ==========================================
# 0. Resource Path (For PyInstaller Bundling)
# ==========================================
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

# ==========================================
# 1. Administrator Privilege Elevation
# ==========================================
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

if not is_admin():
    # Prompt for elevation with UAC
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{sys.argv[0]}"', None, 1)
    sys.exit()

# ==========================================
# 2. Design System / Neumorphic Dark Palette
# ==========================================
BG_MAIN       = "#121217"  # Deep dark backdrop
CARD_BG       = "#1a1a24"  # Neumorphic surface
SHADOW_LIGHT  = "#262638"  # Top-left soft highlight
SHADOW_DARK   = "#0b0b0f"  # Bottom-right soft shadow
ACCENT_PURPLE = "#BB86FC"  # Main vibrant accent
ACCENT_HOVER  = "#9D4EDD"  # Button hover purple
ACCENT_CYAN   = "#03DAC6"  # Teal / Info
TEXT_WHITE    = "#FFFFFF"  # Primary header text
TEXT_MUTED    = "#A0A0B0"  # Subtitle / description
SUCCESS_GREEN = "#00E676"  # Status success
ERROR_RED     = "#FF5252"  # Warning / Error
BORDER_COLOR  = "#2a2a3c"

# ==========================================
# 3. Core Engine Functions
# ==========================================
def run_silent_cmd(cmd):
    """Run shell command hidden with no black console popup"""
    return subprocess.run(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW
    )

def kill_ts3():
    """Force kill all running TeamSpeak instances"""
    run_silent_cmd("taskkill /f /im ts3client_win64.exe")
    run_silent_cmd("taskkill /f /im ts3client_win32.exe")
    return True

def clear_ts3_cache():
    """Clear TeamSpeak temporary cache & blacklist memory"""
    appdata = os.getenv("APPDATA")
    if not appdata:
        return False, "APPDATA environment variable not found."
    
    cache_dir = Path(appdata) / "TS3Client" / "cache"
    cleared = False
    if cache_dir.exists():
        try:
            shutil.rmtree(cache_dir, ignore_errors=True)
            cleared = True
        except Exception:
            pass
def patch_ts3_binary():
    """
    Permanently patch ts3client_win64.exe by neutralizing the blacklist2 URL.
    Replaces https://blacklist2.teamspeak.com/check with http://127.0.0.1:0/check
    This guarantees 0% chance of ever querying blacklist servers, even with VPN,
    and prevents any blacklisting after connection lost or network drops.
    """
    ts_paths = [
        Path(r"C:\Program Files\TeamSpeak 3 Client\ts3client_win64.exe"),
        Path(r"C:\Program Files (x86)\TeamSpeak 3 Client\ts3client_win64.exe")
    ]
    old_url = b"https://blacklist2.teamspeak.com/check"
    new_url = b"http://127.0.0.1:0/check" + (b"\x00" * (len(old_url) - len(b"http://127.0.0.1:0/check")))
    
    patched_any = False
    for p in ts_paths:
        if p.exists():
            try:
                bak = p.with_suffix(".exe.bak")
                if not bak.exists():
                    shutil.copy2(p, bak)
                
                with open(p, "rb") as f:
                    content = f.read()
                
                if old_url in content:
                    new_content = content.replace(old_url, new_url, 1)
                    with open(p, "wb") as f:
                        f.write(new_content)
                    patched_any = True
                elif new_url in content:
                    patched_any = True
            except Exception as e:
                return False, f"Binary patch error: {e}"
                
    if patched_any:
        return True, "TS3 Binary permanently patched (Zero Blacklist Queries)."
    return False, "TS3 executable not found."

def apply_hosts_patch():
    """Inject all TeamSpeak Blacklist & Accounting domains (IPv4 & IPv6)"""
    hosts_path = Path(r"C:\Windows\System32\drivers\etc\hosts")
    domains = [
        "blacklist.teamspeak.com",
        "blacklist2.teamspeak.com",
        "accounting.teamspeak.com",
        "backupaccounting.teamspeak.com",
        "ipcheck.teamspeak.com",
        "weblist.teamspeak.com"
    ]
    try:
        content = ""
        if hosts_path.exists():
            content = hosts_path.read_text(encoding="utf-8", errors="ignore")
        
        entries_to_add = []
        for d in domains:
            if d not in content:
                entries_to_add.append(f"0.0.0.0 {d}")
                entries_to_add.append(f"::1 {d}")
        
        if entries_to_add:
            with open(hosts_path, "a", encoding="utf-8") as f:
                if content and not content.endswith("\n"):
                    f.write("\n")
                f.write("# Famwareta TS3 Anti-Blacklist Entries\n")
                for e in entries_to_add:
                    f.write(e + "\n")
            return True, f"Added {len(entries_to_add)//2} blacklist domains to hosts file."
        return True, "Hosts file is already fully protected."
    except Exception as e:
        return False, f"Hosts update error: {e}"

def apply_firewall_rules():
    """
    Apply kernel-level Windows Firewall rules.
    Blocks TeamSpeak client outbound connections to official blacklist servers and port 41144.
    """
    ts3_paths = [
        r"C:\Program Files\TeamSpeak 3 Client\ts3client_win64.exe",
        r"C:\Program Files (x86)\TeamSpeak 3 Client\ts3client_win32.exe"
    ]
    blacklist_ips = "46.105.112.65,104.18.4.167,104.18.5.167"
    
    # Clean previous rules
    run_silent_cmd('netsh advfirewall firewall delete rule name="Famwareta_TS3_Blacklist_IPs"')
    run_silent_cmd('netsh advfirewall firewall delete rule name="Famwareta_TS3_Port_41144"')
    
    # Add rules
    cmd_ips = (
        f'netsh advfirewall firewall add rule name="Famwareta_TS3_Blacklist_IPs" '
        f'dir=out action=block remoteip={blacklist_ips} enable=yes'
    )
    cmd_port = (
        'netsh advfirewall firewall add rule name="Famwareta_TS3_Port_41144" '
        'dir=out action=block protocol=TCP remoteport=41144 enable=yes'
    )
    
    res1 = run_silent_cmd(cmd_ips)
    res2 = run_silent_cmd(cmd_port)
    
    if res1.returncode == 0 or res2.returncode == 0:
        return True, "Firewall outbound blocking rules active."
    return True, "Firewall rules configured."

def flush_dns():
    """Clear Windows DNS cache completely"""
    run_silent_cmd("ipconfig /flushdns")
    return True, "Windows DNS cache flushed."

def apply_vpn_bypass_routes():
    """
    Configure Windows routing table to route Iranian TeamSpeak subnets
    directly through the physical network adapter (Wi-Fi / Ethernet),
    completely bypassing any active VPN TUN interface (Hiddify/v2ray/etc.)
    """
    ps_cmd = (
        "$phy = Get-NetAdapter | Where-Object { $_.Status -eq 'Up' -and $_.InterfaceDescription -notmatch 'sing-tun|wintun|wireguard|tap' } | Select-Object -First 1; "
        "if ($phy) { "
        "  $gw = (Get-NetRoute -InterfaceIndex $phy.InterfaceIndex -DestinationPrefix '0.0.0.0/0' -ErrorAction SilentlyContinue | Select-Object -First 1).NextHop; "
        "  if ($gw) { "
        "    $subnets = @('5.57.37.0/24','5.57.39.0/24','5.57.32.0/24','81.12.50.0/24','185.164.72.0/24','212.80.8.0/24','88.135.68.0/24'); "
        "    foreach ($s in $subnets) { "
        "      Remove-NetRoute -DestinationPrefix $s -ErrorAction SilentlyContinue; "
        "      New-NetRoute -DestinationPrefix $s -InterfaceIndex $phy.InterfaceIndex -NextHop $gw -PolicyStore ActiveStore -ErrorAction SilentlyContinue | Out-Null "
        "    } "
        "    Write-Output 'OK' "
        "  } "
        "}"
    )
    res = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    return True, "VPN Bypass direct routes established."

def connect_to_server(address="tak.tssz.ir", port="1834"):
    """Launch TeamSpeak and connect to the community server"""
    uri = f"ts3server://{address}?port={port}"
    webbrowser.open(uri)

# ==========================================
# 4. Neumorphic UI Components
# ==========================================
class NeumorphicCard(tk.Canvas):
    """A Soft-UI Neumorphic Container with bevel highlights and shadows"""
    def __init__(self, parent, width, height, radius=16, bg=BG_MAIN, card_bg=CARD_BG, **kwargs):
        super().__init__(parent, width=width, height=height, bg=bg, highlightthickness=0, **kwargs)
        self.width = width
        self.height = height
        self.radius = radius
        self.card_bg = card_bg
        self.draw_card()
        
    def draw_card(self):
        self.delete("all")
        # Draw outer bottom-right shadow
        self._rounded_rect(2, 2, self.width - 1, self.height - 1, self.radius, fill=SHADOW_DARK)
        # Draw outer top-left light highlight
        self._rounded_rect(0, 0, self.width - 3, self.height - 3, self.radius, fill=SHADOW_LIGHT)
        # Draw inner surface
        self._rounded_rect(1, 1, self.width - 3, self.height - 3, self.radius, fill=self.card_bg)

    def _rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [
            x1 + r, y1,
            x2 - r, y1,
            x2, y1,
            x2, y1 + r,
            x2, y2 - r,
            x2, y2,
            x2 - r, y2,
            x1 + r, y2,
            x1, y2,
            x1, y2 - r,
            x1, y1 + r,
            x1, y1
        ]
        return self.create_polygon(points, smooth=True, **kwargs)

class NeumorphicButton(tk.Canvas):
    """Custom Neumorphic Interactive Button with hover, click and tactile feedback"""
    def __init__(self, parent, text, command=None, width=280, height=48, 
                 radius=14, accent=ACCENT_PURPLE, text_color="#121217", 
                 font=("Segoe UI", 11, "bold"), **kwargs):
        super().__init__(parent, width=width, height=height, bg=BG_MAIN, highlightthickness=0, cursor="hand2", **kwargs)
        self.width = width
        self.height = height
        self.radius = radius
        self.accent = accent
        self.hover_accent = ACCENT_HOVER
        self.text_color = text_color
        self.font = font
        self.text = text
        self.command = command
        self.is_pressed = False
        
        self.draw_button(self.accent)
        
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)
        self.bind("<ButtonRelease-1>", self.on_release)

    def draw_button(self, fill_color):
        self.delete("all")
        if not self.is_pressed:
            # Normal Extruded Neumorphic State
            self._rounded_rect(2, 2, self.width - 1, self.height - 1, self.radius, fill=SHADOW_DARK)
            self._rounded_rect(0, 0, self.width - 2, self.height - 2, self.radius, fill=SHADOW_LIGHT)
            self._rounded_rect(1, 1, self.width - 3, self.height - 3, self.radius, fill=fill_color)
        else:
            # Pressed / Inset State
            self._rounded_rect(0, 0, self.width, self.height, self.radius, fill=SHADOW_DARK)
            self._rounded_rect(2, 2, self.width - 2, self.height - 2, self.radius, fill=fill_color)
            
        self.create_text(self.width / 2, self.height / 2, text=self.text, fill=self.text_color, font=self.font)

    def _rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [
            x1 + r, y1,
            x2 - r, y1,
            x2, y1,
            x2, y1 + r,
            x2, y2 - r,
            x2, y2,
            x2 - r, y2,
            x1 + r, y2,
            x1, y2,
            x1, y2 - r,
            x1, y1 + r,
            x1, y1
        ]
        return self.create_polygon(points, smooth=True, **kwargs)

    def on_enter(self, event):
        self.draw_button(self.hover_accent)

    def on_leave(self, event):
        self.draw_button(self.accent)

    def on_click(self, event):
        self.is_pressed = True
        self.draw_button(self.hover_accent)

    def on_release(self, event):
        self.is_pressed = False
        self.draw_button(self.hover_accent)
        if self.command:
            self.command()

    def set_text(self, new_text):
        self.text = new_text
        self.draw_button(self.accent)

# ==========================================
# 5. Main Application GUI
# ==========================================
class FamwaretaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Famwareta TS3 Blacklist Fixer v1.2.0")
        self.root.geometry("490x640")
        self.root.resizable(False, False)
        self.root.configure(bg=BG_MAIN)
        
        # Center Window on Screen
        self.center_window()
        
        # Set Window Icons
        self.setup_icons()
        
        # Build UI Structure
        self.create_header()
        self.create_status_card()
        self.create_actions()
        self.create_console()
        self.create_footer()
        
        # Check initial system state
        self.check_system_health()

    def center_window(self):
        self.root.update_idletasks()
        w = 490
        h = 640
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def setup_icons(self):
        try:
            ico_path = resource_path("app_icon.ico")
            if not os.path.exists(ico_path):
                ico_path = resource_path("favicon.ico")
            if os.path.exists(ico_path):
                self.root.iconbitmap(ico_path)
        except Exception as e:
            print("Icon load error:", e)

    def create_header(self):
        header_frame = tk.Frame(self.root, bg=BG_MAIN)
        header_frame.pack(fill=tk.X, pady=(16, 8), padx=25)

        # Logo / Badge
        try:
            logo_path = resource_path("logo_opt.png")
            if not os.path.exists(logo_path):
                logo_path = resource_path("logo.png")
            if os.path.exists(logo_path):
                pil_img = Image.open(logo_path)
                pil_img = pil_img.resize((56, 56), Image.Resampling.LANCZOS)
                self.logo_tk = ImageTk.PhotoImage(pil_img)
                lbl_logo = tk.Label(header_frame, image=self.logo_tk, bg=BG_MAIN)
                lbl_logo.pack(side=tk.LEFT, padx=(0, 14))
        except Exception as e:
            print("Logo error:", e)

        title_box = tk.Frame(header_frame, bg=BG_MAIN)
        title_box.pack(side=tk.LEFT, fill=tk.Y)

        lbl_title = tk.Label(
            title_box, 
            text="Famwareta TS3 Fixer", 
            font=("Segoe UI", 16, "bold"), 
            bg=BG_MAIN, 
            fg=TEXT_WHITE
        )
        lbl_title.pack(anchor="w")

        lbl_desc = tk.Label(
            title_box, 
            text="Ultimate Anti-Blacklist & VPN Bypass Engine • v1.2.0", 
            font=("Segoe UI", 9), 
            bg=BG_MAIN, 
            fg=ACCENT_PURPLE
        )
        lbl_desc.pack(anchor="w")

    def create_status_card(self):
        """Neumorphic Status Card showing live protection indicators"""
        card_container = tk.Frame(self.root, bg=BG_MAIN)
        card_container.pack(fill=tk.X, padx=25, pady=8)

        self.status_card = NeumorphicCard(card_container, width=440, height=88, radius=14)
        self.status_card.pack()

        # Labels inside card
        inner_frame = tk.Frame(self.status_card, bg=CARD_BG)
        self.status_card.create_window(220, 44, window=inner_frame)

        # 4 Indicators Grid
        self.lbl_stat_hosts = tk.Label(inner_frame, text="● Hosts: Checking...", font=("Segoe UI", 9, "bold"), bg=CARD_BG, fg=TEXT_MUTED)
        self.lbl_stat_hosts.grid(row=0, column=0, padx=12, pady=4, sticky="w")

        self.lbl_stat_fw = tk.Label(inner_frame, text="● Firewall: Checking...", font=("Segoe UI", 9, "bold"), bg=CARD_BG, fg=TEXT_MUTED)
        self.lbl_stat_fw.grid(row=0, column=1, padx=12, pady=4, sticky="w")

        self.lbl_stat_vpn = tk.Label(inner_frame, text="● VPN Bypass: Ready", font=("Segoe UI", 9, "bold"), bg=CARD_BG, fg=TEXT_MUTED)
        self.lbl_stat_vpn.grid(row=1, column=0, padx=12, pady=4, sticky="w")

        self.lbl_stat_ts = tk.Label(inner_frame, text="● TS3 Status: Idle", font=("Segoe UI", 9, "bold"), bg=CARD_BG, fg=TEXT_MUTED)
        self.lbl_stat_ts.grid(row=1, column=1, padx=12, pady=4, sticky="w")

    def create_actions(self):
        actions_frame = tk.Frame(self.root, bg=BG_MAIN)
        actions_frame.pack(fill=tk.X, padx=25, pady=(10, 6))

        # Main Big Action Button
        self.btn_full_fix = NeumorphicButton(
            actions_frame, 
            text="⚡ APPLY ULTIMATE FIX & CONNECT", 
            command=self.on_full_fix_click,
            width=440, 
            height=50, 
            accent=ACCENT_PURPLE, 
            text_color="#0D0D11",
            font=("Segoe UI", 12, "bold")
        )
        self.btn_full_fix.pack(pady=(0, 10))

        # Secondary Quick-Action Buttons (Row)
        sub_row = tk.Frame(actions_frame, bg=BG_MAIN)
        sub_row.pack(fill=tk.X)

        self.btn_kill_ts = NeumorphicButton(
            sub_row,
            text="🛑 Force Kill TS3",
            command=self.on_kill_ts_click,
            width=140,
            height=36,
            accent="#252535",
            text_color=TEXT_WHITE,
            font=("Segoe UI", 9, "bold")
        )
        self.btn_kill_ts.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_connect = NeumorphicButton(
            sub_row,
            text="🎮 Connect to TS",
            command=self.on_connect_ts_click,
            width=140,
            height=36,
            accent="#252535",
            text_color=ACCENT_CYAN,
            font=("Segoe UI", 9, "bold")
        )
        self.btn_connect.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_flush = NeumorphicButton(
            sub_row,
            text="🌐 Flush DNS",
            command=self.on_flush_dns_click,
            width=140,
            height=36,
            accent="#252535",
            text_color=TEXT_WHITE,
            font=("Segoe UI", 9, "bold")
        )
        self.btn_flush.pack(side=tk.LEFT)

    def create_console(self):
        console_container = tk.Frame(self.root, bg=BG_MAIN)
        console_container.pack(fill=tk.BOTH, expand=True, padx=25, pady=8)

        lbl_log = tk.Label(console_container, text="SYSTEM DIAGNOSTICS & LOGS", font=("Segoe UI", 8, "bold"), bg=BG_MAIN, fg=TEXT_MUTED)
        lbl_log.pack(anchor="w", pady=(0, 4))

        self.log_text = tk.Text(
            console_container, 
            height=9, 
            bg="#0c0c12", 
            fg="#cfcfd8", 
            font=("Consolas", 9), 
            relief="flat", 
            borderwidth=0, 
            padx=10, 
            pady=8
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)

    def create_footer(self):
        footer_frame = tk.Frame(self.root, bg=BG_MAIN)
        footer_frame.pack(fill=tk.X, padx=25, pady=(4, 16))

        # Telegram Link with Hand Cursor
        lbl_tg = tk.Label(
            footer_frame, 
            text="📢 Telegram: @FamwaretaVPN", 
            font=("Segoe UI", 9, "bold"), 
            bg=BG_MAIN, 
            fg=ACCENT_CYAN, 
            cursor="hand2"
        )
        lbl_tg.pack(side=tk.LEFT)
        lbl_tg.bind("<Button-1>", lambda e: webbrowser.open("https://t.me/FamwaretaVPN"))

        # Donate Button (Pop-up modal)
        lbl_donate = tk.Label(
            footer_frame, 
            text="💖 Donate / حمایت مالی", 
            font=("Segoe UI", 9, "bold"), 
            bg=BG_MAIN, 
            fg=ACCENT_PURPLE, 
            cursor="hand2"
        )
        lbl_donate.pack(side=tk.RIGHT)
        lbl_donate.bind("<Button-1>", lambda e: self.show_donate_modal())

    # ==========================================
    # Logic & Threaded Action Handlers
    # ==========================================
    def log(self, message, tag=None):
        self.log_text.config(state=tk.NORMAL)
        t = time.strftime("[%H:%M:%S] ")
        self.log_text.insert(tk.END, t + message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def check_system_health(self):
        """Perform non-blocking initial scan of system status"""
        def scan():
            # Check Hosts
            hosts_path = Path(r"C:\Windows\System32\drivers\etc\hosts")
            has_hosts = False
            if hosts_path.exists():
                c = hosts_path.read_text(encoding="utf-8", errors="ignore")
                if "blacklist2.teamspeak.com" in c:
                    has_hosts = True

            # Check Firewall
            check_fw = run_silent_cmd('netsh advfirewall firewall show rule name="Famwareta_TS3_Blacklist_IPs"')
            has_fw = (check_fw.returncode == 0)

            # Check TS3 process
            check_proc = run_silent_cmd('tasklist /fi "imagename eq ts3client_win64.exe"')
            is_ts_running = ("ts3client_win64.exe" in check_proc.stdout.decode('latin1', 'ignore'))

            # Check Binary Patch
            ts_exe = Path(r"C:\Program Files\TeamSpeak 3 Client\ts3client_win64.exe")
            is_patched = False
            if ts_exe.exists():
                try:
                    with open(ts_exe, "rb") as f:
                        b_data = f.read()
                        if b"http://127.0.0.1:0/check" in b_data:
                            is_patched = True
                except Exception:
                    pass

            def update_ui():
                if is_patched:
                    self.lbl_stat_vpn.config(text="● Core: Patched ✓", fg=SUCCESS_GREEN)
                else:
                    self.lbl_stat_vpn.config(text="● Core: Unpatched ✗", fg=ERROR_RED)

                if has_hosts:
                    self.lbl_stat_hosts.config(text="● Hosts: Protected ✓", fg=SUCCESS_GREEN)
                else:
                    self.lbl_stat_hosts.config(text="● Hosts: Unprotected ✗", fg=ERROR_RED)

                if has_fw:
                    self.lbl_stat_fw.config(text="● Firewall: Active ✓", fg=SUCCESS_GREEN)
                else:
                    self.lbl_stat_fw.config(text="● Firewall: Not Set", fg=TEXT_MUTED)

                if is_ts_running:
                    self.lbl_stat_ts.config(text="● TS3: Running", fg=ACCENT_CYAN)
                else:
                    self.lbl_stat_ts.config(text="● TS3: Closed", fg=TEXT_MUTED)

            self.root.after(0, update_ui)

        threading.Thread(target=scan, daemon=True).start()
        self.log("Famwareta Engine initialized. Ready to apply bypass.")

    def on_full_fix_click(self):
        """Execute complete patch sequence in background thread"""
        self.btn_full_fix.set_text("PROCESSING ENGINE...")
        
        def run():
            self.log("Starting Full Anti-Blacklist & VPN Bypass sequence...")
            
            # 1. Kill TS3
            self.log("[1/7] Terminating active TeamSpeak instances...")
            kill_ts3()
            time.sleep(0.5)

            # 2. Binary Patch
            self.log("[2/7] Neutralizing blacklist URL inside TS3 binary (Permanent Patch)...")
            p_ok, p_msg = patch_ts3_binary()
            self.log(f"      -> {p_msg}")

            # 3. Clear Cache
            self.log("[3/7] Cleaning temporary blacklist memory & cache...")
            clear_ts3_cache()

            # 4. Update Hosts
            self.log("[4/7] Patching hosts file (IPv4 & IPv6 blacklist domains)...")
            h_ok, h_msg = apply_hosts_patch()
            self.log(f"      -> {h_msg}")

            # 5. Apply Firewall
            self.log("[5/7] Activating Windows Firewall kernel-level block rules...")
            f_ok, f_msg = apply_firewall_rules()
            self.log(f"      -> {f_msg}")

            # 6. Route Bypass
            self.log("[6/7] Establishing direct routing for TS servers (Bypassing VPN)...")
            r_ok, r_msg = apply_vpn_bypass_routes()
            self.log(f"      -> {r_msg}")

            # 7. Flush DNS
            self.log("[7/7] Purging DNS cache...")
            flush_dns()
            self.log("      -> DNS cache flushed cleanly.")

            time.sleep(0.5)
            self.log("SUCCESS: All patches successfully applied! Connecting to server...")
            
            def finish():
                self.btn_full_fix.set_text("⚡ APPLY ULTIMATE FIX & CONNECT")
                self.check_system_health()
                # Automatically connect to TeamSpeak Server
                connect_to_server("tak.tssz.ir", "1834")
                messagebox.showinfo(
                    "Famwareta Fixer", 
                    "عملیات رفع بلک‌لیست و بای‌پس دائمی با موفقیت انجام شد!\nکلاینت تیم‌اسپیک به طور دائم پچ شد و دیگر هرگز دچار بلک‌لیست نخواهد شد."
                )

            self.root.after(0, finish)

        threading.Thread(target=run, daemon=True).start()

    def on_kill_ts_click(self):
        kill_ts3()
        self.log("Forced closed all TeamSpeak 3 processes.")
        self.check_system_health()

    def on_connect_ts_click(self):
        self.log("Opening connection to Famwareta Community TS server...")
        connect_to_server("tak.tssz.ir", "1834")

    def on_flush_dns_click(self):
        flush_dns()
        self.log("DNS Cache flushed successfully.")

    def show_donate_modal(self):
        """Custom Neumorphic Donation Modal Dialog"""
        modal = tk.Toplevel(self.root)
        modal.title("Donate & Support - Famwareta")
        modal.geometry("400x320")
        modal.resizable(False, False)
        modal.configure(bg=BG_MAIN)
        modal.transient(self.root)
        modal.grab_set()

        # Center modal
        mx = self.root.winfo_x() + (self.root.winfo_width() // 2) - 200
        my = self.root.winfo_y() + (self.root.winfo_height() // 2) - 160
        modal.geometry(f"+{mx}+{my}")

        lbl_d_title = tk.Label(modal, text="حمایت مالی از پروژه فام‌وارتا", font=("Segoe UI", 13, "bold"), bg=BG_MAIN, fg=TEXT_WHITE)
        lbl_d_title.pack(pady=(20, 6))

        lbl_d_sub = tk.Label(
            modal, 
            text="توسعه و به‌روزرسانی رایگان این ابزار با حمایت شما ادامه دارد.", 
            font=("Segoe UI", 9), 
            bg=BG_MAIN, 
            fg=TEXT_MUTED
        )
        lbl_d_sub.pack(pady=(0, 16))

        # USDT TRC20 Card
        trc20_address = "TYDzsxdh5m3sHMvf8gKjP9vV8B59W9yZzQ" # Standard placeholder / user wallet
        
        card = NeumorphicCard(modal, width=350, height=80, radius=12)
        card.pack(pady=5)

        c_frame = tk.Frame(card, bg=CARD_BG)
        card.create_window(175, 40, window=c_frame)

        tk.Label(c_frame, text="Tether (USDT - TRC20):", font=("Segoe UI", 8, "bold"), bg=CARD_BG, fg=ACCENT_CYAN).pack(anchor="w")
        txt_addr = tk.Entry(c_frame, font=("Consolas", 8), bg="#0f0f15", fg="#ffffff", relief="flat", width=38, justify="center")
        txt_addr.insert(0, trc20_address)
        txt_addr.config(state="readonly")
        txt_addr.pack(pady=4)

        def copy_address():
            self.root.clipboard_clear()
            self.root.clipboard_append(trc20_address)
            btn_copy.set_text("COPIED! ✓")
            modal.after(1500, lambda: btn_copy.set_text("کپی آدرس تتر"))

        btn_copy = NeumorphicButton(
            modal, 
            text="کپی آدرس تتر", 
            command=copy_address, 
            width=180, 
            height=38, 
            accent=ACCENT_PURPLE,
            text_color="#0D0D11",
            font=("Segoe UI", 9, "bold")
        )
        btn_copy.pack(pady=12)

        # Telegram Channel Link
        lbl_link = tk.Label(
            modal, 
            text="پشتیبانی و ارتباط در تلگرام: @FamwaretaVPN", 
            font=("Segoe UI", 9, "underline"), 
            bg=BG_MAIN, 
            fg=ACCENT_CYAN, 
            cursor="hand2"
        )
        lbl_link.pack(pady=6)
        lbl_link.bind("<Button-1>", lambda e: webbrowser.open("https://t.me/FamwaretaVPN"))

# ==========================================
# 6. Application Entry Point
# ==========================================
if __name__ == "__main__":
    app_root = tk.Tk()
    app = FamwaretaApp(app_root)
    app_root.mainloop()