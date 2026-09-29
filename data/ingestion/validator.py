from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional

class TransactionSchema(BaseModel):
    transaction_id: str
    timestamp: datetime
    sender: str
    receiver: str
    amount: float
    currency: str
    transaction_type: str
    label: int
    customer_id: Optional[str] = None
    account_id: Optional[str] = None
    country: Optional[str] = None
    channel: Optional[str] = None
    typology: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v):
        if v < 0:
            raise ValueError("Amount must be positive")
        return v
