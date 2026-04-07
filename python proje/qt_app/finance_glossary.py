# -*- coding: utf-8 -*-
"""Finans ve teknik analiz terimleri — şık görünümlü Türkçe rehber."""

from __future__ import annotations


def glossary_html(dark: bool) -> str:
    a = "#3dd9a8" if dark else "#0d9f73"
    a2 = "#6b9fff" if dark else "#1d4ed8"
    muted = "#94a3b8" if dark else "#64748b"
    text = "#e8eef4" if dark else "#0f172a"
    card_bg = "#121922" if dark else "#ffffff"
    card_bd = "#2d3d52" if dark else "#cbd5e1"
    soft = "#0e141c" if dark else "#f1f5f9"
    gold = "#e8c872" if dark else "#b45309"

    return f"""
<html><head><meta charset="utf-8"/></head>
<body style="margin:0;padding:0;font-family:'Segoe UI',Tahoma,sans-serif;color:{text};font-size:14px;line-height:1.55;">

<p style="color:{muted};font-size:12px;margin:0 0 18px 0;padding:12px 14px;background:{soft};border-radius:10px;border:1px solid {card_bd};">
<b style="color:{gold};">Önemli:</b> Bu metinler yatırım tavsiyesi değildir. İngilizce terimleri anlamanıza yardımcı olmak için özet bilgi sunar; kararlarınızı kendi riskinize göre verin.
</p>

<p style="font-size:13px;color:{muted};margin:0 0 20px 0;">
Aşağıda uygulamada sık geçen kavramlar, <b style="color:{a};">kısa tanım</b> ve <b style="color:{a2};">pratik not</b> ile gruplanmıştır. Ok tuşları veya kaydırma ile gezinebilirsiniz.
</p>

<div style="border:1px solid {card_bd};border-radius:12px;padding:14px 16px;margin-bottom:20px;background:{card_bg};">
<h3 style="margin:0 0 10px 0;color:{a};font-size:15px;letter-spacing:0.04em;">Hızlı indeks</h3>
<p style="margin:0;font-size:12px;color:{muted};line-height:1.8;">
Fiyat/Hacim · RSI · MACD · Bollinger · SMA/EMA · ATR · Hacim · Göreli güç · Skor · Sinyal · Trend · Uyumsuzluk ·
Destek/Direnç · Volatilite · Mum · Gap · Beta · Piyasa değeri · Likidite · Spread · CSV
</p>
</div>

<div style="border:1px solid {card_bd};border-radius:14px;padding:16px 18px;margin:14px 0;background:{card_bg};">
<h3 style="margin:0 0 8px 0;color:{a2};font-size:16px;">Fiyat ve hacim (açılış–kapanış)</h3>
<p style="margin:0;"><b>Açılış, en yüksek, en düşük, kapanış ve hacim</b> — Günlük (veya seçilen periyotta) fiyatın hareket aralığı ve işlem hacmidir. Grafik ve tabloların temel yapı taşlarıdır.</p>
<p style="margin:10px 0 0 0;color:{muted};font-size:13px;"><b>Pratik:</b> Kapanış, çoğu göstergede «son fiyat» olarak kullanılır; hacim, hareketin arkasında gerçek ilgi olup olmadığına dair ipucu verir.</p>
</div>

<div style="border:1px solid {card_bd};border-radius:14px;padding:16px 18px;margin:14px 0;background:{card_bg};">
<h3 style="margin:0 0 8px 0;color:{a2};font-size:16px;">RSI (Relative Strength Index)</h3>
<p style="margin:0;">Son dönemdeki kazanç ve kayıpları ölçerek 0–100 arası bir momentum göstergesi üretir. Literatürde 70 üstü «aşırı alım», 30 altı «aşırı satım» bölgesi diye anlatılır.</p>
<p style="margin:10px 0 0 0;color:{muted};font-size:13px;"><b>Pratik:</b> Güçlü trendlerde RSI uzun süre uç bölgelerde kalabilir; tek başına al/sat emri sayılmamalı, fiyat yapısı ve hacimle birlikte düşünülmelidir.</p>
</div>

<div style="border:1px solid {card_bd};border-radius:14px;padding:16px 18px;margin:14px 0;background:{card_bg};">
<h3 style="margin:0 0 8px 0;color:{a2};font-size:16px;">MACD</h3>
<p style="margin:0;"><b>Moving Average Convergence Divergence</b> — İki üssel hareketli ortalamanın farkından türeyen trend ve momentum göstergesi. Sinyal çizgisi ve histogram ile kesişimler ve sapmalar yorumlanır.</p>
<p style="margin:10px 0 0 0;color:{muted};font-size:13px;"><b>Pratik:</b> Sıfır çizgisinin üstü/altı trend eğilimini; histogram daralması momentumun zayıfladığı fikrini verebilir.</p>
</div>

<div style="border:1px solid {card_bd};border-radius:14px;padding:16px 18px;margin:14px 0;background:{card_bg};">
<h3 style="margin:0 0 8px 0;color:{a2};font-size:16px;">Bollinger bantları (BB)</h3>
<p style="margin:0;">Ortada bir hareketli ortalama; üst ve alt bantlar volatiliteye göre genişler veya daralır. Fiyatın bantlara göre konumu oynaklık ve aşırı hareket hakkında fikir verir.</p>
<p style="margin:10px 0 0 0;color:{muted};font-size:13px;"><b>Pratik:</b> Bant daralması sıkça «hareket öncesi sıkışma» olarak okunur; yönü tek başına söylemez.</p>
</div>

<div style="border:1px solid {card_bd};border-radius:14px;padding:16px 18px;margin:14px 0;background:{card_bg};">
<h3 style="margin:0 0 8px 0;color:{a2};font-size:16px;">SMA / EMA</h3>
<p style="margin:0;"><b>Basit / Üssel hareketli ortalama</b> — Basit ortalama tüm günlere eşit ağırlık verir; üssel ortalama son günlere daha fazla ağırlık verir. Trend, destek/direnç ve kesişim stratejilerinde kullanılır.</p>
<p style="margin:10px 0 0 0;color:{muted};font-size:13px;"><b>Pratik:</b> «SMA 20 / 50 / 200» gibi ifadeler periyot uzunluğudur; kısa periyot daha hızlı, uzun periyot daha yavaş tepki verir.</p>
</div>

<div style="border:1px solid {card_bd};border-radius:14px;padding:16px 18px;margin:14px 0;background:{card_bg};">
<h3 style="margin:0 0 8px 0;color:{a2};font-size:16px;">ATR (Average True Range)</h3>
<p style="margin:0;">Gerçek aralığın ortalaması; volatilite ölçüsüdür. Yön göstermez; «fiyat tipik olarak gün içinde ne kadar salınıyor?» sorusuna yaklaşık cevap verir.</p>
<p style="margin:10px 0 0 0;color:{muted};font-size:13px;"><b>Pratik:</b> Stop mesafesi veya pozisyon büyüklüğü düşünülürken referans alınabilir; mutlak doğru mesafe değildir.</p>
</div>

<div style="border:1px solid {card_bd};border-radius:14px;padding:16px 18px;margin:14px 0;background:{card_bg};">
<h3 style="margin:0 0 8px 0;color:{a2};font-size:16px;">Hacim (Volume)</h3>
<p style="margin:0;">İşlem gören pay adedi. Yükseliş veya düşüşte hacmin artması, hareketin «onayı» olarak yorumlanabilir.</p>
<p style="margin:10px 0 0 0;color:{muted};font-size:13px;"><b>Pratik:</b> «Hacim ×» ifadesi çoğu zaman son güne göre son X gün ortalama hacmine oranıdır; düşük hacimli hareketler yanıltıcı olabilir.</p>
</div>

<div style="border:1px solid {card_bd};border-radius:14px;padding:16px 18px;margin:14px 0;background:{card_bg};">
<h3 style="margin:0 0 8px 0;color:{a2};font-size:16px;">Göreli güç (RS, endekse göre)</h3>
<p style="margin:0;">Hisse getirisi ile seçilen endeks getirisi karşılaştırılır. Pozitif değer, dönem içinde endekse göre daha güçlü kapanış performansına işaret edebilir.</p>
<p style="margin:10px 0 0 0;color:{muted};font-size:13px;"><b>Pratik:</b> Endeks yükselirken hissenin geride kalması «göreli zayıflık» olarak okunabilir; tek başına kalite yargısı değildir.</p>
</div>

<div style="border:1px solid {card_bd};border-radius:14px;padding:16px 18px;margin:14px 0;background:{card_bg};">
<h3 style="margin:0 0 8px 0;color:{a2};font-size:16px;">Skor (0–100)</h3>
<p style="margin:0;">Uygulamada birden fazla göstergenin ağırlıklı birleşiminden üretilen otomatik teknik skor. Yüksek değer, modelin kriterlerine göre daha uyumlu bir tablo olduğu fikrini verir.</p>
<p style="margin:10px 0 0 0;color:{muted};font-size:13px;"><b>Pratik:</b> Skor garanti veya kesin getiri anlamına gelmez; piyasa haberi, bilanço ve risk iştahı ayrı boyutlardır.</p>
</div>

<div style="border:1px solid {card_bd};border-radius:14px;padding:16px 18px;margin:14px 0;background:{card_bg};">
<h3 style="margin:0 0 8px 0;color:{a2};font-size:16px;">Sinyal (Al / Tut / Sat)</h3>
<p style="margin:0;">Modelin özet çıktısıdır. «Güçlü al» gibi ifadeler skorun uç bölgelerinde otomatik metin zenginleştirmesi olabilir.</p>
<p style="margin:10px 0 0 0;color:{muted};font-size:13px;"><b>Pratik:</b> Aracı kurum emri veya kişisel yatırım tavsiyesi değildir; kendi kurallarınızla doğrulamanız gerekir.</p>
</div>

<div style="border:1px solid {card_bd};border-radius:14px;padding:16px 18px;margin:14px 0;background:{card_bg};">
<h3 style="margin:0 0 8px 0;color:{a2};font-size:16px;">Trend etiketi</h3>
<p style="margin:0;">Hareketli ortalamalar ve fiyatın göreli konumuna göre üretilen kısa özet (ör. yükseliş baskısı, düşüş baskısı).</p>
<p style="margin:10px 0 0 0;color:{muted};font-size:13px;"><b>Pratik:</b> Tek satırlık özet; ters dönüşleri veya kısa vadeli gürültüyü göstermeyebilir.</p>
</div>

<div style="border:1px solid {card_bd};border-radius:14px;padding:16px 18px;margin:14px 0;background:{card_bg};">
<h3 style="margin:0 0 8px 0;color:{a2};font-size:16px;">Uyumsuzluk / anomali</h3>
<p style="margin:0;">Fiyat yönü ile momentum veya hacim birbirinden ayrıştığında ortaya çıkan uyarı kavramıdır (ör. fiyat yeni tepe yaparken RSI yapmayabilir).</p>
<p style="margin:10px 0 0 0;color:{muted};font-size:13px;"><b>Pratik:</b> Uyumsuzluk «hemen döner» anlamına gelmez; onay için başka göstergeler ve yapı faydalıdır.</p>
</div>

<div style="border:1px solid {card_bd};border-radius:14px;padding:16px 18px;margin:14px 0;background:{card_bg};">
<h3 style="margin:0 0 8px 0;color:{a2};font-size:16px;">Destek / direnç</h3>
<p style="margin:0;"><b>Support / Resistance</b> — Fiyatın geçmişte alıcı veya satıcı baskısıyla tepki verdiği bölgeler. Teknik analizde psikolojik seviyeler de bu kavramla ilişkilendirilir.</p>
<p style="margin:10px 0 0 0;color:{muted};font-size:13px;"><b>Pratik:</b> Kırılım sonrası eski direnç bazen desteğe döner (rol değişimi); her zaman gerçekleşmez.</p>
</div>

<div style="border:1px solid {card_bd};border-radius:14px;padding:16px 18px;margin:14px 0;background:{card_bg};">
<h3 style="margin:0 0 8px 0;color:{a2};font-size:16px;">Volatilite</h3>
<p style="margin:0;"><b>Volatility</b> — Fiyatın zaman içinde ne kadar sallandığı. Yüksek volatilite, daha geniş fiyat aralıkları ve risk algısı anlamına gelebilir.</p>
<p style="margin:10px 0 0 0;color:{muted};font-size:13px;"><b>Pratik:</b> ATR ve Bollinger genişliği volatilite okumalarında sık kullanılır.</p>
</div>

<div style="border:1px solid {card_bd};border-radius:14px;padding:16px 18px;margin:14px 0;background:{card_bg};">
<h3 style="margin:0 0 8px 0;color:{a2};font-size:16px;">Mum (candlestick)</h3>
<p style="margin:0;">Açılış–kapanış gövdesi ve gölge çubuklarıyla bir periyodu gösterir. Yeşil/kırmızı (veya boş/dolu) renklendirme platforma göre değişir.</p>
<p style="margin:10px 0 0 0;color:{muted};font-size:13px;"><b>Pratik:</b> Uzun gövde güçlü kapanış; uzun alt gölge satış sonrası alım denemesi fikri verebilir — bağlam şarttır.</p>
</div>

<div style="border:1px solid {card_bd};border-radius:14px;padding:16px 18px;margin:14px 0;background:{card_bg};">
<h3 style="margin:0 0 8px 0;color:{a2};font-size:16px;">Gap (boşluk)</h3>
<p style="margin:0;">Bir önceki kapanış ile yeni açılış arasında fiyat boşluğu. Haber veya açılışta yoğun emir ile oluşabilir.</p>
<p style="margin:10px 0 0 0;color:{muted};font-size:13px;"><b>Pratik:</b> «Boşluğu doldurma» sık anlatılır; her gap kapanmak zorunda değildir.</p>
</div>

<div style="border:1px solid {card_bd};border-radius:14px;padding:16px 18px;margin:14px 0;background:{card_bg};">
<h3 style="margin:0 0 8px 0;color:{a2};font-size:16px;">Beta</h3>
<p style="margin:0;">Hisse getirisinin piyasa (endeks) getirisine göre duyarlılığının ölçüsü. Beta 1’den büyükse endekse göre daha oynak kabul edilir.</p>
<p style="margin:10px 0 0 0;color:{muted};font-size:13px;"><b>Pratik:</b> Bu uygulamada her tabloda yer almayabilir; genel finans sözlüğü için verilmiştir.</p>
</div>

<div style="border:1px solid {card_bd};border-radius:14px;padding:16px 18px;margin:14px 0;background:{card_bg};">
<h3 style="margin:0 0 8px 0;color:{a2};font-size:16px;">Piyasa değeri & likidite</h3>
<p style="margin:0;"><b>Market cap</b> fiyat × dolaşımdaki pay; <b>likidite</b> ise pozisyonu büyük kaydırmadan alıp satabilme kolaylığıdır.</p>
<p style="margin:10px 0 0 0;color:{muted};font-size:13px;"><b>Pratik:</b> Düşük likiditeli hisselerde spread açılabilir; teknik sinyaller yanılabilir.</p>
</div>

<div style="border:1px solid {card_bd};border-radius:14px;padding:16px 18px;margin:14px 0;background:{card_bg};">
<h3 style="margin:0 0 8px 0;color:{a2};font-size:16px;">Spread (alış–satış farkı)</h3>
<p style="margin:0;">En iyi alış ile en iyi satış kotası arasındaki fark. Dar spread likiditenin iyi olduğu zamanlarda görülür.</p>
</div>

<div style="border:1px solid {card_bd};border-radius:14px;padding:16px 18px;margin:14px 0;background:{card_bg};">
<h3 style="margin:0 0 8px 0;color:{a2};font-size:16px;">CSV</h3>
<p style="margin:0;"><b>Comma-Separated Values</b> — Tablo verisinin metin dosyası; Excel ve benzeri yazılımlarda açılır. Uygulamada UTF-8 ile dışa aktarım sunulur.</p>
</div>

<p style="margin:24px 0 8px 0;padding-top:16px;border-top:1px solid {card_bd};color:{muted};font-size:12px;text-align:center;">
Nyron · Terimler rehberi · Düzenli olarak güncellenebilir
</p>

</body></html>
"""


def apply_glossary_browser_style(browser, dark: bool) -> None:
    browser.setHtml(glossary_html(dark))
    if dark:
        browser.setStyleSheet(
            "QTextBrowser { background-color: #0a0e14; color: #e8eef4; border: none; "
            "border-radius: 0px; padding: 18px 22px; font-size: 14px; selection-background-color: #243548; }"
        )
    else:
        browser.setStyleSheet(
            "QTextBrowser { background-color: #f8fafc; color: #0f172a; border: none; "
            "border-radius: 0px; padding: 18px 22px; font-size: 14px; selection-background-color: #bfdbfe; }"
        )


def build_glossary_widget(parent, dark: bool):
    from PySide6.QtWidgets import QFrame, QLabel, QTextBrowser, QVBoxLayout, QWidget

    root = QWidget(parent)
    root_lay = QVBoxLayout(root)
    root_lay.setContentsMargins(0, 0, 0, 0)
    root_lay.setSpacing(0)

    shell = QFrame()
    shell.setObjectName("glossaryPremiumShell")
    sh_lay = QVBoxLayout(shell)
    sh_lay.setContentsMargins(14, 14, 14, 14)
    sh_lay.setSpacing(0)

    head = QFrame()
    head.setObjectName("glossaryPremiumHead")
    hl = QVBoxLayout(head)
    hl.setContentsMargins(20, 18, 20, 16)
    hl.setSpacing(6)
    t_main = QLabel("Terimler rehberi")
    t_main.setObjectName("glossaryPremiumTitle")
    t_sub = QLabel("Nyron teknik tarama · Gelişmiş sözlük ve gösterge kılavuzu")
    t_sub.setObjectName("glossaryPremiumSub")
    t_sub.setWordWrap(True)
    hl.addWidget(t_main)
    hl.addWidget(t_sub)
    sh_lay.addWidget(head)

    accent = QFrame()
    accent.setObjectName("glossaryPremiumAccentBar")
    accent.setFixedHeight(3)
    sh_lay.addWidget(accent)

    browser = QTextBrowser()
    browser.setReadOnly(True)
    browser.setOpenExternalLinks(False)
    apply_glossary_browser_style(browser, dark)

    inner = QFrame()
    inner.setObjectName("glossaryPremiumBody")
    il = QVBoxLayout(inner)
    il.setContentsMargins(8, 8, 8, 12)
    il.addWidget(browser, 1)
    sh_lay.addWidget(inner, 1)

    root_lay.addWidget(shell, 1)
    return root, browser
