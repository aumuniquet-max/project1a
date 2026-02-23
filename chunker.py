#THIS SCRIPT CHUNKS DATA TO AVOID MEMORY ISSUES
import pandas as pd
from config import CONFIG
def chunker(file_path):
    try:
        for chunk in pd.read_csv(file_path, sep=CONFIG.separator, chunksize=CONFIG.chunk_size, header=0):
            if len(chunk) > 0:
                yield chunk
            else:
                print("EMPTY CHUNK SKIPPED")
    except FileNotFoundError:
        print("File not found. Please check the file path.")
        raise
    except KeyError as e:
        print(f"Missing column in the data: {e}")
        raise
    except Exception as e:
        print(f"An error occurred: {e}")
        raise