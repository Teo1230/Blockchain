import json
import requests
import time
import os
import threading  # Adaugă această linie
from web3 import Web3
from flask import Flask, render_template, request, jsonify
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField
from wtforms.validators import DataRequired

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

class UploadForm(FlaskForm):
    audio = FileField('Fișier audio', validators=[DataRequired()])
    submit = SubmitField('Încarcă')

# Sepolia ABI
try:
    with open(os.path.join('build', 'SepoliaContract.abi')) as f:
        SEPOLIA_ABI = json.load(f)
except Exception as e:
    print(e)

# Proxy Pattern for managing transactions
class TransactionManager:
    def __init__(self, wallet_address, private_key):
        self.wallet_address = wallet_address
        self.private_key = private_key

    def download_transaction(self, filename):
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
            'gas': 2000000,  # Adjusted the gas parameter
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

    def upload_transaction(self, filename):
        nonce = w3.eth.get_transaction_count(self.wallet_address)
        with open(os.path.join('uploads', filename), 'rb') as file:
            audio_data = file.read()

        contract = w3.eth.contract(address=sepolia_address, abi=SEPOLIA_ABI)
        tx = contract.functions.uploadFile(filename).build_transaction({
            'chainId': 11155111,
            'gas': 2000000,
            'gasPrice': w3.eth.generate_gas_price({'value': os.path.getsize(os.path.join('uploads', filename))}),
            'nonce': nonce,
        })

        signed_tx = w3.eth.account.sign_transaction(tx, self.private_key)
        transaction_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        return transaction_hash

    def listen_to_events(self):
        contract = w3.eth.contract(address=sepolia_address, abi=SEPOLIA_ABI)
        event_filter = contract.events.FileUploaded.create_filter(fromBlock="latest")
        print(event_filter)
        print("Listening")
        for event in event_filter.get_new_entries():
            print("DA")
            print(f"New event: {event['args']}")
            # Aici poți adăuga logica suplimentară pentru a trata evenimentele

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

    uploaded_files = os.listdir('uploads')
    costs = {}
    for file in uploaded_files:
        file_size = os.path.getsize(os.path.join('uploads', file))
        transaction_cost = w3.eth.generate_gas_price({'value': file_size})
        costs[file] = w3.from_wei(transaction_cost, 'ether')

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
        transaction_hash=transaction_manager.upload_transaction(filename)
        transaction_cost = w3.eth.generate_gas_price({
            'to': recipient_address,
            'value': Web3.to_wei('0', 'ether')
        })
        return render_template('upload_complete.html', form=form, transaction_cost=transaction_cost,transaction_hash=transaction_hash)

    return render_template('upload.html', form=form)

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
    event_thread = threading.Thread(target=transaction_manager.listen_to_events)
    event_thread.start()

    app.run(debug=True)
