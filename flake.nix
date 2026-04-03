# flake.nix
{
  description = "Python dev environment with uv, uv2nix, pre-commit";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";

    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.uv2nix.follows = "uv2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    pre-commit-hooks = {
      url = "github:cachix/git-hooks.nix"; 
      inputs.nixpkgs.follows = "nixpkgs";
    };
    # pre-commit-hooks.url = "github:cachix/git-hooks.nix";
    # pre-commit-hooks.inputs.nixpkgs.follows = "nixpkgs";
  };
  outputs = { self, nixpkgs, flake-utils, uv2nix, pyproject-nix, pre-commit-hooks, pyproject-build-systems }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs    = nixpkgs.legacyPackages.${system};
        python  = pkgs.python312;
        lib = pkgs.lib;

        # Load your pyproject.toml / uv.lock workspace
        workspace = uv2nix.lib.workspace.loadWorkspace {
          workspaceRoot = ./.;
          # workspaceRoot = self;
        };

        # Build a package overlay from the resolved lockfile
        overlay   = workspace.mkPyprojectOverlay {
          sourcePreference = "wheel";
        };

        # Base Python package set with build systems
        pythonSet = (pkgs.callPackage pyproject-nix.build.packages {
          inherit python;
        }).overrideScope (
          lib.composeManyExtensions [
            pyproject-build-systems.overlays.default
            overlay
          ]
        );

        # Frozen virtualenv for packages.default / apps.default
        timeoEnv = pythonSet.mkVirtualEnv "timeo-env" workspace.deps.default;

                # Editable overlay — senzu itself is installed as an editable package
        # REPO_ROOT must be set in the shell before this is evaluated
        editableOverlay = workspace.mkEditablePyprojectOverlay {
          root = "$REPO_ROOT";
        };
        editablePythonSet = pythonSet.overrideScope (
          lib.composeManyExtensions [
            editableOverlay
            # Hatchling needs the `editables` package at build time for editable
            # installs. uv doesn't lock build-system deps so we wire it in here.
            (final: prev: {
              senzu = prev.senzu.overrideAttrs (old: {
                nativeBuildInputs = (old.nativeBuildInputs or [ ]) ++ [
                  final.editables
                ];
              });
            })
          ]
        );

        # Dev virtualenv: all deps including dev extras, timeo editable
        devEnv = editablePythonSet.mkVirtualEnv "timeo-dev-env" workspace.deps.all;

        # Shared config for both dev shells
        shellEnv = {
          # Stop uv from trying to manage the venv — we already have one
          UV_NO_SYNC = "1";
          # Point uv at the Nix-managed Python so it doesn't download its own
          UV_PYTHON = editablePythonSet.python.interpreter;
          UV_PYTHON_DOWNLOADS = "never";
        };

        shellHookScript = ''
          unset PYTHONPATH
          export REPO_ROOT=$(git rev-parse --show-toplevel)
          echo "timeo dev shell ready. timeo is installed in editable mode."
        '';
        basePackages = [ devEnv pkgs.uv pkgs.pre-commit pkgs.go-task ];

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
        packages.default = timeoEnv;

        apps.default = {
          type = "app";
          program = "${timeoEnv}/bin/senzu";
        };

        # The main development shell
        devShells = {
          # Default: no nix-managed gcloud. If gcloud is already installed on
          # the host it remains available via the inherited PATH.
          default = pkgs.mkShell {
            packages = basePackages;
            env = shellEnv;
            shellHook = shellHookScript;
          };

          # For fresh machines or CI that don't have gcloud pre-installed.
          # Usage: nix develop .#with-gcloud
          with-gcloud = pkgs.mkShell {
            packages = basePackages ++ [ pkgs.google-cloud-sdk ];
            env = shellEnv;
            shellHook = shellHookScript;
          };
        };
      }
    );
}
