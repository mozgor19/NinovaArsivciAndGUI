# Ninova Arşivci v4.0 (GUI Version)

Ninova Arşivci, [Ninova](https://ninova.itu.edu.tr/)'daki dosyaları topluca indirmek için yazılmış bir Python programıdır.  
(Ninova: İstanbul Teknik Üniversitesinin e-öğrenim merkezi)

## v4.0 Özellikler

- Artık main.py dosyası terminal üzerinden değil arayüz üzerinden ders seçimine olanak sağlıyor.
- Uygulama sınıf yapısı üzerinden yeniden tasarlandı.
- Terminal üzerinden çalışma özelliği kaldırıldığı için komut satırı özellikleri devre dışı bırakıldı.

### Bir Sonraki Sürüm (v4.5) için Planlananlar

- Dosyaların One Drive ile senkronizasyonu yapılacak. Bu sayede istenen dosyalar lokalde değil bulutta depolanabilecek.
- Veri tabanı uygulama içinde çalıştırılacak. Bu sayede ekstra bir dosya oluşturulmasının önüne geçilecek ve silinme sorunları olmayacak.

---

## Eski Sürümler

## v3.5 Özellikler

- Artık hangi derslerin indirilebileceğini seçebilirsiniz. Kullanıcı adınız ve şifrenizi yazdıktan sonra hangi kursları indirmek istediğiniz sorulacaktır.
- Daha açıklayıcı hata ve bilgilendirme mesajları eklendi

## v3 Yeni Özellikler

- İndirilen yeni dosyalar, program sonunda ekrana yazdırılıyor.
- Artık dosya kayıtları bir veri tabanında tutuluyor. Bu sayede aynı dosyaların tekrar indirilmesinin önüne geçildi.
- Çoklu süreç sistemi, hıza katkısı olmadığı için kaldırıldı. Kod tabanı, tek çekirdekte çalışmak üzere optimize edildi.
- "-core" komut satırı parametresi kaldırıldı. Program tek çekirdek üzerinde çalışıyor.
- v3 sürümü v2 ile indirilmiş klasörlerde uyumlu çalışır. İndirme klasörünü v3'e yükseltmek için yeni sürümü indirin ve klasör üzerinde indirme işlemi yapın.
- Hatalı şifre girildiğinde programı kapatmak yerine tekrar soruyor.
- Klasör seçme penceresi, son seçilen klasörü hatırlıyor.

## Kurulum

Bu program [Python yorumlayıcısı (interpreter)](https://www.python.org/downloads/) gerektirir.

1. Üst sağ köşedeki yeşil "Code" butonuna tıklayın ve zip olarak indirin
2. NinovaArsivci-Nightly klasörünü zipten çıkarın.
3. Çıkarttığınız klasöre girin ve aşağıdaki komutu yazın. Bu komut gerekli kütüphaneleri yükleyecektir.

```bash
pip install -r requirements.txt
```

## Kullanım

1. Daha önceden zipten çıkartmış olduğunuz klasöre girin
2. Buradan bir uçbirim (terminal) başlatın (Sağ tık > Uçbirimde aç)
3. Aşağıdaki komut ile programı başlatın:

```bash
python main.py
```

## S.S.S.

1. "HATA! src klasörü bulunamadı veya yeri değiştirilmiş. Programı yeniden indirin." diye bir hata alıyorum.  
   Programı arşivden çıkarırken src klasörünü de çıkarmalısın. "main.py" dosyası src klasörü içindeki dosyalarla birlikte çalışır.  
   Eğer hata devam ediyorsa, issues kısmından bana bildir.

2. "No such file or directory" hatası alıyorum.  
   Terminalin açıldığı klasör, main.py ile aynı klasör olmalı.

3. Şifreleri topluyor musun? Şifrem güvende mi?  
   Şifreler tamamen yerelde kalıyor ve Ninova'ya giriş yaptıktan sonra siliniyor.

4. "Veri tabanına manuel müdahele tespit edildi!" hatası alıyorum. Ama ben veri tabanını değiştirmedim  
   Eğer önceki indirme yarıda kesilmişse, veri tabanı bozulabilir. Bu hata önemli değildir ve program akışını etkilemez. Dosyalar indirilir.

## Notlar

- Eğer indirme klasöründe indirilen dosya ile aynı isimde farklı içerikte bir dosya varsa sonuna "\_new" eklenerek kaydedilir.
- İndirdiğiniz dosyaları değiştirseniz de programı çalıştırdığınızda Ninova'daki halleri indirilir ve üstüne yazılır.
- Program çalıştırdığınızda yalnızca varolmayan dosyalar indirilir.
- Programın tamamlanması süresi 2-3 dakika sürebilir.

## Hata bildirimi

Programın github sayfasındaki "issues" sekmesi altından, aldığınız hataları veya önerilerinizi yazabilirsiniz.
