# Grading Console

## CodeForge V1.0 submission

This project is a browser-based grading console for instructors. It allows staff to upload marks, define grade cutoffs, review the distribution, and export final results as a CSV file. The tool is designed to reduce manual work while making grading decisions more transparent and safer.

*This is a challenge prototype and not an official BITS Pilani grading tool.*

- **Live app:** 'https://manandarak.github.io/codeforge-grading-console/'
- **Bug Fix Log:** [BUGFIX_LOG.md](BUGFIX_LOG.md) documents 20 issues, including how each bug was reproduced, the root cause, the fix, and the test used to verify it.
- **Original code:** [original.html](original.html)

## How it works

1. Enter the instructor name.
2. Upload an `.xlsx` file with the columns **BITS ID, Course, Total Marks**. A sample file is available through the app if needed.
3. Choose the relevant course, adjust the grade cutoffs, and click **Review & export**.

Everything runs in the browser, so marks are never uploaded anywhere.

## What was improved in Stage 2

Each change addresses a real grading risk or time-consuming step in the process:

1. **Cutoffs that cannot have gaps or overlaps.** The original version used 16 dropdowns with 101 possible values each and allowed students to fall outside the final result set. The updated flow lets instructors set each grade’s minimum using −/+ controls, while the maximum is derived automatically from the next grade. A always ends at 100, E always starts at 0, and any invalid configuration is flagged directly on the affected card with export blocked until the issue is fixed.
2. **Upload validation.** Every row is checked for common data problems, including blank values, non-numeric or out-of-range marks, missing IDs, duplicate IDs, and decimal entries. Problems are shown by row number so instructors can identify exactly what was excluded and why instead of receiving silently incorrect results.
3. **Grade-aware distribution view.** The app shows one bar per mark, colour-coded by grade band, along with cutoff lines, hover values, and a grade distribution table showing counts and percentages. As cutoffs change, the distribution updates live, making natural clusters and grading gaps much easier to see.
4. **Students just below a cutoff.** The interface highlights students who are only 1–5 marks below the next grade and includes a one-click action to lower that cutoff if the instructor chooses to do so.
5. **Safer export workflow.** Before downloading any file, instructors review the instructor name, course, total student count, grade counts, and warnings such as excluded rows, rounded marks, and borderline students. The CSV is properly escaped, protected against spreadsheet formula injection, displays correctly in Excel, includes the grade ranges used, and is named in a clear, descriptive format such as `grades_Course_A_2026-09-27.csv`.
6. **Quality-of-life improvements.**
   - Searchable, sortable student table with grade and “borderline only” filters
   - Course-specific cutoff memory saved in the browser
   - Warning before closing the tab when work has not yet been exported
   - Downloadable sample file
   - Drag-and-drop upload support
7. **Accessibility and responsiveness.**
   - Labelled inputs and keyboard-friendly controls
   - Screen-reader announcements for file results and validation errors
   - Text description of the chart
   - Visible focus outlines
   - Dark mode
   - Mobile-friendly layout with no horizontal scrolling
   - Respect for reduced-motion preferences

## Use of AI tools

I used **Claude** (Anthropic's AI assistant) during this challenge, mainly for:

- **Finding bugs.** It helped me write a Playwright script that runs the original app in Chrome with different Excel files (normal, messy, text-formatted marks, wrong columns), so I could confirm each bug instead of guessing from the code.
- **Testing.** The 47 checks in `tests/test.py` were written with AI help and run against the final app.
- **Documentation.** It helped me draft the Bug Fix Log and this README.

I went through the bugs and the changes myself, tried the app in the browser with the sample files, and made the final decisions. For example, how to round decimal marks, and keeping the first row when a BITS ID appears twice.

## Testing

The app is tested with a Playwright script in `tests/test.py`, which runs in Chrome and checks 47 scenarios covering file uploads, statistics, grade assignment, validation, the student table, CSV output, the timer, error handling, and mobile layout. The sample files used for testing are stored in `samples/`.

```bash
pip install playwright openpyxl
python tests/test.py        # uses the installed Google Chrome
```

## Deployment

- **GitHub Pages:** push the repository, then go to Settings → Pages and deploy from the `main` branch at the root.
