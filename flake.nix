{
  description = "Esctl - command-line utility to connect and administrate elasticsearch clusters";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable-small";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = {
    self,
    nixpkgs,
    flake-utils,
  }:
    flake-utils.lib.eachDefaultSystem (
      system: let
        pkgs = import nixpkgs {
          inherit system;
        };
      in {
        packages = {
          default = self.packages.${system}.esctl;

          esctl = pkgs.python313Packages.buildPythonApplication {
            pname = "esctl";
            version =
              if self ? shortRev && self.shortRev != null && self.shortRev != ""
              then self.shortRev
              else "dirty";
            src = ./.;
            format = "pyproject";
            build-system = with pkgs.python313Packages; [
              poetry-core
            ];

            propagatedBuildInputs = with pkgs.python313.pkgs; [
              self.packages.${system}.yamlpath
              rich
              requests
              typer
              jmespath
              elasticsearch
              pydantic
              jsonpath-ng
              kubernetes
              ipython
              blake3
              orjson
            ];

            meta = with pkgs.lib; {
              description = "Command-line utility to connect and administrate elasticsearch clusters";
              license = licenses.asl20;
              platforms = platforms.all;
            };
          };

          # ruamel-yaml is too up to date in nixpkgs, so we vendor it here for yamlpath
          ruamel-yaml = pkgs.python313Packages.buildPythonPackage rec {
            pname = "ruamel.yaml";
            version = "0.17.21";
            pyproject = true;
            src = pkgs.fetchPypi {
              inherit pname version;
              sha256 = "sha256-i3zml6LyEnUqNcGsQURx3BbEJMlXO+SSa1b/P10jt68=";
            };
            doCheck = false;
            propagatedBuildInputs = with pkgs.python313.pkgs; [
              setuptools
            ];
            meta = with pkgs.lib; {
              description = "ruamel.yaml is a YAML parser/emitter that supports roundtrip preservation of comments, seq/map flow style, and map key order";
              license = licenses.mit;
              platforms = platforms.all;
            };
          };

          # yamlpath is not in nixpkgs, so we vendor it here
          yamlpath = pkgs.python313Packages.buildPythonPackage rec {
            pname = "yamlpath";
            version = "3.8.2";
            pyproject = true;
            src = pkgs.fetchPypi {
              inherit pname version;
              sha256 = "sha256-TzDMIUtQhdSw53VuBsOvOuWJ7N6WUNKtp+HTRexP2k8=";
            };
            propagatedBuildInputs = with pkgs.python313.pkgs; [
              setuptools
              python-dateutil
              self.packages.${system}.ruamel-yaml
            ];
            doCheck = false;
            meta = with pkgs.lib; {
              description = "Command-line get/set/merge/validate/scan/convert/diff processors for YAML/JSON/Compatible data using powerful, intuitive, command-line friendly syntax";
              license = licenses.isc;
              platforms = platforms.all;
            };
          };
        };

        devShells = {
          # nix develop
          default = pkgs.mkShell {
            inputsFrom = [self.packages.${system}.esctl];
            packages = with pkgs; [
              poetry
              ruff
              python313Packages.mkdocs
              python313Packages.pymdown-extensions
              python313Packages.mike
              python313Packages.mkdocs-awesome-nav
            ];
          };
        };
        formatter = pkgs.alejandra;
      }
    );
}
