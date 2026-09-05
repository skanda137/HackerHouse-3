// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title MatchRegistry
/// @notice Tamper-evident registry linking a content hash (e.g. sha256 of a
/// face image) to a discovered social-media post URL. Only the hash and the
/// URL are stored on-chain — never raw biometric data.
contract MatchRegistry {
    struct Record {
        string postUrl;
        uint256 blockNumber;
        uint256 timestamp;
        address registeredBy;
        bool exists;
    }

    mapping(bytes32 => Record) private records;

    event MatchRegistered(
        bytes32 indexed dataHash,
        string postUrl,
        uint256 blockNumber,
        uint256 timestamp,
        address indexed registeredBy
    );

    error AlreadyRegistered(bytes32 dataHash);

    /// @notice Registers a hash -> postUrl record. Reverts if this exact
    /// hash was already registered, so an on-chain record can never be
    /// silently overwritten with different data.
    function registerMatch(bytes32 dataHash, string calldata postUrl) external {
        if (records[dataHash].exists) {
            revert AlreadyRegistered(dataHash);
        }
        records[dataHash] = Record({
            postUrl: postUrl,
            blockNumber: block.number,
            timestamp: block.timestamp,
            registeredBy: msg.sender,
            exists: true
        });
        emit MatchRegistered(dataHash, postUrl, block.number, block.timestamp, msg.sender);
    }

    /// @notice Reads back a record. `verified` is false and the rest of the
    /// fields are zero-valued if the hash was never registered.
    function verifyMatch(bytes32 dataHash)
        external
        view
        returns (bool verified, string memory postUrl, uint256 blockNumber, uint256 timestamp)
    {
        Record memory r = records[dataHash];
        return (r.exists, r.postUrl, r.blockNumber, r.timestamp);
    }
}
