pragma solidity ^0.4.22;

contract ITSStorageIndex {
    
    struct ContractData {
        address contractAddress;
        //string transactionHash;
        uint256 blockNumber ;
        uint256 cumulativeGasUsed;
        uint256 gasUsed;
        bool exists;
    }

    mapping(uint => ContractData) public contractData;
    uint[] public indexList;
    uint ccounter;
    bytes32[] bytesArray;

    function isExistent(uint contractAddress) public constant returns(bool) {
        return contractData[contractAddress].exists;
    }

    function getContractCount() public constant returns(uint) {
        return indexList.length;
    }

    function newITSContract(uint id, uint256 blockNumber , address contractAddress, uint256 cumulativeGasUsed, uint256 gasUsed) public returns(uint) {
        if(isExistent(id)) revert();
        //contractData[id].transactionHash = transactionHash;
        contractData[id].blockNumber = blockNumber;
        contractData[id].contractAddress = contractAddress;
        contractData[id].cumulativeGasUsed = cumulativeGasUsed;
        contractData[id].gasUsed = gasUsed;
        contractData[id].exists = true;
        ccounter++;
        return indexList.push(id) - 1;
    }

    function getAddress(uint id) public returns(address) {
        return contractData[id].contractAddress;
    }

    function getAllInfo(uint id) public returns(address, uint256, uint256, uint256) {
        return (contractData[id].contractAddress, contractData[id].blockNumber , contractData[id].cumulativeGasUsed, contractData[id].gasUsed);
    }

    function getIndexList() public returns(uint[]) {
        return indexList;
    }

    function getLastID() public returns(uint) {
        return ccounter;
    }
}