import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import threading
import queue
import time
import ssl
import os
import re
import socket
import warnings
import sys
warnings.filterwarnings('ignore')
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from datetime import datetime

BG     = "#0b0f0b"
BG2    = "#101410"
BG3    = "#141a14"
BG4    = "#1a221a"
BORDER = "#1e2e1e"
ACC    = "#4af296"
ACC2   = "#2db86e"
DIM    = "#2a3d2a"
TXT    = "#a8c8a8"
RED    = "#e05555"
YEL    = "#d4b84a"
WHITE  = "#d0e8d0"
FONT   = ("Consolas", 9)
FONTB  = ("Consolas", 9, "bold")

ENV_PATHS = [
    "/.env","/.env.local","/.env.backup","/.env.old","/.env.bak",
    "/.env.save","/.env.example","/.env.production","/.env.staging",
    "/.env.development","/.env.dev","/.env.prod","/.env.test",
    "/.env.sample","/.env.copy","/.env~","/env","/env.txt",
    "/config/.env","/public/.env","/src/.env","/app/.env",
    "/backend/.env","/api/.env","/web/.env","/laravel/.env",
    "/storage/.env","/bootstrap/.env",
]
ENV_KEYS = [
    "APP_KEY","APP_ENV","APP_URL","DB_HOST","DB_DATABASE","DB_USERNAME",
    "DB_PASSWORD","DB_CONNECTION","MAIL_HOST","MAIL_USERNAME","MAIL_PASSWORD",
    "AWS_ACCESS_KEY","AWS_SECRET_KEY","REDIS_HOST","REDIS_PASSWORD",
    "JWT_SECRET","API_KEY","SECRET_KEY","STRIPE_KEY","STRIPE_SECRET",
    "SMTP_HOST","SMTP_USER","SMTP_PASS","FTP_HOST","FTP_USER","FTP_PASS",
    "MONGO_URI","S3_KEY","S3_SECRET","SECRET","PASSWORD","TOKEN",
]
ENV_SENSITIVE = [
    "DB_PASSWORD","DB_USERNAME","DB_DATABASE","DB_HOST","MAIL_PASSWORD",
    "MAIL_USERNAME","APP_KEY","AWS_ACCESS_KEY","AWS_SECRET_KEY","API_KEY",
    "SECRET_KEY","JWT_SECRET","FTP_PASS","FTP_USER","SMTP_PASS","REDIS_PASSWORD",
    "STRIPE_KEY","STRIPE_SECRET",
]
GIT_PATHS = [
    "/.git/config","/.git/HEAD","/.git/index","/.git/COMMIT_EDITMSG",
    "/.git/packed-refs","/.git/refs/heads/master","/.git/refs/heads/main",
    "/.git/refs/heads/develop","/.git/logs/HEAD","/.gitignore",
    "/.gitmodules","/.gitattributes","/.gitconfig",
]
GIT_KEYS = [
    "[core]","[remote","[branch","repositoryformatversion",
    "filemode","bare","logallrefupdates","ref: refs/","url = ","fetch = ",
]
JS_PATHS = [
    "/js/app.js","/js/main.js","/js/index.js","/js/bundle.js",
    "/js/config.js","/js/env.js","/js/api.js","/static/js/main.chunk.js",
    "/static/js/bundle.js","/static/js/app.js","/assets/js/app.js",
    "/assets/js/main.js","/dist/js/app.js","/dist/bundle.js",
    "/build/static/js/main.chunk.js","/app.js","/main.js","/bundle.js",
]
JS_SECRETS = [
    "apiKey","api_key","apiSecret","api_secret","accessToken","access_token",
    "secretKey","secret_key","privateKey","private_key","clientSecret",
    "client_secret","authToken","auth_token","password","aws_access",
    "aws_secret","REACT_APP_","VUE_APP_","NEXT_PUBLIC_",
    "stripe","paypal","twilio","sendgrid","mongodb","mysql://","postgres://",
]
VSFTPD_PATHS = [
    "/vsftpd.conf","/.vsftpd.conf","/vsftpd.conf.bak","/ftpd.conf",
    "/proftpd.conf","/pure-ftpd.conf","/.ftpaccess","/.ftpconfig",
    "/etc/vsftpd.conf","/etc/proftpd.conf","/etc/pure-ftpd.conf",
    "/etc/ftpusers","/etc/vsftpd.user_list",
]
VSFTPD_KEYS = [
    "anonymous_enable","local_enable","write_enable","local_umask",
    "xferlog_enable","chroot_local_user","listen","userlist_enable",
    "vsftpd","proftpd","ftp_username","pasv_min_port","root:x:0:0",
]
FM_FEATURES = [
    "upload","rename","chmod","download","delete","edit","copy","move",
    "extract","compress","create","newfolder","new folder","new file",
    "file manager","filemanager","file size","last modified","permissions",
]
FALSE_POS = [
    "404","not found","page not found","tidak ditemukan","error 404",
    "forbidden","access denied","403","400 bad request",
    "under construction","coming soon","wordpress.com","domain for sale",
    "parked domain","welcome to nginx","it works","index of /",
]


def fetch(url, timeout=8):
    """Fetch URL with better error handling"""
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/plain,text/html,*/*",
            "Connection": "close",
        })
        with urlopen(req, timeout=timeout, context=ctx) as r:
            return r.status, r.read(65536).decode("utf-8", "ignore"), r.url
    except HTTPError as e:
        return e.code, "", url
    except URLError as e:
        return None, "", url
    except socket.timeout:
        return None, "", url
    except Exception as e:
        return None, "", url


def alive(host, timeout=4):
    """Check if host is alive"""
    for port in [80, 443]:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            s.connect((host, port))
            s.close()
            return True
        except Exception:
            pass
    return False


def norm(raw):
    """Normalize domain/URL"""
    raw = raw.strip()
    if not raw:
        return None
    if "://" not in raw:
        raw = "http://" + raw
    try:
        p = urlparse(raw)
        h = (p.netloc or p.path.split("/")[0]).split(":")[0]
        return h if h else None
    except Exception:
        return None


def same(u1, u2):
    """Check if two URLs are same domain"""
    try:
        return urlparse(u1).netloc == urlparse(u2).netloc
    except Exception:
        return False


def chk_env(st, body, u, fu):
    """Check for .env file exposure"""
    if st != 200 or not same(u, fu):
        return False, []
    b = body.strip()
    if len(b) < 5 or "=" not in b:
        return False, []
    bu = b.upper()
    if sum(1 for k in ENV_KEYS if k in bu) < 2:
        return False, []
    creds = []
    for line in b.split("\n"):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            key = line.split("=")[0].strip().upper()
            if any(s in key for s in ENV_SENSITIVE):
                val = line.split("=", 1)[1].strip()
                if val and val not in ("", '""', "''", "null", "NULL"):
                    creds.append(line[:120])
    return True, creds[:15]


def chk_git(st, body, u, fu):
    """Check for .git exposure"""
    if st != 200 or not same(u, fu):
        return False, []
    b = body.strip()
    if len(b) < 5:
        return False, []
    if sum(1 for k in GIT_KEYS if k.lower() in b.lower()) < 2:
        return False, []
    return True, [l.strip() for l in b.split("\n") if l.strip()][:10]


def chk_js(st, body, u, fu):
    """Check for JS secrets"""
    if st != 200 or not same(u, fu):
        return False, []
    if len(body) < 10:
        return False, []
    found = []
    for sec in JS_SECRETS:
        pat = re.escape(sec) + r'''["\']?\s*[:=]\s*["\']([^"\'{}]+)["\']'''
        try:
            for m in re.findall(pat, body, re.IGNORECASE):
                if len(m) > 5 and m not in ("null", "undefined", "true", "false"):
                    found.append(sec + " = " + m[:80])
        except Exception:
            pass
    if not found:
        return False, []
    return True, list(dict.fromkeys(found))[:15]


def chk_vsftpd(st, body, u, fu):
    """Check for VSFTPD config exposure"""
    if st != 200 or not same(u, fu):
        return False, []
    b = body.strip()
    if len(b) < 5:
        return False, []
    if sum(1 for k in VSFTPD_KEYS if k.lower() in b.lower()) < 2:
        return False, []
    return True, [l.strip() for l in b.split("\n") if l.strip() and not l.strip().startswith("#")][:15]


def chk_shell(st, body, u, fu):
    """Check for shell/file manager"""
    if st != 200 or not same(u, fu):
        return False, []
    b = body.lower().strip()
    if len(b) < 10:
        return False, []
    for kw in FALSE_POS:
        if kw in b:
            return False, []
    if sum(1 for f in FM_FEATURES if f in b) >= 3:
        return True, ["file manager detected"]
    return False, []


SCANNERS = {
    "shell":  {"name": "Shell Finder",   "paths": [],            "fn": chk_shell,  "has_path": True},
    "env":    {"name": "ENV Scanner",    "paths": ENV_PATHS,    "fn": chk_env,    "has_path": False},
    "vsftpd": {"name": "VSFTPD Scanner", "paths": VSFTPD_PATHS, "fn": chk_vsftpd, "has_path": False},
    "js":     {"name": "JS Scanner",     "paths": JS_PATHS,     "fn": chk_js,     "has_path": False},
    "git":    {"name": "Git Exposure",   "paths": GIT_PATHS,    "fn": chk_git,    "has_path": False},
}


class Scanner(tk.Frame):
    def __init__(self, parent, key, app):
        super().__init__(parent, bg=BG)
        self.key = key
        self.app = app
        self.info = SCANNERS[key]
        self.running = False
        self.found = []
        self.rq = queue.Queue()
        self.stats = {"total": 0, "vuln": 0, "safe": 0, "start": 0}
        self.domain_path = tk.StringVar()
        self.path_path = tk.StringVar()
        self.output_path = tk.StringVar(value="results.txt")
        self.threads_var = tk.IntVar(value=30)
        self.timeout_var = tk.IntVar(value=8)
        self._build()
        self._poll()

    def _build(self):
        top = tk.Frame(self, bg=BG2)
        top.pack(fill="x")
        inner = tk.Frame(top, bg=BG2, pady=10)
        inner.pack(fill="x", padx=14)

        def entry_col(parent, label, var, cmd, w=20):
            col = tk.Frame(parent, bg=BG2)
            col.pack(side="left", padx=(0, 14))
            tk.Label(col, text=label, bg=BG2, fg=DIM,
                     font=("Consolas", 8, "bold")).pack(anchor="w")
            row = tk.Frame(col, bg=BG2)
            row.pack(anchor="w")
            tk.Entry(row, textvariable=var, bg=BG4, fg=TXT,
                     insertbackground=ACC, font=FONT, relief="flat", bd=0,
                     highlightthickness=1, highlightbackground=BORDER,
                     highlightcolor=ACC, width=w).pack(side="left", ipady=4, padx=(0, 3))
            tk.Button(row, text="Browse", bg=BG3, fg=ACC, font=FONT,
                      relief="flat", cursor="hand2", padx=6, pady=2,
                      activebackground=BG4, command=cmd).pack(side="left")
            return col

        col_d = entry_col(inner, "DOMAIN LIST", self.domain_path, self._browse_domain)
        self.lbl_dn = tk.Label(col_d, text="no file", bg=BG2, fg=DIM, font=("Consolas", 7))
        self.lbl_dn.pack(anchor="w")

        if self.info["has_path"]:
            col_p = entry_col(inner, "PATH LIST", self.path_path, self._browse_path)
            self.lbl_pn = tk.Label(col_p, text="no file", bg=BG2, fg=DIM, font=("Consolas", 7))
            self.lbl_pn.pack(anchor="w")

        col_o = entry_col(inner, "OUTPUT", self.output_path, self._browse_out, w=14)
        tk.Label(col_o, text=" ", bg=BG2, fg=DIM, font=("Consolas", 7)).pack()

        col_s = tk.Frame(inner, bg=BG2)
        col_s.pack(side="left", padx=(0, 14))
        tk.Label(col_s, text="THREADS", bg=BG2, fg=DIM, font=("Consolas", 8, "bold")).pack(anchor="w")
        tk.Spinbox(col_s, from_=1, to=500, textvariable=self.threads_var,
                   bg=BG4, fg=YEL, font=FONTB, relief="flat", bd=0,
                   highlightthickness=1, highlightbackground=BORDER,
                   highlightcolor=ACC, width=6,
                   buttonbackground=BG3).pack(anchor="w", ipady=3)
        tk.Label(col_s, text="TIMEOUT", bg=BG2, fg=DIM, font=("Consolas", 8, "bold")).pack(anchor="w", pady=(4, 0))
        tk.Spinbox(col_s, from_=1, to=60, textvariable=self.timeout_var,
                   bg=BG4, fg=YEL, font=FONTB, relief="flat", bd=0,
                   highlightthickness=1, highlightbackground=BORDER,
                   highlightcolor=ACC, width=6,
                   buttonbackground=BG3).pack(anchor="w", ipady=3)

        col_b = tk.Frame(inner, bg=BG2)
        col_b.pack(side="left", padx=(8, 0))
        tk.Label(col_b, text=" ", bg=BG2, font=("Consolas", 8)).pack()
        bf = tk.Frame(col_b, bg=BG2)
        bf.pack()
        self.btn_start = tk.Button(bf, text="START", bg=ACC2, fg="#000",
                                    font=("Consolas", 9, "bold"), relief="flat",
                                    cursor="hand2", padx=14, pady=5,
                                    activebackground=ACC, command=self._start)
        self.btn_start.pack(side="left", padx=(0, 4))
        self.btn_stop = tk.Button(bf, text="STOP", bg=RED, fg="white",
                                   font=("Consolas", 9, "bold"), relief="flat",
                                   cursor="hand2", padx=14, pady=5,
                                   state="disabled", activebackground="#aa2222",
                                   command=self._stop)
        self.btn_stop.pack(side="left", padx=(0, 4))
        tk.Button(bf, text="CLEAR", bg=BG3, fg=TXT,
                  font=("Consolas", 9, "bold"), relief="flat",
                  cursor="hand2", padx=10, pady=5,
                  activebackground=BG4, command=self._clear).pack(side="left")

        tk.Frame(top, bg=BORDER, height=1).pack(fill="x")

        rh = tk.Frame(self, bg=BG3, pady=5)
        rh.pack(fill="x")
        tk.Frame(rh, bg=BG3, width=12).pack(side="left")
        self.dot = tk.Label(rh, text="o", bg=BG3, fg=DIM, font=("Consolas", 9, "bold"))
        self.dot.pack(side="left", padx=(0, 6))
        tk.Label(rh, text="RESULTS", bg=BG3, fg=ACC, font=("Consolas", 9, "bold")).pack(side="left")
        tk.Button(rh, text="SAVE", bg=BG4, fg=ACC, font=FONTB,
                  relief="flat", padx=10, pady=2, cursor="hand2",
                  activebackground=BG3, command=self._save).pack(side="right", padx=10)
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        self.result_box = scrolledtext.ScrolledText(
            self, bg="#070d07", fg=TXT, font=("Consolas", 9),
            relief="flat", state="disabled", wrap="none",
            selectbackground=BG4, insertbackground=ACC,
        )
        self.result_box.pack(fill="both", expand=True)
        self.result_box.tag_config("vu",  foreground=ACC)
        self.result_box.tag_config("arr", foreground=WHITE)
        self.result_box.tag_config("vtag",foreground=ACC,  font=("Consolas", 9, "bold"))
        self.result_box.tag_config("fu",  foreground=DIM)
        self.result_box.tag_config("ftag",foreground=RED,  font=("Consolas", 9, "bold"))
        self.result_box.tag_config("cr",  foreground=YEL)
        self.result_box.tag_config("inf", foreground=ACC)
        self.result_box.tag_config("dim", foreground=DIM)

        pf = tk.Frame(self, bg=BG3, pady=3)
        pf.pack(fill="x")
        self.lbl_cur = tk.Label(pf, text="", bg=BG3, fg=DIM, font=("Consolas", 7))
        self.lbl_cur.pack(side="left", padx=8)
        
        # CRITICAL FIX: Use default progressbar without custom style
        # This prevents "Layout Horizontal.R.TProgressbar not found" error
        try:
            self.pbar = ttk.Progressbar(pf, orient="horizontal", mode="determinate")
            # Try to configure appearance (optional - won't crash if it fails)
            try:
                self.pbar.config(length=200)
            except:
                pass
        except Exception as e:
            # Fallback: Create a simple frame-based progress indicator
            self.pbar = tk.Frame(pf, bg=BG4, height=4)
            self.pbar.pack(fill="x", expand=True, padx=8, side="right")
            self.pbar_value = 0
            
        self.pbar.pack(fill="x", expand=True, padx=8, side="right")

        sb = tk.Frame(self, bg=BG2)
        sb.pack(fill="x")
        tk.Frame(sb, bg=ACC, height=1).pack(fill="x")
        inner2 = tk.Frame(sb, bg=BG2, pady=4)
        inner2.pack(fill="x", padx=10)
        self.lbl_total  = tk.Label(inner2, text="SCANNED  0", bg=BG2, fg=DIM,  font=("Consolas", 8, "bold"))
        self.lbl_vuln   = tk.Label(inner2, text="VULN  0",    bg=BG2, fg=ACC,  font=("Consolas", 8, "bold"))
        self.lbl_safe   = tk.Label(inner2, text="SAFE  0",    bg=BG2, fg=DIM,  font=("Consolas", 8, "bold"))
        self.lbl_time   = tk.Label(inner2, text="00:00",       bg=BG2, fg=DIM,  font=("Consolas", 8, "bold"))
        self.lbl_status = tk.Label(inner2, text="IDLE",        bg=BG2, fg=DIM,  font=("Consolas", 8, "bold"))
        for w in [self.lbl_total, self.lbl_vuln, self.lbl_safe, self.lbl_time, self.lbl_status]:
            w.pack(side="left", padx=10)

    def _log(self, msg, tag="inf"):
        try:
            self.result_box.config(state="normal")
            self.result_box.insert("end", msg + "\n", tag)
            self.result_box.see("end")
            self.result_box.config(state="disabled")
        except Exception:
            pass

    def _log_result(self, url, vuln, details):
        try:
            self.result_box.config(state="normal")
            if vuln:
                self.result_box.insert("end", url,        "vu")
                self.result_box.insert("end", " ",        "arr")
                self.result_box.insert("end", "VULN\n",  "vtag")
            else:
                self.result_box.insert("end", url,        "fu")
                self.result_box.insert("end", " ",        "arr")
                self.result_box.insert("end", "FAILED\n","ftag")
            self.result_box.see("end")
            self.result_box.config(state="disabled")
        except Exception:
            pass

    def _update_stats(self):
        try:
            self.lbl_total.config(text="SCANNED  " + str(self.stats["total"]))
            self.lbl_vuln.config(text="VULN  " + str(self.stats["vuln"]))
            self.lbl_safe.config(text="SAFE  " + str(self.stats["safe"]))
            elapsed = time.time() - self.stats["start"] if self.stats["start"] else 0
            m, s = divmod(int(elapsed), 60)
            self.lbl_time.config(text="%02d:%02d" % (m, s))
        except Exception:
            pass

    def _poll(self):
        try:
            while True:
                try:
                    item = self.rq.get_nowait()
                except queue.Empty:
                    break
                    
                k = item.get("kind", "")
                if k == "result":
                    self._log_result(item.get("url", ""), item.get("vuln", False), item.get("details", []))
                elif k == "info":
                    self._log(item.get("msg", ""), item.get("tag", "inf"))
                elif k == "stats":
                    self.stats.update(item.get("data", {}))
                    self._update_stats()
                    tw = item.get("tw", 0)
                    if tw > 0:
                        pct = self.stats["total"] / tw * 100
                        try:
                            self.pbar["value"] = min(pct, 100)
                        except:
                            pass  # Fallback progressbar doesn't support value
                elif k == "status":
                    msg = item.get("msg", "")
                    self.lbl_status.config(text=msg[:30])
                    self.lbl_cur.config(text=msg[:65])
                elif k == "done":
                    self._on_done()
        except Exception:
            pass
        try:
            self.after(60, self._poll)
        except Exception:
            pass

    def _browse_domain(self):
        try:
            p = filedialog.askopenfilename(filetypes=[("Text", "*.txt"), ("All", "*.*")])
            if not p:
                return
            self.domain_path.set(p)
            try:
                with open(p, encoding="utf-8", errors="ignore") as f:
                    n = sum(1 for l in f if l.strip() and not l.startswith("#"))
                self.lbl_dn.config(text=os.path.basename(p) + " (" + str(n) + ")")
            except Exception:
                self.lbl_dn.config(text=os.path.basename(p))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _browse_path(self):
        try:
            p = filedialog.askopenfilename(filetypes=[("Text", "*.txt"), ("All", "*.*")])
            if not p:
                return
            self.path_path.set(p)
            try:
                with open(p, encoding="utf-8", errors="ignore") as f:
                    n = sum(1 for l in f if l.strip() and not l.startswith("#"))
                self.lbl_pn.config(text=os.path.basename(p) + " (" + str(n) + ")")
            except Exception:
                self.lbl_pn.config(text=os.path.basename(p))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _browse_out(self):
        try:
            p = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text", "*.txt")])
            if p:
                self.output_path.set(p)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _clear(self):
        try:
            self.result_box.config(state="normal")
            self.result_box.delete("1.0", "end")
            self.result_box.config(state="disabled")
            self.found = []
            self.stats = {"total": 0, "vuln": 0, "safe": 0, "start": 0}
            self._update_stats()
            try:
                self.pbar["value"] = 0
            except:
                pass
            self.lbl_cur.config(text="")
        except Exception:
            pass

    def _save(self):
        try:
            if not self.found:
                self._log("[!] belum ada hasil", "inf")
                return
            p = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text", "*.txt")])
            if not p:
                return
            with open(p, "w", encoding="utf-8") as f:
                f.write("# REAPER SCANNER [" + self.key.upper() + "] - " + str(datetime.now()) + "\n\n")
                for item in self.found:
                    f.write("[VULN] " + item["url"] + "\n")
                    for d in item.get("details", []):
                        f.write("  " + d + "\n")
                    f.write("\n")
            self._log("[+] saved " + str(len(self.found)) + " -> " + p, "inf")
        except Exception as e:
            messagebox.showerror("Error", "Failed to save: " + str(e))

    def _dot_anim(self):
        if not self.running:
            try:
                self.dot.config(fg=DIM)
            except Exception:
                pass
            return
        try:
            self.dot.config(fg=ACC if self.dot.cget("fg") == DIM else DIM)
            self.after(600, self._dot_anim)
        except Exception:
            pass

    def _start(self):
        try:
            dpath = self.domain_path.get().strip()
            if not dpath or not os.path.exists(dpath):
                self._log("[!] load domain list dulu", "inf")
                messagebox.showwarning("Warning", "Please load domain list first!")
                return
            with open(dpath, encoding="utf-8", errors="ignore") as f:
                domains = [l.strip() for l in f if l.strip() and not l.startswith("#")]
            if not domains:
                self._log("[!] domain kosong", "inf")
                return

            paths = list(self.info["paths"])
            if self.info["has_path"]:
                pp = self.path_path.get().strip()
                if not pp or not os.path.exists(pp):
                    self._log("[!] load path list dulu", "inf")
                    messagebox.showwarning("Warning", "Please load path list first!")
                    return
                with open(pp, encoding="utf-8", errors="ignore") as f:
                    paths = [l.strip() for l in f if l.strip() and not l.startswith("#")]
                paths = list(dict.fromkeys(paths))

            if not paths:
                self._log("[!] tidak ada path", "inf")
                return

            self.running = True
            self.found = []
            self.stats = {"total": 0, "vuln": 0, "safe": 0, "start": time.time()}
            try:
                self.pbar["value"] = 0
            except:
                pass
            self.btn_start.config(state="disabled")
            self.btn_stop.config(state="normal")
            self.lbl_status.config(text="SCANNING...")
            self._dot_anim()

            tw = len(domains) * len(paths)
            outfile = self.output_path.get().strip()
            fn = self.info["fn"]

            if outfile:
                with open(outfile, "w", encoding="utf-8") as f:
                    f.write("# REAPER SCANNER [" + self.key.upper() + "] - " + str(datetime.now()) + "\n\n")

            self._log("[*] " + str(len(domains)) + " domains x " + str(len(paths)) + " paths = " + str(tw), "inf")
            self._log("[*] threads:" + str(self.threads_var.get()) + " timeout:" + str(self.timeout_var.get()) + "s", "inf")
            self._log("-" * 50, "dim")

            threading.Thread(
                target=self._engine,
                args=(domains, paths, fn, self.threads_var.get(), self.timeout_var.get(), outfile, tw),
                daemon=True,
            ).start()
        except Exception as e:
            messagebox.showerror("Error", "Failed to start: " + str(e))
            self.running = False
            self.btn_start.config(state="normal")
            self.btn_stop.config(state="disabled")

    def _stop(self):
        self.running = False
        self.lbl_status.config(text="STOPPING...")

    def _on_done(self):
        self.running = False
        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")
        try:
            self.pbar["value"] = 100
        except:
            pass
        self.dot.config(fg=DIM)
        self.lbl_status.config(text="DONE")
        self.lbl_cur.config(text="")
        elapsed = time.time() - self.stats["start"]
        self._log("-" * 50, "dim")
        self._log("[+] done  vuln:" + str(self.stats["vuln"]) + "  time:" + ("%.1f" % elapsed) + "s", "inf")

    def _engine(self, domains, paths, fn, n_threads, timeout, outfile, tw):
        """Main scanning engine with better error handling"""
        wq = queue.Queue(maxsize=n_threads * 80)
        lock = threading.Lock()
        counter = {"total": 0, "vuln": 0, "safe": 0}

        def producer():
            try:
                for domain in domains:
                    if not self.running:
                        break
                    host = norm(domain)
                    if not host:
                        continue
                    if not alive(host, timeout=min(4, timeout)):
                        with lock:
                            counter["safe"] += len(paths)
                            counter["total"] += len(paths)
                        try:
                            self.rq.put({"kind": "stats", "data": dict(counter), "tw": tw})
                        except Exception:
                            pass
                        continue
                    for path in paths:
                        if not self.running:
                            break
                        wq.put((host, path))
                for _ in range(n_threads):
                    wq.put(None)
            except Exception:
                pass

        threading.Thread(target=producer, daemon=True).start()

        def worker():
            while self.running:
                try:
                    item = wq.get(timeout=2)
                    if item is None:
                        break
                    host, path = item
                except queue.Empty:
                    break
                except Exception:
                    break

                try:
                    url = "https://" + host + path
                    self.rq.put({"kind": "status", "msg": host + path})
                    st, body, fu = fetch(url, timeout)
                    if st != 200:
                        url = "http://" + host + path
                        st, body, fu = fetch(url, timeout)

                    vuln, details = fn(st, body, url, fu)

                    with lock:
                        counter["total"] += 1
                        if vuln:
                            counter["vuln"] += 1
                            vuln_url = fu if fu else url
                            self.found.append({"url": vuln_url, "details": details})
                            self.rq.put({"kind": "result", "url": vuln_url, "vuln": True, "details": details})
                            if outfile:
                                try:
                                    with open(outfile, "a", encoding="utf-8") as f:
                                        f.write("[VULN] " + fu + "\n")
                                        for d in details:
                                            f.write("  " + d + "\n")
                                        f.write("\n")
                                except Exception:
                                    pass
                        else:
                            counter["safe"] += 1
                            self.rq.put({"kind": "result", "url": url, "vuln": False, "details": []})
                        self.rq.put({"kind": "stats", "data": dict(counter), "tw": tw})
                except Exception:
                    pass

        threads = [threading.Thread(target=worker, daemon=True) for _ in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        try:
            self.rq.put({"kind": "done"})
        except Exception:
            pass


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("REAPER SCANNER V.1.0")
        self.geometry("1000x680")
        self.minsize(820, 560)
        self.configure(bg=BG)

        # Windows-specific fixes
        try:
            if sys.platform == "win32":
                self.iconbitmap(default='')
        except Exception:
            pass

        self.frames = {}
        self.active_key = None
        self.active_btn = None

        self._build_header()
        self._build_sidebar()
        self._build_main()
        self._show("shell")

    def _build_header(self):
        hdr = tk.Frame(self, bg=BG2)
        hdr.pack(fill="x")
        tk.Frame(hdr, bg=ACC, height=2).pack(fill="x")
        inner = tk.Frame(hdr, bg=BG2, pady=8)
        inner.pack(fill="x", padx=14)
        left = tk.Frame(inner, bg=BG2)
        left.pack(side="left")
        tk.Label(left, text="REAPER SCANNER", bg=BG2, fg=ACC,
                 font=("Consolas", 14, "bold")).pack(anchor="w")
        self.lbl_sub = tk.Label(left, text="V.1.0", bg=BG2, fg=DIM,
                                 font=("Consolas", 8))
        self.lbl_sub.pack(anchor="w")
        right = tk.Frame(inner, bg=BG2)
        right.pack(side="right")
        tk.Label(right, text="Author  : @anakbiasa3302", bg=BG2, fg=DIM, font=FONT).pack(anchor="e")
        tk.Label(right, text="Channel : t.me/goobotproject", bg=BG2, fg=DIM, font=FONT).pack(anchor="e")
        tk.Frame(hdr, bg=BORDER, height=1).pack(fill="x")

    def _build_sidebar(self):
        self.sidebar = tk.Frame(self, bg=BG2, width=170)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        tk.Frame(self.sidebar, bg=BORDER, width=1).pack(side="right", fill="y")

        tk.Label(self.sidebar, text="SCANNERS", bg=BG2, fg=DIM,
                 font=("Consolas", 7, "bold")).pack(anchor="w", padx=14, pady=(14, 6))

        self.side_btns = {}
        for key, info in SCANNERS.items():
            btn = tk.Button(
                self.sidebar,
                text=info["name"],
                bg=BG2, fg=DIM,
                font=("Consolas", 9),
                relief="flat", cursor="hand2",
                anchor="w", padx=14, pady=10,
                bd=0, activebackground=BG3,
                activeforeground=ACC,
                command=lambda k=key: self._show(k),
            )
            btn.pack(fill="x")
            self.side_btns[key] = btn

    def _build_main(self):
        self.main = tk.Frame(self, bg=BG)
        self.main.pack(side="left", fill="both", expand=True)

        for key in SCANNERS:
            f = Scanner(self.main, key, self)
            f.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.frames[key] = f

    def _show(self, key):
        self.active_key = key
        info = SCANNERS[key]
        self.lbl_sub.config(text="V.1.0  -  " + info["name"])

        for k, btn in self.side_btns.items():
            if k == key:
                btn.config(bg=BG4, fg=ACC, font=("Consolas", 9, "bold"))
            else:
                btn.config(bg=BG2, fg=DIM, font=("Consolas", 9))

        for k, f in self.frames.items():
            if k == key:
                f.lift()
            else:
                f.lower()


if __name__ == "__main__":
    try:
        app = App()
        app.mainloop()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()
