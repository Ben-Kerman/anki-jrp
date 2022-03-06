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
