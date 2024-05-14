import json
import requests
import time
import os
import threading
from web3 import Web3
from flask import Flask, render_template, request, jsonify
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField
from wtforms.validators import DataRequired
from flask import redirect, url_for
from tinydb import TinyDB, Query
from functools import partial
from hexbytes import HexBytes

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'

# Wallet address and private key
wallet_address = "0xe3F95625afaeb380369860F63835F1B3fe28e6D9"
private_key = "96ffe4bb597493bd40f1f2c76ebc4709f6117aa5e92da73540372cf70f0d2076"

# Recipient address for payments
recipient_address = "0x92F9f60767F3c74ae2947b5a7da9805A9108Af3B"

# Sepolia API
api_key = "CTC2E2QD1ZNHFTWU7KF1BQQZ98GBUQ9XCF"
sepolia_address = "0x1b44F3514812d835EB1BDB0acB33d3fA3351Ee43"
url = f"https://api-sepolia.etherscan.io/api?module=account&action=balance&address={wallet_address}&tag=latest&apikey={api_key}"

# Initialize web3 with Infura provider
w3 = Web3(Web3.HTTPProvider('https://sepolia.infura.io/v3/15d37f1332cf4f7ebf85be6f6abb0ee3'))

# Validate the wallet address
if not w3.is_address(wallet_address):
    raise ValueError(f"Invalid wallet address: {wallet_address}")

def value_based_gas_price_strategy(web3, transaction_params):
    if transaction_params and transaction_params.get('value', 0) > Web3.to_wei(1, 'ether'):
        return Web3.to_wei(20, 'gwei')
    else:
        return Web3.to_wei(5, 'gwei')

w3.eth.set_gas_price_strategy(value_based_gas_price_strategy)

def value_based_gas_price_strategy(web3, transaction_params):
    try:
        # Obțineți prețurile gazului de la ETH Gas Station
        response = requests.get("https://ethgasstation.info/api/ethgasAPI.json")
        gas_prices = response.json()
        
        # Afișați prețurile gazului
        print("Gas Prices from ETH Gas Station:")
        print(f"Fast: {gas_prices['fast']} Gwei")
        print(f"Standard: {gas_prices['standard']} Gwei")
        print(f"SafeLow: {gas_prices['safeLow']} Gwei")
        
        # Alegeți prețul gazului în funcție de valoarea tranzacției
        if transaction_params and transaction_params.get('value', 0) > Web3.to_wei(1, 'ether'):
            gas_price = gas_prices['fast']
        else:
            gas_price = gas_prices['standard']
        
        # Convertiți prețul gazului din Gwei în Wei
        gas_price_wei = Web3.toWei(gas_price, 'gwei')
        
        return gas_price_wei
    except Exception as e:
        print(f"An error occurred while fetching gas prices: {e}")
        # În caz de eroare, folosim un preț gaz implicit
        return Web3.toWei(5, 'gwei')


# Funcție pentru estimarea costului gazului pentru o tranzacție
def estimate_gas_cost(transaction):
    try:
        gas_estimate = w3.eth.estimate_gas(transaction)
        return gas_estimate
    except Exception as e:
        print(f"An error occurred while estimating gas cost: {e}")
        return None

# Funcție pentru fixarea limită de cost a gazului pentru o tranzacție
def set_gas_limit(gas_estimate):
    if gas_estimate:
        # Setăm limita de cost a gazului la o valoare mai mare decât estimarea
        gas_limit = int(gas_estimate * 1.5)  # Puteti ajusta factorul dupa preferinta
        return gas_limit
    else:
        return None

# Funcție pentru gestionarea erorilor de limită a gazului
def handle_gas_limit_error(e, transaction):
    # Aici puteti implementa o logica specifica pentru gestionarea erorilor de gaz
    print(f"An error occurred while setting gas limit: {e}")
    print(f"Transaction: {transaction}")

# Funcție pentru efectuarea tranzacției cu limita de cost a gazului fixată
def send_transaction_with_gas_limit(transaction, gas_limit):
    try:
        transaction['gas'] = gas_limit
        signed_tx = w3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        return tx_hash
    except Exception as e:
        print(f"An error occurred while sending transaction with gas limit: {e}")
        return None

# Exemplu de utilizare
transaction = {
    'to': recipient_address,
    'from': wallet_address,
    'value': Web3.to_wei('1', 'ether'),
    'nonce': w3.eth.get_transaction_count(wallet_address),
}

# Estimam costul gazului pentru tranzactie
gas_estimate = estimate_gas_cost(transaction)

# Setam limita de cost a gazului
gas_limit = set_gas_limit(gas_estimate)

if gas_limit:
    # Trimitem tranzactia cu limita de cost a gazului fixata
    tx_hash = send_transaction_with_gas_limit(transaction, gas_limit)
    if tx_hash:
        print(f"Transaction sent successfully. Hash: {HexBytes(tx_hash).hex()}")
    else:
        print("Failed to send transaction.")
else:
    print("Failed to set gas limit.")

class UploadForm(FlaskForm):
    audio = FileField('Audio File', validators=[DataRequired()])
    submit = SubmitField('Upload')

# Update the votes for a specific file in the database
def update_votes(filename):
    Music = Query()
    db.update({'votes': db.get(Music.filename == filename)['votes'] + 1}, Music.filename == filename)

# Route for voting
@app.route('/vote', methods=['POST'])
def vote():
    filename = request.form['filename']
    update_votes(filename)
    return redirect(url_for('index'))

# Initialize TinyDB database
db = TinyDB('music.json')

# Save uploaded music to the database
def save_uploaded_music(filename, uploader_address):
    db.insert({'filename': filename, 'uploader_address': uploader_address, 'votes': 0})

# Get uploaded music from the database
def get_uploaded_music():
    if os.path.exists('music.json') and os.path.getsize('music.json') > 0:
        with open('music.json') as f:
            data = json.load(f)
        return list(data["_default"].values())
    else:
        return []

# Sepolia ABI
try:
    with open(os.path.join('build', 'contracts', 'MusicContract.json')) as f:
        contract_json = json.load(f)
        SEPOLIA_ABI = contract_json['abi']
except Exception as e:
    print(e)

# Proxy Pattern for managing transactions
class TransactionManager:
    def __init__(self, wallet_address, private_key):
        self.wallet_address = wallet_address
        self.private_key = private_key

    def download_transaction(self, filename):
        try:
            nonce = w3.eth.get_transaction_count(self.wallet_address)
            with open(os.path.join('uploads', filename), 'rb') as file:
                audio_data = file.read()

            transaction_cost = w3.eth.generate_gas_price({
                'to': recipient_address,
                'value': Web3.to_wei('0', 'ether')
            })

            tx = {
                'to': recipient_address,
                'from': self.wallet_address,
                'nonce': nonce,
                'maxFeePerGas': transaction_cost,
                'maxPriorityFeePerGas': Web3.to_wei('1', 'gwei'),
                'value': Web3.to_wei('0', 'ether'),  # Transaction value
                'gas': 30000000,  # Adjusted the gas parameter
                'chainId': 11155111  # Add the chainId parameter
            }

            signed_tx = w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            transaction_hash=tx_hash.hex()

            while True:
                try:
                    receipt = w3.eth.get_transaction_receipt(tx_hash)
                    if receipt:
                        print(f"Transaction {tx_hash.hex()} mined.")
                        break
                    print("Waiting for transaction to be mined...")
                    time.sleep(10)
                except Exception as e:
                    print(f"An error occurred while waiting for transaction receipt: {e}")

            with open(os.path.join('downloads', filename), 'wb') as file:
                file.write(audio_data)
            return transaction_hash
        except FileNotFoundError:
            print("File not found.")
        except IOError as e:
            print(f"Error reading or writing file: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    def upload_transaction(self, filename):
        try:
            nonce = w3.eth.get_transaction_count(self.wallet_address)
            with open(os.path.join('uploads', filename), 'rb') as file:
                audio_data = file.read()

            contract = w3.eth.contract(address=sepolia_address, abi=SEPOLIA_ABI)
            tx = contract.functions.uploadFile(filename).build_transaction({
                'chainId': 11155111,
                'gas': 30000000,
                'gasPrice': w3.eth.generate_gas_price({'value': os.path.getsize(os.path.join('uploads', filename))}),
                'nonce': nonce,
            })

            signed_tx = w3.eth.account.sign_transaction(tx, self.private_key)
            transaction_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            return transaction_hash
        except ValueError as e:
            print(f"Invalid value: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    def delete_transaction(self, filename):
        try:
            nonce = w3.eth.get_transaction_count(self.wallet_address)

            contract = w3.eth.contract(address=sepolia_address, abi=SEPOLIA_ABI)
            tx = contract.functions.deleteFile(filename).build_transaction({
                'chainId': 11155111,
                'gas': 30000000,
                'nonce': nonce,
            })

            signed_tx = w3.eth.account.sign_transaction(tx, self.private_key)
            transaction_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            return transaction_hash
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    def listen_to_events(self):
        try:
            # Sepolia ABI
            with open(os.path.join('build', 'contracts', 'MusicContract.json')) as f:
                music_contract_json = json.load(f)
                MUSIC_ABI = music_contract_json['abi']
                MUSIC_ADDRESS = music_contract_json['networks']['11155111']['address']  # Update here

            # VotingContract ABI și adresă
            with open(os.path.join('build', 'contracts', 'VotingContract.json')) as f:
                voting_contract_json = json.load(f)
                VOTING_ABI = voting_contract_json['abi']
                VOTING_ADDRESS = voting_contract_json['networks']['11155111']['address']  # Update here

            # Creare contracte web3 pentru fiecare contract
            music_contract = w3.eth.contract(address=MUSIC_ADDRESS, abi=MUSIC_ABI)
            voting_contract = w3.eth.contract(address=VOTING_ADDRESS, abi=VOTING_ABI)

            # Filtru de evenimente pentru MusicContract
            music_event_filter = music_contract.events.FileUploaded.createFilter(fromBlock="latest")
            print("Listening for events from MusicContract...")

            # Filtru de evenimente pentru VotingContract
            voting_event_filter = voting_contract.events.VoteCasted.createFilter(fromBlock="latest")
            print("Listening for events from VotingContract...")

            # Ascultare evenimente pentru MusicContract
            for event in music_event_filter.get_new_entries():
                print("New event from MusicContract:")
                print(f"File uploaded: {event['args']['filename']} by {event['args']['uploader']}")
                print(f"Amount: {event['args']['amount']} ETH")

            # Ascultare evenimente pentru VotingContract
            for event in voting_event_filter.get_new_entries():
                print("New event from VotingContract:")
                print(f"Vote casted by: {event['args']['voter']}")
                print(f"For file: {event['args']['filename']}")
        except Exception as e:
            print(f"An error occurred: {e}")


transaction_manager = TransactionManager(wallet_address, private_key)

@app.route('/')
def index():
    syncing = w3.eth.syncing
    if syncing:
        print(f"Current block: {syncing['currentBlock']}, Highest block: {syncing['highestBlock']}")
    else:
        print("Node is fully synchronized.")

    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        balance = w3.from_wei(int(data['result']), 'ether')
        print(f"Current balance: {balance} ETH")
    except requests.Timeout:
        return "Timeout error: Could not connect to Etherscan API."
    except requests.RequestException as e:
        return f"An error occurred: {e}"

    # În loc să citești fișierele din folderul 'uploads', obține informațiile din baza de date
    uploaded_files = get_uploaded_music()
    costs = {}
    for file_info in uploaded_files:
        file_size = os.path.getsize(os.path.join('uploads', file_info['filename']))
        transaction_cost = w3.eth.generate_gas_price({'value': file_size})
        costs[file_info['filename']] = w3.from_wei(transaction_cost, 'ether')

    total_cost = sum(costs.values())

    form = UploadForm()
    return render_template('index.html', wallet_address=wallet_address, balance=balance, uploaded_files=uploaded_files,
                           form=form, costs=costs, total_cost=total_cost)

@app.route('/download/<filename>')
def download_music(filename):
    print(f"Downloading {filename}...")
    transaction_hash=transaction_manager.download_transaction(filename)
    transaction_cost = w3.eth.generate_gas_price({
        'to': recipient_address,
        'value': Web3.to_wei('0', 'ether')
    })
    return render_template('download_complete.html', filename=filename, transaction_cost=transaction_cost,transaction_hash=transaction_hash)

@app.route('/upload', methods=['GET', 'POST'])
def upload_music():
    form = UploadForm()
    if form.validate_on_submit():
        audio = form.audio.data
        filename = audio.filename
        audio.save(os.path.join('uploads', filename))
        save_uploaded_music(filename, wallet_address)
        transaction_hash=transaction_manager.upload_transaction(filename)
        transaction_cost = w3.eth.generate_gas_price({
            'to': recipient_address,
            'value': Web3.to_wei('0', 'ether')
        })
        return render_template('upload_complete.html', form=form, transaction_cost=transaction_cost,transaction_hash=transaction_hash)

    return render_template('upload.html', form=form)

@app.route('/delete/<filename>', methods=['POST'])
def delete_music(filename):
    # Verificăm dacă fișierul există în baza de date și dacă utilizatorul este proprietarul fișierului
    file_info = db.get(Query().filename == filename)
    if file_info and file_info['uploader_address'] == wallet_address:
        # Apelăm funcția de ștergere a fișierului din contractul MusicContract
        transaction_hash = transaction_manager.delete_transaction(filename)
        # Ștergem fișierul din baza de date
        db.remove(Query().filename == filename)
        # Convert the HexBytes object to a string
        transaction_hash_str = HexBytes(transaction_hash).hex()
        return jsonify({"success": True, "transaction_hash": transaction_hash_str})  # Convert to string before returning
    else:
        return jsonify({"success": False, "message": "File not found or you are not the owner"}), 404

@app.route('/calculate_cost', methods=['POST'])
def calculate_cost():
    file = request.files['audio']
    file_size = file.seek(0, os.SEEK_END)
    transaction_cost = w3.eth.generate_gas_price({'value': file_size})
    return jsonify({"transaction_cost": str(w3.from_wei(transaction_cost, 'ether'))})

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    # Ascultă evenimentele Sepolia într-un thread separat
    
    event_thread = threading.Thread(target=partial(transaction_manager.listen_to_events))
    event_thread.start()

    app.run(debug=True)
