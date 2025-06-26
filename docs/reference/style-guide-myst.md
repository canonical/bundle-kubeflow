---
relatedlinks: https://github.com/canonical/canonical-sphinx-extensions, [reStructuredText&#32;Primer](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html), [Canonical&#32;Documentation&#32;Style&#32;Guide](https://docs.ubuntu.com/styleguide/en)
myst:
  substitutions:
    advanced_reuse_key: "This is a substitution that includes a code block:
                       ```
                       code block
                       ```"
---

(myst_style_guide)=

# MyST style guide

The documentation files use a mixture of [Markdown](https://commonmark.org/) and [MyST](https://myst-parser.readthedocs.io/) syntax.

See the following sections for syntax help and conventions.

```{note}
This style guide assumes that you are using the [Sphinx documentation starter pack](https://github.com/canonical/starter-pack).
Some of the mentioned syntax requires Sphinx extensions (which are enabled in the starter pack).
```

For general style conventions, see the [Canonical Documentation Style Guide](https://docs.ubuntu.com/styleguide/en).

## Headings

```{list-table}
   :header-rows: 1

* - Input
  - Description
* - `# Title`
  - Page title and H1 heading
* - `## Heading`
  - H2 heading
* - `### Heading`
  - H3 heading
* - `#### Heading`
  - H4 heading
* - ...
  - Further headings
```

Adhere to the following conventions:

- Do not use consecutive headings without intervening text.
- Do not skip levels (for example, do not follow an H2 heading with an H4 heading).
- Use sentence style for headings (capitalise only the first word).

## Inline formatting

```{list-table}
   :header-rows: 1

* - Input
  - Output
* - `` {guilabel}`UI element` ``
  - {guilabel}`UI element`
* - `` `code` ``
  - `code`
* - `` {file}`file path` ``
  - {file}`file path`
* - `` {command}`command` ``
  - {command}`command`
* - `` {kbd}`Key` ``
  - {kbd}`Key`
* - `*Italic*`
  - *Italic*
* - `**Bold**`
  - **Bold**

```

Adhere to the following conventions:

- Use italics sparingly. Common uses for italics are titles and names (for example, when referring to a section title that you cannot link to, or when introducing the name for a concept).
- Use bold sparingly. Avoid using bold for emphasis and rather rewrite the sentence to get your point across.

## Code blocks

Start and end a code block with three back ticks:

    ```

You can specify the code language after the back ticks to enforce a specific lexer, but in many cases, the default lexer works just fine.

`````{list-table}
   :header-rows: 1

* - Input
  - Output
* - ````

    ```
    # Demonstrate a code block
    code:
    - example: true
    ```

    ````

  - ```
    # Demonstrate a code block
    code:
    - example: true
    ```
* - ````

    ```yaml
    # Demonstrate a code block
    code:
    - example: true
    ```

    ````

  - ```yaml
    # Demonstrate a code block
    code:
    - example: true

    ```

`````

To include back ticks in a code block, increase the number of surrounding back ticks:

`````{list-table}
   :header-rows: 1

* - Input
  - Output
* -
    `````

    ````
    ```
    ````

    `````

  -
    ````

    ```

    ````

`````

### Terminal output

Showing a terminal view can be useful to show the output of a specific command or series of commands, where it is important to see the difference between input and output.
In addition, including a terminal view can help break up a long text and make it easier to consume, which is especially useful when documenting command-line-only products.

To show a terminal view, use the following directive:

`````{list-table}
   :header-rows: 1

* - Input
  - Output
* - ````

    ```{terminal}
    :input: command number one
    :user: root
    :host: vm

    output line one
    output line two
    :input: another command
    more output
    ```

    ````

  - ```{terminal}
    :input: command number one
    :user: root
    :host: vm

    output line one
    output line two
    :input: another command
    more output
    ```

`````

Input is specified as the `:input:` option (or prefixed with `:input:` as part of the main content of the directive).
Output is the main content of the directive.

To override the prompt (`user@host:~$` by default), specify the `:user:` and/or `:host:` options.
To make the terminal scroll horizontally instead of wrapping long lines, add `:scroll:`.

## Links

How to link depends on if you are linking to an external URL or to another page in the documentation.

### External links

For external links, use Markdown syntax.
You can also use just the URL, but this will usually cause issues with the spelling check, so you should specify the link text as code in this case.

```{list-table}
   :header-rows: 1

* - Input
  - Output
* - `[Canonical website](https://canonical.com)`
  - [Canonical website](https://canonical.com)
* - `https://canonical.com`
  - [{spellexception}`https://canonical.com`](https://canonical.com)
* - ``[`https://canonical.com`](https://canonical.com)``
  - [`https://canonical.com`](https://canonical.com)
```

To display a URL as text and prevent it from being linked, add a `<span></span>`:

```{list-table}
   :header-rows: 1

* - Input
  - Output
* - `https:/<span></span>/canonical.com`
  - {spellexception}`https:/<span></span>/canonical.com`

```

#### Related links

You can add links to related websites or Discourse topics to the sidebar

To add a link to a related website, add the following field at the top of the page:

    relatedlinks: https://github.com/canonical/canonical-sphinx-extensions, [RTFM](https://www.google.com)

To override the title, use Markdown syntax. Note that spaces are ignored; if you need spaces in the title, replace them with `&#32;`, and include the value in quotes if Sphinx complains about the metadata value because it starts with `[`.

To add a link to a Discourse topic, configure the Discourse instance in the {file}`custom_conf.py` file.
Then add the following field at the top of the page (where `12345` is the ID of the Discourse topic):

    discourse: 12345

#### YouTube links

To add a link to a YouTube video, use the following directive:

`````{list-table}
   :header-rows: 1

* - Input
  - Output
* - ````

    ```{youtube} https://www.youtube.com/watch?v=iMLiK1fX4I0
    :title: Demo
    ```

    ````

  - ```{youtube} https://www.youtube.com/watch?v=iMLiK1fX4I0
    :title: Demo
    ```

`````

The video title is extracted automatically and displayed when hovering over the link.
To override the title, add the `:title:` option.

### Internal references

For internal references, both Markdown and MyST syntax are supported. In most cases, you should use MyST syntax though, because it resolves the link text automatically and gives an indication of the link in GitHub rendering.

(section_target_myst)=
#### Referencing a section

To reference a section within the documentation (either on the same page or on another page), add a target to that section and reference that target.

You can add targets at any place in the documentation. However, if there is no heading or title for the targeted element, you must specify a link text.

(a_random_target_myst)=
```{list-table}
   :header-rows: 1

* - Input
  - Output
  - Output on GitHub
  - Description
* - `(target_ID)=`
  -
  - \(target_ID\)=
  - Adds the target ``target_ID``.
* - `` {ref}`a_section_target_myst` ``
  - {ref}`a_section_target_myst`
  - \{ref\}`a_section_target_myst`
  - References a target that has a title.
* - `` {ref}`link text <a_random_target_myst>` ``
  - {ref}`link text <a_random_target_myst>`
  - \{ref\}`link text <a_random_target_myst>`
  - References a target and specifies a title.
* - `` {ref}`starter-pack:home` ``
  - {ref}`starter-pack:home`
  - \{ref\}`starter-pack:home`
  - You can also reference targets in other doc sets.
* - ``[`xyz`](a_random_target_myst)``
  - [`xyz`](a_random_target_myst)
  - [`xyz`](a_random_target_myst) (link is broken)
  - Use Markdown syntax if you need markup on the link text.
```

Adhere to the following conventions:

- Never use external links to reference a section in the same doc set or a doc set that is linked with Intersphinx. It would likely cause a broken link in the future.
- Override the link text only when it is necessary. If you can use the section title as link text, do so, because the text will then update automatically if the title changes.
- Never "override" the link text with the same text that would be generated automatically.

#### Referencing a page

If a documentation page does not have a target, you can still reference it by using the `{doc}` role with the file name and path.
Use MyST syntax to automatically extract the link text. When overriding the link text, use Markdown syntax.

```{list-table}
   :header-rows: 1

* - Input
  - Output
  - Output on GitHub
  - Status
* - `` {doc}`index` ``
  - {doc}`index`
  - {doc}<span></span>`index`
  - Preferred.
* - `[](index)`
  - [](index)
  -
  - Do not use.
* - `[Index page](index)`
  - [Index page](index)
  - [Index page](index)
  - Preferred when overriding the link text.
* - `` {doc}`Index page <index>` ``
  - {doc}`Index page <index>`
  - {doc}<span></span>`Index page <index>`
  - Alternative when overriding the link text.

```

Adhere to the following conventions:

- Only use the `{doc}` role when you cannot use the `{ref}` role, thus only if there is no target at the top of the file and you cannot add it. When using the `{doc}` role, your reference will break when a file is renamed or moved.
- Override the link text only when it is necessary. If you can use the document title as link text, do so, because the text will then update automatically if the title changes.
- Never "override" the link text with the same text that would be generated automatically.

## Navigation

Every documentation page must be included as a sub-page to another page in the navigation.

This is achieved with the [`toctree`](https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html#directive-toctree) directive in the parent page: <!-- wokeignore:rule=master -->

````
```{toctree}
:hidden:

sub-page1
sub-page2
```
````

If a page should not be included in the navigation, you can suppress the resulting build warning by putting the following instruction at the top of the file:

```
---
orphan: true
---
```

Use orphan pages sparingly and only if there is a clear reason for it.

```{tip}
Instead of hiding pages that you do not want to include in the documentation from the navigation, you can exclude them from being built.
This method will also prevent them from being found through the search.

To exclude pages from the build, add them to the `custom_excludes` variable in the {file}`custom_conf.py` file.
```

## Lists

````{list-table}
   :header-rows: 1

* - Input
  - Output
* - ```
    - Item 1
    - Item 2
    - Item 3
    ```
  - - Item 1
    - Item 2
    - Item 3
* - ```
    1. Step 1
    1. Step 2
    1. Step 3
    ```
  - 1. Step 1
    1. Step 2
    1. Step 3
* - ```
    1. Step 1
       - Item 1
         * Sub-item
       - Item 2
    1. Step 2
       1. Sub-step 1
       1. Sub-step 2
    ```
  - 1. Step 1
       - Item 1
         * Sub-item
       - Item 2
    1. Step 2
       1. Sub-step 1
       1. Sub-step 2
````

Adhere to the following conventions:

- In numbered lists, use `1.` for all items to generate the step numbers automatically.
  You can also use a higher number for the first item to start with that number.
- Use `-` for unordered lists. When using nested lists, you can use `*` for the nested level.

### Definition lists

````{list-table}
   :header-rows: 1

* - Input
  - Output
* - ```
    Term 1
    : Definition

    Term 2
    : Definition
    ```
  - Term 1
    : Definition

    Term 2
    : Definition
````

## Tables

You can use standard Markdown tables. However, using the reST [list table](https://docutils.sourceforge.io/docs/ref/rst/directives.html#list-table) syntax is usually much easier.
See the [Sphinx documentation](https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html#table-directives) for all table syntax alternatives. <!-- wokeignore:rule=master -->

Both markups result in the following output:

```{list-table}
   :header-rows: 1

* - Header 1
  - Header 2
* - Cell 1

    Second paragraph cell 1
  - Cell 2
* - Cell 3
  - Cell 4
```

### Markdown tables

```
| Header 1                           | Header 2 |
|------------------------------------|----------|
| Cell 1<br><br>2nd paragraph cell 1 | Cell 2   |
| Cell 3                             | Cell 4   |
```

### List tables

See [list tables](https://docutils.sourceforge.io/docs/ref/rst/directives.html#list-table) for reference.

````
```{list-table}
   :header-rows: 1

* - Header 1
  - Header 2
* - Cell 1

    2nd paragraph cell 1
  - Cell 2
* - Cell 3
  - Cell 4
```
````

## Notes

`````{list-table}
   :header-rows: 1

* - Input
  - Output
* - ````
    ```{note}
    A note.
    ```
    ````
  - ```{note}
    A note.
    ```
* - ````
    ```{tip}
    A tip.
    ```
    ````
  - ```{tip}
    A tip.
    ```
* - ````
    ```{important}
    Important information
    ```
    ````
  - ```{important}
    Important information.
    ```
* - ````
    ```{caution}
    This might damage your hardware!
    ```
    ````
  - ```{caution}
    This might damage your hardware!
    ```


`````

Adhere to the following conventions:

- Use notes sparingly.
- Only use the following note types: `note`, `tip`, `important`, `caution`
- Only use a caution if there is a clear hazard of hardware damage or data loss.

## Images

````{list-table}
   :header-rows: 1

* - Input
  - Output
* - ```
    ![Alt text](https://assets.ubuntu.com/v1/b3b72cb2-canonical-logo-166.png)
    ```
  - ![Alt text](https://assets.ubuntu.com/v1/b3b72cb2-canonical-logo-166.png)
* - ````
    ```{figure} https://assets.ubuntu.com/v1/b3b72cb2-canonical-logo-166.png
       :width: 100px
       :alt: Alt text

       Figure caption
    ```
    ````
  - ```{figure} https://assets.ubuntu.com/v1/b3b72cb2-canonical-logo-166.png
       :width: 100px
       :alt: Alt text

       Figure caption
    ```
````

Adhere to the following conventions:

- For local pictures, start the path with `/` (for example, `/images/image.png`).
- Use `PNG` format for screenshots and `SVG` format for graphics.
- See [Five golden rules for compliant alt text](https://abilitynet.org.uk/news-blogs/five-golden-rules-compliant-alt-text) for information about how to word the alt text.

## Reuse

A big advantage of MyST in comparison to plain Markdown is that it allows to reuse content.

### Substitution

To reuse sentences or paragraphs that have little markup and special formatting, use [substitutions](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html#substitutions). <!-- wokeignore:rule=master -->

Substitutions can be defined in the following locations:

- Globally, in a file named {file}`reuse/substitutions.yaml` that is loaded into the [`myst_substitutions`](https://myst-parser.readthedocs.io/en/v0.13.5/using/syntax-optional.html#substitutions-with-jinja2) variable in {file}`custom_conf.py`:

  ```{code-block} python
     :caption: "{spellexception}`custom_conf.py`"

  import os
  import yaml

  ...

  if os.path.exists('./reuse/substitutions.yaml'):
    with open('./reuse/substitutions.yaml', 'r') as fd:
        myst_substitutions = yaml.safe_load(fd.read())
  ```

  ```{code-block} yaml
     :caption: "{spellexception}`reuse/substitutions.yaml`"

  # Key/value substitutions to use within the Sphinx doc.
  {version_number: "0.1.0",
   formatted_text: "*Multi-line* text\n that uses basic **markup**.",
   site_link: "[Website link](https://example.com)"}
- Locally, putting the definitions at the top of a single file in the following format:

  ````
  ---
  myst:
    substitutions:
      version_number: "0.1.0"
      formatted_text: "*Multi-line* text
                       that uses basic **markup**."
      advanced_reuse_key: "This is a substitution that includes a code block:
                         ```
                         code block
                         ```"

  ---
  ````

You can combine both options by defining a default substitution in `reuse/substitutions.py` and overriding it at the top of a file.

The definitions from the above examples are rendered as follows:

```{list-table}
   :header-rows: 1

* - Input
  - Output
* - `{{version_number}}`
  - {{version_number}}
* - `{{formatted_text}}`
  - {{formatted_text}}
* - `{{site_link}}`
  - {{site_link}}
* - `{{advanced_reuse_key}}`
  - {{advanced_reuse_key}}
```

Adhere to the following convention:

- Substitutions do not work on GitHub. Therefore, use substitution names that indicate the included content (for example, `note_not_supported` instead of `reuse_note`).

### File inclusion

To reuse longer sections or text with more advanced markup, you can put the content in a separate file and include the file or parts of the file in several locations.

To select parts of the text in a file, use `:start-after:` and `:end-before:` if possible. You can combine those with `:start-line:` and `:end-line:` if required (if the same text occurs more than once). Using only `:start-line:` and `:end-line:` is error-prone though.

You cannot put any targets into the content that is being reused (because references to this target would be ambiguous then). You can, however, put a target right before including the file.

By combining file inclusion and substitutions, you can even replace parts of the included text.

`````{list-table}
     :header-rows: 1

* - Input
  - Output
* - ````

    % Include parts of the content from
    % file [style-guide.rst](style-guide.rst)
    ```{include} style-guide.rst
        :start-after: "Adhere to the following conventions:"
        :end-before: "  Use the ones specified above."
    ```

    ````

  -
    % Include parts of the content from file [style-guide.rst](style-guide.rst)
    ```{include} style-guide.rst
        :start-after: "Adhere to the following conventions:"
        :end-before: "  Use the ones specified above."
    ```

`````

Adhere to the following convention:

- File inclusion does not work on GitHub. Therefore, always add a comment linking to the included file.
- Files that only contain text that is reused somewhere else should be placed in the {file}`reuse` folder and end with the extension ``.txt`` to distinguish them from normal content files.
- To make sure inclusions don't break, consider adding HTML comments (`<!-- some comment -->`) to the source file as markers for starting and ending.

## Tabs

The recommended way of creating tabs is to use the tabs that the [Sphinx design](https://sphinx-design.readthedocs.io/en/latest/) extension provides.

``````{list-table}
   :header-rows: 1

* - Input
  - Output
* - `````

    ````{tab-set}

    ```{tab-item} Tab 1
    :sync: key1

    Content Tab 1
    ```

    ```{tab-item} Tab 2
    :sync: key2

    Content Tab 2
    ```

    ````

    `````

  - ````{tab-set}

    ```{tab-item} Tab 1
    :sync: key1

    Content Tab 1
    ```

    ```{tab-item} Tab 2
    :sync: key2

    Content Tab 2
    ```
    ````
``````

Alternatively, you can use the [Sphinx tabs](https://sphinx-tabs.readthedocs.io/en/latest/) extension, which is also enabled by default. This was previously recommended due to limitations in Sphinx Design that are now fixed.

``````{list-table}
   :header-rows: 1

* - Input
  - Output
* - `````

    ````{tabs}

    ```{group-tab} Tab 1

    Content Tab 1
    ```

    ```{group-tab} Tab 2

    Content Tab 2
    ```

    ````

    `````

  - ````{tabs}

    ```{group-tab} Tab 1

    Content Tab 1
    ```

    ```{group-tab} Tab 2

    Content Tab 2
    ```
    ````
``````

## Collapsible sections

There is no support for details sections in MyST, but you can insert HTML to create them.

````{list-table}
   :header-rows: 1

* - Input
  - Output
* - ```
    <details>
    <summary>Details</summary>

    Content
    </details>
    ```

  - <details>
    <summary>Details</summary>

    Content
    </details>

````

## Glossary

You can define glossary terms in any file. Ideally, all terms should be collected in one glossary file though, and they can then be referenced from any file.

`````{list-table}
   :header-rows: 1

* - Input
  - Output
* - ````

    ```{glossary}

    MyST example term
      Definition of the example term.
    ```

    ````

  - ```{glossary}

    MyST example term
      Definition of the example term.
    ```

* - ``{term}`MyST example term` ``
  - {term}`MyST example term`
`````

## More useful markup

`````{list-table}
   :header-rows: 1

* - Input
  - Output
  - Description
* - ````

    ```{versionadded} X.Y
    ```

    ````
  - ```{versionadded} X.Y
    ```
  - Can be used to distinguish between different versions.
* - ```
    ---
    ```
  - A horizontal line
  - Can be used to visually divide sections on a page.
* - ```
    <!-- This is a comment -->
    ```
  - <!-- This is a comment -->
  - Not visible in the output.
* - ```
    {abbr}`API (Application Programming Interface)`
    ```
  - {abbr}`API (Application Programming Interface)`
  - Hover to display the full term.
* - ```
    {spellexception}`PurposelyWrong`
    ```
  - {spellexception}`PurposelyWrong`
  - Explicitly exempt a term from the spelling check.

`````
