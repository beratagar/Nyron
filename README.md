## Nyron

`Nyron`, Borsa İstanbul hisseleri için teknik tarama yapan (varsayılan evren: **BIST 500 / XU500**) masaüstü bir analiz uygulamasıdır. Yahoo Finance verisi üzerinden indikatörleri hesaplar, 0–100 arası skor üretir ve “Al / Tut / Sat” sinyalini özetler.

## Ekran görüntüleri

### Ana ekran (tarama)
![Ana ekran](assets/screenshots/1_anaekran.png)

### Sonuçlar
![Sonuçlar](assets/screenshots/2_sonuclar.png)

### Fırsatlar
![Fırsatlar](assets/screenshots/3_firsatlar.png)

### Detay (hisse ekranı)
![Detay](assets/screenshots/4_detay.png)

## Özellikler

- **Teknik tarama**: RSI, MACD, Bollinger, SMA ve hacim bileşenlerinden birleşik skor (0–100)
- **Sinyal**: `BUY / WAIT / SELL` (arayüzde “Al / Tut / Sat”)
- **Uyumsuzluk uyarıları**: fiyat/hacim/momentum tutarsızlıklarını işaretleme
- **Filtreleme**: sinyal, sektör, RSI/skor aralıkları, trend, hacim/likidite, göreli güç vb.
- **Fırsat merkezi**: model alım listesi + “Neden bu hisse?” açıklaması
- **CSV dışa aktarma**: filtrelenmiş tabloyu UTF-8 CSV olarak kaydetme
- **Hisse detayı**: tabloda çift tık ile uygulama içi detay ekranı (grafik + indikatörler + özet + haber)
- **Tema**: koyu ve aydınlık tema

## Kurulum ve çalıştırma (Windows)

### 1) Tek tık

- `run.bat` çalıştır:
  - Python kontrolü
  - `requirements.txt` kurulumu
  - `logs/` klasörü oluşturma
  - `main.py` başlatma

### 2) Terminal ile

```bash
cd "proje-klasoru"
python -m pip install -r requirements.txt
python main.py
```

## Proje yapısı

- `main.py`: giriş noktası
- `run.bat`: Windows tek tık çalıştırma
- `requirements.txt`: bağımlılıklar
- `config.py`: eşikler/tema/evren ayarları
- `qt_app/`: PySide6 arayüz
- `nyron/`: analiz motoru (veri çekme, indikatör, sinyal, filtreler)
- `data/`: evren cache’i ve yardımcı veriler
- `logs/`: loglar (`logs/app.log`)
- `assets/screenshots/`: ekran görüntüleri

## Evren (BIST 500 / XU500)

Uygulama hisse listesini şu sırayla okur:

1. `data/bist500.txt` (önerilen cache)
2. `data/stocks.txt` (manuel liste)

Dosyalarda her satıra bir sembol yazabilirsiniz (örn. `ASELS` veya `ASELS.IS`).

## Sorun giderme

- **Uygulama kapanıyor / açılmıyor**: `logs/app.log` içindeki “CRITICAL / Traceback” bölümüne bakın.
- **Eksik paket**: `python -m pip install --upgrade pip` ardından `python -m pip install -r requirements.txt`
- **Bazı hisselerde veri yok**: Yahoo Finance bazı semboller için boş/eksik veri döndürebilir; bu durumda uygulama o sembolü atlar.

## Yasal uyarı

Bu uygulama, **öğrenci olarak kişisel eğitim ve kendimi geliştirme** amacıyla hazırlanmıştır.

- Üretilen skorlar/sinyaller/haberler dahil tüm çıktılar **bilgilendirme amaçlıdır**; **yatırım tavsiyesi değildir**.
- Uygulamanın ürettiği sonuçların **doğruluğu, güncelliği, eksiksizliği veya belirli bir amaca uygunluğu hakkında garanti verilmez**.
- Bu uygulama ve çıktıları, **yatırım kararı vermek** veya **alım-satım yapmak** için kullanılmamalıdır.
- Kullanıcı, bu uygulamayı kullanarak aldığı tüm kararların **tam sorumluluğunu** kabul eder; geliştirici **doğrudan/dolaylı hiçbir zarardan sorumlu tutulamaz**.
- Veri kaynağı olarak kullanılan üçüncü taraf servisler (örn. Yahoo Finance) zaman zaman **boş, hatalı veya gecikmeli** veri döndürebilir.

