import pandas as pd
from datasets import load_dataset
from data.ingestion.dataset_registry import DATASET_REGISTRY
from data.ingestion.schema_mapper import normalize_record, clean_data
from data.ingestion.validator import TransactionSchema
from pydantic import ValidationError

def load_and_validate_dataset(registry_name: str, max_records: int = 1000) -> pd.DataFrame:
    if registry_name not in DATASET_REGISTRY:
        raise ValueError(f"Dataset {registry_name} not found in registry.")
        
    config = DATASET_REGISTRY[registry_name]
    
    try:
        ds = load_dataset(
            config["path"], 
            split=config["split"], 
            streaming=True
        )
    except Exception as e:
        raise RuntimeError(f"Failed to download or load dataset from Hugging Face: {e}")
        
    records = []
    mapping = config["mapper"]
    
    iterator = iter(ds)
    count = 0
    while count < max_records:
        try:
            raw_record = next(iterator)
        except StopIteration:
            break
            
        normalized = normalize_record(raw_record, mapping)
        records.append(normalized)
        count += 1
        
    if not records:
        raise ValueError("Dataset is empty after loading.")
        
    df = pd.DataFrame(records)
    df = clean_data(df)
    
    valid_records = []
    for record in df.to_dict(orient="records"):
        try:
            validated = TransactionSchema.model_validate(record)
            valid_records.append(validated.model_dump())
        except ValidationError:
            pass
            
    if not valid_records:
        raise ValueError("No valid records found after schema validation.")
        
    return pd.DataFrame(valid_records)
