CAM Profile Generator (Django)

Çok segmentli CAM hareket profili üretici.
Mutlak zaman (100 birim = 1.00 s) ve mutlak pozisyon (mm) tablosu girersin; sistem her satırı bir segment bitişi olarak yorumlar, arayı S-curve (quintic) ile örnekler, Position / Velocity / Acceleration grafiklerini çizer ve CSV indirmeni sağlar.



✨ Özellikler

Tablo sütunları: Time [unit] (absolute), Position [mm] (absolute), Lambda (0–1), C (0–1), Motion Profile

İstediğin kadar satır ekle/sil (her satır bir segment bitişi)

100 unit = 1.00 s zaman ölçeği

Dwell yapmak için aynı pozisyonda yeni satır ekle (ör. 200, 500 → 300, 500)

λ (Lambda) ile tepe hızın konumunu (merkezini), C ile eğrinin keskinliğini ayarla

Grafikler: Position, Velocity, Acceleration (PNG olarak sayfada)

CSV dışa aktarma (örneklenmiş birleşik profil, zaman/konum/hız/ivme/jerk)

Basit, tek sayfalık form arayüzü (Django template)

🧰 Teknolojiler

Python 3.13+

Django 5.x

NumPy, Pandas, Matplotlib

🚀 Hızlı Başlangıç (Windows / VS Code)
cd C:\Projects
git clone https://github.com/<kullanıcı-adın>/<repo-adın>.git camweb
cd camweb

# Sanal ortam
& "C:\Python313\python.exe" -m venv .venv
.\.venv\Scripts\Activate.ps1

# Bağımlılıklar
python -m pip install --upgrade pip
pip install -r requirements.txt   # yoksa: pip install django numpy pandas matplotlib

# Çalıştır
python manage.py migrate
python manage.py runserver


Tarayıcı: http://127.0.0.1:8000/

PowerShell “activation policy” hatası alırsan:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass ardından .venv’i yeniden etkinleştir.

🧑‍💻 Kullanım

Tabloya segment bitişlerini gir:

Time [unit] (absolute): 100 ⇒ 1.00 s, 200 ⇒ 2.00 s…

Position [mm] (absolute): 0 ⇒ orijin, 500 ⇒ 500 mm…

Lambda (λ): 0.0–1.0 (tepe hızın yeri; 0.5 = ortada)

C: 0.0–1.0 (0 = lineere yakın, 1 = tam S-eğrisi)

Çiz: Grafikler oluşur; CSV İndir ile veriyi indir.

Örnek (ileri → dwell → geri):

Time	Position	λ	C	Profile
100	500	0.5	1.0	Polynomial of 5th degree
200	500	0.5	1.0	Straight line
300	0	0.5	1.0	Polynomial of 5th degree
🔩 Mimari Notları

Absolute → Delta Dönüşümü:
Frontend mutlak zaman/pozisyon gönderir; backend convert_absolute_rows() bunları süre (Δt) ve artış (Δx)’e çevirir.

Zaman Ölçeği: TIME_UNITS_PER_SECOND = 100.0 (utils.py)

Profil: Quintic smoothstep + yumuşak λ zaman bükmesi. C ile lineer ↔ S-curve karışımı.

Türevler: np.gradient(x, t) ile hız/ivme; segment geçişinde duplicate zaman örnekleri düşürülür.

🔗 API Uçları

POST /generate/
Gövde (JSON):

{
  "rows": [
    {"Time": 100, "Position": 500, "Lambda": 0.5, "C": 1.0, "Motion Profile": "Polynomial of 5th degree"},
    {"Time": 200, "Position": 500, "Lambda": 0.5, "C": 1.0, "Motion Profile": "Straight line"}
  ],
  "npts_per_seg": 100
}


Yanıt: { ok, preview, img1, img2, img3 } (grafikler Base64 PNG, tablo ilk 100 satır).

GET /export_csv/
Son üretilen profilin CSV çıktısı.

CSRF: Template içinde {% csrf_token %} gizli alanı var, fetch header’ına X-CSRFToken eklenir.

📁 Dizin Yapısı
camweb/
├─ manage.py
├─ config/
│  ├─ settings.py
│  ├─ urls.py
├─ camapp/
│  ├─ templates/camapp/index.html
│  ├─ utils.py
│  ├─ views.py
│  └─ urls.py
└─ requirements.txt


requirements.txt (önerilen):

Django>=5.0
numpy
pandas
matplotlib