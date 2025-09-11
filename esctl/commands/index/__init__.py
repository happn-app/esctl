import typer

from .cache import app as cache_app
from .settings import app as settings_app

app = typer.Typer()


app.add_typer(cache_app)
app.add_typer(settings_app)
