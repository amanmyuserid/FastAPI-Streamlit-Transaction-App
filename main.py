from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# Global transaction list
# Is list mein har naya transaction top (shuruat) mein add hoga.
# Example structure:
# {
#   "date": "2023-10-27 10:30:00",
#   "description": "Lunch",
#   "credit": None,
#   "debit": 150.0,
#   "running_balance": 850.0
# }
# {
#   "date": "2023-10-26 09:00:00",
#   "description": "Salary",
#   "credit": 1000.0,
#   "debit": None,
#   "running_balance": 1000.0
# }
transactions_db: List[dict] = []
current_running_balance: float = 0.0 # Initial balance, you can set it as per your need

app = FastAPI(
    title="Transaction Manager API",
    description="Ek simple API jo financial transactions ko manage karta hai."
)

# Pydantic model for request body of add_transaction
class AddTransactionRequest(BaseModel):
    transaction_type: str = Field(..., pattern="^(Credit|Debit)$", description="Transaction type (Credit or Debit only)")
    amount: float = Field(..., gt=0, description="Amount, must be greater than 0")
    description: Optional[str] = Field("", description="Optional description for the transaction")

# Pydantic model for response of transaction_detail
class TransactionDetail(BaseModel):
    date: str
    description: str
    credit: Optional[float]
    debit: Optional[float]
    running_balance: float

# Function to add transaction to the global list
def add_transaction_to_list(
    transaction_type: str, 
    amount: float, 
    description: str = ""
):
    global current_running_balance
    
    transaction_date = datetime.now().strftime("%Y-%m-%d")
    
    credit_value = None
    debit_value = None
    
    if transaction_type == "Credit":
        credit_value = amount
        current_running_balance += amount
    elif transaction_type == "Debit":
        debit_value = amount
        if amount > current_running_balance:
            raise ValueError("Debit amount exceeds current running balance.")
        current_running_balance -= amount
        
    
    new_transaction = {
        "date": transaction_date,
        "description": description,
        "credit": credit_value,
        "debit": debit_value,
        "running_balance": current_running_balance
    }
    
    # Add to the top of the list
    transactions_db.insert(0, new_transaction)
    
    print(f"Transaction added: {new_transaction}")
    print(f"Current running balance: {current_running_balance}")

# Endpoint 1: Add a new transaction
@app.post("/add_transaction", response_model=dict, summary="Add a new financial transaction")
async def add_transaction(request: AddTransactionRequest = Body(...)):
    """
    Ek naya transaction add karta hai (Credit ya Debit).
    
    - **transaction_type**: 'Credit' ya 'Debit' hona chahiye.
    - **amount**: Amount jo 0 se zyada ho.
    - **description**: Transaction ki description (optional).
    """
    try:
        add_transaction_to_list(
            transaction_type=request.transaction_type,
            amount=request.amount,
            description=request.description
        )
        return {"message": "Transaction successfully added!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error at the time of {request.transaction_type} Transaction: {str(e)}")

# Endpoint 2: Retrieve all transaction details
@app.get("/transaction_detail", response_model=List[TransactionDetail], summary="Get all transaction details")
async def transaction_detail():
    """
    Saare store kiye gaye transactions ko return karta hai,
    latest se oldest tak.
    """
    if not transactions_db:
        return [] # Empty list return karega agar koi transaction nahi hai
    return transactions_db

# Optional: Root endpoint for basic check
@app.get("/")
async def root():
    return {"message": "Welcome to the Transaction Manager API! Use /docs for API documentation."}