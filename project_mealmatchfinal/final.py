import os
import sys
import time
import random
import openpyxl  
import pygame as p      
import customtkinter as c
from PIL import Image as PILImage, ImageTk

# ============== CONFIG ==============
c.set_appearance_mode("light")
c.set_default_color_theme("blue")
DIR = os.path.dirname(os.path.abspath(__file__))
P_S = os.path.join

# ============== audio init (safe) ==============
MUS = CLK = None
try:
    p.mixer.init()
    mus_path = P_S(DIR, "assets", "bonmusic.mp3")
    clk_path = P_S(DIR, "assets", "click.wav")
    MUS = p.mixer.Sound(mus_path) if os.path.exists(mus_path) else None
    CLK = p.mixer.Sound(clk_path) if os.path.exists(clk_path) else None
    
    if MUS: 
        MUS.set_volume(0.25); MUS.play(-1)
    if CLK:
        CLK.set_volume(0.45)
except Exception :
    MUS = CLK = None

def play():
    try:
        if CLK:
            CLK.play()
    except Exception:
        pass

# ============== DATA LOADER ==============
KEYS = [
    "nama", "rasa", "budget", "cuaca", "porsi",
    "kalori", "karbo", "protein", "lemak",
    "harga", "deskripsi",
]

def load_foods_from_excel():
    file = os.path.join(DIR, "assets", "data_makanan.xlsx")
    if not os.path.exists(file):
        return []
    
    try:
        # Load workbook menggunakan openpyxl (ringan)
        wb = openpyxl.load_workbook(file, data_only=True)
        sheet = wb.active
        # Ambil semua data sebagai list of rows
        rows = list(sheet.iter_rows(values_only=True))
        if not rows: return []

        # Baris pertama adalah header
        raw_headers = rows[0]
        # Bersihkan header (lowercase & strip)
        headers = [str(h).lower().strip() if h is not None else "" for h in raw_headers]

        # Mapping nama kolom lama ke baru (sama seperti logika pandas sebelumnya)
        mapping = {
            "kalori (kkal)": "kalori", "karbo (g)": "karbo",
            "protein (g)": "protein", "lemak (g)": "lemak",
        }
        
        # Terapkan mapping ke header
        final_headers = [mapping.get(h, h) for h in headers]

        # Cek apakah semua KEY wajib ada di excel
        for k in KEYS:
            if k not in final_headers:
                print(f"Kolom hilang: {k}") # Debugging info
                return []

        # Konversi data baris menjadi list of dictionaries (records)
        data_list = []
        for row_values in rows[1:]: # Skip header
            record = {}
            # Map value ke header yang sesuai
            row_dict = {}
            for i, header in enumerate(final_headers):
                if i < len(row_values):
                    val = row_values[i]
                    # Logika fillna(""): jika None ganti jadi string kosong
                    row_dict[header] = val if val is not None else ""
                else:
                    row_dict[header] = ""
            
            # Hanya ambil kolom yang ada di KEYS
            clean_record = {k: row_dict.get(k, "") for k in KEYS}
            data_list.append(clean_record)
            
        return data_list

    except Exception as e:
        print("Error loading excel:", e)
        return []

FOODS = load_foods_from_excel()

def get_match(answer):
    ans = {k: str(v).strip().lower() for k, v in answer.items()}
    for food in FOODS:
        cocok = True
        for k, v in ans.items():
            f = str(food.get(k, "")).strip().lower()
            if f != v:
                cocok = False
                break
        if cocok:
            return food
    
    return FOODS[0] if FOODS else {}

# ============== SAFE BACKGROUND HELPER ==============
def bg(parent, filename):
    app = parent.winfo_toplevel()
    try:
        W = app.W
        H = app.H
    except Exception:
        W, H = 500, 600   

    path = P_S(DIR, "assets", filename)
    if not os.path.exists(path):
        lbl = c.CTkLabel(parent, text="", fg_color="#FFF6EE")
        lbl.place(x=0, y=0, relwidth=1, relheight=1)
        return lbl
    try:
        img = PILImage.open(path)

        target_ratio = W / H
        img_ratio = img.width / img.height

        if img_ratio > target_ratio:
            new_height = H
            new_width = int(H * img_ratio)
        else:
            new_width = W
            new_height = int(W / img_ratio)
        img = img.resize((new_width, new_height), PILImage.LANCZOS)

        # crop tengah supaya pas dengan ukuran frame
        left = (new_width - W) // 2
        top = (new_height - H) // 2
        img = img.crop((left, top, left + W, top + H))

        ctk_img = c.CTkImage(light_image=img, size=(W, H))
        lbl = c.CTkLabel(parent, image=ctk_img, text="")
        lbl.image = ctk_img

    except Exception as e:
        print("WARN load bg:", e)
        lbl = c.CTkLabel(parent, text="", fg_color="#FFF6EE")

    lbl.place(x=0, y=0, relwidth=1, relheight=1)
    return lbl

# ============== FOOD VISUAL ==============
class FoodArtist(c.CTkCanvas):
    def __init__(self, master, food_name, width=200, height=130):
        super().__init__(master, width=width, height=height, bg="#FFF8F0", highlightthickness=0)
        self.food_name = food_name.lower()
        self.draw()

    def draw(self):
        self.delete("all") 
        name = self.food_name

        # --- FUNGSI BANTUAN GAMBAR ---
        def draw_plate():
            self.create_oval(30, 95, 170, 125, fill="#D0D0D0", outline="") # Shadow
            self.create_oval(30, 85, 170, 120, fill="white", outline="#B0B0B0", width=2) # Rim
            self.create_oval(40, 90, 160, 115, fill="#F5F5F5", outline="") # Inner

        def draw_bowl(color="#E74C3C"):
            self.create_oval(40, 110, 160, 125, fill="#A9A9A9", outline="") # Shadow
            self.create_arc(45, 60, 155, 125, start=180, extent=180, fill=color, outline="#922B21", width=2) # Body
            self.create_oval(45, 60, 155, 80, fill="#EC7063", outline="#922B21") # Rim top

        def draw_rice_mound(color="#FFFDD0"):
            self.create_oval(60, 65, 140, 105, fill=color, outline="#CCC")
            for _ in range(8): # Texture
                rx, ry = random.randint(70, 130), random.randint(75, 95)
                self.create_oval(rx, ry, rx+2, ry+2, fill="#DDD", outline="")

        def draw_egg_sunny(x=110, y=75):
            self.create_oval(x-20, y-15, x+20, y+15, fill="white", outline="#EEE")
            self.create_oval(x-10, y-8, x+10, y+10, fill="#FFD700", outline="#DAA520")

        # 1. VARIAN NASI
        if "rice bowl" in name:  
            draw_bowl(color="#F5CBA7")
            self.create_oval(60, 75, 140, 115, fill="#FFFDD0", outline="")   
            if "ayam" in name:
                self.create_oval(80, 70, 120, 95, fill="#D35400", outline="#8B4513")
        
        elif "nasi" in name or "rice" in name:
            draw_plate()
            draw_rice_mound(color="#FFFDD0")
            draw_egg_sunny()

        # 2. VARIAN AYAM
        elif "nasi ayam bakar pedas" in name:
            draw_plate()
            draw_rice_mound(color="#FFFDD0")  
            self.create_oval(70, 60, 130, 105, fill="#8B4513", outline="#5D4037")
            for x in range(75, 130, 10):
                self.create_line(x, 65, x+5, 100, fill="#3E2723", width=3)
                self.create_oval(40, 80, 70, 110, fill="#5D9D78", outline="")
                self.create_oval(130, 50, 150, 70, fill="#C0392B", outline="")

        elif "ayam" in name or "chicken" in name:
            draw_plate()
            draw_rice_mound(color="#FFFDD0") # Putih
            self.create_oval(70, 60, 130, 105, fill="#D35400", outline="#B4A296") # Paha
            self.create_rectangle(125, 85, 155, 95, fill="#F5CBA7", outline="") # Tulang
            self.create_oval(40, 80, 70, 110, fill="#5D9D78", outline="") # Sayur
            self.create_oval(130, 50, 150, 70, fill="#C0392B", outline="") # Sambal

        # 3. VARIAN BUBUR
        elif "bubur" in name:  
            draw_bowl(color="#3498DB")
            self.create_oval(50, 65, 150, 85, fill="#FDFEFE", outline="")
            self.create_rectangle(70, 70, 90, 80, fill="#D35400", outline="") 
            self.create_oval(100, 70, 120, 80, fill="#F1C40F", outline="") 
        
        # 4. VARIAN KUAH 
        elif any(x in name for x in ["mie", "bakso", "ramen", "wonton kuah", "tom yum odeng", "spicy tteokbokki"]):
            draw_bowl()
            kuah_col = "#D35400" if "ramen" in name else "#FAD7A0"
            self.create_oval(50, 65, 150, 85, fill=kuah_col, outline="")
        
            if "bakso" in name: # Bola Bakso
                self.create_oval(80, 70, 100, 90, fill="#BDC3C7", outline="#7F8C8D")
                self.create_oval(105, 65, 125, 85, fill="#BDC3C7", outline="#7F8C8D")
            
            self.create_line(60, 70, 90, 80, fill="#2ECC71", width=3) # Sayur
            self.create_line(135, 30, 120, 90, fill="#5D4037", width=3) # Sumpit
            self.create_line(145, 30, 125, 90, fill="#5D4037", width=3)

        # 5. VARIAN DAGING 
        elif any(x in name for x in ["steak", "beef"]):
            draw_plate()
            fill_c = "#5D4037"
            self.create_oval(60, 70, 140, 110, fill=fill_c, outline="black")

        # 6. VARIAN JAPAN FOOD
        elif any(x in name for x in ["onigiri", "takoyaki"]):
            if "onigiri" in name:
                draw_plate()
                self.create_polygon(100, 50, 60, 110, 140, 110,
                                    fill="#FDFEFE", outline="#BDC3C7")
                self.create_rectangle(90, 90, 110, 110,
                                      fill="#2C3E50", outline="")
            else :
                draw_plate()
                for i in range(3):
                    self.create_oval(65 + i*30, 75, 95 + i*30, 105,
                                     fill="#D68910", outline="#A04000")
                self.create_line(60, 85, 150, 95, fill="#FDFEFE", width=3)
                self.create_line(60, 90, 150, 100, fill="#C0392B", width=2)

        # 7. VARIAN MAKANAN RINGAN 
        elif any(x in name for x in ["siomay", "gyoza", "tahu kocek", "lumpia pedas"]):
            draw_plate()
            self.create_oval(50, 80, 150, 115, fill="#873600", outline="") # Bumbu Kacang
            self.create_oval(70, 70, 100, 90, fill="#F1C40F", outline="#D68910") # Siomay
            self.create_rectangle(110, 70, 130, 90, fill="#FDFEFE", outline="#BDC3C7") # Tahu

        elif any(x in name for x in ["fruit sando", "garlic bread", "churros", "spicy paper roll", "spicy corn ribs"]):
            if any(x in name for x in ["churros", "spicy paper roll", "spicy corn ribs"]):
                 self.create_line(60, 60, 140, 120, fill="#F5CBA7", width=30, capstyle="round") # Wrap
                 self.create_line(70, 70, 130, 110, fill="#5D4037", width=5) # Isi
            else: 
                 self.create_arc(60, 90, 140, 130, start=180, extent=180, fill="#E67E22", outline="") # Bots
                 self.create_polygon(60, 90, 140, 90, 100, 100, fill="#F1C40F", outline="") # Cheese
                 self.create_arc(60, 50, 140, 100, start=0, extent=180, fill="#E67E22", outline="") # Top

        elif any(x in name for x in ["roti", "toast", "cheesecuit", "mille crepes", "dimsum mentai", "tahu isi mercon"]):
            draw_plate()
            if "bakar" in name or "toast" in name:
                self.create_rectangle(70, 70, 130, 110, fill="#F5CBA7", outline="#8B4513") # Roti
                self.create_rectangle(75, 75, 125, 105, fill="#5D4037", outline="") # Selai coklat
            elif any(x in name for x in ["mille crepes", "cheesecuit"]):
                self.create_rectangle(60, 90, 140, 110, fill="#F5CBA7", outline="#8B4513")
                self.create_rectangle(60, 70, 140, 90, fill="#5D4037", outline="")
                self.create_rectangle(60, 50, 140, 70, fill="#F5CBA7", outline="#8B4513")
            else: 
                self.create_rectangle(50, 70, 150, 110, fill="#DC9935", outline="#D68910", width=2)
                self.create_line(50, 90, 150, 90, fill="#D68910")

        elif any(x in name for x in ["donat", "cake", "brownies", "mochi", "corndog", "puding vla", "milk bun", "pancake"]):
            if any(x in name for x in ["mochi", "corndog", "milk bun", "pancake"]):
                self.create_oval(80, 70, 120, 100, fill="#F1948A", outline="") # Scoop Pink
                self.create_oval(80, 50, 120, 80, fill="#EEE4BB", outline="") # Scoop Yellow
            elif "donat" in name:
                self.create_oval(60, 60, 140, 120, fill="#D35400", outline="")
                self.create_oval(60, 60, 140, 120, fill="#E91E63", outline="", width=0) # Icing
                self.create_oval(90, 80, 110, 100, fill="#FFF8F0", outline="") # Hole
                for i in range(10): 
                    sx, sy = random.randint(70,130), random.randint(70,110)
                    if 85 < sx < 115 and 75 < sy < 105: continue
                    self.create_line(sx, sy, sx+3, sy, fill=random.choice(["yellow","cyan","white"]), width=2)
            else: 
                draw_plate()
                self.create_polygon(80, 60, 120, 60, 120, 100, 80, 100, fill="#704C04")
                self.create_line(80, 80, 120, 80, fill="#F5CBA7", width=2)
                self.create_oval(95, 55, 105, 65, fill="red", outline="")

        elif any(x in name for x in ["jasuke", "salad", "yogurt", "cilok", "zuppa soup", "cuanki", "rujak cireng kuah"]):
            draw_bowl(color="#F8F9F9")
            if "jasuke" in name or "zuppa soup" in name :
                self.create_oval(60, 70, 140, 110, fill="#F7DC6F", outline="")  # jagung
                for _ in range(3):
                    self.create_line(65, 80 + _*5, 135, 85 + _*5, fill="white", width=3)
            elif "salad" in name:
                for i in range(5):
                    x = random.randint(60, 140)
                    y = random.randint(60, 110)
                    self.create_oval(x, y, x+25, y+15, fill="#27AE60", outline="")
                self.create_oval(85, 80, 105, 100, fill="#E74C3C", outline="")  # tomat
                self.create_oval(110, 85, 125, 95, fill="#F4D03F", outline="") # jagung        
            elif "yogurt" in name:
                self.create_oval(60, 70, 140, 110, fill="#FDFEFE", outline="")
                fruits = ["#E74C3C", "#F7DC6F", "#5DADE2"]
                for i in range(4):
                    x = random.randint(70, 130)
                    y = random.randint(70, 100)
                    self.create_oval(x, y, x+15, y+15, fill=random.choice(fruits), outline="")
            else :
                for i in range(3):
                    self.create_oval(70 + i*25, 80, 90 + i*25, 100,
                                     fill="#D5D8DC", outline="#AAB7B8")
                self.create_line(70, 90, 140, 95, fill="#F5CBA7", width=4)

        elif "croissant" in name: 
            draw_plate()
            self.create_arc(60, 70, 140, 130, start=30, extent=300, fill="#F5CBA7", outline="#D68910", width=3)
            self.create_oval(80, 80, 95, 95, fill="#E74C3C", outline="")
            self.create_oval(105, 90, 120, 105, fill="#F4D03F", outline="")

        # 8. DEFAULT (Hanya jika makanan benar-benar tidak dikenal)
        else:
            self.create_oval(40, 110, 160, 130, fill="#BDC3C7", outline="") 
            self.create_arc(50, 50, 150, 130, start=0, extent=180, fill="#95A5A6", outline="#7F8C8D", width=2)
            self.create_oval(95, 45, 105, 55, fill="#7F8C8D", outline="")
            self.create_text(100, 90, text="?", font=("Arial", 40, "bold"), fill="white")

# ============== PAGES ==============
 
nama_user = ""

class Splash(c.CTkFrame):
    def __init__(self, master, go_cb):
        super().__init__(master, fg_color="transparent")
        bg(self, "bg_splash.jpg")

        c.CTkButton(
            self,
            text="TAP TO START",
            width=220,
            height=50,
            corner_radius=24,
            fg_color="#5C381E",
            hover_color="#8A6040",
            font=("Poppins", 16, "bold"),
            command=lambda: (play(), go_cb())
        ).place(relx=0.5, rely=0.58, anchor="center")

class Menu(c.CTkFrame):
    def __init__(self, master, quiz_cb):
        super().__init__(master, fg_color="transparent")
        bg(self, "bg_menu.jpg")

        self.entry_nama = c.CTkEntry(
            self, placeholder_text="type here", width=230, height=40, 
            corner_radius=18, font=("Poppins", 14)
        )
        self.entry_nama.place(relx=0.5, rely=0.45, anchor="center")
        
        c.CTkButton(
            self,
            text="CONTINUE",
            command=lambda: (play(), self.simpan_nama(quiz_cb)),
            width=180,
            height=44,
            corner_radius=24,
            fg_color="#5C381E",
            hover_color="#8A6040",
            font=("Poppins", 16, "bold"),
        ).place(relx=0.5, rely=0.55, anchor="center")

    def simpan_nama(self, quiz_cb):
        global nama_user
        nama_user = self.entry_nama.get().strip()
        
        if nama_user == "":
            self.shake_entry(); return
        quiz_cb()

    def shake_entry(self):
        for o in [0.02, -0.02, 0.01, -0.01, 0]:
            self.entry_nama.place(relx=0.5+o, rely=0.45, anchor="center")
            self.update(); time.sleep(0.05)
        self.entry_nama.place(relx=0.5, rely=0.45, anchor="center")
        
class Quiz(c.CTkFrame):
    def __init__(self, master, res_cb):
        super().__init__(master, fg_color="transparent")
        bg(self, "bg_quiz.jpg")

        self.content_frame = c.CTkFrame(
            self, width=350, height=330, fg_color="#FFF8F0", 
            corner_radius=30, border_width=3, border_color="#5C381E"
        )
        self.content_frame.pack_propagate(False)

        self.target_rely, self.current_rely = 0.5, 0.58
        self.content_frame.place(relx=0.5, rely=self.current_rely, anchor="center")

        self.Q = [("rasa","Rasa:",[("pedas","Pedas"),("manis","Manis"),("gurih","Gurih")]),
                  ("budget","Budget:",[("murah","Murah"),("sedang","Sedang"),("mahal","Mahal")]),
                  ("cuaca","Cuaca:",[("panas","Panas"),("dingin","Dingin"),("hujan","Hujan")]),
                  ("porsi","Porsi:",[("ringan","Ringan"),("berat","Berat")])
        ]

        self.idx = 0
        self.ans = {}
        self.res_cb = res_cb

        self.counter_lbl = c.CTkLabel(
            self.content_frame,  text="",
            font=("Poppins", 14, "bold"),
            text_color="white",
            fg_color="#8A6040",      
            corner_radius=24,
            width=100,
            height=30
        )
        self.counter_lbl.pack(pady=(25,10))

        self.title_lbl = c.CTkLabel(
            self.content_frame, text="",
            font=("Poppins", 16, "bold"), #5C381E #8A6040
            text_color="#5C381E",
            fg_color="transparent"
        )
        self.title_lbl.pack(pady=(0, 25))

        self.btn_content_frame = c.CTkFrame(self.content_frame, fg_color="transparent")
        self.btn_content_frame.pack()
        self.load_quiz()

    def load_quiz(self):
        for w in self.btn_content_frame.winfo_children(): 
            w.destroy()
        k, title, opts = self.Q[self.idx]
        self.counter_lbl.configure(text=f"{self.idx+1}/{len(self.Q)}")
        self.title_lbl.configure(text=title)
        for val, label in opts:
            this_key = k
            btn = c.CTkButton(
                self.btn_content_frame,
                text=label,
                width=300,
                height=50,
                corner_radius=24,
                fg_color="#5C381E",
                hover_color="#8A6040", 
                font=("Poppins", 17, "bold"),
                command=lambda v=val, key=this_key: self.next_answer(k, v)
            )
            btn.pack(pady=5)

    def next_answer(self, key, val):
        play()
        # store answer
        self.ans[key] = val
        self.idx += 1
        if self.idx >= len(self.Q):
            self.res_cb(self.ans)
        else:
            self.load_quiz()

class Result(c.CTkFrame):
    def __init__(self, master, ans, menu_cb):
        super().__init__(master, fg_color="transparent")
        bg(self, "bg_result.jpg")

        global nama_user
        M = get_match(ans) or {}

        self.content_frame = c.CTkFrame(
            self, width=300, height=550, fg_color="#FFF8F0", corner_radius=30, 
            border_width=3, border_color="#5C381E"
        )
        self.content_frame.pack_propagate(False)
        self.target_rely, self.current_rely = 0.5, 1.3 
        self.content_frame.place(relx=0.5, rely=self.current_rely, anchor="center")

        c.CTkLabel(
            self.content_frame,
            text=f"Haiii {nama_user}!",
            font=("Poppins", 16, "bold"),
            text_color="#5C381E"
        ).pack(pady=(25,0))

        food_name = M.get("nama", "Makanan").title()
        self.art_canvas = FoodArtist(self.content_frame, food_name, width=200, height=130)
        self.art_canvas.pack(pady=(0, 0))

        c.CTkLabel(
            self.content_frame, 
            text=food_name, 
            font=("Poppins", 24, "bold"), 
            text_color="#5C381E", 
            wraplength=320, justify="center"
        ).pack(pady=(0, 0))

        c.CTkLabel(
            self.content_frame, 
            text="⭐" * 5 , 
            font=("Segoe UI Emoji", 14)
        ).pack(pady=(0, 5))

        info_box = c.CTkFrame(self.content_frame, fg_color="transparent")
        info_box.pack(pady=0)
        self.create_badge(info_box, f"{M.get('harga','-')}", "#DDCAB0", "#6A481F")
        self.create_badge(info_box, f"{M.get('porsi','-')}", "#DDCAB0", "#6A481F")

        c.CTkLabel(
            self.content_frame, 
            text=f'"{M.get("deskripsi","-")}"', 
            font=("Poppins", 12, "italic"), 
            text_color="#555", 
            wraplength=340, justify="center"
        ).pack(pady=(10, 10))

        c.CTkLabel(self.content_frame, text="📊 Informasi Gizi", font=("Poppins", 12, "bold"), text_color="#8A6040").pack(pady=(0, 5))
        nut_frame = c.CTkFrame(self.content_frame, fg_color="transparent")
        nut_frame.pack(pady=(0, 10))
        nuts_data = [("Kalori", M.get("kalori","-"), "#EBCAB0", "#74251C"), ("Karbo", M.get("karbo","-"), "#FCF3CF", "#6B5233"),
                     ("Protein", M.get("protein","-"), "#FCF3CF", "#6B5233"), ("Lemak", M.get("lemak","-"), "#EBCAB0", "#74251C")]
        
        for i, (label, val, bg_c, txt_c) in enumerate(nuts_data):
            card = c.CTkFrame(nut_frame, width=75, height=65, fg_color=bg_c, corner_radius=15)
            card.grid(row=i//2, column=i%2, padx=5, pady=5); card.pack_propagate(False)
            c.CTkLabel(card, text=val, font=("Poppins", 13, "bold"), text_color=txt_c).pack(pady=(0, 0))
            c.CTkLabel(card, text=label, font=("Poppins", 10, "bold"), text_color=txt_c).pack(pady=(0, 0))

        btn_frame = c.CTkFrame(self.content_frame, fg_color="transparent")
        btn_frame.pack(side="bottom", pady=20)
        
        c.CTkButton(
            btn_frame, text="BACK", width=100, height=40, 
            corner_radius=20, fg_color="#AC8465", hover_color="#5C381E", 
            font=("Poppins", 13, "bold"), command=lambda: (play(), menu_cb())
        ).pack(side="left", padx=5)
        c.CTkButton(
            btn_frame, text="EXIT", width=100, height=40, 
            corner_radius=20, fg_color="#E37165", hover_color="#922B21", 
            font=("Poppins", 13, "bold"), command=lambda: sys.exit()
        ).pack(side="left", padx=5)
        
        self.animate_entry()

    def create_badge(self, parent, text, bg_col, txt_col):
        f = c.CTkFrame(parent, fg_color=bg_col, corner_radius=15)
        f.pack(side="left", padx=5)
        c.CTkLabel(f, text=text, font=("Poppins", 11, "bold"), text_color=txt_col).pack(padx=10, pady=3)

    def animate_entry(self):
        if self.current_rely > self.target_rely:
            self.current_rely -= max(0.015, (self.current_rely - self.target_rely) * 0.15)
            self.content_frame.place(relx=0.5, rely=self.current_rely, anchor="center")
            self.after(16, self.animate_entry)
        else: self.content_frame.place(relx=0.5, rely=self.target_rely, anchor="center")

# ============== APP CONTROLLER ==============
class App(c.CTk):
    def __init__(self):
        super().__init__()
        W, H = 500, 600
        self.W, self.H = W, H
        self.geometry(f"{W}x{H}")
        self.after(20, lambda: self.geometry(f"{self.W}x{self.H}"))
        self.resizable(False, False)
        self.title("MealMatch")
        self.current = None
        self.after(10, self.show_splash)

        #mengatur presisi
        try:
            icon_path = P_S(DIR, "assets", "bg_splash.jpg")
            if os.path.exists(icon_path): self.wm_iconphoto(True, ImageTk.PhotoImage(PILImage.open(icon_path)))
        except: 
            pass
        
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{W}x{H}+{(sw-W)//2}+{(sh-H)//2}")
        self.current = None; self.after(10, self.show_splash)

    def show(self, frame_class, *args):
        #kalau ada halaman lama dihapus, supaya memori tidak full
        if self.current: 
            try: self.current.destroy() 
            except: pass
        #membuat halaman baru yg disimpan sebagai halaman aktif
        self.current = frame_class(self, *args); self.current.pack(fill="both", expand=True)
    
    def show_splash(self): 
        self.show(Splash, lambda: self.show(Menu, lambda: self.show(Quiz, self.show_result)))
    def show_result(self, ans): 
        self.show(Result, ans, lambda: self.show(Menu, lambda: self.show(Quiz, self.show_result)))

App().mainloop()