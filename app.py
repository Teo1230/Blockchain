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
import ipfshttpclient

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'


wallet_address = "0x17394F8a71b2DF2cd27A85C4Ad33AaF135f9ed0b"

private_key = "0x3dd92484469c16b9723822b204d7ecaccf94180a2ce48b163fbe72d7b3d04def"

recipient_address = "0xE100a0cf2D531fEecf0ed52C979ceE43CDb6258F"

api_key = "CTC2E2QD1ZNHFTWU7KF1BQQZ98GBUQ9XCF"
sepolia_address = "0xF63b963c6753fA72f0eA5BeB0dbd4DAF8e626A6e"

w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))

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
        response = requests.get("https://ethgasstation.info/api/ethgasAPI.json")
        gas_prices = response.json()
        
        print("Gas Prices from ETH Gas Station:")
        print(f"Fast: {gas_prices['fast']} Gwei")
        print(f"Standard: {gas_prices['standard']} Gwei")
        print(f"SafeLow: {gas_prices['safeLow']} Gwei")
        
        if transaction_params and transaction_params.get('value', 0) > Web3.to_wei(1, 'ether'):
            gas_price = gas_prices['fast']
        else:
            gas_price = gas_prices['standard']
        
        gas_price_wei = Web3.toWei(gas_price, 'gwei')
        
        return gas_price_wei
    except Exception as e:
        print(f"An error occurred while fetching gas prices: {e}")
        return Web3.toWei(5, 'gwei')


def estimate_gas_cost(transaction):
    try:
        gas_estimate = w3.eth.estimate_gas(transaction)
        return gas_estimate
    except Exception as e:
        print(f"An error occurred while estimating gas cost: {e}")
        return None

def set_gas_limit(gas_estimate):
    if gas_estimate:
        gas_limit = int(gas_estimate * 1.5)
        return gas_limit
    else:
        return None

def handle_gas_limit_error(e, transaction):
    print(f"An error occurred while setting gas limit: {e}")
    print(f"Transaction: {transaction}")

def send_transaction_with_gas_limit(transaction, gas_limit):
    try:
        transaction['gas'] = gas_limit
        signed_tx = w3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        return tx_hash
    except Exception as e:
        print(f"An error occurred while sending transaction with gas limit: {e}")
        return None

transaction = {
    'to': recipient_address,
    'from': wallet_address,
    'value': Web3.to_wei('1', 'ether'),
    'nonce': w3.eth.get_transaction_count(wallet_address),
}

gas_estimate = estimate_gas_cost(transaction)

gas_limit = set_gas_limit(gas_estimate)

if gas_limit:
    tx_hash = send_transaction_with_gas_limit(transaction, gas_limit)
    if tx_hash:
        print(f"Transaction sent successfully. Hash: {HexBytes(tx_hash).hex()}")
    else:
        print("Failed to send transaction.")
else:
    print("Failed to set gas limit.")
client = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001')

db = TinyDB('music.json')

def store_vote_on_ipfs(vote_data):
    try:
        vote_json = json.dumps(vote_data)
        res = client.add_bytes(vote_json.encode())
        return res['Hash']
    except Exception as e:
        print(f"Error storing vote on IPFS: {e}")
        return None

def get_vote_from_ipfs(ipfs_hash):
    try:
        data = client.cat(ipfs_hash)
        vote_data = json.loads(data.decode())
        return vote_data
    except Exception as e:
        print(f"Error retrieving vote from IPFS: {e}")
        return None

def update_votes(filename, vote_data):
    Music = Query()
    db.update({'votes': db.get(Music.filename == filename)['votes'] + 1}, Music.filename == filename)
    ipfs_hash = store_vote_on_ipfs(vote_data)
    if ipfs_hash:
        db.update({'ipfs_hash': ipfs_hash}, Music.filename == filename)

class UploadForm(FlaskForm):
    audio = FileField('Audio File', validators=[DataRequired()])
    submit = SubmitField('Upload')

@app.route('/vote', methods=['POST'])
def vote():
    filename = request.form['filename']
    vote_data = {
        'voter_address': request.remote_addr,
        'filename': filename
    }
    update_votes(filename, vote_data)
    return redirect(url_for('index'))



def save_uploaded_music(filename, uploader_address):
    db.insert({'filename': filename, 'uploader_address': uploader_address, 'votes': 0})

def get_uploaded_music():
    if os.path.exists('music.json') and os.path.getsize('music.json') > 0:
        with open('music.json') as f:
            data = json.load(f)
        return list(data["_default"].values())
    else:
        return []

try:
    with open(os.path.join('build', 'contracts', 'MusicContract.json')) as f:
        contract_json = json.load(f)
        SEPOLIA_ABI = contract_json['abi']
except Exception as e:
    print(e)

class TransactionManager:
    def __init__(self, wallet_address, private_key):
        self.wallet_address = wallet_address
        self.private_key = private_key

    def download_transaction(self, filename):
        try:
            if not w3.eth.get_balance(self.wallet_address) > 0:
                raise ValueError("Sender account has insufficient balance or is invalid")

            nonce = w3.eth.get_transaction_count(self.wallet_address)

            contract = w3.eth.contract(address=sepolia_address, abi=SEPOLIA_ABI)


            tx_params = {
                'from': self.wallet_address,
                'chainId': 1337,
                'gas': 30000000,
                'gasPrice': w3.eth.gas_price,
                'nonce': nonce,
            }

            tx_hash = contract.functions.downloadTransaction(filename).transact(tx_params)

            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

            with open(os.path.join('uploads', filename), 'rb') as file:
                audio_data = file.read()
            with open(os.path.join('downloads', filename), 'wb') as file:
                file.write(audio_data)

            return tx_hash.hex()

        except ValueError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
    def upload_transaction(self, filename):
        try:
            nonce = w3.eth.get_transaction_count(self.wallet_address)
            with open(os.path.join('uploads', filename), 'rb') as file:
                audio_data = file.read()

            contract = w3.eth.contract(address=sepolia_address, abi=SEPOLIA_ABI)

            tx = contract.functions.uploadFile(filename).transact({
                    'from':wallet_address,
                    'chainId': 1337,
                    'gas': 30000000,
                    'gasPrice': w3.eth.generate_gas_price({'value': os.path.getsize(os.path.join('uploads', filename))}),
                    'nonce': nonce,
                })


            return tx
        except ValueError as e:
            print(f"Invalid value: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    def delete_transaction(self, filename):
        try:
            nonce = w3.eth.get_transaction_count(self.wallet_address)

            contract = w3.eth.contract(address=sepolia_address, abi=SEPOLIA_ABI)

            tx = contract.functions.deleteFile(filename).transact({
                'from': wallet_address,
                'chainId': 1337,
                'gasPrice': w3.eth.gas_price,
                    'gas': 30000000,
                'nonce': nonce,
            })
            return tx
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    def listen_to_events(self):
        try:
            with open(os.path.join('build', 'contracts', 'MusicContract.json')) as f:
                music_contract_json = json.load(f)
                MUSIC_ABI = music_contract_json['abi']
                MUSIC_ADDRESS = music_contract_json['networks']['1337']['address']

            with open(os.path.join('build', 'contracts', 'VotingContract.json')) as f:
                voting_contract_json = json.load(f)
                VOTING_ABI = voting_contract_json['abi']
                VOTING_ADDRESS = voting_contract_json['networks']['1337']['address']

            music_contract = w3.eth.contract(address=MUSIC_ADDRESS, abi=MUSIC_ABI)
            voting_contract = w3.eth.contract(address=VOTING_ADDRESS, abi=VOTING_ABI)

            music_event_filter = music_contract.events.FileUploaded.createFilter(fromBlock="latest")
            voting_event_filter = voting_contract.events.VoteCasted.createFilter(fromBlock="latest")

            while True:
                for event in music_event_filter.get_new_entries():
                    print("New event from MusicContract:")
                    print(f"File uploaded: {event['args']['filename']} by {event['args']['uploader']}")
                    print(f"Amount: {event['args']['amount']} ETH")

                for event in voting_event_filter.get_new_entries():
                    print("New event from VotingContract:")
                    print(f"Vote casted by: {event['args']['voter']}")
                    print(f"For file: {event['args']['filename']}")

                time.sleep(5)

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
        balance=w3.eth.get_balance(wallet_address)
        balance = w3.from_wei(balance, 'ether')
        print(f"Current balance: {balance} ETH")
    except requests.Timeout:
        return "Timeout error: Could not connect to Etherscan API."
    except requests.RequestException as e:
        return f"An error occurred: {e}"

    def get_uploaded_music():
        return db.all()

    uploaded_files = get_uploaded_music()
    form = UploadForm()
    costs = {}
    for file_info in uploaded_files:
        file_size = os.path.getsize(os.path.join('uploads', file_info['filename']))
        transaction_cost = w3.eth.generate_gas_price({'value': file_size})
        costs[file_info['filename']] = w3.from_wei(transaction_cost, 'ether')

    total_cost = sum(costs.values())

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
    file_info = db.get(Query().filename == filename)
    if file_info and file_info['uploader_address'] == wallet_address:
        transaction_hash = transaction_manager.delete_transaction(filename)
        db.remove(Query().filename == filename)
        transaction_hash_str = HexBytes(transaction_hash).hex()
        return jsonify({"success": True, "transaction_hash": transaction_hash_str})
    else:
        return jsonify({"success": False, "message": "File not found or you are not the owner"}), 404

@app.route('/calculate_cost', methods=['POST'])
def calculate_cost():
    file = request.files['audio']
    file_size = file.seek(0, os.SEEK_END)
    transaction_cost = w3.eth.generate_gas_price({'value': file_size})
    return jsonify({"transaction_cost": str(w3.from_wei(transaction_cost, 'ether'))})

@app.route("/wallets", methods=['GET'])
def get_wallets():
    return {"accounts": w3.eth.accounts}

@app.route("/balance", methods=['GET'])
def get_balance():
    try:
        balance = w3.eth.get_balance('0x17394F8a71b2DF2cd27A85C4Ad33AaF135f9ed0b')
        return {"balance": w3.from_wei(balance, 'ether')}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    if not os.path.exists('downloads'):
        os.makedirs('downloads')


    event_thread = threading.Thread(target=partial(transaction_manager.listen_to_events))
    event_thread.start()

    app.run(debug=True)
