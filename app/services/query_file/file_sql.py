import pandas as pd
import duckdb
import re
import os
import json
import logging

logging.basicConfig(level=logging.INFO)

def getFileType(filePath:str):
    return os.path.splitext(filePath)[-1].lower().replace('.', '')

def createDataFrame(filePath:str)->pd.DataFrame:
    fileType = os.path.splitext(filePath)[-1].lower().replace('.', '')
    try:
        if fileType=='csv':
            df = pd.read_csv(filePath)
        elif (fileType=='xlsx') or  (fileType=='xls'):
            df = pd.read_excel(filePath)
        elif fileType=='parquet':
            df = pd.read_parquet(filePath)
        elif fileType=='json':
            with open(filePath, 'r') as f:
                data = json.load(f)
            df = pd.json_normalize(data)
        else:
            raise ValueError(f"Unsupported File type : {fileType}")
        
        if df.empty:
            raise ValueError("Loaded file is empty")
        return df
    except Exception as e:
        logging.error(f"[createDataFrame] Failed to read file: {e}")
        return None

def cleanColumns(df:pd.DataFrame)->pd.DataFrame:
    """
    Clean column names for SQL purpose:
    1. Lowercase column names
    2. Replace space and '-' with '_'
    3. Remove non-alphanumeric characters
    """
    cleaned_cols = []
    for col in df.columns:
        col = col.strip().lower()
        col = re.sub(r'\W+', '_', col)           # Replace non-word chars with _
        col = re.sub(r'^_+|_+$', '', col)        # Remove leading/trailing _
        col = re.sub(r'__+', '_', col)           # Collapse multiple underscores
        cleaned_cols.append(col)
    df.columns = cleaned_cols
    return df

def queryDataframe(df:pd.DataFrame, sql:str)->pd.DataFrame:
    try:
        result = duckdb.query_df(df=df,virtual_table_name="df" ,sql_query=sql).to_df()
        return result
        
    except Exception as e:
        logging.error(f"[queryDataFrame] Query failed: {e}")
        return None
    
def analyzeData(df:pd.DataFrame)->dict:
    schema_info = {}

    for col in df.columns:
        column_dtype = df[col].dtype

        col_info = {
            "dtype":str(column_dtype),
            "sample_values":df[col].dropna().unique()[:5].tolist()
        }
        if pd.api.types.is_numeric_dtype(df[col]):
            col_info.update({
                "min":df[col].min(),
                "max":df[col].max(),
                "mean":df[col].mean(),
                "median":df[col].median(),
                "standard_deviation":df[col].std()
            })
        elif pd.api.types.is_string_dtype(df[col]):
            col_info.update({
                "number_of_unique_values":df[col].nunique(),
                "most_common":df[col].value_counts().head(5).to_dict()
            })
        schema_info[col] = col_info

    return schema_info

def processFile(filePath:str, analyze:bool=True)->tuple[pd.DataFrame | dict] | pd.DataFrame | None:
    df = createDataFrame(filePath=filePath)
    if df is None:
        return None
    df = cleanColumns(df)
    
    if analyze:
        schema=analyzeData(df)
        return df, schema
    return df



filePath = '/Users/siddharthnarolia/Projects/Github/utilities/app/services/sample_data/sample.csv'
QUERY = "select distinct units from df order by 1 "
df, schema = processFile(filePath=filePath)
df = queryDataframe(df=df, sql=QUERY)
print(df)
# print(df)
# print(df.dtypes)
# print(analyzeData(pd.read_csv(filePath)))