list:
	@just --list --unsorted

[group('format')]
pyfmt:
  uv run ruff format

[group('format')]
mdfmt:
  markdownlint-cli2 --config .markdownlint-cli2.jsonc --fix '**/*.md'

[group('format')]
yamlfmt:
  yamlfix -c .yamlfix.toml . --exclude '.venv/**/*'

[group('format')]
fmt: pyfmt mdfmt yamlfmt

[group('lint')]
pylint:
  uv run ruff check .

[group('lint')]
pyfmt-check:
  uv run ruff format --check

[group('lint')]
yamllint:
  yamllint --config-file=.yamllint.yaml --format=colored .

[group('lint')]
mdlint:
  markdownlint-cli2 --config .markdownlint-cli2.jsonc '**/*.md'

[group('lint')]
lint: pylint pyfmt-check yamllint mdlint

[group('docs')]
docs:
  uv run mkdocs serve
