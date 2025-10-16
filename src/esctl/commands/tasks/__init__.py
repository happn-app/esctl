import typer

from .cancel import app as cancel_app

app = typer.Typer(rich_markup_mode="rich")


app.add_typer(cancel_app)
