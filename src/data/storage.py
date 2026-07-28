import pandas as pd
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def save_to_parquet(df: pd.DataFrame, file_path: Path) -> bool:
    """
    Lưu DataFrame thành file Parquet nén Snappy (sử dụng engine pyarrow).
    """
    if df.empty:
        logger.warning(f"DataFrame is empty. Skip saving to {file_path}")
        return False
        
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        # Parquet requires column names to be string
        df.columns = df.columns.astype(str)
        df.to_parquet(file_path, engine='pyarrow', compression='snappy')
        return True
    except Exception as e:
        logger.error(f"Error saving to {file_path}: {e}")
        return False

def load_from_parquet(file_path: Path) -> pd.DataFrame:
    """
    Đọc dữ liệu từ file Parquet.
    """
    if file_path.exists():
        try:
            return pd.read_parquet(file_path, engine='pyarrow')
        except Exception as e:
            logger.error(f"Error loading from {file_path}: {e}")
            
    return pd.DataFrame()
