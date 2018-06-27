pragma solidity ^0.4.16;


contract ITSContract {
    uint256 id;
    string imgname;
    string author;
    string date;
    string publisher;
    string storagelink;
    string fhash;
    string features;
    

    constructor (uint256 _id, string _imgname, string _author, string _date, string _publisher, string _storagelink, string _fhash, string _features) public{
        id = _id;
        imgname = _imgname;
        author = _author;
        date = _date;
        publisher = _publisher;
        storagelink = _storagelink;
        fhash = _fhash;
        features = _features;
    }

    function setImage(uint256 _id, string _imgname, string _author, string _date, string _publisher, string _storagelink, string _fhash) public{
        id = _id;
        imgname = _imgname;
        author = _author;
        date = _date;
        publisher = _publisher;
        storagelink = _storagelink;
        fhash = _fhash;
    }

    function getImage() public constant returns (uint, string, string, string, string, string, string, string) {
        return (id, imgname, author, date, publisher, storagelink, fhash, features);
    }
    
}