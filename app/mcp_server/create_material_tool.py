from services.db_service import DBConnectionManager
import logging
from fastmcp import FastMCP
import json

mcp = FastMCP("Create Material Tool")

@mcp.tool()
def create_material_record(input_data:str):
    """
    Tool to create a material record in the database.
    Input should be a JSON string with the following fields:
    - material_name (str): The name of the material to be created
    - specification (str): The specification of the material to be created
    - subcategory (int): The subcategory id of the material to be created
    - brand_name (str): The brand name of the material to be created
    - typeOfMaterial (str): The type of the material to be created
    - organization_id (int): The organization id to which the material belongs
    """
    try:
        # Parse the JSON input
        data = json.loads(input_data)
        material_name = data.get("material_name")
        specification = data.get("specification")
        subcategory = data.get("subcategory")
        brand_name = data.get("brand_name")
        typeOfMaterial = data.get("typeOfMaterial")
        organization_id = data.get("organization_id")

        # Validate required fields
        if not all([material_name, specification, subcategory is not None, brand_name, typeOfMaterial, organization_id is not None]):
            return "Error: Missing required fields in input data"

    except json.JSONDecodeError:
        return "Error: Invalid JSON input. Please provide a valid JSON string with material details."
    except Exception as e:
        return f"Error parsing input: {str(e)}"

    with DBConnectionManager() as db_manager:
        connection = db_manager.db_connection()
        if connection is None:
            logging.error("Failed to connect to the database. Cannot create material record in organization material table.")
            return "Error: Failed to connect to the database. Cannot create material record."
        
        cursor = connection.cursor()
        create_material_query = """
                            INSERT INTO organization_materiallibrary (material_name, specification, subcategory, brand_name, type, organization_id) 
                            VALUES (%s, %s, %s, %s, %s, %s)
                            """
        params = (material_name, specification, subcategory, brand_name, typeOfMaterial, organization_id)

        try:
            cursor.execute(create_material_query, params)
            connection.commit()
            logging.info("Material record created successfully.")
        except Exception as e:
            logging.error(f"Error creating material record: {e}")
        finally:
            cursor.close()


if __name__ == "__main__":
    mcp.run(transport="stdio")