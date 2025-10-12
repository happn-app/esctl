{
  description = "CLI tool to run commands on ES clusters packaged with poetry2nix";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable-small";
    flake-utils.url = "github:numtide/flake-utils";
    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.flake-utils.follows = "flake-utils";
    };
  };

  outputs = {
    self,
    nixpkgs,
    flake-utils,
    poetry2nix,
  }:
    flake-utils.lib.eachDefaultSystem (
      system: let
        pkgs = import nixpkgs {
          inherit system;
        };
        # create a custom "mkPoetryApplication" API function that under the hood uses
        # the packages and versions (python3, poetry etc.) from our pinned nixpkgs above:
        inherit (poetry2nix.lib.mkPoetry2Nix {inherit pkgs;}) mkPoetryApplication;
        esctl = mkPoetryApplication {
          projectDir = ./.;
          preferWheels = true;
        };
      in {
        # Used for `nix shell` and `nix profile install`
        packages.default = esctl;

        # Used for `nix run`
        apps.default = {
          type = "app";
          program = "${esctl}/bin/esctl";
        };

        devShells = {
          # Development shell with esctl available and all dependencies
          # Used with `nix develop`
          default = pkgs.mkShell {
            inputsFrom = [esctl];
            packages = [esctl];
          };
          # Development shell with only poetry available
          # Used with `nix develop .#poetry`
          poetry = pkgs.mkShell {
            packages = [pkgs.poetry];
          };
        };

        # Used for `nix fmt`
        formatter = pkgs.alejandra;
      }
    );
}
