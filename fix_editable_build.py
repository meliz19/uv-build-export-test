import subprocess
import tempfile
import shutil
from pathlib import Path
import click
import toml

def find_monorepo_root():
    """Finds the monorepo root by locating the project-consumer directory."""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / "project-a-consumer").exists():
            return current
        current = current.parent
    raise RuntimeError("Monorepo root not found.")

def get_version_from_pyproject(pyproject_path):
    """Extracts version from a given pyproject.toml file."""
    with pyproject_path.open("r", encoding="utf-8") as f:
        data = toml.load(f)
        return data["project"]["version"]

def create_temporary_build_env(monorepo_root):
    """Creates a temporary directory for a clean build environment."""
    temp_dir = Path(tempfile.mkdtemp())
    click.echo(f"Creating temporary build environment at {temp_dir}")

    # Copy project-consumer to temp_dir
    project_consumer_src = monorepo_root / "project-a-consumer"
    project_consumer_temp = temp_dir / "project-a-consumer"
    shutil.copytree(
        project_consumer_src.as_posix(), 
        project_consumer_temp.as_posix(),
        ignore=shutil.ignore_patterns(".venv", "dist", "uv.lock"))

    # Read dependencies from the original project-consumer's pyproject.toml
    pyproject_path = project_consumer_temp / "pyproject.toml"
    with pyproject_path.open("r", encoding="utf-8") as f:
        data = toml.load(f)

    editable_dependencies = data["tool"]["uv"]["sources"]
    dependencies = data["project"]["dependencies"]
    editable_dependencies_to_delete = []

    for dep_name, dep_value in editable_dependencies.items():
        if dep_name in dependencies:
            editable_dependencies_to_delete.append(dep_name)
            if isinstance(dep_value, dict) and dep_value.get("path"):
                dep_path = Path(dep_value["path"])
                dep_pyproject = dep_path / "pyproject.toml"

                if dep_pyproject.exists():
                    fixed_version = get_version_from_pyproject(dep_pyproject)
                    dep_name_index = dependencies.index(dep_name)
                    dependencies[dep_name_index] = f"{dep_name}=={fixed_version}"
                    click.echo(f"Resolved {dep_name} == {fixed_version}")
    
    if editable_dependencies_to_delete:
        for dep in editable_dependencies_to_delete:
            del data["tool"]["uv"]["sources"][dep]
    
    if not data["tool"]["uv"]["sources"]:
        del data["tool"]["uv"]["sources"]

    # Write the modified pyproject.toml to the temporary directory
    with pyproject_path.open("w", encoding="utf-8") as f:
        toml.dump(data, f)

    return temp_dir

@click.command()
@click.option("--build", is_flag=True, help="Build project-consumer in an isolated environment.")
def main(build):
    """Creates a temporary environment with fixed dependency versions and builds project-consumer."""
    monorepo_root = find_monorepo_root()
    
    temp_env = create_temporary_build_env(monorepo_root)

    if build:
        # click.echo("Installing dependencies in isolated environment...")
        # subprocess.run(["uv", "sync", "--directory", f"{temp_env.as_posix()}/project-a-consumer"], cwd=temp_env / "project-a-consumer", check=True)
        
        click.echo("Building project-consumer...")
        subprocess.run(["uv", "build", "--directory", f"{temp_env.as_posix()}/project-a-consumer"], cwd=temp_env / "project-a-consumer", check=True)

        shutil.copytree(temp_env / "project-a-consumer" / "dist", monorepo_root / "project-a-consumer" / "dist" )

    click.echo(f"Build completed in {temp_env}")
    click.echo("temp directory to be deleted...")



if __name__ == "__main__":
    main()
