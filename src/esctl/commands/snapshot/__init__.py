import typer

from .restore import app as restore_app
from .list import app as list_app


app = typer.Typer(rich_markup_mode="rich")
app.add_typer(restore_app)
app.add_typer(list_app)
