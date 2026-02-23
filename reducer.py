#THIS SCRIPT REDUCES MAPPED CHUNKS TO FINAL COUNT OF DIAGNOSIS AND AGE GROUP COMBINATIONS
import pandas as pd
from config import CONFIG
#define reducer that takes one argument which is chunks
def reducer(chunks):
    #use pd.concat to stack all chunks into one dataframe
    df = pd.concat(chunks, ignore_index=True)
    #drop duplicates on sample_id so no patient is counted twice across chunks
    df = df.drop_duplicates(subset=[CONFIG.sample_id])
    #groupby diagnosis and AGE_GROUP
    result = df.groupby([CONFIG.diagnosis, "AGE_GROUP"]).size().reset_index(name="count")
    #count and sort by diagnosis then AGE_GROUP
    result = result.sort_values(by=[CONFIG.diagnosis, "AGE_GROUP"])

    #VERIFICATION
    assert len(result) > 0, "ERROR: reducer empty"
    assert result["count"].sum() > 0, "ERROR: all counts are zero"
    print(f"Verification passed: {result['count'].sum()} total patients across {len(result)} diagnosis and age group combinations")

    return result