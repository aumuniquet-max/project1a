#THIS SCRIPT MAPS CHUNKS OF DATA ROW BY ROW TO ORGANIZE INTO AGE GROUPS AND CLEAN DIAGNOSIS
import pandas as pd
from config import CONFIG
#define mapper
def mapper(chunk):
    #select only the three columns needed using CONFIG field names
    chunk = chunk[[CONFIG.sample_id, CONFIG.diagnosis, CONFIG.age]].copy()
    #convert age to numeric and drop rows
    chunk[CONFIG.age] = pd.to_numeric(chunk[CONFIG.age], errors='coerce')
    chunk = chunk.dropna(subset=[CONFIG.age])
    #strip NOS from diagnosis and standardize with strip
    chunk[CONFIG.diagnosis] = chunk[CONFIG.diagnosis].str.replace(', NOS', '', case=False, regex=False).str.strip()
    #assign AGE_GROUP
    chunk["AGE_GROUP"] = pd.cut(x=chunk[CONFIG.age], bins=list(CONFIG.bin_edges), labels=list(CONFIG.bin_labels))
    #drop rows where AGE_GROUP is missing
    chunk = chunk.dropna(subset=["AGE_GROUP"])
    #return the clean chunk
    return chunk