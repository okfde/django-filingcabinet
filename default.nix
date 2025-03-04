with import <nixpkgs> { };
let
  ld_packages = [
    imagemagick
    libcxx
    hdf5
    blas
    qpdf
  ];
in
pkgs.mkShell {
  name = "fcdocs";
  shellHook = ''
    export LD_LIBRARY_PATH=${builtins.concatStringsSep ":" (map (x: x + "/lib") ld_packages)}:$LD_LIBRARY_PATH
    export DYLD_LIBRARY_PATH=$LD_LIBRARY_PATH:$DYLD_LIBRARY_PATH
    export HDF5_DIR=${hdf5.dev}
  '';
  buildInputs = [
    python38Packages.python
    python38Packages.setuptools
    python38Packages.numexpr
    python38Packages.pikepdf
    python38Packages.numpy
    imagemagick
    pkg-config
    hdf5
    hdf5.dev
    tesseract
    blas.dev
    qpdf
    libcxx.dev
    rustc
  ];
}
