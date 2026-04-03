{
  description = "Dev shell with Python, uv, uv2nix, task, and pre-commit";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    uv2nix.url = "github:pyproject-nix/uv2nix";
    uv2nix.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs = { self, nixpkgs, flake-utils, uv2nix }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        workspace = uv2nix.lib.loadWorkspace { workspaceRoot = ./.; };
        overlay = workspace.mkPyprojectOverlay {
          sourcePreference = "wheel";
        };
        python = pkgs.python3;
        pythonSet = (pkgs.callPackage uv2nix.lib.mkPythonSet { inherit python; }).overrideScope overlay;
        venv = pythonSet.mkVirtualEnv "dev-env" workspace.deps.default;
      in
      {
        devShells.default = pkgs.mkShell {
          packages = [
            venv
            pkgs.uv
            pkgs.go-task
            pkgs.pre-commit
          ];

          env = {
            UV_NO_SYNC = "1";
            UV_PYTHON = "${venv}/bin/python";
            UV_PYTHON_DOWNLOADS = "never";
          };

          shellHook = ''
            echo "🐍 Python     $(python --version)"
            echo "📦 uv         $(uv --version)"
            echo "🚀 task       $(task --version)"
            echo "🪝 pre-commit $(pre-commit --version)"
          '';
        };
      }
    );
}
