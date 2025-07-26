import pandas as pd
import duckdb
import json
import os
import logging
import re
from typing import List
from file_sql import createDataFrame, cleanColumns, queryDataframe, analyzeData, processFile

logging.basicConfig(level=logging.INFO)

NUMBER_OF_FILES_ALLOWED = 5

def createDataFrames(Files:list):
    
    if Files is None:
        logging.warning("Please provide at least one file")
    if len(Files)>5:
        logging.warning("Maximum of five files allowed")
    dataframes = {}
    schema_information = {}
    for file in Files:
        try:
            fileName = os.path.splitext(os.path.basename(file))[0]
            fileName = re.sub(r'\W+', '_', fileName).strip('_')
            df,schema = processFile(file)
            dataframes.update({
                fileName:df
            })
            schema_information.update({
                fileName:schema
            })
        except Exception as e:
            logging.info(f"Error loading file {fileName} -> {e}")
    return dataframes, schema_information


def queryOnJoinedFiles(dfs:dict[str, pd.DataFrame], sql:str)->pd.DataFrame|None:
    """
    Registers multiple dataframes with Duckdb
    and runs a multi table sql

    Parameters:
    --dfs : Dictionary with dataframe names, to be used as table_name
    --sql : The Query to be used for SQL code
    
    Returns:
    -- Dataframe in case query gives a valid result else returns None
    """

    try:
        conn = duckdb.connect(database=':memory:')
        for table_name, df in dfs.items():
            conn.register(table_name, df)
            logging.info(f"Registering table {table_name} with its dataframe")
        
        # execute query
        result = conn.execute(sql).fetch_df()
        return result
    except Exception as e:
        logging.info(f"Error {e}")
        return None


def ProcessData(Files:list, sql:str):
    dataframes, schema = createDataFrames(Files=Files)
    queriedDataframe = queryOnJoinedFiles(dataframes, sql)
    return dataframes, schema, queriedDataframe

def _getFilePathList(base_path:str)->list|None:
    files_paths = []
    for file in os.listdir(base_path):
        full_path = os.path.join(base_path, file)
        if os.path.isfile(full_path):
            files_paths.append(full_path)
    
    return files_paths

Files = _getFilePathList("/Users/siddharthnarolia/Projects/Github/utilities/app/services/sample_data")

QUERY = """SELECT 
    c.name AS customer_name,
    p.product_name,
    oi.quantity,
    (oi.quantity * p.price) AS total_price,
    o.order_date
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
JOIN customers c ON o.customer_id = c.customer_id
JOIN products p ON oi.product_id = p.product_id
LIMIT 10;
"""



# filePath = '/Users/siddharthnarolia/Projects/Github/utilities/app/services/sample_data/sample.csv'
# SQL = "Select * from sample"
# dataframes, schema=createDataFrames([filePath])

