import typer

from .allocation_explain import app as allocation_app
from .reroute import app as reroute_app
from .settings import app as settings_app

app = typer.Typer()


app.add_typer(reroute_app)
app.add_typer(allocation_app)
app.add_typer(settings_app)
