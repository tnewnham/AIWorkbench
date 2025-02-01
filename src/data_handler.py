import os
import pandas as pd
import json

def infer_data_type(series):
    """Infer the data type of a pandas Series."""
    if pd.api.types.is_integer_dtype(series):
        return "integer"
    elif pd.api.types.is_float_dtype(series):
        return "float"
    elif pd.api.types.is_bool_dtype(series):
        return "boolean"
    elif pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    else:
        return "string"

def process_file(file_path):
    """Process a single file and return its JSON representation and schema."""
    file_name = os.path.basename(file_path)
    if file_name.endswith('.csv'):
        df = pd.read_csv(file_path)
        tables = {file_name.replace('.csv', ''): df}
    elif file_name.endswith('.xlsx'):
        xls = pd.ExcelFile(file_path)
        tables = {sheet_name: xls.parse(sheet_name) for sheet_name in xls.sheet_names}
    else:
        raise ValueError(f"Unsupported file format: {file_name}")

    json_data = {}
    schema = {"tables": []}

    for table_name, df in tables.items():
        json_data[table_name] = df.to_dict(orient='records')
        table_schema = {
            "name": table_name,
            "description": None,
            "columns": []
        }
        for column in df.columns:
            column_schema = {
                "name": column,
                "datatype": infer_data_type(df[column]),
                "description": None,
                "is_key": False  # Default to False; adjust as needed
            }
            table_schema["columns"].append(column_schema)
        
        # Placeholder for relationships
        table_schema["relationships"] = [
            {
                "related_table": None,
                "key": None,
                "relationship_type": None
            }
        ]

        schema["tables"].append(table_schema)

    return json_data, schema

def process_directory(directory):
    """Process CSV, XLSX, and JSON files in the specified directory."""
    combined_data = []
    combined_schema = {}

    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        
        if filename.endswith('.csv'):
            # Process CSV files
            df = pd.read_csv(file_path)
            combined_data.append(df.to_dict(orient='records'))
            # Update schema based on CSV structure
            combined_schema.update({filename: df.dtypes.to_dict()})

        elif filename.endswith('.xlsx'):
            # Process XLSX files
            df = pd.read_excel(file_path)
            combined_data.append(df.to_dict(orient='records'))
            # Update schema based on XLSX structure
            combined_schema.update({filename: df.dtypes.to_dict()})

        elif filename.endswith('.json'):
            # Process JSON files
            with open(file_path, 'r') as json_file:
                data = json.load(json_file)
                combined_data.append(data)
                # Update schema based on JSON structure
                if isinstance(data, list) and data:
                    combined_schema.update({filename: {key: type(value).__name__ for key, value in data[0].items()}})
                elif isinstance(data, dict):
                    combined_schema.update({filename: {key: type(value).__name__ for key, value in data.items()}})

    return combined_data, combined_schema

def save_json(data, file_path):
    """Save JSON data to a file, prompting if the file already exists."""
    if os.path.exists(file_path):
        overwrite = input(f"File {file_path} already exists. Overwrite? (y/n): ").strip().lower()
        if overwrite != 'y':
            print(f"Skipping save for {file_path}.")
            return
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"Data saved to {file_path}.")

def json_to_excel(json_file_path, excel_file_path):
    """Convert a JSON file with multiple tables into an Excel file with separate sheets."""
    # Load JSON data
    with open(json_file_path, 'r') as f:
        data = json.load(f)

    # Create a Pandas Excel writer using XlsxWriter as the engine
    with pd.ExcelWriter(excel_file_path, engine='xlsxwriter') as writer:
        # Iterate over each table in the JSON data
        for table_name, records in data.items():
            # Convert the records to a DataFrame
            df = pd.DataFrame(records)
            # Write the DataFrame to a sheet named after the table
            df.to_excel(writer, sheet_name=table_name, index=False)

    print(f"Data from {json_file_path} has been written to {excel_file_path}.")

def main(directory, data_output_path, schema_output_path, json_file_path=None, excel_file_path=None):
    """Process a directory and save the combined data and schema to specified paths."""
    combined_data, combined_schema = process_directory(directory)
    save_json(combined_data, data_output_path)
    save_json(combined_schema, schema_output_path)

    # If json_file_path and excel_file_path are provided, convert JSON to Excel
    if json_file_path and excel_file_path:
        json_to_excel(json_file_path, excel_file_path)

# if __name__ == "__main__":  

#     #Example usage
#     json_to_excel("data.json", "Semantic_Model/Semantic_Model.xlsx")
#     directory = "semantic_model/structured_vector_files"
#     data_output_path = "data/data.json"
#     schema_output_path = "data/schema.json"
#     # json_file_path = "data.json"
#     # excel_file_path = "Semantic_Model/Semantic_Model.xlsx"
#     main(directory, data_output_path, schema_output_path, json_file_path = None, excel_file_path = None)
