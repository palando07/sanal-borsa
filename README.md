# Sanal Borsa

Gerçek piyasa fiyatlarıyla, sanal parayla hisse senedi, kripto, altın ve döviz alıp satabileceğin; işlemlerinin gidişatını izleyebileceğin web uygulaması. Telefona "ana ekrana ekle" ile uygulama olarak kurulabilir.

Adres: https://palando07.github.io/sanal-borsa/

## Özellikler

- 100.000 ₺ sanal başlangıç parası, %0,1 komisyon
- BIST 100'deki şirketler, 47 ABD hissesi, 8 endeks fonu (S&P 500, Nasdaq 100, Türkiye, altın, tahvil…), 21 kripto para, dolar, euro, sterlin, frank, gram/ons altın ve gümüş, Brent petrol; üstte BIST 100 endeksi
- Adet veya TL tutarıyla alış/satış; piyasa, limit ve stop (zarar durdur) emirleri
- İzleme listesi (☆) ve fiyat alarmları (uygulama açıkken bildirim)
- Hisse bilgi kartı: önceki kapanış, gün ve 52 haftalık aralık, hacim
- Rehber: temel kavramlar
- Portföy yedeği alma ve geri yükleme (JSON dosyası)
- Haberler: Google Haberler'den piyasa gündemi, portföydeki varlıkların ve her hissenin son haberleri (yarım saatte bir)
- Yatırım günlüğü: her işleme "neden" notu; Performans sekmesinde alış ve satış gerekçeleri sonuçla yan yana
- Portföyü BIST 100 ile karşılaştıran grafik, performans sekmesi ve aylık getiri
- Portföy değeri grafiği, pozisyon bazında kâr/zarar, gerçekleşen K/Z ve işlem geçmişi
- Portföy yalnızca kullanılan cihazda (tarayıcıda) saklanır

## Fiyatlar nereden geliyor

- **Hisse, döviz, altın:** `.github/workflows/prices.yml` yarım saatte bir başlar ve yaklaşık 50 dakika boyunca 5 dakikada bir `scripts/fetch_prices.py` dosyasını çalıştırır. Betik Yahoo Finance'ten son 5 günün fiyatlarını alıp `data` dalındaki `prices.json` dosyasına yazar; uygulama bu dosyayı okur. Borsa verileri ayrıca 15 dakikaya kadar gecikmeli olabilir.
- **Kripto:** Uygulama Binance'ten 15 saniyede bir canlı fiyat alır. Binance'e ulaşılamazsa 5 dakikalık veriler kullanılır.
- Gram altın ve gümüş, ons fiyatı × USD/TRY ÷ 31,10 ile hesaplanır.
- Piyasa kapalıyken işlemler son fiyattan gerçekleşir.
- Limit ve stop emirleri uygulama açıkken kontrol edilir. Uygulama kapalıyken fiyat emrin seviyesine geldiyse (5 günlük 30 dakikalık seriye göre), emir uygulama açıldığında o seviyeden gerçekleşir.

GitHub, 60 gün boyunca hiç commit gelmeyen herkese açık depolarda zamanlanmış iş akışlarını durdurur. Fiyatlar güncellenmeyi bırakırsa Actions sekmesinden iş akışını yeniden etkinleştirmek yeterli.
