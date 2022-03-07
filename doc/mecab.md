# Installing MeCab

If you're not on Windows you'll need to install MeCab yourself.

## macOS

MeCab is available through [Homebrew](https://formulae.brew.sh/formula/mecab)
and [MacPorts](https://ports.macports.org/port/mecab/).

Make sure the executable is in your PATH, or manually set the exe location in
the add-on's preferences.

Please report any macOS-related issues that aren't mentioned here. Since I don't
own any macOS devices I can't test the add-on on macOS myself.

## Linux

Your distro might have a MeCab package, for example:

- [Ubuntu](https://packages.ubuntu.com/search?keywords=mecab)
- Arch (AUR): [mecab](https://aur.archlinux.org/packages/mecab),
  [mecab-git](https://aur.archlinux.org/packages/mecab-git)

If you can't find anything, compile MeCab yourself by following the instructions
below.

### Requirements

- A C++ compiler. Ideally g++ which, if it isn't installed by already, should be
  available in a package called `gcc`, `g++`, or similar on most distros.  
  Check if it works by running `g++ --version`.
- `libiconv`. Probably already present as part of glibc.
- `git`, for cloning the repo. You can also skip step 1 below and download the
  source tarball linked here: https://taku910.github.io/mecab/#download.

### Compile & Install

1. Clone the repository: `git clone https://github.com/taku910/mecab.git`
2. cd into the `mecab` directory in the repo. It should contain a file
   called `configure`.
3. Run this command:  
   ```./configure --prefix=/usr --sysconfdir=/etc --libexecdir=/usr/lib --with-charset=utf-8```  
   For some distros the prefix and directories might be different.
4. If `configure` finished without errors, run `make` (and ensure it succeeds).
5. Create a temporary target directory.
6. Run `make DESTDIR="<tgt dir>" install`, where `<tgt dir>` is the absolute
   path of the directory from the previous step.
7. Copy or move `<tgt dir>/usr/bin/mecab` and `<tgt dir>/usr/lib/libmecab.so.2`
   to a new directory. Create an empty file named `mecabrc` in the same
   directory.
8. In the add-on's preferences menu, uncheck _Use system-wide MeCab executable_
   and set _MeCab executable path_ to where you put the `mecab` executable in
   the previous step.

Alternative to step 5-8 you could also create and install a custom package, in
which case you can leave the add-on settings on their default values.
