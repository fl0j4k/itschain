from web3 import Web3, HTTPProvider
import datetime
import base64


class ImageHandler:

    #**
    # Method for executing the deployment of the contract
    #**
    def deploy_contract(self, w3, contract_interface, id, imgname, author, date, publisher, storage, fhash, jsonFeatures, ethaccount, ethpass):
        resp = w3.personal.unlockAccount(w3.toChecksumAddress(ethaccount), ethpass)
        giveback = "104_FAILED"
        w3.miner.start(1)
        if resp == True:
            try:
                DeployedContract = w3.eth.contract(abi=contract_interface['abi'],bytecode=contract_interface['bin'])
                tx_hash = DeployedContract.constructor(id, imgname, author, date, publisher, storage, fhash, jsonFeatures).transact()
                tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
                giveback = tx_receipt
            except Exception:
                giveback = "ERROR_Blockchain: Maybe insufficient funds or gas?"
        return giveback

    #**
    # Returns id of last deployed contract
    #**
    def getLastId(self,GETHNODE, INDEXSTORAGE):
        w3 = Web3(HTTPProvider(GETHNODE))
        contract_interface = {'abi': None, 'bin': None}
        #address = "0x7bb6106b5BaFF9E565294Ee763239fc6AEac7E78"
        address = INDEXSTORAGE

        with open("chainlogic/contracts/ITSStorageIndex_sol_ITSStorageIndex.abi", 'r') as abi_definition:
            contract_interface['abi'] = abi_definition.read()

        with open("chainlogic/contracts/ITSStorageIndex_sol_ITSStorageIndex.bin", 'r') as abi_definition:
            contract_interface['bin'] = abi_definition.read()

        store_var_contract = w3.eth.contract(address=address, abi=contract_interface['abi'])
        lastid = store_var_contract.functions.getLastID().call()
        return lastid

    #**
    # Prepares the deployment of the final contract
    #**
    def insertHandler(self, imgname, author, jsonFeatures, filename, storagelink, fhash, ethaccount, ethpass, GETHNODE, INDEXSTORAGE):
        w3 = Web3(HTTPProvider(GETHNODE))
        w3.eth.defaultAccount = w3.toChecksumAddress(ethaccount);
        contract_interface = {'abi': None, 'bin': None}

        with open("chainlogic/contracts/itscontract_sol_ITSContract.abi", 'r') as abi_definition:
            contract_interface['abi'] = abi_definition.read()

        with open("chainlogic/contracts/itscontract_sol_ITSContract.bin", 'r') as abi_definition:
            contract_interface['bin'] = abi_definition.read()

        ffilename = filename

        id = self.getLastId(GETHNODE,INDEXSTORAGE)
        currentTime = datetime.datetime.now()
        date = currentTime.strftime("%d.%m.%Y %H:%M:%S")
        publisher = ethaccount
        #print("HASH: ", fhash)

        ethpass = base64.b64decode(ethpass).decode('utf-8')
        tx_receipt = self.deploy_contract(w3, contract_interface, id, imgname, author, date, publisher, storagelink, fhash, ffilename, ethaccount, ethpass)

        if type(tx_receipt) != str:
            address = tx_receipt.contractAddress
            print("Deployed: \n", format(address))

            address_storage = INDEXSTORAGE

            with open("chainlogic/contracts/ITSStorageIndex_sol_ITSStorageIndex.abi", 'r') as abi_definition:
                contract_interface['abi'] = abi_definition.read()

            with open("chainlogic/contracts/ITSStorageIndex_sol_ITSStorageIndex.bin", 'r') as abi_definition:
                contract_interface['bin'] = abi_definition.read()

            store_var_contract = w3.eth.contract(address=address_storage, abi=contract_interface['abi'])
            tx_hash = store_var_contract.functions.newITSContract(id, tx_receipt.blockNumber, tx_receipt.contractAddress,
                                                   tx_receipt.cumulativeGasUsed,
                                                   tx_receipt.gasUsed).transact()
            tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
        else:
            address = tx_receipt

        w3.miner.stop()
        return address
