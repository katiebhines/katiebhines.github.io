# Katie B. Hines Senior Center website

A simple, large-print website for the Katie B. Hines Senior Center in Carolina Beach.
The Events list updates itself every day from New Hanover County's Carolina Beach calendar.

## How to put it online (free, about 15 minutes)

1. **Make a GitHub account.** Go to https://github.com/signup and follow the steps.
2. **Make a new repository** (a folder for the site). Click the **+** at the top right → **New repository**.
   Name it `katie-b-hines` (any name works). Choose **Public**. Click **Create repository**.
3. **Upload the files.** On the new page click **uploading an existing file**.
   Unzip `katie-b-hines-site.zip` on your computer, open the folder, select **everything inside it**
   (including the `.github` folder; on a Mac press Cmd+Shift+. to show hidden folders), and drag it into the page.
   Click **Commit changes**.
   - If the `.github` folder will not upload by dragging, click **Add file → Create new file**, type
     `.github/workflows/update-events.yml` as the name, paste in that file's text, and save. Do the same for `.github/workflows/pages.yml`.
4. **Turn on the website.** Go to **Settings → Pages**. Under **Source** pick **GitHub Actions**.
5. **Allow the daily update.** Go to **Settings → Actions → General**, scroll to **Workflow permissions**,
   choose **Read and write permissions**, and click **Save**.
6. Go to the **Actions** tab, click **Publish website**, then **Run workflow**. After a minute or two your site is live at
   `https://YOUR-USERNAME.github.io/katie-b-hines/`.

## How the events update

- Every morning, GitHub runs `scripts/update_events.py`. It visits the county Nutrition page
  (https://www.nhcgov.com/524/Nutrition), finds the newest Carolina Beach monthly calendar PDF, reads the
  "Special Events" list, adds county holiday closures, and saves them to `events.json`. The site then re-publishes.
- If the county changes the PDF layout or the download fails, the old events stay up. To fix an event by hand,
  open `events.json` on GitHub, click the pencil icon, edit, and commit.
- To update right away: **Actions → Update events → Run workflow**.
- The weekly class schedule (`classes.html`) and lunch details are typed in by hand. Check them against the new
  county calendar each month.

## Preview on your own computer

From this folder run `python3 -m http.server` and open http://localhost:8000.
