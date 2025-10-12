---
title: Installation
tags:
  - Setup
---

## Installing from source

Use `pipx` to install `esctl`, the easiest way is:

```sh
$ pipx install .

installed package esctl 1.11.2, installed using Python 3.13.7
These apps are now globally available
  - esctl
done! ✨ 🌟 ✨
```

If you've already installed from source and want to force install, you can use

```sh
pipx install . --force
```

If you just want to upgrade:

```sh
pipx upgrade esctl
```

## Installing with NIX

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
