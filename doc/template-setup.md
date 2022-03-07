# Note Type Setup

In order for the add-on to work properly, you'll have to make some adjustments
to your card templates.

## Fields

Every field that should be processed by the script that generates furigana and
accent highlighting needs to be enclosed in an HTML element with the
attribute `data-jrp-generate`.

If you previously used the Migaku Japanese Add-on you'll likely have lines like
this somewhere in your templates:

```html
<div display-type="kanji" class="wrapped-japanese">{{Sentence}}</div>
```

Those can be replaced with this:

```html
<div data-jrp-generate>{{Sentence}}</div>
```

If you didn't use the Migaku Add-on before, all you need to do is find the tag
(in `{{}}`) for the field you want to generate from, and place HTML tags around
like in the line above.

---

If you have existing notes with Migaku syntax and don't want to upgrade to the
improved syntax you can tell the card script to interpret your fields in Migaku
mode by setting the attribute's value to `migaku`:

```html
<div data-jrp-generate="migaku">{{Sentence}}</div>
```

## Card Front

Any fields on the front of the class also need to be children of an element with
the class `jrp-front`. This can be the element with the generate attribute:

```html
<div class="jrp-front" data-jrp-generate>{{Sentence}}</div>
```

Or any enclosing element:

```html
<div class="jrp-front">
	<div data-jrp-generate>{{Sentence}}</div>
</div>
```

## Vertical Writing

Vertical writing (縦書き) is fully supported. Simply add the `jr-vertical`
class to an element and all generated elements below it will use vertical
styling. The class doesn't enable vertical writing mode by itself, but you can
change that by adding this to your note type's style sheet:

```css
.jrp-vertical {
	writing-mode: vertical-rl;
}
```
