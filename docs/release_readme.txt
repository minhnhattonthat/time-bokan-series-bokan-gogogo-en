Time Bokan Series: Bokan GoGoGo (PlayStation) - English translation patch v{version}

Unofficial fan translation. This zip holds the patch and this file only. No game data is included, and pre-patched
images must not be shared.


WHAT YOU NEED

Your own dump of the Japanese disc, SLPS-03133, as BIN/CUE with one data track (Redump: {name},
http://redump.org/discs/quicksearch/SLPS-03133/). The patch changes the .bin only:

    {name}.bin
    Size    {base_size} bytes
    CRC32   {base_crc32}
    MD5     {base_md5}
    SHA-1   {base_sha1}

After patching, the .bin has:

    CRC32   {new_crc32}
    SHA-1   {new_sha1}


HOW TO PATCH

1. Copy the game folder, so your original stays as it is.
2. Apply {patch} to the .bin with xdelta3 or Delta Patcher:

       xdelta3 -d -s "original.bin" {patch} "patched.bin"

3. Replace the .bin in the copy with the patched file, under the same file name. The .cue stays as it is.
4. Open the .cue in your emulator and start from a cold boot. Savestates made on the original disc hold the old graphics
   and will not show the English. Memory card saves work on both.


TRANSLATION STATUS

Movie dialogue               English subtitles burned into the story movies; voices stay Japanese
Menus, options, HUD          Translated
Course, machine and          Translated (all lettering is drawn as graphics in this game)
  character names
Dokurobey's briefings        Translated
Credits roll                 Translated, re-lettered in the staff roll movie
Memory card save titles      English (full-width, as the original's)
Title logo                   Left in Japanese, as no official English logo is known
Opening song                 Not subtitled, as in the original
Songs and voices             Left in Japanese


KNOWN ISSUES

- Nobody checked the movie subtitles by ear. They come from two passes of machine transcription, corrected from the
  frames, context and knowledge of the series; about a quarter of the lines are best guesses, among them the names
  Julie, Komaro, Nandara and the Great Tall-Tale Comet.
- A few short cries and lines over noise had audio too unclear to read and have no subtitle.
- Names follow the official English spellings, so the subtitles say "Tonzra" and "Rescueman" where the voice says
  "Tonzura" and "Otasukeman".
- Two names are shortened on the sprites to fit: "Andromedama" (Andromedama Alpha in the movies) and the course
  "Whyzca" (the Whyzca Plain).
- Some credit name readings follow published credit lists or are best readings of their kanji.
- 15 graphics labels were never seen drawn in testing (among them the hero machines' description panels). They are
  translated anyway.

Tested on PCSX-Redux 30282.20261104.5 only, by scripted warps to every scene rather than a full playthrough. Not tested
on real hardware or other emulators. Please report bugs:
https://github.com/minhnhattonthat/time-bokan-series-bokan-gogogo-en/issues


CREDITS

Translation and tools: minhnhattonthat, with extensive AI assistance (Claude by Anthropic), including the machine
transcription of the movies. Corrections are very welcome.
Fonts: Bangers, Jersey 10, Tiny5, Liberation Serif and Liberation Sans, under the SIL Open Font License 1.1.
Time Bokan Series: Bokan GoGoGo is (c) Banpresto and Tatsunoko Production. This project is not affiliated with them.

Patch SHA-1: {patch_sha1}
