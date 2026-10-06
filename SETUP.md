# `venky10008/venky10008` profile setup

This package is already arranged in the exact repository structure. After extracting it, **do not create another folder around the files**.

Repository root should contain:

- `README.md`
- `venky-ascii.svg`
- `info-card.svg`
- `contrib-heatmap.svg`
- `data/contributions.json`
- `scripts/fetch_contributions.py`
- `scripts/render_heatmap_svg.py`
- `scripts/requirements.txt`
- `.github/workflows/update-profile-art.yml`

Then push the extracted contents directly to the public repository:

`https://github.com/Venky10008/venky10008`

After pushing, open **Actions → Update profile art → Run workflow** once. The workflow fetches the public contribution calendar, renders the animated SVG heatmap, and commits the refreshed files. It then runs daily automatically.

The original portrait photo is not included in the repository; only the generated SVG is included.
