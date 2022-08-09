# Installing MeCab

If you're not on Windows you'll need to install MeCab yourself.

## macOS

### Install MeCab

MeCab is available through [Homebrew](https://formulae.brew.sh/formula/mecab):
`brew install mecab`
and [MacPorts](https://ports.macports.org/port/mecab/).
`sudo port install mecab`

### Troubleshooting

#### Make sure the executable is in $PATH

1. Try running `mecab` in your terminal.
2. If you see something like `zsh: command not found: mecab`, continue: you probably need to put the mecab executable in $PATH. If not, you can try to [Manually set the executable](#manually-set-the-executable).
3. Figure out where your executable is. If you installed with Homebrew, it's likely in `/opt/homebrew/bin/mecab`. If you installed with MacPorts, it's likely to be in `/opt/local/bin/mecab`. Try pasting the path in your terminal and running to see if it's there.
4. If you don't get `command not found: mecab` anymore – congrats, you found it!
5. Figure out which shell you're using: `echo $SHELL`. Whatever you see after `/bin/` is your shell name.
6. If you're on `bash`: run this command, and replace **\*path\*** with the mecab path from Step 3

   ```bash
   echo "export PATH=*path*:$PATH" >> ~/.bash_profile
   ```

7. If you're on `zsh`: run this command, and replace **\*path\*** with the mecab path from Step 3

   ```zsh
   echo "export PATH=*path*:$PATH" >> ~/.zprofile
   ```

8. Done! Check if it works by closing and reopening your terminal and running `mecab`. You shouldn't get the `command not found: mecab` output anymore.

#### Manually set the executable

1. When you have mecab installed, try running `which mecab` in your terminal.
2. The output of the command should give you a path to the mecab executable: `/something/something/mecab`.
3. Copy the output of the command.
4. Open Anki, go to the add-on settings (Tools -> JRP add-on preferences).
5. Paste the output into the "MeCab executable path" preference.
6. Uncheck the "Use system-wide MeCab executable" preeference.

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

- A C++ compiler. Ideally g++ which, if it isn't installed already, should be
  available in a package called `gcc`, `g++`, or similar on most distros. Check
  if it works by running `g++ --version`.
- `libiconv`. Probably already present as part of glibc.
- `git`, for cloning the repo. You can also skip step 1 below by using the
  source tarball linked here instead: https://taku910.github.io/mecab/#download

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
   path of the directory you just made.
7. Copy or move `<tgt dir>/usr/bin/mecab` and `<tgt dir>/usr/lib/libmecab.so.2`
   to a new directory. Create an empty file named `mecabrc` in the same
   directory.
8. In the add-on's preferences menu, uncheck _Use system-wide MeCab executable_
   and set _MeCab executable path_ to where you put the `mecab` executable in
   the previous step.

Alternative to step 5-8 you could also create and install a custom package, in
which case you can leave the add-on settings on their default values.
