# Funlight Editor

# ⚠️ Work in Progress
This project is under active development and not production-ready yet.

A modern, intelligent code editor with integrated AI assistance powered by OpenAI's GPT models.

![Python Version](https://img.shields.io/badge/python-3.11%2B-blue)
![PySide6](https://img.shields.io/badge/PySide6-latest-green)
![License](https://img.shields.io/badge/license-MIT-blue)

## Features

- 🤖 **AI Assistant**
  - Code analysis and suggestions
  - Direct code editing capabilities
  - Natural language interaction
  - Context-aware responses

- 📝 **Code Editor**
  - Syntax highlighting
  - Line numbers
  - Dark theme
  - Multiple file support
  - Tab-based interface

- 🎨 **Modern UI**
  - Clean, minimalist design
  - Intuitive layout
  - Responsive interface
  - Customizable themes

## Requirements

- Python 3.11 or higher
- PySide6
- OpenAI API key

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/funlight-editor.git
cd funlight-editor
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your OpenAI API key:
   - Option 1: Set environment variable:
     ```bash
     set OPENAI_API_KEY=your-api-key-here
     ```
   - Option 2: Enter it when prompted in the application

## Usage

Run the editor:
```bash
python main.py
```

### AI Assistant Features

- **Code Analysis**: Click "Analyze" to get insights about your code
- **Suggestions**: Get AI-powered suggestions for improvements
- **Code Editing**: Let the AI help you modify your code
- **Chat Interface**: Ask questions and get help in natural language

### Keyboard Shortcuts

- `Enter`: Send message to AI
- `Shift + Enter`: New line in input field
- `Ctrl + N`: New file
- `Ctrl + O`: Open file
- `Ctrl + S`: Save file
- `Ctrl + Tab`: Switch between files

## Project Structure

```
funlight-editor/
├── main.py              # Main application entry point
├── chatgpt_api.py       # OpenAI API integration
├── gui/
│   ├── ai_assistant.py  # AI Assistant implementation
│   ├── editor_window.py # Main editor window
│   └── code_editor.py   # Code editor component
└── requirements.txt     # Project dependencies
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- OpenAI for the GPT API
- Qt/PySide6 for the GUI framework
- All contributors and users of the project

## Support

For support, please open an issue in the GitHub repository or contact the maintainers.
