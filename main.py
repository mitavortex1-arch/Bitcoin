
"""
BTC — BITCOIN
Educational Blockchain Architecture
Single-file Python implementation

Components:
1. Cryptography
2. Transactions
3. UTXO Ledger
4. Mempool
5. Merkle Tree
6. Block Engine
7. Proof of Work
8. Blockchain
9. Consensus Validation
10. Mining
11. Network Node
12. Explorer / Reporting

Educational simulation, NOT Bitcoin mainnet software.
"""

import hashlib
import json
import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional


# ============================================================
# 1. CRYPTOGRAPHY ENGINE
# ============================================================

class CryptoEngine:

    @staticmethod
    def sha256(data: str) -> str:
        return hashlib.sha256(data.encode()).hexdigest()

    @staticmethod
    def double_sha256(data: str) -> str:
        first = hashlib.sha256(data.encode()).digest()
        return hashlib.sha256(first).hexdigest()

    @staticmethod
    def hash_object(data) -> str:
        serialized = json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":")
        )
        return CryptoEngine.double_sha256(serialized)


# ============================================================
# 2. TRANSACTION INPUT
# ============================================================

@dataclass
class TransactionInput:
    previous_tx: str
    output_index: int


# ============================================================
# 3. TRANSACTION OUTPUT
# ============================================================

@dataclass
class TransactionOutput:
    address: str
    amount: int


# ============================================================
# 4. TRANSACTION ENGINE
# ============================================================

class Transaction:

    def __init__(
        self,
        inputs: List[TransactionInput],
        outputs: List[TransactionOutput],
        coinbase=False
    ):

        self.inputs = inputs
        self.outputs = outputs
        self.coinbase = coinbase
        self.timestamp = time.time()

        self.txid = self.calculate_id()

    def calculate_id(self):

        data = {
            "inputs": [asdict(x) for x in self.inputs],
            "outputs": [asdict(x) for x in self.outputs],
            "coinbase": self.coinbase,
            "timestamp": self.timestamp
        }

        return CryptoEngine.hash_object(data)

    def to_dict(self):

        return {
            "txid": self.txid,
            "inputs": [asdict(x) for x in self.inputs],
            "outputs": [asdict(x) for x in self.outputs],
            "coinbase": self.coinbase
        }


# ============================================================
# 5. UTXO LEDGER
# ============================================================

class UTXOEngine:

    def __init__(self):
        self.utxos = {}

    def add_transaction(self, transaction):

        if not transaction.coinbase:

            for tx_input in transaction.inputs:

                key = (
                    tx_input.previous_tx,
                    tx_input.output_index
                )

                if key not in self.utxos:
                    raise ValueError("UTXO does not exist")

                del self.utxos[key]

        for index, output in enumerate(transaction.outputs):

            key = (transaction.txid, index)

            self.utxos[key] = {
                "address": output.address,
                "amount": output.amount
            }

    def balance(self, address):

        return sum(
            item["amount"]
            for item in self.utxos.values()
            if item["address"] == address
        )

    def get_utxos(self, address):

        return {
            key: value
            for key, value in self.utxos.items()
            if value["address"] == address
        }


# ============================================================
# 6. TRANSACTION VALIDATION
# ============================================================

class TransactionValidator:

    @staticmethod
    def validate(transaction, ledger):

        if not transaction.outputs:
            return False

        if any(o.amount <= 0 for o in transaction.outputs):
            return False

        if transaction.coinbase:
            return len(transaction.inputs) == 0

        if not transaction.inputs:
            return False

        input_total = 0
        seen = set()

        for tx_input in transaction.inputs:

            key = (
                tx_input.previous_tx,
                tx_input.output_index
            )

            if key in seen:
                return False

            seen.add(key)

            utxo = ledger.utxos.get(key)

            if utxo is None:
                return False

            input_total += utxo["amount"]

        output_total = sum(
            output.amount
            for output in transaction.outputs
        )

        return input_total >= output_total


# ============================================================
# 7. MEMPOOL ENGINE
# ============================================================

class Mempool:

    def __init__(self):
        self.transactions = {}

    def add(self, transaction, ledger):

        if not TransactionValidator.validate(
            transaction, ledger
        ):
            raise ValueError("Invalid transaction")

        self.transactions[transaction.txid] = transaction

    def remove(self, txid):

        self.transactions.pop(txid, None)

    def get_transactions(self):

        return list(self.transactions.values())


# ============================================================
# 8. MERKLE TREE ENGINE
# ============================================================

class MerkleEngine:

    @staticmethod
    def calculate_root(transactions):

        hashes = [tx.txid for tx in transactions]

        if not hashes:
            return CryptoEngine.sha256("")

        while len(hashes) > 1:

            if len(hashes) % 2 == 1:
                hashes.append(hashes[-1])

            next_level = []

            for i in range(0, len(hashes), 2):

                combined = hashes[i] + hashes[i + 1]

                next_level.append(
                    CryptoEngine.double_sha256(combined)
                )

            hashes = next_level

        return hashes[0]


# ============================================================
# 9. BLOCK ENGINE
# ============================================================

class Block:

    def __init__(
        self,
        index,
        transactions,
        previous_hash,
        difficulty
    ):

        self.index = index
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.timestamp = time.time()

        self.merkle_root = MerkleEngine.calculate_root(
            transactions
        )

        self.difficulty = difficulty
        self.nonce = 0
        self.block_hash = None

    def calculate_hash(self):

        header = {
            "index": self.index,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "merkle_root": self.merkle_root,
            "difficulty": self.difficulty,
            "nonce": self.nonce
        }

        return CryptoEngine.hash_object(header)


# ============================================================
# 10. PROOF OF WORK ENGINE
# ============================================================

class MiningEngine:

    @staticmethod
    def mine(block):

        target = "0" * block.difficulty

        while True:

            block_hash = block.calculate_hash()

            if block_hash.startswith(target):

                block.block_hash = block_hash

                return block

            block.nonce += 1


# ============================================================
# 11. BLOCKCHAIN ENGINE
# ============================================================

class Blockchain:

    INITIAL_REWARD = 50
    HALVING_INTERVAL = 210000

    def __init__(self, difficulty=3):

        self.chain = []
        self.difficulty = difficulty

        self.ledger = UTXOEngine()
        self.mempool = Mempool()

        self.create_genesis_block()

    def create_genesis_block(self):

        genesis = Block(
            index=0,
            transactions=[],
            previous_hash="0" * 64,
            difficulty=self.difficulty
        )

        MiningEngine.mine(genesis)

        self.chain.append(genesis)

    @property
    def latest_block(self):

        return self.chain[-1]

    def reward_for_height(self, height):

        halvings = height // self.HALVING_INTERVAL

        if halvings >= 64:
            return 0

        return self.INITIAL_REWARD >> halvings

    def create_transaction(
        self,
        sender,
        recipient,
        amount,
        fee=0
    ):

        if amount <= 0 or fee < 0:
            raise ValueError("Invalid amount or fee")

        available = self.ledger.get_utxos(sender)

        selected = []
        total = 0

        for key, value in available.items():

            selected.append(key)
            total += value["amount"]

            if total >= amount + fee:
                break

        if total < amount + fee:
            raise ValueError("Insufficient funds")

        inputs = [
            TransactionInput(
                previous_tx=txid,
                output_index=index
            )
            for txid, index in selected
        ]

        outputs = [
            TransactionOutput(recipient, amount)
        ]

        change = total - amount - fee

        if change > 0:
            outputs.append(
                TransactionOutput(sender, change)
            )

        transaction = Transaction(inputs, outputs)

        self.mempool.add(transaction, self.ledger)

        return transaction

    def mine_block(self, miner_address):

        transactions = self.mempool.get_transactions()

        height = len(self.chain)

        reward = self.reward_for_height(height)

        fees = sum(
            sum(i.amount for i in tx.outputs)
            for tx in transactions
        )

        # Calculate transaction fees from consumed inputs.
        fees = sum(
            sum(self.ledger.utxos[
                (i.previous_tx, i.output_index)
            ]["amount"] for i in tx.inputs)
            - sum(o.amount for o in tx.outputs)
            for tx in transactions
        )

        coinbase = Transaction(
            inputs=[],
            outputs=[
                TransactionOutput(
                    miner_address,
                    reward + fees
                )
            ],
            coinbase=True
        )

        block_transactions = [coinbase] + transactions

        block = Block(
            index=height,
            transactions=block_transactions,
            previous_hash=self.latest_block.block_hash,
            difficulty=self.difficulty
        )

        MiningEngine.mine(block)

        self.add_block(block)

        return block

    def add_block(self, block):

        if block.previous_hash != self.latest_block.block_hash:
            raise ValueError("Previous block mismatch")

        if block.block_hash != block.calculate_hash():
            raise ValueError("Invalid block hash")

        if not block.block_hash.startswith(
            "0" * self.difficulty
        ):
            raise ValueError("Insufficient Proof of Work")

        if block.merkle_root != MerkleEngine.calculate_root(
            block.transactions
        ):
            raise ValueError("Invalid Merkle root")

        # Validate all transactions against a temporary ledger.
        import copy
        trial_ledger = copy.deepcopy(self.ledger)

        coinbases = [
            tx for tx in block.transactions if tx.coinbase
        ]

        if len(coinbases) != 1 or block.transactions[0] not in coinbases:
            raise ValueError("Invalid coinbase placement")

        for tx in block.transactions[1:]:

            if not TransactionValidator.validate(
                tx, trial_ledger
            ):
                raise ValueError("Invalid transaction")

            trial_ledger.add_transaction(tx)

        coinbase = coinbases[0]

        if not TransactionValidator.validate(
            coinbase, trial_ledger
        ):
            raise ValueError("Invalid coinbase")

        trial_ledger.add_transaction(coinbase)

        height = block.index

        if height != len(self.chain):
            raise ValueError("Invalid block height")

        fees = sum(
            sum(self.ledger.utxos[
                (i.previous_tx, i.output_index)
            ]["amount"] for i in tx.inputs)
            - sum(o.amount for o in tx.outputs)
            for tx in block.transactions[1:]
        )

        maximum_reward = self.reward_for_height(height) + fees

        if sum(o.amount for o in coinbase.outputs) > maximum_reward:
            raise ValueError("Excessive coinbase reward")

        self.ledger = trial_ledger
        self.chain.append(block)

        for tx in block.transactions[1:]:
            self.mempool.remove(tx.txid)

    # --------------------------------------------------------
    # 12. CONSENSUS / CHAIN VALIDATION
    # --------------------------------------------------------

    def validate_chain(self):

        for i in range(1, len(self.chain)):

            current = self.chain[i]
            previous = self.chain[i - 1]

            if current.previous_hash != previous.block_hash:
                return False

            if current.block_hash != current.calculate_hash():
                return False

            if not current.block_hash.startswith(
                "0" * current.difficulty
            ):
                return False

            if current.merkle_root != MerkleEngine.calculate_root(
                current.transactions
            ):
                return False

        return True

    # --------------------------------------------------------
    # 13. BLOCKCHAIN EXPLORER
    # --------------------------------------------------------

    def get_block(self, height):

        return self.chain[height]

    def get_stats(self):

        return {
            "network": "BTC Educational Network",
            "block_height": len(self.chain) - 1,
            "total_blocks": len(self.chain),
            "pending_transactions": len(
                self.mempool.transactions
            ),
            "difficulty": self.difficulty,
            "chain_valid": self.validate_chain()
        }

    def export_chain(self):

        return json.dumps(
            [
                {
                    "height": block.index,
                    "hash": block.block_hash,
                    "previous_hash": block.previous_hash,
                    "merkle_root": block.merkle_root,
                    "nonce": block.nonce,
                    "transactions": [
                        tx.to_dict()
                        for tx in block.transactions
                    ]
                }
                for block in self.chain
            ],
            indent=4
        )


# ============================================================
# 14. NETWORK NODE
# ============================================================

class BitcoinNode:

    def __init__(self, node_id):

        self.node_id = node_id
        self.blockchain = Blockchain()
        self.peers = []

    def connect_peer(self, peer):

        if peer not in self.peers:
            self.peers.append(peer)

    def get_status(self):

        return {
            "node_id": self.node_id,
            "connected_peers": len(self.peers),
            "blockchain": self.blockchain.get_stats()
        }


# ============================================================
# 15. SYSTEM BOOTSTRAP / EXECUTION
# ============================================================

def main():

    print("=" * 60)
    print("BTC — BITCOIN ARCHITECTURE")
    print("=" * 60)

    node = BitcoinNode("BTC-NODE-001")

    blockchain = node.blockchain

    # Genesis block already exists.
    # Create an initial simulated mining reward.

    first_reward = Transaction(
        inputs=[],
        outputs=[
            TransactionOutput("ALICE", 50)
        ],
        coinbase=True
    )

    initial_block = Block(
        index=1,
        transactions=[first_reward],
        previous_hash=blockchain.latest_block.block_hash,
        difficulty=blockchain.difficulty
    )

    MiningEngine.mine(initial_block)
    blockchain.add_block(initial_block)

    # Alice sends Bitcoin to Bob.

    transaction = blockchain.create_transaction(
        sender="ALICE",
        recipient="BOB",
        amount=15,
        fee=1
    )

    print("\nTRANSACTION CREATED")
    print("Transaction ID:", transaction.txid)

    # Miner processes the transaction.

    mined_block = blockchain.mine_block("MINER-001")

    print("\nBLOCK MINED")
    print("Block Height:", mined_block.index)
    print("Block Hash:", mined_block.block_hash)
    print("Nonce:", mined_block.nonce)

    # Check balances.

    print("\nUTXO BALANCES")

    print("Alice:", blockchain.ledger.balance("ALICE"))
    print("Bob:", blockchain.ledger.balance("BOB"))
    print("Miner:", blockchain.ledger.balance("MINER-001"))

    # Consensus validation.

    print("\nCONSENSUS VALIDATION")

    print("Chain Valid:", blockchain.validate_chain())

    # System status.

    print("\nNETWORK STATUS")

    print(json.dumps(node.get_status(), indent=4))

    print("\nBLOCKCHAIN EXPORT")

    print(blockchain.export_chain())

    print("\nBTC SYSTEM OPERATIONAL")


if __name__ == "__main__":
    main()
