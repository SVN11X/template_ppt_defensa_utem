# Glossary

The shared language of this project. Use these terms exactly, in code and in conversation. The second column holds the word the owner uses, so a request in another language maps to the right term.

| Term | Owner's word | Means here | Does not mean |
|------|--------------|------------|---------------|
| defense | defensa | The oral presentation of the thesis before the commission, followed by questions. | The written thesis. |
| commission | comisión | The people who grade the defense. | The audience. |
| pattern | modelo | One slide of the catalog that the build copies and fills, named by its slide name. | A PowerPoint layout. |
| catalog | plantilla, catálogo | `templates/utem-defense-template.potx`, the set of patterns. | The old template with 19 layouts. |
| slide entry | lámina | One item under `laminas` in `content/01-defensa.yml`. | A slide of the catalog. |
| marker | marcador | A `{{key}}` in a pattern that the build replaces with a field. | A [bracket] placeholder. |
| placeholder | corchetes | Text between brackets that the student must still complete, for example `[cifra]`. | A PowerPoint placeholder shape. |
| backup slide | lámina de respaldo | A hidden slide shown only to answer a question. | An appendix of the thesis. |
| speaker script | guion | What the student says on each slide, with its seconds. | The slide text. |
| section | sección, pestaña | One of the five parts of the defense shown as tabs. | A PowerPoint section. |
