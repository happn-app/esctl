# esctl

## Installation

### With NIX

To install nix check out our [nix-toolkit README](https://github.com/happn-app/nix-toolkit?tab=readme-ov-file#installing-nix).

To install `esctl` in your user profile:

```sh
nix profile install 'git+ssh://git@github.com/happn-app/esctl'
```

For a temporary shell with `esctl` available:

```sh
nix shell 'git+ssh://git@github.com/happn-app/esctl'
```

You can also run the app directly:

```sh
nix run 'git+ssh://git@github.com/happn-app/esctl' -- --help
```

### With uv

```sh
uv tool install .
```

If you already have it installed and want to upgrade:

```sh
uv tool install . --force
```

Or if you're not in esctl's source directory:

```sh
uv tool upgrade esctl
```

### With pipx

#### From source

```sh
pipx install .
```

If you already have it installed and want to upgrade:

```sh
pipx install . --force
```

Or if you're not in esctl's source directory:

```sh
pipx upgrade esctl
```

#### From built wheels

```sh
pipx install https://github.com/happn-app/esctl/releases/latest/esctl-latest.whl
```
