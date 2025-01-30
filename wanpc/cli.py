"""Command line interface for wanpc."""
import json
from pathlib import Path
from typing import Optional, Dict, Any
import typer
from rich.console import Console
from rich.table import Table
from rich.text import Text
from cookiecutter.main import cookiecutter
from rich.prompt import Prompt, Confirm

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

@app.command()
def list(
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