import typer

from .allocation import app as allocation_app
from .health import app as health_app
from .indices import app as indices_app
from .nodes import app as nodes_app
from .recovery import app as recovery_app
from .shards import app as shards_app
from .tasks import app as tasks_app

app = typer.Typer()

app.add_typer(allocation_app)
app.add_typer(health_app)
app.add_typer(nodes_app)
app.add_typer(indices_app)
app.add_typer(recovery_app)
app.add_typer(shards_app)
app.add_typer(tasks_app)
