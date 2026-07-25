from services.db_service import DBConnectionManager
import logging
from fastmcp import FastMCP
import json

mcp = FastMCP("Create Task Tool")

@mcp.tool()
def create_task_record(input_data:str):
    """
    Tool to create a task record in the database.
    Input should be a JSON string with the following fields:
    - task_name (str): The name of the task to be created
    - task_status (str): The status of the task to be created
    - start_date (str): The start date of the task to be created
    - end_date (str): The end date of the task to be created
    - task_group_id (int): The task group id to which the task belongs
    - estimated_amount (float): The estimated amount for the task to be created
    """
    try:
        # Parse the JSON input
        data = json.loads(input_data)
        task_name = data.get("task_name")
        task_status = data.get("task_status")
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        task_group_id = data.get("task_group_id")
        estimated_amount = data.get("estimated_amount")

        # Validate required fields
        if not all([task_name, task_status, start_date, end_date, task_group_id is not None, estimated_amount is not None]):
            return "Error: Missing required fields in input data"

    except json.JSONDecodeError:
        return "Error: Invalid JSON input. Please provide a valid JSON string with task details."
    except Exception as e:
        return f"Error parsing input: {str(e)}"

    with DBConnectionManager() as db_manager:
        connection = db_manager.db_connection()
        if connection is None:
            logging.error("Failed to connect to the database. Cannot create task record in task table.")
            return "Error: Failed to connect to the database. Cannot create task record."
        
        cursor = connection.cursor()
        create_task_query = """
                            INSERT INTO task_tasks (task_name, task_status, start_date, end_date, task_group_id, estimated_amount) 
                            VALUES (%s, %s, %s, %s, %s, %s)
                            """
        params = (task_name, task_status, start_date, end_date, task_group_id, estimated_amount)

        try:
            cursor.execute(create_task_query, params)
            connection.commit()
            logging.info("Task record created successfully.")
        except Exception as e:
            logging.error(f"Error creating task record: {e}")
        finally:
            cursor.close()


if __name__ == "__main__":
    mcp.run(transport="stdio")