from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any
import pandas as pd

class BaseAdapter(ABC):
    def __init__(self, cfg: dict[str, Any]) -> None:
        self.cfg = cfg  # one "source" block from config
    
    @abstractmethod
    def load_table(self, table_name: str) -> pd.DataFrame: ...