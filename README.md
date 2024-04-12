# Sepolia Music Platform

Sepolia Music Platform este o platformă de gestionare a fișierelor audio bazată pe tehnologia blockchain Ethereum. Utilizează un contract inteligent pentru a încărca și descărca fișiere audio, oferind transparență și securitate.

## Funcționalități

- **Încărcare fișier audio**: Utilizatorii pot încărca fișiere audio în platformă.
- **Descărcare fișier audio**: Utilizatorii pot descărca fișiere audio de pe platformă.
- **Calcul cost tranzacție**: Platforma calculează costul tranzacției Ethereum necesar pentru încărcarea unui fișier.

## Cerințe

- Python 3.x
- Flask
- Web3.py
- Requests

## Instalare

1. Clonați repository-ul:

   ```bash
   git clone https://github.com/yourusername/sepolia-music-platform.git
Instalați dependențele:

bash
Copy code
pip install -r requirements.txt
Configurare inițială
Configurați adresa portofelului Ethereum și cheia privată în app.py.

python
Copy code
wallet_address = "0xYourWalletAddress"
private_key = "YourPrivateKey"
Configurați adresa destinatarului pentru plăți în app.py.

python
Copy code
recipient_address = "0xRecipientAddress"
Configurați adresa și cheia API pentru Etherscan în app.py.

python
Copy code
api_key = "YourEtherscanAPIKey"
Configurați adresa contractului Sepolia și ABI-ul în app.py.

python
Copy code
sepolia_address = "SepoliaContractAddress"
Utilizare
Rulați aplicația:

bash
Copy code
python app.py
Aplicația va rula pe http://localhost:5000.
