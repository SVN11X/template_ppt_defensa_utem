---
name: build-defense
description: Draft or update a UTEM thesis defense presentation in this repository. Reads the thesis in thesis/, writes content/01-defensa.yml (slide text, speaker script with seconds per slide, hidden backup slides), builds build/defensa.pptx and drafts content/02-ensayos.md. Use it when the student asks to prepare, draft, update, shorten or rehearse their defense, even if they only say "arma mi defensa".
---

# build-defense

You help a UTEM undergraduate student prepare the presentation for their thesis defense. Talk to the student in Spanish, in plain words. The rules for the content are in `content/00-guia.md`. Read it first and follow it.

## 1. Gather what you need

1. Read the thesis in `thesis/`. If the folder is missing or empty, ask the student to create it and put the PDF of the thesis there, then stop.
2. Ask the student, in one message, only what the thesis does not say: the time limit their school gave them, their name as it should appear, the guide professor, the degree title (for example Ingeniero Civil en ...), the city and year. Never guess these.
3. Run `python scripts/build_deck.py --models` to see the slide patterns and their fields.

## 2. Write content/01-defensa.yml

Keep the structure of the example file: `defensa`, five `secciones` and the list of `laminas`.

1. Follow the three moments of the guide: start, body and closing. A usual defense has 14 to 18 visible slides.
2. Write every slide title as the idea of the slide, not its topic.
3. Copy the general objective, the specific objectives and the research question word for word from the thesis.
4. Use plain Spanish for someone outside the specialty. Explain each technical term in one sentence the first time it appears, in the slide or in the script.
5. Take every number from the thesis and name its source in `fuente`, for example "Fuente: Tabla 5.1 de la tesis". When a number, chart or image is missing, write it between brackets, for example `[porcentaje de aciertos]`. Never invent a result.
6. Do not use semicolons or dashes as separators in slide text. Use periods and commas.
7. Add 3 to 8 backup slides with the `respaldo-*` patterns. Cover at least "why this solution and not another" and "the limitations of the work", the two questions commissions ask most.
8. Give every visible slide `segundos` and a `guion`: short spoken sentences, natural, meant to rehearse without memorizing. Keep the total under the school limit minus 5 minutes.
9. For each figure the student must export, set the path it should have in `figures/` and list it in your final report with its page or figure number in the thesis.

## 3. Build and check

1. Run `python scripts/build_deck.py`. Fix every error, and every warning that is not a pending image or bracket.
2. Check the reported time of the visible slides against the limit.

## 4. Draft the rehearsal plan

Fill `content/02-ensayos.md` with the limit, the target time and the defense date, and write the practice questions with the backup slide that answers each one.

## 5. Report to the student

In Spanish and briefly: how many slides and minutes, the brackets still open, the images to export with their source in the thesis, and the next step (review `content/01-defensa.yml`, then build and rehearse).

## Do not

- Do not edit `templates/` or `scripts/`. If a pattern does not fit, say so and propose the closest one.
- Do not copy whole paragraphs of the thesis into the slides.
- Do not commit or upload anything from `thesis/`.
