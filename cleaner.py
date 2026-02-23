#THIS SCRIPTS CLEANS DATA TO THREE NECESSARY COLUMNS
import pandas as pd
df = pd.read_csv('clinical.tsv', sep='\t', low_memory=False) #FIX MIX OF DTYPE
selected_columns = {'cases.case_id': 'Case ID', 'demographic.age_at_index': 'Age', 'diagnoses.primary_diagnosis': 'Diagnosis'}
df_filtered = df[list(selected_columns.keys())].copy()
df_filtered.columns = list(selected_columns.values())

# REMOVE DUPLICATES AND CHECK HOW MANY ROWS ARE LEFT AFTERWARDS
print("Rows before dedup:", len(df_filtered))
df_filtered = df_filtered.drop_duplicates(subset=['Case ID'])
print("Rows after dedup:", len(df_filtered))

#FIlTER OUT NOS

df_filtered['Diagnosis'] = df_filtered['Diagnosis'].str.replace(', NOS', '', case=False, regex=False).str.strip()



#REMOVE UNWANTED DIAGNOSES
EXCLUDE = ['not reported', 'diagnosis', "'--"]

df_filtered = df_filtered[
    ~df_filtered['Diagnosis'].str.lower().isin(EXCLUDE)
]

df_filtered = df_filtered.reset_index(drop=True)
df_filtered.to_csv('cleaner_clinical.tsv', sep='\t', index=False)

print(df_filtered['Diagnosis'].value_counts())