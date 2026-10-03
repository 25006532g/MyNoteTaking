# NoteTaker - Personal Note Management Application

A modern, responsive web application for managing personal notes with a beautiful user interface and full CRUD functionality.

## 🌟 Features

- **Create Notes**: Add new notes with titles and rich content
- **Edit Notes**: Update existing notes with real-time editing
- **Delete Notes**: Remove notes you no longer need
- **Search Notes**: Find notes quickly by searching titles and content
- **Auto-save**: Notes are automatically saved as you type
- **Note Translation**: Detect the source language, compare original and translated text side by side, then confirm or revert
- **Responsive Design**: Works perfectly on desktop and mobile devices
- **Modern UI**: Beautiful gradient design with smooth animations
- **Real-time Updates**: Instant feedback and updates

## 🚀 Live Demo

The application is deployed and accessible at: **https://3dhkilc88dkk.manus.space**

## 🛠 Technology Stack

### Frontend
- **HTML5**: Semantic markup structure
- **CSS3**: Modern styling with gradients, animations, and responsive design
- **JavaScript (ES6+)**: Interactive functionality and API communication

### Backend
- **Python Flask**: Web framework for API endpoints
- **SQLAlchemy**: ORM for database operations
- **Flask-CORS**: Cross-origin resource sharing support

### Database
- **SQLite**: Lightweight, file-based database for data persistence

## 📁 Project Structure

```
notetaking-app/
├── src/
│   ├── models/
│   │   ├── user.py          # User model (template)
│   │   └── note.py          # Note model with database schema
│   ├── routes/
│   │   ├── user.py          # User API routes (template)
│   │   └── note.py          # Note API endpoints
│   ├── static/
│   │   ├── index.html       # Frontend application
│   │   └── favicon.ico      # Application icon
│   ├── database/
│   │   └── app.db           # SQLite database file
│   └── main.py              # Flask application entry point
├── venv/                    # Python virtual environment
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## 🔧 Local Development Setup

### Prerequisites
- Python 3.11+
- pip (Python package manager)

### Installation Steps

1. **Clone or download the project**
   ```bash
   python -m venv venv
   ```

2. **Activate the virtual environment**
   ```bash
   source venv/bin/activate
   ```

   Remark: On Windows, use `venv\Scripts\activate`

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure OpenRouter translation**
   Create a repository-root `.env` file with your OpenRouter key:
   ```env
   OPEN_ROUTER_KEY=your-openrouter-api-key
   ```

   The key is read by Flask on the server and is never sent to the browser. To choose a different OpenRouter model, optionally add `OPEN_ROUTER_MODEL` to `.env`. Translation instructions are loaded from the editable repository-root file `prompt/translate.txt`.

   Database connections use `DATABASE_URL` when set, preferring the pooled Neon URL for application traffic. Keep `DATABASE_URL_UNPOOLED` set to the direct Neon URL for schema and data migrations. Without `DATABASE_URL`, the app uses the local SQLite database.

   For Vercel, add the pooled Neon URL as the `DATABASE_URL` project environment variable and enable it for each deployment environment you use (Production, Preview, and Development). Vercel does not read the ignored local `.env`; without a remote URL, the app now stops with a configuration error instead of trying to write SQLite files to its read-only deployment filesystem. `POSTGRES_URL` is also accepted for Vercel Postgres integrations.

### Deploy to Vercel

1. Push this repository to GitHub, then in Vercel choose **Add New → Project** and import the repository.
2. Set the project root directory to the repository root. Vercel recognizes the Flask app at `src/main.py`; it exports the required top-level `app` object. Leave the build command at its default.
3. In **Settings → Environment Variables**, add:
   - `DATABASE_URL`: the pooled Neon connection URL from the project `.env`; enable it for Production, Preview, and Development as needed.
   - `OPEN_ROUTER_KEY`: the OpenRouter key, required for the translation endpoint.
   - `OPEN_ROUTER_MODEL`: optional; omit it to use the default model.
4. Save the variables and deploy. After changing variables later, redeploy so the new deployment receives them.
5. Open the deployment URL and verify the home page, `/api/notes`, and a translation. Check Vercel **Deployments → Functions → Logs** if a request fails.

Do not add `.env` to Git or configure `DATABASE_URL_UNPOOLED` for normal app traffic. The app uses pooled `DATABASE_URL`; keep the direct URL for migration commands only.

   To copy local SQLite records to Neon, run a dry-run first, then explicitly apply the migration:
   ```bash
   python scripts/migrate_sqlite_to_neon.py
   python scripts/migrate_sqlite_to_neon.py --apply
   ```
   The migration creates missing tables, inserts missing rows, preserves the SQLite file, and stops on conflicting row IDs rather than overwriting Neon data.

5. **Run the application**
   ```bash
   python src/main.py
   ```

6. **Access the application**
   - Open your browser and go to `http://localhost:5001`

## 📡 API Endpoints

### Notes API
- `GET /api/notes` - Get all notes
- `POST /api/notes` - Create a new note
- `GET /api/notes/<id>` - Get a specific note
- `PUT /api/notes/<id>` - Update a note
- `DELETE /api/notes/<id>` - Delete a note
- `GET /api/notes/search?q=<query>` - Search notes
- `POST /api/translate` - Translate a title and note body into a supported language

The translation request accepts `title`, `content`, and `target_language` (for example, `ja` or `zh-TW`). The OpenRouter API key stays server-side in `.env`; do not put it in frontend code.

### Request/Response Format
```json
{
  "id": 1,
  "title": "My Note Title",
  "content": "Note content here...",
  "created_at": "2025-09-03T11:26:38.123456",
  "updated_at": "2025-09-03T11:27:30.654321"
}
```

## 🎨 User Interface Features

### Sidebar
- **Search Box**: Real-time search through note titles and content
- **New Note Button**: Create new notes instantly
- **Notes List**: Scrollable list of all notes with previews
- **Note Previews**: Show title, content preview, and last modified date

### Editor Panel
- **Title Input**: Edit note titles
- **Content Textarea**: Rich text editing area
- **Translation Preview**: Compare line-numbered original and translated text, confirm both fields together, or restore the original text
- **Save Button**: Manual save option (auto-save also available)
- **Delete Button**: Remove notes with confirmation
- **Real-time Updates**: Changes reflected immediately

### Design Elements
- **Gradient Background**: Beautiful purple gradient backdrop
- **Glass Morphism**: Semi-transparent panels with backdrop blur
- **Smooth Animations**: Hover effects and transitions
- **Responsive Layout**: Adapts to different screen sizes
- **Modern Typography**: Clean, readable font stack

## 🔒 Database Schema

### Notes Table
```sql
CREATE TABLE note (
    id INTEGER PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## 🚀 Deployment

The application is configured for easy deployment with:
- CORS enabled for cross-origin requests
- Host binding to `0.0.0.0` for external access
- Production-ready Flask configuration
- Persistent SQLite database

## 🔧 Configuration

### Environment Variables
- `FLASK_ENV`: Set to `development` for debug mode
- `SECRET_KEY`: Flask secret key for sessions

### Database Configuration
- Database file: `src/database/app.db`
- Automatic table creation on first run
- SQLAlchemy ORM for database operations

## 📱 Browser Compatibility

- Chrome/Chromium (recommended)
- Firefox
- Safari
- Edge
- Mobile browsers (iOS Safari, Chrome Mobile)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

## 🆘 Support

For issues or questions:
1. Check the browser console for error messages
2. Verify the Flask server is running
3. Ensure all dependencies are installed
4. Check network connectivity for the deployed version

## 🎯 Future Enhancements

Potential improvements for future versions:
- User authentication and multi-user support
- Note categories and tags
- Rich text formatting (bold, italic, lists)
- File attachments
- Export functionality (PDF, Markdown)
- Dark/light theme toggle
- Offline support with service workers
- Note sharing capabilities

---

**Built with ❤️ using Flask, SQLite, and modern web technologies**

