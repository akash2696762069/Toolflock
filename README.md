# 🚀 Toolflock - Beautiful Utility Hub

![Python Version](https://img.shields.io/badge/python-3.12-blue.svg)
![Flask Version](https://img.shields.io/badge/flask-3.0+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)

Toolflock is a modern, SEO-optimized web application featuring 10+ essential online tools with elegant design and professional functionality.

## ✨ Features

- 📅 **Age Calculator** - Calculate precise age and time differences
- 📄 **PDF Tools** - Merge, split, compress, and convert PDFs
- 🔄 **File Converter** - Convert images and videos between formats
- 🔗 **URL Shortener** - Create short, memorable links with analytics
- 📷 **QR Generator** - Generate custom QR codes with styling options
- 🖼️ **Image Tools** - Bulk resize, compress, and optimize images
- 📐 **Unit Converter** - Convert between different measurement units
- ⚡ **Speed Test** - Test internet connection speed and latency
- 🎥 **Screen Recorder** - Browser-based screen recording
- ✍️ **Grammar Checker** - Advanced grammar and spelling validation

## 🎯 SEO & Performance Optimized

- ✅ Complete meta tags and structured data (JSON-LD)
- ✅ Open Graph and Twitter Card integration
- ✅ Sitemap.xml and robots.txt for search engines
- ✅ Lazy loading and image optimization
- ✅ Progressive Web App (PWA) ready
- ✅ Mobile-first responsive design

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)

**Windows:**
```bash
./setup.bat
```

**Linux/macOS:**
```bash
chmod +x setup.sh
./setup.sh
```

### Option 2: Manual Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/akash2696762069/Toolflock.git
   cd Toolflock
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/macOS
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run the application:**
   ```bash
   python app.py
   ```

6. **Open your browser:** `http://127.0.0.1:5000`

## 🐳 Docker Deployment

### Using Docker Compose (Recommended)
```bash
docker-compose up -d
```

### Using Docker
```bash
docker build -t toolflock .
docker run -p 5000:5000 toolflock
```

## 📁 Project Structure

```
Toolflock/
├── app.py                 # Main Flask application
├── config.py             # Configuration management
├── requirements.txt      # Python dependencies
├── runtime.txt          # Python version for deployment
├── Procfile             # Heroku deployment config
├── Dockerfile           # Docker configuration
├── docker-compose.yml   # Multi-container setup
├── .env.example         # Environment variables template
├── .gitignore           # Git ignore rules
├── setup.sh/.bat        # Automated setup scripts
├── static/              # CSS, JS, images
│   ├── styles.css       # Main stylesheet
│   └── favicon.ico      # Site icon
├── templates/           # HTML templates
│   ├── header.html      # Common header
│   ├── home.html        # Homepage
│   └── ...              # Tool-specific pages
└── uploads/             # File upload directory
```

## ⚙️ Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```env
# Flask Configuration
SECRET_KEY=your-secret-key
FLASK_ENV=development
FLASK_DEBUG=True

# Database
DATABASE_URL=sqlite:///data.db

# Email (optional)
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# External APIs (optional)
GOOGLE_API_KEY=your-google-api-key
```

## 🚀 Deployment

### Heroku
```bash
heroku create your-app-name
heroku config:set FLASK_ENV=production
git push heroku main
```

### Render/Railway
- Connect your GitHub repository
- Set environment variables
- Deploy automatically

### VPS/Cloud Server
```bash
# Install dependencies
sudo apt update && sudo apt install python3 python3-pip nginx

# Clone and setup
git clone https://github.com/akash2696762069/Toolflock.git
cd Toolflock
pip3 install -r requirements.txt

# Configure nginx and run with gunicorn
gunicorn --bind 0.0.0.0:5000 app:app
```

## 🔧 Development

### Adding New Tools

1. Create template in `templates/your_tool.html`
2. Add route in `app.py`
3. Update navigation in `templates/header.html`
4. Add tool to `templates/all_tools.html`

### Testing
```bash
python -m pytest tests/
```

### Code Formatting
```bash
black app.py
flake8 app.py
```

## 📈 Features in Development

- [ ] User authentication and accounts
- [ ] Tool usage analytics
- [ ] API endpoints for tools
- [ ] Batch processing capabilities
- [ ] Dark mode theme
- [ ] Multi-language support

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Flask](https://flask.palletsprojects.com/)
- Icons by [Font Awesome](https://fontawesome.com/)
- Styling inspired by modern design principles

## 📞 Support

- **Email:** akash980vk@gmail.com
- **GitHub Issues:** [Create an issue](https://github.com/akash2696762069/Toolflock/issues)
- **Documentation:** [Wiki](https://github.com/akash2696762069/Toolflock/wiki)

---

<div align="center">
  <strong>🌟 Built with ❤️ by Akash</strong><br>
  <em>Where Elegance Meets Utility</em>
</div>
