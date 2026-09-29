DATASET_REGISTRY = {
    "ibm_aml": {
        "path": "eexzzm/IBM-Transactions-for-Anti-Money-Laundering-HI-Small-Trans",
        "split": "train",
        "mapper": {
            "Timestamp": "timestamp",
            "Account": "sender",
            "Account.1": "receiver",
            "Amount Paid": "amount",
            "Payment Currency": "currency",
            "Payment Format": "transaction_type",
            "Is Laundering": "label"
        }
    }
}
