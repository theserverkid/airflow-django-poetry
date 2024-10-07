# Airflow Poetry Django Operator

This custom Airflow operator allows you to run Django functions within a Poetry-managed environment directly from your Airflow DAGs. It's particularly useful for executing Django tasks that require specific dependencies or virtual environments.

## Features

- Execute Django functions within a Poetry-managed environment
- Automatically sets up Django environment
- Supports passing arguments to the target function
- Handles serialization and deserialization of arguments and return values
- Cleans up temporary files after execution

## Installation

1. Ensure you have Airflow installed in your environment.
2. Copy the `PoetryDjangoOperator` class into your Airflow plugins or DAG file.

## Usage

Here's a basic example of how to use the `PoetryDjangoOperator` in your DAG:

```python
from airflow import DAG
from airflow.utils.dates import days_ago
from your_module import PoetryDjangoOperator

default_args = {
    'owner': 'airflow',
    'start_date': days_ago(1),
}

dag = DAG('poetry_django_example', default_args=default_args, schedule_interval=None)

run_django_task = PoetryDjangoOperator(
    task_id='run_django_task',
    project_settings_file='your_project.settings',
    project_name='your_project',
    project_stage='development',
    function_name='your_function',
    function_file_path='your_app.tasks',
    op_kwargs={'arg1': 'value1', 'arg2': 'value2'},
    dag=dag,
)
```

## Parameters

- `project_settings_file`: The Django settings module (e.g., 'myproject.settings')
- `project_name`: Your Django project name
- `project_stage`: The stage of your project (e.g., 'development', 'production')
- `function_name`: The name of the Django function to execute
- `function_file_path`: The import path to the file containing your function
- `string_args`: Optional list of string arguments to pass to the function
- `op_args`: Optional list of positional arguments to pass to the function
- `op_kwargs`: Optional dictionary of keyword arguments to pass to the function
- `templates_dict`: Optional dictionary of templates to render

## How It Works

1. The operator creates temporary files for input arguments, output, and the Python script.
2. It sets up the Django environment using the provided settings.
3. The target function is imported and executed with the provided arguments.
4. Results are pickled and saved to the output file.
5. The operator reads the results and cleans up temporary files.
6. Poetry is used to manage the Python environment and dependencies.

## Requirements

- Airflow
- Poetry
- Django

## Notes

- Ensure that your Airflow environment has access to your Django project and its dependencies.
- The operator assumes that Poetry is installed or can be installed in the execution environment.
- Make sure your Django project's `pyproject.toml` file is properly configured with all necessary dependencies.

## Contributing

Contributions to improve the operator are welcome. Please feel free to submit issues or pull requests.