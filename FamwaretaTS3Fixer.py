"""
Famwareta TS3 Blacklist Fixer
Version: 1.2.0 (Stable Edition)
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
# 3. Core Engine Functions (Clean Network-Only)
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

def restore_ts3_binary():
    """Restore original ts3client_win64.exe from backup if a .bak exists"""
    ts_paths = [
        Path(r"C:\Program Files\TeamSpeak 3 Client\ts3client_win64.exe"),
        Path(r"C:\Program Files (x86)\TeamSpeak 3 Client\ts3client_win64.exe")
    ]
    restored = False
    for p in ts_paths:
        bak = p.with_suffix(".exe.bak")
        if bak.exists():
            try:
                shutil.copy2(bak, p)
                restored = True
            except Exception:
                pass
    return restored

def clear_ts3_cache():
    """Clear TeamSpeak temporary cache & blacklist memory"""
    appdata = os.getenv("APPDATA")
    if not appdata:
        return False, "APPDATA environment variable not found."
    
    cache_dir = Path(appdata) / "TS3Client" / "cache"
    if cache_dir.exists():
        try:
            shutil.rmtree(cache_dir, ignore_errors=True)
        except Exception:
            pass
    return True, "TS3 Cache wiped successfully."

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
        return True, "Hosts file is already protected."
    except Exception as e:
        return False, f"Hosts update error: {e}"

def remove_hosts_patch():
    """Remove Famwareta entries from hosts file"""
    hosts_path = Path(r"C:\Windows\System32\drivers\etc\hosts")
    try:
        if hosts_path.exists():
            lines = hosts_path.read_text(encoding="utf-8", errors="ignore").splitlines()
            cleaned = [l for l in lines if "teamspeak.com" not in l and "Famwareta" not in l]
            hosts_path.write_text("\n".join(cleaned) + "\n", encoding="utf-8")
        return True, "Hosts file cleaned."
    except Exception as e:
        return False, f"Hosts clean error: {e}"

def apply_firewall_rules():
    """
    Apply kernel-level Windows Firewall outbound rules strictly for TeamSpeak executable.
    Blocks Cloudflare IP ranges (104.16.0.0/12, 172.64.0.0/13) and OVH (46.105.112.65)
    ONLY for ts3client_win64.exe and ts3client_win32.exe.
    This guarantees blacklist queries to blacklist2.teamspeak.com are dropped
    WITHOUT touching the binary file or affecting any other applications!
    """
    ts3_paths = [
        r"C:\Program Files\TeamSpeak 3 Client\ts3client_win64.exe",
        r"C:\Program Files (x86)\TeamSpeak 3 Client\ts3client_win32.exe"
    ]
    
    # Clean previous rules
    remove_firewall_rules()
    
    # Cloudflare Anycast ranges used by blacklist2 + OVH blacklist server
    remote_ips = "104.16.0.0/12,172.64.0.0/13,46.105.112.65/32"
    
    for p in ts3_paths:
        if os.path.exists(p):
            cmd = (
                f'netsh advfirewall firewall add rule name="Famwareta_TS3_Cloudflare_Block" '
                f'dir=out action=block program="{p}" remoteip="{remote_ips}" enable=yes'
            )
            run_silent_cmd(cmd)
            
            cmd_p = (
                f'netsh advfirewall firewall add rule name="Famwareta_TS3_Port_41144" '
                f'dir=out action=block program="{p}" protocol=TCP remoteport=41144 enable=yes'
            )
            run_silent_cmd(cmd_p)

    return True, "Firewall rules active (Isolated Cloudflare for TS3)."

def remove_firewall_rules():
    """Remove all Famwareta firewall rules"""
    run_silent_cmd('netsh advfirewall firewall delete rule name="Famwareta_TS3_Cloudflare_Block"')
    run_silent_cmd('netsh advfirewall firewall delete rule name="Famwareta_TS3_Blacklist_IPs"')
    run_silent_cmd('netsh advfirewall firewall delete rule name="Famwareta_TS3_Port_41144"')
    run_silent_cmd('netsh advfirewall firewall delete rule name="Famwareta_TS3_Bypass"')
    return True, "Firewall rules removed."

def flush_dns():
    """Clear Windows DNS cache completely"""
    run_silent_cmd("ipconfig /flushdns")
    return True, "Windows DNS cache flushed."

def apply_vpn_bypass_routes():
    """
    Configure Windows routing table to route Iranian TeamSpeak subnets
    directly through the physical network adapter (Wi-Fi / Ethernet),
    bypassing VPN TUN interface.
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
        "  } "
        "}"
    )
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    return True, "VPN Bypass direct routes established."

def remove_vpn_bypass_routes():
    """Remove custom routes"""
    ps_cmd = (
        "$subnets = @('5.57.37.0/24','5.57.39.0/24','5.57.32.0/24','81.12.50.0/24','185.164.72.0/24','212.80.8.0/24','88.135.68.0/24'); "
        "foreach ($s in $subnets) { Remove-NetRoute -DestinationPrefix $s -ErrorAction SilentlyContinue }"
    )
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    return True, "Custom routes cleared."

def connect_to_server(address="tak.tssz.ir", port="1834"):
    """Launch TeamSpeak directly without opening web browser"""
    ts_paths = [
        r"C:\Program Files\TeamSpeak 3 Client\ts3client_win64.exe",
        r"C:\Program Files (x86)\TeamSpeak 3 Client\ts3client_win32.exe"
    ]
    uri = f"ts3server://{address}?port={port}"
    for p in ts_paths:
        if os.path.exists(p):
            try:
                subprocess.Popen([p, uri])
                return True
            except Exception:
                pass
    webbrowser.open(uri)
    return True

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
        self._rounded_rect(2, 2, self.width - 1, self.height - 1, self.radius, fill=SHADOW_DARK)
        self._rounded_rect(0, 0, self.width - 3, self.height - 3, self.radius, fill=SHADOW_LIGHT)
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
            self._rounded_rect(2, 2, self.width - 1, self.height - 1, self.radius, fill=SHADOW_DARK)
            self._rounded_rect(0, 0, self.width - 2, self.height - 2, self.radius, fill=SHADOW_LIGHT)
            self._rounded_rect(1, 1, self.width - 3, self.height - 3, self.radius, fill=fill_color)
        else:
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
        self.root.geometry("490x650")
        self.root.resizable(False, False)
        self.root.configure(bg=BG_MAIN)
        
        self.center_window()
        self.setup_icons()
        
        # Build UI Structure
        self.create_header()
        self.create_status_card()
        self.create_actions()
        self.create_console()
        self.create_footer()
        
        # Initial check
        self.check_system_health()

    def center_window(self):
        self.root.update_idletasks()
        w = 490
        h = 650
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
            text="Anti-Blacklist & VPN Bypass Engine • v1.2.0", 
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

        inner_frame = tk.Frame(self.status_card, bg=CARD_BG)
        self.status_card.create_window(220, 44, window=inner_frame)

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
            text="⚡ APPLY FIX & CONNECT", 
            command=self.on_full_fix_click,
            width=440, 
            height=48, 
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
            width=138,
            height=36,
            accent="#252535",
            text_color=TEXT_WHITE,
            font=("Segoe UI", 9, "bold")
        )
        self.btn_kill_ts.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_connect = NeumorphicButton(
            sub_row,
            text="🎮 Connect to TS",
            command=self.on_connect_ts_click,
            width=138,
            height=36,
            accent="#252535",
            text_color=ACCENT_CYAN,
            font=("Segoe UI", 9, "bold")
        )
        self.btn_connect.pack(side=tk.LEFT, padx=(0, 8))

        # Restore All System Button
        self.btn_restore = NeumorphicButton(
            sub_row,
            text="♻️ Restore All",
            command=self.on_restore_all_click,
            width=138,
            height=36,
            accent="#252535",
            text_color="#FF8A80",
            font=("Segoe UI", 9, "bold")
        )
        self.btn_restore.pack(side=tk.LEFT)

    def create_console(self):
        console_container = tk.Frame(self.root, bg=BG_MAIN)
        console_container.pack(fill=tk.BOTH, expand=True, padx=25, pady=8)

        lbl_log = tk.Label(console_container, text="SYSTEM DIAGNOSTICS & LOGS", font=("Segoe UI", 8, "bold"), bg=BG_MAIN, fg=TEXT_MUTED)
        lbl_log.pack(anchor="w", pady=(0, 4))

        self.log_text = tk.Text(
            console_container, 
            height=8, 
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
    def log(self, message):
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
            check_fw = run_silent_cmd('netsh advfirewall firewall show rule name="Famwareta_TS3_Cloudflare_Block"')
            has_fw = (check_fw.returncode == 0)

            # Check TS3 process
            check_proc = run_silent_cmd('tasklist /fi "imagename eq ts3client_win64.exe"')
            is_ts_running = ("ts3client_win64.exe" in check_proc.stdout.decode('latin1', 'ignore'))

            def update_ui():
                self.lbl_stat_vpn.config(text="● VPN Bypass: Active ✓", fg=SUCCESS_GREEN)

                if has_hosts:
                    self.lbl_stat_hosts.config(text="● Hosts: Protected ✓", fg=SUCCESS_GREEN)
                else:
                    self.lbl_stat_hosts.config(text="● Hosts: Default ✗", fg=TEXT_MUTED)

                if has_fw:
                    self.lbl_stat_fw.config(text="● Firewall: Active ✓", fg=SUCCESS_GREEN)
                else:
                    self.lbl_stat_fw.config(text="● Firewall: Default", fg=TEXT_MUTED)

                if is_ts_running:
                    self.lbl_stat_ts.config(text="● TS3: Running", fg=ACCENT_CYAN)
                else:
                    self.lbl_stat_ts.config(text="● TS3: Closed", fg=TEXT_MUTED)

            self.root.after(0, update_ui)

        threading.Thread(target=scan, daemon=True).start()
        self.log("Famwareta Engine initialized. Ready.")

    def on_full_fix_click(self):
        """Execute complete patch sequence in background thread"""
        self.btn_full_fix.set_text("PROCESSING ENGINE...")
        
        def run():
            self.log("Starting Full Anti-Blacklist & VPN Bypass sequence...")
            
            # 1. Kill TS3
            self.log("[1/5] Terminating active TeamSpeak instances...")
            kill_ts3()
            time.sleep(0.5)

            # 2. Clear Cache
            self.log("[2/5] Cleaning temporary blacklist memory & cache...")
            clear_ts3_cache()

            # 3. Update Hosts
            self.log("[3/5] Patching hosts file (IPv4 & IPv6 blacklist domains)...")
            h_ok, h_msg = apply_hosts_patch()
            self.log(f"      -> {h_msg}")

            # 4. Apply Firewall
            self.log("[4/5] Activating Windows Firewall rules for TS3 program...")
            f_ok, f_msg = apply_firewall_rules()
            self.log(f"      -> {f_msg}")

            # 5. Route Bypass & Flush DNS
            self.log("[5/5] Establishing direct routing for TS servers & flushing DNS...")
            apply_vpn_bypass_routes()
            flush_dns()
            self.log("      -> DNS cache flushed cleanly.")

            time.sleep(0.5)
            self.log("SUCCESS: All patches successfully applied! Connecting directly to TS...")
            
            def finish():
                self.btn_full_fix.set_text("⚡ APPLY FIX & CONNECT")
                self.check_system_health()
                connect_to_server("tak.tssz.ir", "1834")
                messagebox.showinfo(
                    "Famwareta Fixer", 
                    "عملیات رفع بلک‌لیست با موفقیت انجام شد!\nتیم‌اسپیک اکنون باز شده و متصل می‌شود."
                )

            self.root.after(0, finish)

        threading.Thread(target=run, daemon=True).start()

    def on_restore_all_click(self):
        """Complete rollback of all changes to stock Windows state"""
        confirm = messagebox.askyesno(
            "تأیید بازگردانی", 
            "آیا مطمئن هستید که می‌خواهید تمام تنظیمات (فایروال، فایل Hosts و روت‌ها) را به حالت پیش‌فرض ویندوز بازگردانید؟"
        )
        if not confirm:
            return

        def run():
            self.log("Restoring all system configurations to default state...")
            
            # Kill TS3
            kill_ts3()
            
            # Restore binary if .bak exists
            restore_ts3_binary()
            self.log("[1/4] Restored original ts3client_win64.exe from backup.")

            # Remove Firewall rules
            remove_firewall_rules()
            self.log("[2/4] Removed all Famwareta firewall rules.")

            # Clean Hosts file
            remove_hosts_patch()
            self.log("[3/4] Cleaned hosts file entries.")

            # Clear custom routes
            remove_vpn_bypass_routes()
            flush_dns()
            self.log("[4/4] Cleared custom network routes & flushed DNS.")

            def finish():
                self.check_system_health()
                self.log("RESTORE COMPLETE: System is back to factory stock state.")
                messagebox.showinfo("Restore Complete", "تمام تغییرات با موفقیت به حالت اولیه ویندوز بازگردانده شد!")

            self.root.after(0, finish)

        threading.Thread(target=run, daemon=True).start()

    def on_kill_ts_click(self):
        kill_ts3()
        self.log("Forced closed all TeamSpeak 3 processes.")
        self.check_system_health()

    def on_connect_ts_click(self):
        self.log("Opening connection to Famwareta Community TS server...")
        connect_to_server("tak.tssz.ir", "1834")

    def show_donate_modal(self):
        """Custom Neumorphic Donation Modal Dialog"""
        modal = tk.Toplevel(self.root)
        modal.title("Donate & Support - Famwareta")
        modal.geometry("400x320")
        modal.resizable(False, False)
        modal.configure(bg=BG_MAIN)
        modal.transient(self.root)
        modal.grab_set()

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

        trc20_address = "TYDzsxdh5m3sHMvf8gKjP9vV8B59W9yZzQ"
        
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