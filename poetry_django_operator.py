import datetime
import os
import pickle
import random
import string
from typing import Dict, Iterable, List, Optional

from airflow.hooks.subprocess import SubprocessHook
from airflow.models import BaseOperator
from airflow.utils.python_virtualenv import write_python_script


class PoetryDjangoOperator(BaseOperator):
    def __init__(
            self,
            *,
            project_name: str = None,
            project_stage: str = None,
            function_name: str = None,
            function_file_path: str = None,
            op_args: Optional[List] = None,
            op_kwargs: Optional[Dict] = None,
            string_args: Optional[Iterable[str]] = None,
            templates_dict: Optional[Dict] = None,
            templates_exts: Optional[List[str]] = None,
            **kwargs,
    ):
        self.string_args = string_args or []
        self.project_name = project_name
        self.project_stage = project_stage
        self.function_name = function_name
        self.function_file_path = function_file_path
        self.op_args = op_args or []
        self.op_kwargs = op_kwargs or {}
        self.templates_dict = templates_dict

        super().__init__(**kwargs, )

    def _write_args(self, filename):
        if self.op_args or self.op_kwargs:
            with open(filename, "wb") as file:
                pickle.dump({"args": self.op_args, "kwargs": self.op_kwargs}, file)

    def _write_string_args(self, filename):
        with open(filename, "w") as file:
            file.write("\n".join(map(str, self.string_args)))

    def _write_script_file(self, script_filename, script_template_file):
        python_source = (
            "def execution_function():\n"
            f"    from {self.function_file_path} import {self.function_name}\n"
            f"    {self.function_name}()\n"
        )

        write_python_script(
            jinja_context=dict(
                op_args=self.op_args,
                op_kwargs=self.op_kwargs,
                pickling_library="pickle",
                python_callable="execution_function",
                python_callable_source=python_source,
            ),
            filename=script_template_file,
            render_template_as_native_obj=self.dag.render_template_as_native_obj,
        )

        with open(script_filename, "w") as script_file:
            script_file.write("import os \n")
            script_file.write("import django \n")
            script_file.write(
                f'os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vsuite.config.settings") \n'
            )
            script_file.write("print('Current Working Directory ' , os.getcwd()) \n\n")
            script_file.write("print('Working Dir Files' , os.listdir()) \n\n")
            script_file.write("print('Current Base DIR' , os.getenv('BASE_DIR')) \n\n")
            script_file.write("BASE_DIR = os.path.dirname(os.path.dirname(__file__)) \n\n")
            script_file.write("print('Current Base DIR' , os.getenv('BASE_DIR')) \n\n")
            script_file.write("django.setup() \n\n")
            for template_line in open(script_template_file):
                script_file.write(template_line)

    def _read_result(self, filename):
        if os.stat(filename).st_size == 0:
            return None
        with open(filename, "rb") as file:
            try:
                return pickle.load(file)
            except ValueError:
                self.log.error("Error deserializing result.")
                raise

    def execute(self, context: Dict):
        context.update(self.op_kwargs)
        context["templates_dict"] = self.templates_dict

        # TODO kwargs support
        op_kwargs = {}
        self.op_kwargs = op_kwargs

        if self.templates_dict:
            self.op_kwargs["templates_dict"] = self.templates_dict
        random_string = str(datetime.datetime.now().strftime("%d-%m-%Y")) + "--" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        tmp_dir = f'/opt/airflow/dags/{self.project_stage}/{self.project_name}'

        input_filename = os.path.join(tmp_dir, f"{random_string}-script-airflow-system.in")
        output_filename = os.path.join(tmp_dir, f"{random_string}-script-airflow-system.out")
        string_args_filename = os.path.join(tmp_dir, f"{random_string}-string_args-airflow-system.txt")
        script_filename = os.path.join(tmp_dir, f"{random_string}-script-airflow-system.py")
        script_template_filename = os.path.join(tmp_dir, f"{random_string}-script_template-airflow-system.py")

        self._write_args(input_filename)
        self._write_string_args(string_args_filename)
        self._write_script_file(script_filename, script_template_filename)

        poetry_url = "curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py"

        SubprocessHook().run_command(
            command=['bash',
                     '-c',
                     f" poetry --help || {poetry_url} | python  "
                     ],
            env=os.environ.copy(),
            output_encoding='utf-8'
        )

        SubprocessHook().run_command(
            command=['bash',
                     '-c',
                     f" cd /opt/airflow/dags/{self.project_stage}/{self.project_name} && "
                     f" export PIP_USER=false && "
                     f" source $HOME/.poetry/env && "
                     f" poetry lock && "
                     f" poetry install && "
                     f" poetry run python3 {script_filename} {input_filename} {output_filename} {string_args_filename}"
                     ],
            env=os.environ.copy(),
            output_encoding='utf-8'
        )

        return_value = self._read_result(output_filename)

        try:
            os.remove(input_filename)
        except FileNotFoundError:
            pass

        try:
            os.remove(output_filename)
        except FileNotFoundError:
            pass

        try:
            os.remove(string_args_filename)
        except FileNotFoundError:
            pass

        try:
            os.remove(script_filename)
        except FileNotFoundError:
            pass
        try:
            os.remove(script_template_filename)
        except FileNotFoundError:
            pass

        self.log.info("Done. Returned value was: %s", return_value)
        return return_value
