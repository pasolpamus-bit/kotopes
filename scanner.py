import requests

class HybridScanner:
    def __init__(self, helius_url):
        self.helius_url = helius_url
        # Добавляем расширенные заголовки для обхода блокировок
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json'
        }

    def get_bybit_futures_list(self):
        """Получает фьючерсные пары Bybit с оборотом от $500k до $500M"""
        try:
            # Используем основной эндпоинт V5 для деривативов
            url = "https://api.bybit.com/v5/market/tickers?category=linear"
            response = requests.get(url, headers=self.headers, timeout=15)
            
            if response.status_code != 200:
                print(f"[-] Ошибка API Bybit: Код {response.status_code}")
                return []

            data = response.json()
            ticker_list = data.get('result', {}).get('list', [])
            
            symbols = []
            for item in ticker_list:
                # Нам нужны только пары к USDT
                if not item['symbol'].endswith('USDT'):
                    continue
                
                # Turnover24h — это объем торгов в USDT
                turnover = float(item.get('turnover24h', 0))
                
                # Расширяем фильтр: ищем монеты с объемом от 500к до 500млн
                if 500000 < turnover < 500000000:
                    symbol = item['symbol'].replace('USDT', '')
                    symbols.append(symbol)
            
            return symbols
        except Exception as e:
            print(f"[-] Критическая ошибка Bybit API: {e}")
            return []

    def get_solana_contract(self, symbol):
        """Поиск контракта через DexScreener с проверкой сети"""
        try:
            url = f"https://api.dexscreener.com/latest/dex/search?q={symbol}"
            resp = requests.get(url, headers=self.headers, timeout=10).json()
            pairs = resp.get('pairs', [])
            
            if not pairs:
                return None
                
            for pair in pairs:
                # Фильтруем только Solana и проверяем совпадение тикера
                if pair.get('chainId') == 'solana':
                    base_token = pair.get('baseToken', {})
                    if base_token.get('symbol', '').upper() == symbol.upper():
                        return base_token.get('address')
            return None
        except:
            return None

    def get_top_holders(self, mint_address):
        """Запрос ТОП-10 холдеров через Helius RPC"""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTokenLargestAccounts",
            "params": [mint_address]
        }
        try:
            resp = requests.post(self.helius_url, json=payload, timeout=10).json()
            return resp.get('result', {}).get('value', [])[:10]
        except:
            return []