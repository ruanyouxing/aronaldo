{
  description = "env setup";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }: 
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
      
      myPythonEnv = pkgs.python313.withPackages (p: with p; [
        discordpy
        gspread
        google-auth
        python-dotenv
      ]);

    in {
      devShells.${system}.default = pkgs.mkShell {
        buildInputs = [
          myPythonEnv
          pkgs.pyright   
          pkgs.black
        ];
      };
      apps.${system}.default = {
        type = "app";
        program = "${pkgs.writeShellScriptBin "run-app" ''
          ${myPythonEnv}/bin/python ./main.py
        ''}/bin/run-app";
      };
    };
}
