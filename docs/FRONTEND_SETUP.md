# Frontend Dependencies Setup

## CodeMirror Download Required

The frontend uses CodeMirror for the Markdown editor. This needs to be downloaded separately.

### Steps:

1. Download CodeMirror 5.x from: https://codemirror.net/
   - Direct download: https://codemirror.net/codemirror.zip

2. Extract the downloaded file

3. Copy the following files/directories to `frontend/libs/codemirror/`:
   - `lib/codemirror.js`
   - `lib/codemirror.css`
   - `mode/markdown/markdown.js`
   - `theme/default.css`

4. Verify the structure:
   ```
   frontend/libs/codemirror/
   ├── lib/
   │   ├── codemirror.js
   │   └── codemirror.css
   ├── mode/
   │   └── markdown/
   │       └── markdown.js
   ├── theme/
   │   └── default.css
   └── .gitkeep
   ```

### After Download

Once downloaded, the application should work properly when started with `start.bat`.

### Alternative: CDN

If you don't want to download locally, you can modify `frontend/index.html` to use CDN links instead.
