"""Command line interface for wanpc."""
import json
from pathlib import Path
from typing import Optional, Dict, Any
import typer
from rich.console import Console
from rich.table import Table
from rich.text import Text
from cookiecutter.main import cookiecutter
import tomli, tomli_w
from rich.prompt import Prompt, Confirm
import shutil
from validate_pyproject import api, errors
import subprocess
import re
import webbrowser, threading, time

from .config import Config
from . import logger

def format_help(text: str) -> str:
    """Format help text with proper word wrapping."""
    return str(Text.from_markup(text).plain)

def get_config() -> Dict[str, Any]:
    """Load and return the configuration."""
    cfg = Config()
    return cfg._config

def save_config(cfg: Dict[str, Any]) -> None:
    """Save configuration."""
    config = Config()
    config._config = cfg
    config._save_config()

def is_valid_email(email: str) -> bool:
    """Validate an email address using a regular expression."""
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email) is not None

def load_cookiecutter_config(template_path: str) -> Dict[str, Any]:
    """Load cookiecutter.json from template directory."""
    try:
        config_path = Path(template_path).expanduser().resolve() / "cookiecutter.json"
        if not config_path.exists():
            raise typer.BadParameter(f"No cookiecutter.json found in {template_path}")
        
        with open(config_path) as f:
            return json.load(f)
    except Exception as e:
        raise typer.BadParameter(f"Failed to load cookiecutter.json: {str(e)}")

def prompt_for_defaults(template_path: str, existing_defaults: Dict[str, Any] = None) -> Dict[str, Any]:
    """Prompt user for default values based on cookiecutter.json."""
    cookiecutter_config = load_cookiecutter_config(template_path)
    defaults = {}
    existing_defaults = existing_defaults or {}

    console.print("\n[bold]Template variables from cookiecutter.json:[/bold]")
    console.print("[yellow]Press Enter to skip setting a default value[/yellow]\n")

    for key, default_value in cookiecutter_config.items():
        existing_value = existing_defaults.get(key)
        prompt_text = f"[cyan]{key}[/cyan]"
        if existing_value is not None:
            prompt_text += f" [yellow](current: {existing_value})[/yellow]"
        elif default_value is not None:
            prompt_text += f" [dim](cookiecutter default: {default_value})[/dim]"
        
        value = Prompt.ask(prompt_text, default="")
        if value:  # Only set if user provided a value
            defaults[key] = value

    return defaults

app = typer.Typer(
    help=format_help("""\
A wrapper around cookiecutter for easy project templating.\n
[bold]Description:[/bold]\n
\tA command-line tool that simplifies project creation using cookiecutter templates.\n
\tSupports template management and default values at both template and global levels.\n
[bold]Commands:[/bold]\n
\t[cyan]list[/cyan]     List available templates\n
\t[cyan]create[/cyan]   Create a new project from a template\n
\t[cyan]config[/cyan]   Manage templates and default values\n
[bold]Quick Start:[/bold]\n
\t1. Add a template:\n
\t   $ wanpc config add-template --name python-pkg --path ~/templates/python\n
\t2. Set some defaults:\n
\t   $ wanpc config set-default --name python-pkg --key author --value "Your Name"\n
\t   $ wanpc config set-global-default --key license --value MIT\n
\t3. Create a project:\n
\t   $ wanpc create python-pkg\n
For detailed help on any command, use:\n
\t$ wanpc COMMAND --help\n""")
)
console = Console()

def display_template_info(template_name: str, template_data: Dict[str, Any], cfg: Dict[str, Any]) -> None:
    """Display detailed information about a template."""
    console.print(f"\n[bold cyan]Template:[/bold cyan] {template_name}")
    
    if "description" in template_data:
        console.print(f"[bold]Description:[/bold] {template_data['description']}")
    
    console.print(f"[bold]Path:[/bold] {template_data['path']}")
    
    # Show template-specific defaults
    defaults = template_data.get("defaults", {})
    if defaults:
        console.print("\n[bold]Template Defaults:[/bold]")
        for key, value in defaults.items():
            console.print(f"  [cyan]{key}[/cyan] = {value}")
    
    # Show applicable global defaults
    global_defaults = cfg.get("global_defaults", {})
    if global_defaults:
        console.print("\n[bold]Applicable Global Defaults:[/bold]")
        for key, value in global_defaults.items():
            if key not in defaults:  # Only show if not overridden by template default
                console.print(f"  [cyan]{key}[/cyan] = {value}")


#todo fix alias
@app.command(name="list")
def my_list_command(
    show_defaults: bool = typer.Option(
        False,
        "--show-defaults", "-d",
        help=format_help("[cyan]--show-defaults[/cyan] displays both template-specific and global default values")
    )
):
    """List available templates\n
    \tShows all configured templates and their paths.\n
    \tUse --show-defaults to see all configured default values.\n
    \nExamples:\n
    \t$ wanpc list\n
    \t$ wanpc list --show-defaults"""
    table = Table(title="Available Templates")
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="yellow")
    table.add_column("Path", style="green")

    try:
        cfg = get_config()
        templates = cfg.get("templates", {})
        
        if not templates:
            console.print("[yellow]No templates configured. Use 'wanpc config add-template' to add one.[/yellow]")
            return
        
        if show_defaults:
            for name, data in templates.items():
                display_template_info(name, data, cfg)
        else:
            for name, data in templates.items():
                table.add_row(
                    name,
                    data.get("description", "No description"),
                    data.get("path", "Not set")
                )
            console.print(table)

    except Exception as e:
        console.print(f"[red]Error listing templates: {str(e)}[/red]")
        raise typer.Exit(1)
    
#@app.command()
def run_docs(
    target_dir: Optional[Path] = typer.Argument(
        None,
        help="The target directory where the docs folder will be created (defaults to current directory)"
    ),
    port: int = typer.Option(
        8000,
        "--port",
        "-p",
        help="Port to serve documentation on"
    )
):
    """Run the documentation using Sphinx with auto-rebuild on changes."""
    try:
        if target_dir is None:
            target_dir = Path.cwd()
        elif Path(target_dir/"docs"/"_build"/"html").exists():
            target_dir = Path(target_dir).expanduser().resolve()
            target_dir = target_dir/"docs"/"_build"/"html"
        else:
            target_dir = Path(target_dir).expanduser().resolve()

        docs_path = target_dir / "docs"
        if not docs_path.exists():
            console.print(f"[red]Error: The docs folder does not exist in {docs_path}[/red]")
            raise typer.Exit(1)

        # Build and serve documentation with auto-reload
        console.print("[green]Starting documentation server with auto-rebuild...[/green]")
        
        
        # Use sphinx-autobuild instead of manual server
        subprocess.run([
            "poetry", "run", "sphinx-autobuild",
            str(docs_path / "source"),  # Source dir
            str(docs_path / "_build" / "html"),  # Output dir
            f"--port={port}",  # Specify port
            "--watch", str(target_dir),  # Watch project directory
            "--open-browser",  # Auto-open browser
            "--re-ignore", ".*/_build/.*",  # Ignore build directory
        ], check=True, cwd=target_dir)

        # Open browser after a short delay
        def open_browser():
            time.sleep(2) 
            webbrowser.open(f"http://localhost:{port}")
            
        threading.Thread(target=open_browser).start()

    except Exception as e:
        console.print(f"[red]Error serving documentation: {str(e)}[/red]")
        raise typer.Exit(1)   


def run_docs_main():
    typer.run(run_docs)


@app.command()
def add_docs(
    target_dir: Optional[Path] = typer.Argument(
        None,
        help="The target directory where the docs folder will be created (defaults to current directory)"
    )
):
    """Add a docs folder with initial documentation structure."""
    docs_made = False
    docs_path = ""
    try:
        if target_dir is None:
            target_dir = Path.cwd()
        else:
            target_dir = Path(target_dir).expanduser().resolve()

        pyproject_path = target_dir / "pyproject.toml"
        if not pyproject_path.exists():
            console.print(f"[red]Error: pyproject.toml not found in {target_dir}[/red]")
            raise typer.Exit(1)

        with open(pyproject_path, "rb") as f:
            pyproject_data = tomli.load(f)
            project_data = pyproject_data.get("project", pyproject_data.get("tool", {}).get("poetry", {}))
            name = project_data.get("name")
            authors = project_data.get("authors", [])
            if authors and isinstance(authors[0], str):
                # Convert authors to list of objects
                authors = [{"name": author.split("<")[0].strip(), "email": author.split("<")[1].strip(">").strip()} for author in authors]
            release = project_data.get("version", "0.1.0")
            year = 2025
            
            if not name:
                console.print(f"[red]Error: 'name' not found in pyproject.toml[/red]")
                raise typer.Exit(1)
            
            if not is_valid_email(authors[0]["email"]):
                console.print(f"[red]Error: Invalid email address found in pyproject.toml[/red]")
                raise typer.Exit(1)


        docs_path = target_dir / "docs"
        if docs_path.exists():
            console.print(f"[red]Error: The docs folder already exists in {docs_path}[/red]")
            raise typer.Exit(1)

        # Get the template path from the configuration
        cfg = get_config()
        templates = cfg.get("templates", {})
        if not templates:
            console.print(f"[red]Error: No templates found in configuration[/red]")
            raise typer.Exit(1)

        # Use the path of the first template to find the docs template
        first_template_path = Path(next(iter(templates.values()))["path"])
        template_path = first_template_path.parent / "docs" / "docs"
        
        if not template_path.exists():
            console.print(f"[red]Error: Docs template path does not exist: {template_path}[/red]")
            raise typer.Exit(1)
        
        requirements_path = template_path.parent.parent / "requirements.txt"

        # Copy the template to the target directory
        shutil.copytree(template_path, docs_path)
        docs_made = True

        # Modify the copied files according to the package in question
        # For example, you can replace placeholders in the copied files
        for file_path in docs_path.rglob('*'):
            if file_path.is_file():
                content = file_path.read_text()
                content = content.replace('{{ cookiecutter.project_slug }}', (name))
                content = content.replace('{{ cookiecutter.project_name }}', (name))
                content = content.replace('{{ cookiecutter.author_name }}', (authors[0]["name"]))
                content = content.replace('{{ cookiecutter.version }}', (release))
                content = content.replace('{{ cookiecutter.release }}', (release))
                content = content.replace('{{ cookiecutter.year }}', str(year))
                content = content.replace('{{ cookiecutter.project_slug.upper() }}', name.upper())
                file_path.write_text(content) 

        # Add documentation dependencies to pyproject.toml
        if not requirements_path.exists():
            console.print(f"[red]Error: requirements.txt not found in {template_path}[/red]")
            raise typer.Exit(1)

        with open(requirements_path, "r") as req_file:
            doc_dependencies = [line.strip() for line in req_file if line.strip() and not line.startswith("#") and not line.startswith('{')]

        # Add documentation dependencies to pyproject.toml
        doc_dependencies = {
            "sphinx": ">=7.1.2",
            "sphinx-autodoc-typehints": ">=1.24.0",
            "sphinx-notfound-page": ">=1.0.0",
            "sphinx-autobuild": ">=2021.3.14",
            "sphinx-rtd-theme": ">=1.3.0",
            "nbsphinx": ">=0.9.3",
            "sphinx-togglebutton": ">=0.3.2",
            "myst-parser": ">=2.0.0",
            "sphinxcontrib-mermaid": ">=0.9.2",
            "sphinx-design": ">=0.5.0",
            "sphinx-pydantic": ">=0.1.1",
            "myst-nb" : ">=0.13.1",
            "nbsphinx" : ">=0.9.3",
        }

        if "tool" not in pyproject_data:
            pyproject_data["tool"] = {}
        if "poetry" not in pyproject_data["tool"]:
            pyproject_data["tool"]["poetry"] = {}
        if "group" not in pyproject_data["tool"]["poetry"]:
            pyproject_data["tool"]["poetry"]["group"] = {}
        if "docs" not in pyproject_data["tool"]["poetry"]["group"]:
            pyproject_data["tool"]["poetry"]["group"]["docs"] = {}
        if "dependencies" not in pyproject_data["tool"]["poetry"]["group"]["docs"]:
            pyproject_data["tool"]["poetry"]["group"]["docs"]["dependencies"] = {}

        # Ensure no duplicates are added
        existing_dependencies = pyproject_data["tool"]["poetry"]["group"]["docs"]["dependencies"]
        for dep, version in doc_dependencies.items():
            existing_dependencies[dep] = version

        # Updating pyproject.toml to pass validate-pyproject
        pyproject_data["project"]["authors"] = authors
        if "version" not in pyproject_data["project"]:
            pyproject_data["project"]["version"] = release
        if "name" not in pyproject_data["project"]:
            pyproject_data["project"]["name"] = name

        with open(pyproject_path, "wb") as f:
            tomli_w.dump(pyproject_data, f)

        console.print(f"[green]Docs folder created successfully in {docs_path}[/green]")
        console.print(f"[green]Documentation dependencies added to pyproject.toml[/green]")

        # now we can use validate-pyproject
        validator = api.Validator()

        try:
            validator(pyproject_data)
            console.print(f"[green]Created pyproject.toml file is valid[/green]")
        except errors.ValidationError as ex:
            print(f"Invalid Document: {ex.message}")

        yml_path = first_template_path.parent / ".gitlab-ci.yml"
        if yml_path.exists() and not (target_dir / ".gitlab-ci.yml").exists():
            with open(yml_path, "r") as yml_file:
                yml_content = yml_file.read()
            yml_content = yml_content.replace("$PROJECT_NAME", name)
            yml_content = yml_content.replace("{{ cookiecutter.project_slug }}", name)
            with open(target_dir / ".gitlab-ci.yml", "w") as yml_file:
                yml_file.write(yml_content)

        # Install documentation dependencies using poetry
        console.print("[green]Installing documentation dependencies using Poetry...[/green]")
        subprocess.run(["poetry", "install", "--with", "docs"], check=True, cwd=target_dir)

        # Build the HTML documentation using Sphinx
        subprocess.run(["poetry","lock"], check=True, cwd=target_dir)
        subprocess.run(["poetry", "install"], check=True, cwd=target_dir)
        console.print("[green]Building HTML documentation using Sphinx...[/green]")
        subprocess.run(["poetry", "run", "sphinx-apidoc", "-o", str(docs_path / "source"), name], check=True, cwd=target_dir)
        console.print(f"[green]HTML documentation built successfully in {docs_path / '_build' / 'html'}[/green]")


    except Exception as e:
        console.print(f"[red]Error creating docs folder: {str(e)}[/red]")
        if docs_made:
            shutil.rmtree(docs_path)
            console.print(f"[yellow]Deleted {docs_path} due to failed installation[/yellow]")
        raise typer.Exit(1)

@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def create(
    ctx: typer.Context,
    template: str = typer.Argument(
        ...,
        help=format_help("[cyan]template[/cyan] is the name of the template to use (run [cyan]wanpc list[/cyan] to see available templates)")
    ),
    output_dir: Path = typer.Option(
        Path.cwd(),
        "--output-dir", "-o",
        help=format_help("[cyan]--output-dir[/cyan] specifies where to create the project (defaults to current directory)")
    ),
    no_defaults: bool = typer.Option(
        False,
        "--no-defaults",
        help=format_help("[cyan]--no-defaults[/cyan] skips using any default values from config")
    ),
):
    """Create a new project from a template\n
    \tUses the specified template to create a new project.\n
    \tBy default, it will:\n
    \t\t1. Use template-specific defaults if available\n
    \t\t2. Fall back to global defaults if no template default exists\n
    \t\t3. Create the project in the current directory\n
    \nExamples:\n
    \t$ wanpc create python-pkg\n
    \t$ wanpc create python-pkg --output-dir ~/projects/new-pkg\n
    \t$ wanpc create python-pkg --no-defaults\n
    \t$ wanpc create python-pkg --author "John Doe" --license MIT  # Override defaults"""
    try:
        cfg = get_config()
        templates = cfg.setdefault("templates", {})
        
        if template not in templates:
            console.print(f"[red]Error: Template '{template}' not found[/red]")
            raise typer.Exit(1)
            
        template_data = templates[template]
        template_path = template_data.get("path")
        
        if not template_path:
            console.print(f"[red]Error: No path set for template '{template}'[/red]")
            raise typer.Exit(1)
        
        # Verify template path exists
        template_path = Path(template_path).expanduser().resolve()
        if not template_path.exists():
            console.print(f"[red]Error: Template path does not exist: {template_path}[/red]")
            raise typer.Exit(1)

        # Load cookiecutter.json to get required values
        cookiecutter_config = load_cookiecutter_config(str(template_path))
        if not cookiecutter_config:
            console.print(f"[red]Error: No cookiecutter.json found in {template_path}[/red]")
            raise typer.Exit(1)

        # Debug: Log cookiecutter config contents
        logger.debug("Cookiecutter config contents:")
        for key, value in cookiecutter_config.items():
            logger.debug(f"  {key}: {value} (type: {type(value)})")

        # Parse any command line overrides
        extra_context = {}
        for item in ctx.args:
            if item.startswith("--"):
                key = item[2:]  # Remove --
                if key in cookiecutter_config and len(ctx.args) > ctx.args.index(item) + 1:
                    value = ctx.args[ctx.args.index(item) + 1]
                    if not value.startswith("--"):
                        extra_context[key] = value
                        console.print(f"[yellow]Using override for {key}: {value}[/yellow]")

        # Add defaults if enabled (but don't override command line values)
        if not no_defaults:
            try:
                merged_defaults = Config.get_merged_defaults(cfg, template)
                if merged_defaults:
                    # Only add defaults for keys that weren't specified on command line
                    for key, value in merged_defaults.items():
                        if key not in extra_context:
                            extra_context[key] = value
                            if key in template_data.get("defaults", {}):
                                if key in cfg.get("global_defaults", {}):
                                    console.print(f"  {key}: {value} [yellow](template default, overriding global)[/yellow]")
                                else:
                                    console.print(f"  {key}: {value} [yellow](template default)[/yellow]")
                            else:
                                console.print(f"  {key}: {value} [blue](global default)[/blue]")
            except KeyError:
                console.print(f"[red]Error: Template '{template}' not found in config[/red]")
                raise typer.Exit(1)

        # Prompt for any missing values
        console.print("\n[bold cyan]Please provide values for the following:[/bold cyan]")
        for key, default_value in cookiecutter_config.items():
            try:
                logger.debug(f"Processing key: {key}, value: {default_value} (type: {type(default_value)})")
                
                if key not in extra_context and not key.startswith('_'):  # Skip internal keys
                    # Skip derived values (those that are Jinja2 templates)
                    if type(default_value) == str and default_value.find('{{') != -1:
                        logger.debug(f"Skipping template value: {key}")
                        continue
                    
                    # For list values, only show as choices, not as default
                    if type(default_value) == list:
                        choices = [str(choice) for choice in default_value]
                        value = Prompt.ask(
                            f"[cyan]{key}[/cyan] [dim](choices: {', '.join(choices)})[/dim]",
                            choices=choices,
                            default=choices[0]
                        )
                    else:
                        # For non-list values, show default
                        prompt = f"[cyan]{key}[/cyan]"
                        if default_value:
                            prompt += f" [dim](default: {default_value})[/dim]"
                        value = Prompt.ask(prompt, default=str(default_value) if default_value else "")
                        
                    extra_context[key] = value
            except Exception as e:
                logger.error(f"Error processing {key}: {str(e)}")
                raise

        try:
            # Create output directory if it doesn't exist
            output_dir = Path(output_dir).expanduser().resolve()
            output_dir.mkdir(parents=True, exist_ok=True)

            # Run cookiecutter with our collected values
            cookiecutter(
                str(template_path),
                output_dir=str(output_dir),
                extra_context=extra_context,
                no_input=True  # We've already collected all values
            )
            console.print(f"[green]Created project from template '{template}'[/green]")
        except Exception as e:
            console.print(f"[red]Error creating project: {str(e)}[/red]")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error creating project: {str(e)}[/red]")
        raise typer.Exit(1)

@app.command()
def config(
    action: str = typer.Argument(
        ...,
        help=format_help("""\
[bold]Action to perform:[/bold]\n
\t[cyan]show[/cyan]                 Display current configuration\n
\t[cyan]config-path[/cyan]          Show configuration file path\n
\t[cyan]add-template[/cyan]         Add a new template\n
\t[cyan]set-description[/cyan]      Set template description\n
\t[cyan]set-default[/cyan]          Set template-specific default\n
\t[cyan]set-global-default[/cyan]   Set global default\n
\t[cyan]remove-template[/cyan]      Remove a template\n
\t[cyan]remove-default[/cyan]       Remove template default\n
\t[cyan]remove-global-default[/cyan] Remove global default\n
\n[bold]Examples:[/bold]\n
\t$ wanpc config show\n
\t$ wanpc config config-path\n
\t$ wanpc config add-template --name python-pkg --path ~/templates/python\n
\t$ wanpc config set-description --name python-pkg\n
\t$ wanpc config set-default --name python-pkg --key author --value "John Doe"\n
\t$ wanpc config set-global-default --key license --value MIT""")
    ),
    name: Optional[str] = typer.Option(
        None,
        "--name", "-n",
        help=format_help("[cyan]--name[/cyan] specifies the template name (required for template operations)")
    ),
    path: Optional[str] = typer.Option(
        None,
        "--path", "-p",
        help=format_help("[cyan]--path[/cyan] specifies the template path (required when adding templates)")
    ),
    key: Optional[str] = typer.Option(
        None,
        "--key", "-k",
        help=format_help("[cyan]--key[/cyan] specifies the default key name (required for default operations)")
    ),
    value: Optional[str] = typer.Option(
        None,
        "--value", "-v",
        help=format_help("[cyan]--value[/cyan] specifies the value to set (required when setting defaults)")
    ),
    description: Optional[str] = typer.Option(
        None,
        "--description", "-d",
        help=format_help("[cyan]--description[/cyan] specifies the template description")
    ),
):
    """Manage wanpc configuration\n
    \tAllows managing templates and their default values.\n
    \tYou can add/remove templates and set default values at both\n
    \tthe template and global levels.\n
    \n\tTemplate defaults take precedence over global defaults."""
    try:
        cfg = get_config()

        if action == "config-path":
            console.print("\n[bold]Configuration file location:[/bold]")
            config_file = Config().config_file
            console.print(f"[cyan]{config_file}[/cyan]")
            
            if config_file.exists():
                console.print("[green]Status: File exists[/green]")
                size = config_file.stat().st_size
                console.print(f"Size: {size} bytes")
            else:
                console.print("[yellow]Status: File does not exist yet[/yellow]")
                console.print("A new configuration file will be created when needed")
            return

        if action == "show":
            if not cfg:
                console.print("[yellow]No configuration found.[/yellow]")
                return
            console.print("\n[bold]Current Configuration:[/bold]")
            console.print(json.dumps(cfg, indent=2))
            return

        if action == "add-template":
            # Interactive mode if required values are not provided
            if not name:
                name = Prompt.ask("[cyan]Enter template name[/cyan]")
                if not name:
                    raise typer.BadParameter("Template name is required")

            if not path:
                path = Prompt.ask("[cyan]Enter template path[/cyan]")
                if not path:
                    raise typer.BadParameter("Template path is required")

            if not description:
                description = Prompt.ask(
                    "[cyan]Enter template description[/cyan] [dim](optional, press Enter to skip)[/dim]",
                    default="No description"
                )

            # Convert relative path to absolute path
            template_path = Path(path)
            if not template_path.is_absolute():
                template_path = Path.cwd() / template_path
            template_path = template_path.resolve()
            
            # Validate path exists
            if not template_path.exists():
                console.print(f"[red]Error: Template path does not exist: {template_path}[/red]")
                raise typer.Exit(1)
                
            # Validate cookiecutter.json exists
            cookiecutter_json = template_path / "cookiecutter.json"
            if not cookiecutter_json.exists():
                console.print(f"[red]Error: No cookiecutter.json found in {template_path}[/red]")
                raise typer.Exit(1)

            templates = cfg.setdefault("templates", {})
            templates[name] = {
                "path": str(template_path),
                "defaults": {},
                "description": description
            }

            save_config(cfg)
            console.print(f"[green]Added template '{name}' with path: {template_path}[/green]")
            if description and description != "No description":
                console.print(f"[green]Description: {description}[/green]")
            return

        if action == "set-description":
            if not name:
                name = typer.prompt("Enter the name of the template")
            if not description:
                description = typer.prompt("Enter the description of the template")

            templates = cfg.get("templates", {})
            if name not in templates:
                raise typer.BadParameter(f"Template '{name}' not found")

            templates[name]["description"] = description if description else "No description"
            save_config(cfg)
            console.print(f"[green]Updated description for {name}[/green]")
            return

        if action == "set-default":
            # if not name or not key or value is None:
            #     raise typer.BadParameter("--name, --key, and --value are required")

            if not name:
                name = typer.prompt("Enter the name of the template")
            if not key:
                key = typer.prompt("Enter the key of the template")
            if not value:
                value = typer.prompt("Enter the value of the template")

            templates = cfg.get("templates", {})
            if name not in templates:
                raise typer.BadParameter(f"Template '{name}' not found")

            template_data = templates[name]
            template_path = template_data["path"]

            # Verify key exists in cookiecutter.json
            cookiecutter_config = load_cookiecutter_config(template_path)
            if key not in cookiecutter_config:
                raise typer.BadParameter(
                    f"Key '{key}' not found in cookiecutter.json. "
                    f"Available keys: {', '.join(cookiecutter_config.keys())}"
                )

            template_data.setdefault("defaults", {})[key] = value
            save_config(cfg)
            console.print(f"[green]Set default for {name}:[/green] {key}={value}")
            return

        if action == "set-global-default":
            # if not key or value is None:
            #     raise typer.BadParameter("--key and --value are required")

            if not key:
                key = typer.prompt("Enter the key")
            if not value:
                value = typer.prompt("Enter the value")

            global_defaults = cfg.setdefault("global_defaults", {})
            global_defaults[key] = value
            save_config(cfg)
            console.print(f"[green]Set global default:[/green] {key}={value}")
            return

        if action == "remove-template":
            if not name:
                name = typer.prompt("Enter the name of the template")
            

            templates = cfg.get("templates", {})
            if name not in templates:
                raise typer.BadParameter(f"Template '{name}' not found")
            
            if not Confirm.ask(f"[yellow]Are you sure you want to remove the template '{name}'?[/yellow]"):
                console.print("[red]Operation cancelled[/red]")
                return

            del templates[name]
            save_config(cfg)
            console.print(f"[green]Removed template:[/green] {name}")
            return

        if action == "remove-default":
            # Interactive mode if flags not provided
            if not name:
                templates = cfg.get("templates", {})
                if not templates:
                    raise typer.BadParameter("No templates configured.")
                
                console.print("\n[bold]Available templates:[/bold]")
                for name in templates:
                    console.print(f"  - {name}")
                name = Prompt.ask("[cyan]Enter template name[/cyan]")

            templates = cfg.get("templates", {})
            if name not in templates:
                raise typer.BadParameter(f"Template '{name}' not found")

            if not key:
                defaults = templates[name].get("defaults", {})
                if not defaults:
                    raise typer.BadParameter(f"No defaults configured for template '{name}'")
                
                console.print("\n[bold]Available defaults:[/bold]")
                for key, value in defaults.items():
                    console.print(f"  - {key} = {value}")
                key = Prompt.ask("[cyan]Enter default key to remove[/cyan]")

            defaults = templates[name].get("defaults", {})
            if key not in defaults:
                raise typer.BadParameter(f"Default '{key}' not found in template '{name}'")

            if Confirm.ask(f"[yellow]Are you sure you want to remove default '{key}' from template '{name}'?[/yellow]"):
                del defaults[key]
                save_config(cfg)
                console.print(f"[green]Removed default from {name}:[/green] {key}")
            return

        if action == "remove-global-default":
            # Interactive mode if flags not provided
            if not key:
                global_defaults = cfg.get("global_defaults", {})
                if not global_defaults:
                    raise typer.BadParameter("No global defaults configured.")
                
                console.print("\n[bold]Available global defaults:[/bold]")
                for key, value in global_defaults.items():
                    console.print(f"  - {key} = {value}")
                key = Prompt.ask("[cyan]Enter global default key to remove[/cyan]")

            global_defaults = cfg.get("global_defaults", {})
            if key not in global_defaults:
                raise typer.BadParameter(f"Global default '{key}' not found")

            if Confirm.ask(f"[yellow]Are you sure you want to remove global default '{key}'?[/yellow]"):
                del global_defaults[key]
                save_config(cfg)
                console.print(f"[green]Removed global default:[/green] {key}")
            return

        raise typer.BadParameter(
            f"Invalid action: {action}. Use --help to see available actions."
        )

    except Exception as e:
        raise typer.Exit(f"Error managing config: {str(e)}")

def main():
    """Entry point for the CLI."""
    app()

if __name__ == "__main__":
    main()
