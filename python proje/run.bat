@echo off
chcp 65001 > nul
title BORSA İSTANBUL HİSSE ANALIZ SİSTEMİ

REM Her zaman bu .bat dosyasının klasöründen çalış
cd /d "%~dp0"

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║  📊 BORSA İSTANBUL HİSSE ANALIZ SİSTEMİ                  ║
echo ║  Teknik Analiz + Anomaly Detection + GUI                 ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Python kontrolünü yapar
python --version > nul 2>&1
if errorlevel 1 (
    echo ❌ HATA: Python yüklü değil!
    echo Lütfen Python 3.8+ kurun: https://www.python.org
    pause
    exit /b 1
)

REM requirements kontrol edilir ve gerekli paketler kurulur
echo ⏳ Bağımlılıklar kontrol ediliyor...
python -m pip install -q -r requirements.txt > nul 2>&1

if errorlevel 1 (
    echo ⚠️  Bağımlılıklar kurulurken hata oluştu, yine de devam ediliyor...
)

REM Gerekli klasörleri oluştur
if not exist "logs" mkdir logs

REM
echo.
echo ✅ Uygulama başlatılıyor...
echo.

python main.py
if errorlevel 1 py -3 main.py

if errorlevel 1 (
    echo.
    echo ❌ Uygulama hatası ile kapandı.
    echo Hata detayları: logs/app.log
    pause
)
