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

### With pipx

```sh
pipx install .
```

If you already have it installed and want to upgrade:
```sh
pipx install . --force
```
