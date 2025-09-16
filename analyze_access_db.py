#!/usr/bin/env python3
import pyodbc
import os
import json
from typing import Dict, List, Any

def analyze_access_database(db_path: str) -> Dict[str, Any]:
    """Analyze Access database structure and return detailed schema information"""

    if not os.path.exists(db_path):
        return {"error": f"Database file not found: {db_path}"}

    try:
        # Connect to Access database
        conn_str = f'DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={db_path};'
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        analysis = {
            "database_file": db_path,
            "file_size": os.path.getsize(db_path),
            "tables": {},
            "relationships": [],
            "business_rules": []
        }

        # Get all tables
        tables = cursor.tables(tableType='TABLE').fetchall()

        for table in tables:
            table_name = table.table_name
            print(f"Analyzing table: {table_name}")

            # Get columns
            columns = []
            cursor.execute(f"SELECT * FROM [{table_name}] WHERE 1=0")
            for column in cursor.description:
                col_info = {
                    "name": column[0],
                    "type": str(column[1]),
                    "size": column[2] if column[3] is None else column[3],
                    "nullable": column[6],
                    "precision": column[4],
                    "scale": column[5]
                }
                columns.append(col_info)

            # Get primary keys
            try:
                primary_keys = []
                pk_result = cursor.primaryKeys(table=table_name).fetchall()
                for pk in pk_result:
                    primary_keys.append(pk.column_name)
            except:
                primary_keys = []

            # Get foreign keys
            try:
                foreign_keys = []
                fk_result = cursor.foreignKeys(table=table_name).fetchall()
                for fk in fk_result:
                    fk_info = {
                        "column": fk.column_name,
                        "referenced_table": fk.referenced_table_name,
                        "referenced_column": fk.referenced_column_name
                    }
                    foreign_keys.append(fk_info)

                    # Add to relationships
                    analysis["relationships"].append({
                        "from_table": table_name,
                        "from_column": fk.column_name,
                        "to_table": fk.referenced_table_name,
                        "to_column": fk.referenced_column_name
                    })
            except:
                foreign_keys = []

            # Get sample data to understand content
            sample_data = []
            try:
                cursor.execute(f"SELECT TOP 5 * FROM [{table_name}]")
                sample_data = cursor.fetchall()
            except:
                pass

            analysis["tables"][table_name] = {
                "columns": columns,
                "primary_keys": primary_keys,
                "foreign_keys": foreign_keys,
                "sample_data": [[str(cell) if cell is not None else None for cell in row] for row in sample_data]
            }

        # Extract business rules from the structure
        analysis["business_rules"] = extract_business_rules(analysis)

        cursor.close()
        conn.close()

        return analysis

    except Exception as e:
        return {"error": f"Error analyzing database: {str(e)}"}

def extract_business_rules(analysis: Dict[str, Any]) -> List[str]:
    """Extract business rules from database structure"""
    rules = []

    # Look for patterns in table names and columns
    for table_name, table_info in analysis["tables"].items():
        # Colegios (schools) related tables
        if "colegio" in table_name.lower():
            rules.append(f"Table '{table_name}' manages school/colegio data")

        # Product related tables
        if "articulo" in table_name.lower() or "producto" in table_name.lower():
            rules.append(f"Table '{table_name}' manages product data")

        # Size/variation related
        if "talla" in table_name.lower():
            rules.append(f"Table '{table_name}' manages product sizes/variations")

        # Pricing related
        if "precio" in table_name.lower():
            rules.append(f"Table '{table_name}' manages pricing data")

        # Inventory related
        if "inventario" in table_name.lower() or "stock" in table_name.lower():
            rules.append(f"Table '{table_name}' manages inventory data")

        # Check for specific column patterns
        for col in table_info["columns"]:
            col_name = col["name"].lower()
            if "cantidad" in col_name or "cant" in col_name:
                rules.append(f"Column '{col['name']}' in '{table_name}' manages quantities")
            if "descuento" in col_name:
                rules.append(f"Column '{col['name']}' in '{table_name}' manages discounts")

    # Analyze relationships for business logic
    for rel in analysis["relationships"]:
        rules.append(f"Relationship: {rel['from_table']}.{rel['from_column']} -> {rel['to_table']}.{rel['to_column']}")

    return list(set(rules))  # Remove duplicates

def main():
    """Main function to analyze both databases"""
    databases = [
        "C:/julia-confecciones/sistema en uso/Programa Inventario - Fuente/Comercial_jc.mdb",
        "C:/julia-confecciones/sistema en uso/Programa Inventario - Fuente/Mes_trabajo.mdb"
    ]

    results = {}

    for db_path in databases:
        print(f"\nAnalyzing database: {db_path}")
        result = analyze_access_database(db_path)

        if "error" in result:
            print(f"Error: {result['error']}")
        else:
            print(f"Found {len(result['tables'])} tables")
            results[db_path] = result

    # Save results to JSON files
    for db_path, result in results.items():
        filename = f"{os.path.basename(db_path)}_analysis.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        print(f"Analysis saved to {filename}")

    # Print summary
    print("\n" + "="*50)
    print("DATABASE STRUCTURE ANALYSIS SUMMARY")
    print("="*50)

    for db_path, result in results.items():
        if "error" not in result:
            print(f"\nDatabase: {os.path.basename(db_path)}")
            print(f"File size: {result['file_size']:,} bytes")
            print(f"Tables found: {len(result['tables'])}")
            print(f"Relationships found: {len(result['relationships'])}")

            print("\nTables:")
            for table_name in result["tables"].keys():
                print(f"  - {table_name}")

            print("\nBusiness Rules:")
            for rule in result["business_rules"][:10]:  # Show first 10
                print(f"  - {rule}")

if __name__ == "__main__":
    main()