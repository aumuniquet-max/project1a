from dataclasses import dataclass 
from typing import Final, Tuple 

@dataclass(frozen=True)
class Config: 
    """AGE IS IN YEARS, BINNING INTO 10 YEAR INTERVALS, UP TO 100 YEARS.
CHUNK SIZE = 250 ROWS AT A TIME, TO AVOID MEMORY ISSUES"""
    sample_id: str
    diagnosis:str
    age: str
    bin_edges: Tuple[int, ...]
    bin_labels: Tuple[str, ...]
    chunk_size: int
    separator: str
CONFIG: Final[Config] = Config(
    sample_id='Case ID',
    diagnosis='Diagnosis',
    age='Age',
    bin_edges=(0, 20, 40, 60, 80, 100),
    bin_labels=('0-20', '21-40', '41-60', '61-80', '81-100'),
    chunk_size= 250,
    separator='\t'
) 

