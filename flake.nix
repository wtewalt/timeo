{
  description = "Dev shell with Python, uv, release-please, task, and pre-commit";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            python3
            uv
            release-please
            go-task
            pre-commit
          ];

          shellHook = ''
            echo "🐍 Python        $(python3 --version)"
            echo "📦 uv            $(uv --version)"
            echo "🚀 task          $(task --version)"
            echo "🔖 release-please $(release-please --version)"
            echo "🪝 pre-commit    $(pre-commit --version)"
          '';
        };
      }
    );
}
