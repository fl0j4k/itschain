import sys
import time
import pprint
import json
from chainlogic import Web3, HTTPProvider
from solc import compile_source

# Connection to the remote server
w3 = Web3(HTTPProvider("http://131.130.122.226:8545"))
w3.eth.defaultAccount = w3.eth.accounts[0];
#w3.personal.unlockAccount('0x1526a9531fc2d3871311bf1875d078bcefb712b9', '12Jakfl02#')
contract_interface = {'abi': None, 'bin': None}
#address = "0x667aB0812631E185C71f4bA33345a77544C2c2e2"
#address = "0x3296025991E39481C964bdC58242b6878FbA968A"
#address = "0x667aB0812631E185C71f4bA33345a77544C2c2e2"
#address = "0xcEF05e5714FA03905CFD36b0F78994013E1b30C0"
#address = "0xC920b54A180842f940ADB334a16DBA2418F2A858"
#address = "0xD9c83E9e856a80118A80BBC0F0e51649A33A6771" 0x2031115C6207298E365f0766cEB70d3E1AC7698F
#address = "0x93858d78FFfE567f50E1fBcd0d8378a01E1aeecc"
#address = "0xcAcA02692D50d79119e128d9903CA4c8eD54f6E8"
address = "0x7bb6106b5BaFF9E565294Ee763239fc6AEac7E78"

with open("target/MappedStructWithIndex_sol_MappedStructsWithIndex.abi", 'r') as abi_definition:
    contract_interface['abi'] = abi_definition.read()

with open("target/MappedStructWithIndex_sol_MappedStructsWithIndex.bin", 'r') as abi_definition:
    contract_interface['bin'] = abi_definition.read()


store_var_contract = w3.eth.contract(address=address,abi=contract_interface['abi'])
#print("Output: ", store_var_contract.functions.newEntity(3, '0x3296025991E39481C964bdC58242b6878FbA968A').transact() )
idarray = store_var_contract.functions.getEntity().call()

for n in idarray:
    address = store_var_contract.functions.getAddress(n).call()
    print("Output: ", address )

    with open("target/itscontract_sol_ITSContract.abi", 'r') as abi_definition:
        contract_interface['abi'] = abi_definition.read()

    with open("target/itscontract_sol_ITSContract.bin", 'r') as abi_definition:
        contract_interface['bin'] = abi_definition.read()

    #address = "0x3296025991E39481C964bdC58242b6878FbA968A"

    image_contract = w3.eth.contract(
        address=address,
        abi=contract_interface['abi'])

    print("Output: ", image_contract.functions.getImage().call())

