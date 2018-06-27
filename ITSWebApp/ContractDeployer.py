import os
from web3 import Web3, HTTPProvider
import configparser

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
config = configparser.ConfigParser()
config.read(os.path.join(__location__, 'config.cfg'))

GETHNODE = config['WEB3']['GETHNODE']
COINBASE = config['WEB3']['COINBASE']
PASSW = config['WEB3']['PASSW']

def deploy_contract(w3, contract_interface):
    resp = w3.personal.unlockAccount(w3.toChecksumAddress(COINBASE), PASSW)
    w3.miner.start(1)
    DeployedContract = w3.eth.contract(
        abi=contract_interface['abi'],
        bytecode=contract_interface['bin'])
    tx_hash = DeployedContract.constructor().transact()
    print("Waiting for mining contract . . . \n")
    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
    #print("Hash: \n", tx_receipt)
    address=tx_receipt.contractAddress
    return address


# Connection to the remote server
w3 = Web3(HTTPProvider(GETHNODE))
w3.eth.defaultAccount = w3.eth.accounts[0];
contract_interface = {'abi': None, 'bin': None}

with open("chainlogic/contracts/ITSStorageIndex_sol_ITSStorageIndex.abi", 'r') as abi_definition:
    contract_interface['abi'] = abi_definition.read()

with open("chainlogic/contracts/ITSStorageIndex_sol_ITSStorageIndex.bin", 'r') as abi_definition:
    contract_interface['bin'] = abi_definition.read()

address = deploy_contract(w3, contract_interface)
w3.miner.stop()

print("Set the following address in the config.cfg at INDEXSTORAGE: \n", format(address))
