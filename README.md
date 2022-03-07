# Japanese Readings and Pitch Accent Add-on

This Anki add-on allows automatically generating readings (furigana) and pitch
accent information for an entire field with a single button press. It can also
convert any amount of cards in bulk.

## Getting Started

1. Make sure you have Anki version 2.1.49 or later installed.
2. On non-Windows platforms only, [install MeCab]() since only a Windows
   executable is bundled with the addon.
3. Install the full version of the add-on
   from [AnkiWeb](https://ankiweb.net/shared/info/TBD).  
   Alternatively, download one of the `.ankiaddon` files from the
   [latest release](https://github.com/Ben-Kerman/anki-jrp/releases/latest)
   and install it from file in Anki's add-on menu.  
   The smallest file contains only the addon itself, which means you will need
   to supply your own pitch accent/variant data and install MeCab alongside a
   dictionary for it to use externally.  
   The `full` file has everything, including a MeCab exe for Windows, but you'll
   still have to use your own dictionary for MeCab.  
   The `ipadic` file contains everything the addon needs out of the box and is
   probably what most users will want to install initially.  
   This is also the version shared on AnkiWeb.
4. Restart Anki, open the "Manage Note Types" menu (`Ctrl`+`⇧`+`N`) and set up
   your templates as described [here]().
5. Open the add-on's preferences under "Tools", go the "Note Types" tab, then
   select and click "Add" for all note types you set up in the previous step.  
   If you previously used the Migaku Japanese Add-on with any note type
   click `Remove MIA/Migaku` in its section, otherwise this add-on will not work
   properly.
6. Save your preferences. You should now be able to preview or review any cards
   that contain reading/accent syntax with furigana and accent coloring /
   indicators.

## Adding Readings and Pitch Accent Information

### Individual

To generate or remove readings and accent info for a single note, select it in
the Anki browser, focus the field you want to change and click one of the
conversion buttons at the right of the editor toolbar (or press the associated
shortcut).

### Bulk Conversion

The _Notes_ entry in the browser's menu bar contains an action for converting
notes in bulk. Select any notes you want to change, choose the bulk conversion
action from the menu bar, adjust the configuration dialog to what you want and
click _Convert_. All notes need to be of the same note type, since it wouldn't
be possible to determine the target field otherwise.

With the _Default_ and _Migaku_ conversion types, any notes that already contain
reading/accent syntax will be converted directly to the closest equivalent in
the target syntax without regenerating (unless the corresponding option is
checked), or left unchanged if the existing syntax type is the same as the
target.

If you're converting large amounts of notes, such as sentence mining decks
containing hundreds or thousands of cards, make sure to back everything up
before running the conversion. Exporting the deck(s) with scheduling information
(but without media, since the conversion only changes the notes themselves)
should be sufficient.

## Syntax

The add-on supports its own fully featured syntax and is also compatible with
the syntax from the old Migaku Japanese Add-on.

### Default

In the default syntax, readings are written in square brackets with kanji on the
left and furigana on the right separated by a `|`, like `[漢字|かんじ]`.  
Words with pitch accent information are enclosed in curly braces that contain
the word (including reading tags) itself and comma-separated pitch accent
information after a semicolon: `{[受|う]け[入|い]れる;Y4,0}`.

The accent information normally consists of a comma-separated list of numbers,
each representing the accented mora or 0 for unaccented (平板) words. The only
special cases are unknown accents marked with a `?` (which can only occur by
converting Migaku syntax), and split accents like 一目瞭然 (いち↓もく・りょ→うぜん)
are a special case and are composed of several parts separated by dashes. Each
part consists of the number of the accented mora, an `@` sign, and the number of
moras it applies to. For example: `{[一目瞭然|いちもくりょうぜん];2@4-0@4,0}`.

An `!` and `Y` can be placed before the actual pitch accent information.
Exclamation marks indicate ambiguous accents, such as for many kana-only words
or certain words with multiple accents. If present, a Y (from 用 as in 活用・用言)
will cause all accents other than [0] to be displayed as the kifuku (起伏)
pattern. The add-on automatically inserts ambiguity marks if it found more than
one possible set of accents with the same reading for a word during lookup, you
should then manually look up the words in question and adjust the accent tags as
needed. Ys are added to all words identified as 動詞 (verbs) or 形容詞 (i-adjectives)
by MeCab.

The base readings of conjugated words can be indicated in two ways, inline
like `{[行|い][って=く];Y0}`, or after the accent(s) like `{[来|き]た;Y1|くる}`.

### Migaku

For backwards compatibility, Migaku-style syntax is also supported, but using it
brings some limitations with it:

- Only one reading per word is possible, leading to furigana frequently
  duplicating characters from the word, like <ruby>この先<rt>このさき</rt></ruby>,
  <ruby>付き合<rt>つきあ</rt></ruby>う or <ruby>変わり身<rt>かわりみ</rt></ruby>.
- The base reading of conjugable words must always be included in full, even the
  part that is identical to the reading of the conjugated form. This is also
  true if the base reading and actual reading are the same, so the Migaku
  version of what would be `{[陥|おとしい]れる;Y5,0}` in default syntax
  is `陥[おとしい,おとしいれる;k5,h]れる`.
- Since words are space-separated, ASCII spaces can't be represented properly
  and are replaced with en spaces (U+2002).
- Ambiguous accents can't be marked and thus won't be highlighted.
- Split accents can't be accurately represented and will be displayed as
  unknown.
