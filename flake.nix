# flake.nix
{
  description = "Python dev environment with uv, uv2nix, pre-commit";

  inputs = {
    nixpkgs.url         = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url     = "github:numtide/flake-utils";

    # uv2nix: build uv-managed Python projects with Nix
    uv2nix.url           = "github:pyproject-nix/uv2nix";
    uv2nix.inputs.nixpkgs.follows = "nixpkgs";

    # pyproject.nix: PEP 517/518/621 support
    pyproject-nix.url   = "github:pyproject-nix/pyproject.nix";
    pyproject-nix.inputs.nixpkgs.follows = "nixpkgs";

    # pre-commit hooks as Nix derivations
    pre-commit-hooks.url = "github:cachix/git-hooks.nix";
    pre-commit-hooks.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs = { self, nixpkgs, flake-utils, uv2nix, pyproject-nix, pre-commit-hooks }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs    = nixpkgs.legacyPackages.${system};
        python  = pkgs.python312;

        # Load your pyproject.toml / uv.lock workspace
        workspace = uv2nix.lib.workspace.loadWorkspace {
          workspaceRoot = ./.;
        };

        # Build a package overlay from the resolved lockfile
        overlay   = workspace.mkPyprojectOverlay {
          sourcePreference = "wheel";
        };

        pythonSet =
          (pkgs.callPackage pyproject-nix.build.packages {
            inherit python;
          }).overrideScope overlay;

        # Pre-commit hook configuration (see pre-commit-hooks.nix tab)
        preCommitChecks = pre-commit-hooks.lib.${system}.run {
          src = ./.;
          hooks = {
            ruff.enable          = true;
            ruff-format.enable   = true;
            mypy.enable           = true;
            check-toml.enable    = true;
            check-yaml.enable    = true;
            end-of-file-fixer.enable = true;
            trim-trailing-whitespace.enable = true;
          };
        };

      in {
        # Install pre-commit hooks on `nix flake check`
        checks.pre-commit = preCommitChecks;

        # The main development shell
        devShells.default = pkgs.mkShell {
          packages = [
            pkgs.uv
            python
            pkgs.pre-commit
          ];

          # Expose the uv2nix virtual env to the shell
          env = {
            UV_PYTHON      = "${python}/bin/python";
            UV_NO_SYNC     = "1"; # managed by nix; skip auto-sync
            VIRTUAL_ENV    =
              (pythonSet.mkVirtualEnv "project-env" workspace.deps.default);
          };

          shellHook = ''
            # Install pre-commit hooks if not already installed
            ${preCommitChecks.shellHook}
            echo "Python $(python --version) | uv $(uv --version)"
          '';
        };

        # Optional: build the default package from pyproject.toml
        packages.default =
          pythonSet.mkVirtualEnv "project-env" workspace.deps.default;
      }
    );
}
